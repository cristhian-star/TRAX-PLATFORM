from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import inspect
import unittest

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app import create_app, db
from app.config.config import TestingConfig
from app.models.audit_log import AuditLog
from app.models.payment_obligation import PaymentObligation
from app.models.payment_order import PaymentOrder
from app.models.professional import Professional
from app.models.user import User
from app.services.in_memory_psp_payment_order_creation_adapter import (
    InMemoryPSPPaymentOrderCreationAdapter,
)
from app.services.payment_order_persistence_service import (
    ActivePaymentOrderExistsError,
    cancel_payment_order,
    get_active_payment_order,
    get_payment_order,
    materialize_payment_order_expiration,
    register_or_get_payment_order,
)
from app.services.psp_payment_order_contract import (
    PaymentOrderCreationCommand,
    PaymentOrderIdempotencyConflictError,
)


class PaymentOrderPersistenceTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestingConfig)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.actor = User(
            nombre="Operator", email="operator@example.test", password="hash",
            rol="ADMIN",
        )
        self.professional = Professional(
            nombre="Professional", servicio="Service", zona="CABA"
        )
        db.session.add_all((self.actor, self.professional))
        db.session.flush()
        self.created_at = datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc)
        self.obligation = PaymentObligation(
            internal_reference="obligation-0001",
            amount=Decimal("1250.50"),
            currency="ARS",
        )
        db.session.add(self.obligation)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def _command(self, suffix="0001", **changes):
        values = dict(
            local_order_id=f"local-order-{suffix}",
            obligation_reference=self.obligation.internal_reference,
            professional_id=self.professional.id,
            amount=Decimal("1250.50"),
            currency="ARS",
            concept="Servicio acordado",
            external_reference=f"external-reference-{suffix}",
            idempotency_key=f"private-idempotency-key-{suffix}",
            created_at=self.created_at,
            expires_at=self.created_at + timedelta(hours=72),
        )
        values.update(changes)
        return PaymentOrderCreationCommand(**values)

    @staticmethod
    def _result(command):
        return InMemoryPSPPaymentOrderCreationAdapter().create_payment_order(command)

    def _register(self, command, now=None):
        return register_or_get_payment_order(
            db.session,
            self.obligation.id,
            command,
            self._result(command),
            actor_user_id=self.actor.id,
            clock=lambda: now or self.created_at,
        )

    def test_creation_replay_lookup_and_audit_are_durable_and_exact(self):
        command = self._command()
        first = self._register(command)
        replay = self._register(command, self.created_at + timedelta(hours=1))

        self.assertEqual(first.id, replay.id)
        self.assertEqual(get_payment_order(db.session, first.id).id, first.id)
        self.assertEqual(
            get_active_payment_order(
                db.session, self.obligation.id, clock=lambda: self.created_at
            ).id,
            first.id,
        )
        self.assertEqual(Decimal(first.amount), Decimal("1250.50"))
        self.assertEqual(first.currency, "ARS")
        self.assertEqual(first.status, "ACTIVE")
        self.assertEqual(
            ["PAYMENT_ORDER_CREATED"],
            [item.action for item in db.session.query(AuditLog).all()],
        )
        self.assertNotIn(command.idempotency_key, str(db.session.query(AuditLog).first().metadata_json))
        self.assertNotIn(first.checkout_url, str(db.session.query(AuditLog).first().metadata_json))

    def test_same_key_with_different_material_content_conflicts(self):
        command = self._command()
        self._register(command)
        changed = replace(command, concept="Otro servicio")
        with self.assertRaises(PaymentOrderIdempotencyConflictError):
            register_or_get_payment_order(
                db.session,
                self.obligation.id,
                changed,
                self._result(changed),
                actor_user_id=self.actor.id,
                clock=lambda: self.created_at,
            )

    def test_only_one_effectively_active_order_and_successor_after_expiry(self):
        first_command = self._command()
        first = self._register(first_command)
        second_command = self._command("0002")
        with self.assertRaises(ActivePaymentOrderExistsError):
            self._register(second_command, self.created_at + timedelta(hours=1))

        boundary = first_command.expires_at
        second_command = self._command(
            "0002",
            created_at=boundary,
            expires_at=boundary + timedelta(hours=72),
        )
        second = self._register(second_command, boundary)
        self.assertEqual(first.status, "EXPIRED")
        self.assertEqual(first.closed_at, first.expires_at)
        self.assertEqual(second.status, "ACTIVE")
        self.assertEqual(self._register(first_command, boundary).id, first.id)

    def test_expiration_boundary_and_cancellation_are_idempotent(self):
        order = self._register(self._command())
        before = materialize_payment_order_expiration(
            db.session,
            order.id,
            actor_user_id=self.actor.id,
            clock=lambda: self.created_at + timedelta(hours=72) - timedelta(microseconds=1),
        )
        self.assertEqual(before.status, "ACTIVE")
        expired = materialize_payment_order_expiration(
            db.session,
            order.id,
            actor_user_id=self.actor.id,
            clock=lambda: self.created_at + timedelta(hours=72),
        )
        self.assertEqual(expired.status, "EXPIRED")
        self.assertEqual(
            cancel_payment_order(
                db.session,
                order.id,
                actor_user_id=self.actor.id,
                clock=lambda: self.created_at + timedelta(hours=73),
            ).status,
            "EXPIRED",
        )

        successor_created_at = self.created_at + timedelta(hours=72)
        successor = self._register(
            self._command(
                "0002",
                created_at=successor_created_at,
                expires_at=successor_created_at + timedelta(hours=72),
            ),
            successor_created_at,
        )
        cancelled = cancel_payment_order(
            db.session,
            successor.id,
            actor_user_id=self.actor.id,
            clock=lambda: self.created_at + timedelta(hours=72, minutes=1),
        )
        original_closed_at = cancelled.closed_at
        self.assertEqual(cancelled.status, "CANCELLED")
        self.assertEqual(
            cancel_payment_order(
                db.session,
                successor.id,
                actor_user_id=self.actor.id,
                clock=lambda: self.created_at + timedelta(hours=80),
            ).closed_at,
            original_closed_at,
        )

    def test_outer_rollback_removes_order_and_audit_and_session_recovers(self):
        Session = sessionmaker(bind=db.engine, expire_on_commit=False)
        writer = Session()
        verifier = Session()
        try:
            command = self._command()
            register_or_get_payment_order(
                writer,
                self.obligation.id,
                command,
                self._result(command),
                actor_user_id=self.actor.id,
                clock=lambda: self.created_at,
            )
            writer.rollback()
            self.assertEqual(verifier.query(PaymentOrder).count(), 0)
            self.assertEqual(verifier.query(AuditLog).count(), 0)
            writer.add(User(
                nombre="Recovered", email="recovered@example.test", password="hash"
            ))
            writer.flush()
        finally:
            writer.rollback()
            writer.close()
            verifier.close()

    def test_second_session_cancellation_reloads_locked_order_without_duplicate_audit(self):
        order = self._register(self._command())
        db.session.commit()
        Session = sessionmaker(bind=db.engine, expire_on_commit=False)
        stale_session = Session()
        winner_session = Session()
        try:
            stale_order = stale_session.get(PaymentOrder, order.id)
            self.assertEqual(stale_order.status, "ACTIVE")
            first = cancel_payment_order(
                winner_session,
                order.id,
                actor_user_id=self.actor.id,
                clock=lambda: self.created_at + timedelta(hours=1),
            )
            winner_session.commit()
            cancelled_at = first.cancelled_at

            replay = cancel_payment_order(
                stale_session,
                order.id,
                actor_user_id=self.actor.id,
                clock=lambda: self.created_at + timedelta(hours=2),
            )
            stale_session.commit()
            self.assertEqual(replay.cancelled_at, cancelled_at)
        finally:
            stale_session.close()
            winner_session.close()
        verifier = Session()
        try:
            self.assertEqual(
                verifier.query(AuditLog).filter_by(
                    entity_type="payment_order",
                    action="PAYMENT_ORDER_CANCELLED",
                ).count(),
                1,
            )
        finally:
            verifier.close()

    def _raw_order_values(self, suffix="invalid"):
        command = self._command()
        return dict(
            obligation_id=self.obligation.id,
            professional_id=self.professional.id,
            local_order_id=f"local-{suffix}",
            external_reference=f"external-{suffix}",
            idempotency_key=f"invalid-idempotency-{suffix}",
            amount=Decimal("1250.50"),
            currency="ARS",
            concept=command.concept,
            provider="fake",
            live_mode=False,
            external_order_id=f"provider-{suffix}",
            checkout_url="https://checkout.example.test/order",
            status="ACTIVE",
            created_at=self.created_at.replace(tzinfo=None),
            expires_at=(self.created_at + timedelta(hours=72)).replace(tzinfo=None),
        )

    def test_database_constraints_reject_each_invalid_state_shape_independently(self):
        one_hour = (self.created_at + timedelta(hours=1)).replace(tzinfo=None)
        expires = (self.created_at + timedelta(hours=72)).replace(tzinfo=None)
        cases = (
            {"status": "ACTIVE", "closed_at": one_hour},
            {"status": "ACTIVE", "cancelled_at": one_hour},
            {"status": "EXPIRED", "closed_at": None},
            {"status": "EXPIRED", "closed_at": expires, "cancelled_at": one_hour},
            {"status": "CANCELLED", "closed_at": None, "cancelled_at": one_hour},
            {"status": "CANCELLED", "closed_at": one_hour, "cancelled_at": None},
            {
                "status": "CANCELLED",
                "closed_at": one_hour,
                "cancelled_at": one_hour + timedelta(minutes=1),
            },
        )
        for index, changes in enumerate(cases):
            with self.subTest(changes=changes):
                values = self._raw_order_values(str(index))
                values.update(changes)
                db.session.add(PaymentOrder(**values))
                with self.assertRaises(IntegrityError):
                    db.session.flush()
                db.session.rollback()

    def test_database_constraints_reject_amount_currency_and_expiry_independently(self):
        cases = (
            {"amount": Decimal("0")},
            {"amount": Decimal("1.001")},
            {"currency": "USD"},
            {"expires_at": (self.created_at + timedelta(hours=71)).replace(tzinfo=None)},
        )
        for index, changes in enumerate(cases):
            with self.subTest(changes=changes):
                values = self._raw_order_values(f"scalar-{index}")
                values.update(changes)
                db.session.add(PaymentOrder(**values))
                with self.assertRaises(IntegrityError):
                    db.session.flush()
                db.session.rollback()

    def test_service_has_no_commit_rollback_or_external_adapter_call(self):
        import app.services.payment_order_persistence_service as service

        source = inspect.getsource(service)
        self.assertNotIn(".commit(", source)
        self.assertNotIn(".rollback(", source)
        self.assertNotIn("create_payment_order(", source)


if __name__ == "__main__":
    unittest.main()
