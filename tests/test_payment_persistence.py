import inspect
import unittest
from decimal import Decimal

from sqlalchemy.exc import IntegrityError

from app import create_app, db
from app.config.config import TestingConfig
from app.models.payment_attempt import PaymentAttemptRecord
from app.models.payment_obligation import PaymentObligation
from app.services.payment_orchestration import (
    PaymentObligation as PaymentObligationRequest,
    PaymentOrchestrationResult,
    PaymentOutcome,
)
from app.services.payment_persistence_service import (
    OBLIGATION_REFERENCE_CONSTRAINT,
    PaymentPersistenceConflictError,
    _is_postgresql_constraint_violation,
    apply_reconciliation,
    create_or_get_obligation,
    get_attempts,
    register_or_get_attempt,
)
from app.services.psp_contract import PaymentAttemptStatus


class PaymentPersistenceTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestingConfig)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    @staticmethod
    def _request(reference="obligation-001", amount="1250.500", key="key-001"):
        return PaymentObligationRequest(reference, Decimal(amount), "ARS", key)

    @staticmethod
    def _result(request, outcome=PaymentOutcome.APPROVED, attempt_id="attempt-001"):
        status = None if outcome is PaymentOutcome.RECONCILIATION_REQUIRED else PaymentAttemptStatus(outcome.value)
        return PaymentOrchestrationResult(
            request.internal_reference,
            request.amount,
            request.currency,
            request.idempotency_key,
            attempt_id,
            status,
            outcome,
            outcome is PaymentOutcome.RECONCILIATION_REQUIRED,
        )

    def test_obligation_replay_preserves_decimal_and_conflict_is_explicit(self):
        request = self._request()
        first = create_or_get_obligation(db.session, request)
        replay = create_or_get_obligation(db.session, request)
        self.assertEqual(first.id, replay.id)
        self.assertEqual(Decimal(first.amount), request.amount)
        with self.assertRaises(PaymentPersistenceConflictError):
            create_or_get_obligation(db.session, self._request(amount="1250.501"))

    def test_attempt_replay_query_and_conflict_are_explicit(self):
        request = self._request()
        obligation = create_or_get_obligation(db.session, request)
        result = self._result(request)
        first = register_or_get_attempt(db.session, obligation, result)
        replay = register_or_get_attempt(db.session, obligation, result)
        self.assertEqual(first.id, replay.id)
        self.assertEqual([first.id], [item.id for item in get_attempts(db.session, obligation.id)])
        changed = self._result(request, PaymentOutcome.REJECTED, "attempt-002")
        with self.assertRaises(PaymentPersistenceConflictError):
            register_or_get_attempt(db.session, obligation, changed)

    def test_reconciliation_allows_only_forward_or_idempotent_transitions(self):
        request = self._request()
        obligation = create_or_get_obligation(db.session, request)
        uncertain = self._result(request, PaymentOutcome.RECONCILIATION_REQUIRED, None)
        attempt = register_or_get_attempt(db.session, obligation, uncertain)
        pending = self._result(request, PaymentOutcome.PENDING, "provider-001")
        reconciled = apply_reconciliation(db.session, attempt.id, pending)
        self.assertEqual(reconciled.orchestration_result, "PENDING")
        self.assertEqual(reconciled.external_attempt_id, "provider-001")
        self.assertEqual(apply_reconciliation(db.session, attempt.id, pending).id, attempt.id)
        approved = self._result(request, PaymentOutcome.APPROVED, "provider-001")
        apply_reconciliation(db.session, attempt.id, approved)
        with self.assertRaises(PaymentPersistenceConflictError):
            apply_reconciliation(db.session, attempt.id, pending)

    def test_same_state_can_complete_missing_external_identifier_but_not_replace_it(self):
        request = self._request()
        obligation = create_or_get_obligation(db.session, request)
        uncertain = self._result(request, PaymentOutcome.RECONCILIATION_REQUIRED, None)
        attempt = register_or_get_attempt(db.session, obligation, uncertain)
        completed = self._result(request, PaymentOutcome.RECONCILIATION_REQUIRED, "provider-001")
        apply_reconciliation(db.session, attempt.id, completed)
        self.assertEqual(attempt.external_attempt_id, "provider-001")
        with self.assertRaises(PaymentPersistenceConflictError):
            apply_reconciliation(
                db.session,
                attempt.id,
                self._result(request, PaymentOutcome.RECONCILIATION_REQUIRED, "provider-002"),
            )

    def test_database_constraints_reject_invalid_rows_and_foreign_keys(self):
        db.session.add(PaymentObligation(internal_reference="bad", amount=Decimal("0"), currency="ARS"))
        with self.assertRaises(IntegrityError):
            db.session.flush()
        db.session.rollback()

        db.session.execute(db.text("PRAGMA foreign_keys=ON"))
        db.session.add(PaymentAttemptRecord(
            obligation_id=999999,
            idempotency_key="missing-obligation",
            external_attempt_id=None,
            financial_status=None,
            orchestration_result="RECONCILIATION_REQUIRED",
            requires_reconciliation=True,
        ))
        with self.assertRaises(IntegrityError):
            db.session.flush()

    def test_outer_transaction_controls_atomic_rollback_and_session_recovery(self):
        request = self._request()
        obligation = create_or_get_obligation(db.session, request)
        register_or_get_attempt(db.session, obligation, self._result(request))
        db.session.rollback()
        self.assertEqual(db.session.query(PaymentObligation).count(), 0)
        self.assertEqual(db.session.query(PaymentAttemptRecord).count(), 0)
        self.assertIsNotNone(create_or_get_obligation(db.session, self._request("obligation-002")))

    def test_service_never_commits_or_calls_a_psp(self):
        import app.services.payment_persistence_service as service

        source = inspect.getsource(service)
        self.assertNotIn(".commit(", source)
        self.assertNotIn("PSPAdapter", source)
        self.assertNotIn("create_attempt(", source)

    def test_obligation_replay_requires_exact_structured_diagnostics(self):
        class Diagnostic:
            def __init__(self, constraint_name):
                self.constraint_name = constraint_name

        class DriverError(Exception):
            def __init__(self, sqlstate, constraint_name, with_diag=True):
                self.sqlstate = sqlstate
                if with_diag:
                    self.diag = Diagnostic(constraint_name)

        def integrity(sqlstate, constraint_name, with_diag=True):
            return IntegrityError(
                "INSERT", {}, DriverError(sqlstate, constraint_name, with_diag)
            )

        self.assertTrue(_is_postgresql_constraint_violation(
            integrity("23505", OBLIGATION_REFERENCE_CONSTRAINT),
            "23505", OBLIGATION_REFERENCE_CONSTRAINT,
        ))
        for error in (
            integrity("23514", "ck_payment_obligations_amount_positive"),
            integrity("23505", "uq_other_constraint"),
            integrity("23505", OBLIGATION_REFERENCE_CONSTRAINT, False),
        ):
            with self.subTest(error=error.orig):
                self.assertFalse(_is_postgresql_constraint_violation(
                    error, "23505", OBLIGATION_REFERENCE_CONSTRAINT
                ))


if __name__ == "__main__":
    unittest.main()
