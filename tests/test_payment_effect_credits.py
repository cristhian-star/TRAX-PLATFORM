from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal, localcontext
import unittest
from threading import Event
from sqlalchemy import event as sql_event
from unittest.mock import Mock, patch

from app.config.config import Config
from app.models.contract_request import ContractRequest
from app.models.payment_order import PaymentOrder
from app.models.subscription import Subscription
from app.models.verification_request import VerificationRequest
from app.models.payment_order_reconciliation import PaymentOrderReconciliationEvidence as Evidence
from app.models.payment_effect import (
    TransactionalCreditPolicy as PolicyRecord, PaymentEffectDecision as Decision,
    TransactionalCommission as Commission, TransactionalCreditLot as Lot,
    TransactionalCreditGrant as Grant, TransactionalCreditAllocation as Allocation,
    PaymentEffectAudit as Audit, PaymentEffectPaymentClaim as PaymentClaim,
)
from app.services.payment_effect_service import (
    CreditPolicy, EffectiveCommission, PaymentEffectService, PaymentEffectUnavailableError,
    build_payment_effect_service,
)
from app.services.payment_order_application_service import PaymentOrderApplicationService
from app.services.in_memory_psp_payment_order_creation_adapter import InMemoryPSPPaymentOrderCreationAdapter
from tests import test_mercadopago_order_reconciliation as fixtures


class PaymentEffectCreditsTest(unittest.TestCase):
    tearDown = fixtures.ReconciliationTest.tearDown
    event = fixtures.ReconciliationTest.event
    receive = fixtures.ReconciliationTest.receive
    count = fixtures.ReconciliationTest.count
    remote = fixtures.ReconciliationTest.remote
    credential = fixtures.ReconciliationTest.credential

    def setUp(self):
        fixtures.ReconciliationTest.setUp(self)
        self.now += timedelta(minutes=1)
        with self.factory.Session.begin() as session:
            session.add(VerificationRequest(user_id=self.actor, tipo_usuario="PROFESIONAL", estado="APROBADO"))
        self.policy = CreditPolicy("fictional-v1", Decimal("100.00"), "ARS")
        self.policy_provider = Mock(return_value=self.policy)
        self.proofs = {}
        self.proof_provider = Mock(side_effect=self._proof)
        self.service = PaymentEffectService(session_factory=self.factory, policy_provider=self.policy_provider,
            commission_provider=self.proof_provider, effects_enabled=True, commission_enabled=True, clock=lambda: self.now)
        self.counter = 0

    def _proof(self, evidence_id):
        self.assertEqual(self.factory.open_sessions, 0)
        return self.proofs.get(evidence_id)

    def evidence(self, amount="100.00", timing="BEFORE_LOCAL_EXPIRY", payment_id=None):
        """Synthetic trusted timeliness; 4E's UNKNOWN is never silently upgraded."""
        if self.counter:
            with self.factory.Session.begin() as session:
                contract = session.get(ContractRequest, self.contract)
                new = ContractRequest(cliente_id=contract.cliente_id, professional_id=self.professional,
                    professional_user_id=self.actor, servicio="Fixture", estado="CONFIRMADA", precio_acordado=Decimal("1250.50"))
                session.add(new)
                session.flush()
                contract_id = new.id
            application = PaymentOrderApplicationService(session_factory=self.factory,
                adapter=InMemoryPSPPaymentOrderCreationAdapter(), clock=lambda: fixtures.NOW)
            application.create_order(actor_user_id=self.actor, contract_request_id=contract_id)
            with self.factory.Session.begin() as session:
                order = session.query(PaymentOrder).order_by(PaymentOrder.id.desc()).first()
                order.provider, order.external_order_id = "mercadopago", f"ORDfixture{self.counter}"
                self.context = replace(self.context, payment_order_id=order.id, external_order_id=order.external_order_id,
                                       external_reference=order.external_reference)
                self.order_id = order.id
            self.content = fixtures.payload(self.context)
            self.content["transactions"]["payments"][0]["id"] = f"PAYfixture{self.counter}"
        if payment_id is not None:
            self.content["transactions"]["payments"][0]["id"] = payment_id
        self.counter += 1
        work_id = self.receive(f"evidence-{self.counter}", resource=self.context.external_order_id)
        self.assertEqual(self.processor.process(work_id), "DONE")
        with self.factory.Session.begin() as session:
            evidence = session.query(Evidence).filter_by(payment_order_id=self.context.payment_order_id).one()
            evidence.timing = timing
            identity, digest = evidence.id, evidence.snapshot_hash
        self.proofs[identity] = EffectiveCommission(identity, digest, self.context.payment_order_id,
            self.professional, self.context.external_order_id, f"settlement-{self.counter}", Decimal(amount),
            "ARS", False, fixtures.NOW.replace(tzinfo=None) + timedelta(seconds=1), fixtures.NOW.replace(tzinfo=None) + timedelta(seconds=1))
        return identity

    def balance(self):
        with self.factory.Session() as session, localcontext() as context:
            context.prec = 128
            return sum((lot.remaining_amount for lot in session.query(Lot).all()), Decimal(0))

    def subscription(self, source="SUBSCRIPTION", days=10):
        with self.factory.Session.begin() as session:
            item = Subscription(user_id=self.actor, plan="PRO", estado="ACTIVA", source_type=source,
                started_at=self.now - timedelta(days=1), expires_at=self.now + timedelta(days=days), auto_renew=False)
            session.add(item)
            session.flush()
            return item.id

    def test_missing_policy_has_no_default_or_extension(self):
        identity = self.evidence()
        self.policy_provider.return_value = None
        self.assertEqual(self.service.apply_evidence(identity), "PENDING_POLICY")
        self.assertEqual(self.count(Lot), 0)
        self.assertEqual(self.count(Grant), 0)
        with self.factory.Session() as session:
            self.assertIsNone(session.query(Commission).one().net_amount)

    def test_missing_trusted_commission_and_provider_exception_are_pending(self):
        identity = self.evidence()
        for failure in (None, RuntimeError("PRIVATE-COMMISSION-MARKER")):
            self.proof_provider.side_effect = failure if failure else None
            self.proof_provider.return_value = None
            self.assertEqual(self.service.apply_evidence(identity), "PENDING_POLICY")
        self.assertEqual(self.count(Lot), 0)

    def test_policy_exception_is_pending_without_secret(self):
        identity = self.evidence()
        self.policy_provider.side_effect = RuntimeError("PRIVATE-POLICY-MARKER")
        self.assertEqual(self.service.apply_evidence(identity), "PENDING_POLICY")
        with self.factory.Session() as session:
            self.assertNotIn("PRIVATE", repr(session.query(Decision).one().reason))

    def test_explicit_policy_validation_rejects_floats_zero_currency_and_version(self):
        for price, currency, version in ((100.0,"ARS","v1"),(Decimal(0),"ARS","v1"),
                (Decimal("1.001"),"ARS","v1"),(Decimal("NaN"),"ARS","v1"),
                (Decimal(1),"USD","v1"),(Decimal(1),"ARS","")):
            with self.assertRaises(ValueError):
                CreditPolicy(version, price, currency)

    def test_complete_credit_grants_exactly_30_days_and_audits(self):
        identity = self.evidence()
        self.assertEqual(self.service.apply_evidence(identity), "ACCRUED")
        with self.factory.Session() as session:
            grant = session.query(Grant).one()
            subscription = session.get(Subscription, grant.subscription_id)
            self.assertEqual(grant.expires_at - grant.starts_at, timedelta(days=30))
            self.assertEqual(subscription.source_type, "TRANSACTIONAL")
            self.assertEqual(grant.credits_consumed, 1)
            self.assertEqual(session.query(Allocation).one().amount, Decimal("100.00"))
        self.assertEqual(self.balance(), Decimal(0))
        self.assertEqual(self.count(Audit), 2)
        from app.services.subscription_service import has_pro_access
        self.assertTrue(has_pro_access(self.actor, now=self.now))
        self.assertFalse(has_pro_access(self.actor, now=self.now + timedelta(days=30)))

    def test_replay_same_evidence_and_same_payment_snapshot_no_double_credit(self):
        identity = self.evidence()
        self.assertEqual(self.service.apply_evidence(identity), "ACCRUED")
        self.assertEqual(self.service.apply_evidence(identity), "REPLAY")
        self.content["last_updated_date"] = (fixtures.NOW + timedelta(seconds=2)).isoformat()
        work_id = self.receive("new-snapshot", resource=self.context.external_order_id)
        self.assertEqual(self.processor.process(work_id), "DONE")
        with self.factory.Session.begin() as session:
            other = session.query(Evidence).order_by(Evidence.id.desc()).first()
            other.timing = "BEFORE_LOCAL_EXPIRY"
            self.proofs[other.id] = replace(self.proofs[identity], evidence_id=other.id, snapshot_hash=other.snapshot_hash)
            other_id = other.id
        self.assertEqual(self.service.apply_evidence(other_id), "REPLAY")
        self.assertEqual(self.count(Lot), 1)
        self.assertEqual(self.count(Grant), 1)

    def test_pending_policy_can_resume_once_policy_and_proof_exist(self):
        identity = self.evidence()
        self.policy_provider.return_value = None
        self.assertEqual(self.service.apply_evidence(identity), "PENDING_POLICY")
        self.policy_provider.return_value = self.policy
        self.assertEqual(self.service.apply_evidence(identity), "ACCRUED")
        self.assertEqual(self.count(Commission), 1)
        self.assertEqual(self.count(Lot), 1)

    def test_decimal_accumulation_conversion_and_remnant(self):
        self.assertEqual(self.service.apply_evidence(self.evidence("60.01")), "ACCRUED")
        self.assertEqual(self.count(Grant), 0)
        self.assertEqual(self.service.apply_evidence(self.evidence("50.02")), "ACCRUED")
        self.assertEqual(self.balance(), Decimal("10.03"))
        self.assertEqual(self.count(Grant), 1)
        with self.factory.Session() as session:
            amounts = [row.amount for row in session.query(Allocation).order_by(Allocation.id)]
            self.assertEqual(amounts, [Decimal("60.01"), Decimal("39.99")])

    def test_fractional_credit_contributions_never_round_up(self):
        self.service.apply_evidence(self.evidence("99.99"))
        self.assertEqual(self.count(Grant), 0)
        self.service.apply_evidence(self.evidence("0.01"))
        self.assertEqual(self.count(Grant), 1)
        self.assertEqual(self.balance(), Decimal(0))

    def test_exact_large_policy_storage_has_no_binary_rounding(self):
        huge = Decimal("123456789012345678901234567890.01")
        with self.factory.Session.begin() as session:
            session.add(PolicyRecord(version="large", currency="ARS", threshold=huge))
        with self.factory.Session() as session:
            self.assertEqual(session.get(PolicyRecord,"large").threshold,huge)

    def test_active_transactional_period_not_interrupted_and_excess_preserved(self):
        self.subscription("TRANSACTIONAL", days=5)
        self.service.apply_evidence(self.evidence("200.00"))
        self.assertEqual(self.count(Grant), 0)
        self.assertEqual(self.service.consume_credit(self.professional), "ACTIVE_PERIOD")
        self.now += timedelta(days=5)
        self.assertEqual(self.service.consume_credit(self.professional), "GRANTED")
        self.assertEqual(self.balance(), Decimal("100.00"))
        self.assertEqual(self.service.consume_credit(self.professional), "ACTIVE_PERIOD")
        self.now += timedelta(days=30)
        self.assertEqual(self.service.consume_credit(self.professional), "GRANTED")
        self.assertEqual(self.count(Grant), 2)

    def test_expired_lot_40_days_not_rejuvenated_by_new_contribution(self):
        identity = self.evidence("60.00")
        self.service.apply_evidence(identity)
        with self.factory.Session() as session:
            lot = session.query(Lot).one()
            self.assertEqual(lot.expires_at - lot.credited_at, timedelta(days=40))
        self.now += timedelta(days=40)
        self.assertEqual(self.service.consume_credit(self.professional), "INSUFFICIENT_CREDITS")
        self.assertEqual(self.balance(), Decimal("60.00"))

    def test_paid_subscription_exemption_no_commission_or_credit(self):
        self.subscription()
        self.assertEqual(self.service.apply_evidence(self.evidence()), "EXEMPT")
        self.assertEqual(self.count(Lot), 0)
        with self.factory.Session() as session:
            self.assertEqual(session.query(Commission).one().status,"EXEMPT")
            self.assertIsNone(session.query(Commission).one().net_amount)

    def test_flags_default_and_composition_never_enable_effects(self):
        self.assertIs(Config.PAYMENT_EFFECTS_ENABLED,False)
        self.assertIs(Config.TRANSACTIONAL_COMMISSION_ENABLED,False)
        service = build_payment_effect_service(app=self.app,session_factory=self.factory)
        self.assertEqual(service.apply_evidence(123),"DISABLED")
        self.assertEqual(service.consume_credit(self.professional),"DISABLED")

    def test_commission_flag_off_blocks_credit_even_with_providers(self):
        identity=self.evidence()
        self.service._commission_enabled=False
        self.assertEqual(self.service.apply_evidence(identity),"PENDING_POLICY")
        self.proof_provider.assert_not_called()
        self.assertEqual(self.count(Lot),0)

    def test_late_and_uncertain_timing_never_create_credit(self):
        for timing in ("UNKNOWN","AFTER_LOCAL_EXPIRY"):
            self.assertEqual(self.service.apply_evidence(self.evidence(timing=timing)),"PENDING_REVIEW")
        self.assertEqual(self.count(Lot),0)

    def test_proof_mismatch_or_absent_effective_amount_fails_closed(self):
        identity=self.evidence()
        original=self.proofs[identity]
        for changes in ({"professional_id":999},{"currency":"USD"},{"net_amount":Decimal(0)},
                {"net_amount":100.0},{"snapshot_hash":"x"*64},{"external_identity":"../bad"}):
            self.proofs[identity]=replace(original,**changes)
            self.assertEqual(self.service.apply_evidence(identity),"PENDING_POLICY")
        self.assertEqual(self.count(Lot),0)

    def test_policy_version_redefinition_and_price_change_are_reviewed(self):
        self.service.apply_evidence(self.evidence("60.00"))
        self.policy_provider.return_value=CreditPolicy("fictional-v1",Decimal("80.00"),"ARS")
        self.assertEqual(self.service.apply_evidence(self.evidence("50.00")),"PENDING_REVIEW")
        self.policy_provider.return_value=CreditPolicy("fictional-v2",Decimal("80.00"),"ARS")
        self.service.apply_evidence(self.evidence("50.00"))
        self.assertEqual(self.service.consume_credit(self.professional),"PENDING_REVIEW")
        self.assertEqual(self.count(Grant),0)

    def test_reversal_after_grant_reviews_without_revocation_or_compensation(self):
        identity=self.evidence("200.00")
        self.service.apply_evidence(identity)
        self.content["transactions"]["refunds"]=[dict(id="REF1",transaction_id="PAY123",amount="1.00",status="processed")]
        work_id=self.receive("reversal",resource=self.context.external_order_id)
        self.assertEqual(self.processor.process(work_id),"DONE")
        with self.factory.Session() as session:
            latest=session.query(Evidence).order_by(Evidence.id.desc()).first().id
        self.assertEqual(self.service.apply_evidence(latest),"PENDING_REVIEW")
        self.assertEqual(self.balance(),Decimal("100.00"))
        self.now+=timedelta(days=30)
        self.assertEqual(self.service.consume_credit(self.professional),"PENDING_REVIEW")
        with self.factory.Session() as session:
            self.assertEqual(session.query(Subscription).one().estado,"ACTIVA")
        self.assertEqual(self.count(Grant),1)

    def test_refund_total_chargeback_and_out_of_order_approval_block(self):
        identity=self.evidence()
        self.content.update(status="charged_back",status_detail="accredited")
        self.content["transactions"]["chargebacks"]=[dict(id="CBK1",transaction_id="PAY123",status="in_process")]
        work_id=self.receive("chargeback",resource=self.context.external_order_id)
        self.assertEqual(self.processor.process(work_id),"DONE")
        self.assertEqual(self.service.apply_evidence(identity),"PENDING_REVIEW")
        self.assertEqual(self.count(Lot),0)

    def test_repeated_consume_and_concurrent_replay_do_not_double_apply(self):
        identity=self.evidence()
        # Concurrent provider does not assert global sessions of another worker.
        self.service._commission=lambda eid:self.proofs[eid]
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes=list(pool.map(self.service.apply_evidence,[identity,identity]))
        self.assertCountEqual(outcomes,["ACCRUED","REPLAY"])
        self.assertEqual(self.count(Grant),1)
        self.assertEqual(self.count(Lot),1)

    def test_concurrent_distinct_contributions_no_lost_balance(self):
        identities=[self.evidence("60.00"),self.evidence("60.00")]
        self.service._commission=lambda eid:self.proofs[eid]
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(list(pool.map(self.service.apply_evidence,identities)),["ACCRUED","ACCRUED"])
        self.assertEqual(self.balance(),Decimal("20.00"))
        self.assertEqual(self.count(Grant),1)

    def test_rollback_after_conversion_and_public_error_has_no_secret_context(self):
        identity=self.evidence()
        from app.services import payment_effect_service as effects
        original=effects._decision
        def crash(*args):
            original(*args)
            raise RuntimeError("PRIVATE-ROLLBACK-MARKER")
        with patch.object(effects,"_decision",side_effect=crash),self.assertRaises(PaymentEffectUnavailableError) as caught:
            self.service.apply_evidence(identity)
        error=caught.exception
        self.assertIsNone(error.__context__)
        self.assertIsNone(error.__cause__)
        self.assertNotIn("PRIVATE",repr(error.args))
        for model in (Commission,Lot,Grant,Allocation,Decision,Audit,PolicyRecord,PaymentClaim):
            self.assertEqual(self.count(model),0)
        self.assertEqual(self.service.apply_evidence(identity),"ACCRUED")

    def test_unverified_owner_does_not_receive_credit(self):
        identity=self.evidence()
        with self.factory.Session.begin() as session:
            session.query(VerificationRequest).delete()
        self.assertEqual(self.service.apply_evidence(identity),"NOT_ELIGIBLE")
        self.assertEqual(self.count(Lot),0)

    def test_commission_identity_collision_different_orders_reviewed(self):
        identity=self.evidence("60.00")
        self.service.apply_evidence(identity)
        other=self.evidence("60.00")
        self.proofs[other]=replace(self.proofs[other],external_identity=self.proofs[identity].external_identity)
        self.assertEqual(self.service.apply_evidence(other),"PENDING_REVIEW")
        self.assertEqual(self.balance(),Decimal("60.00"))

    def test_full_refund_before_grant_is_reviewed(self):
        identity=self.evidence()
        self.content.update(status="refunded",status_detail="refunded")
        self.content["transactions"]["refunds"]=[dict(id="REFtotal",transaction_id="PAY123",amount="1250.50",status="processed")]
        work_id=self.receive("total-refund",resource=self.context.external_order_id)
        self.assertEqual(self.processor.process(work_id),"DONE")
        self.assertEqual(self.service.apply_evidence(identity),"PENDING_REVIEW")
        self.assertEqual(self.count(Grant),0)

    def test_future_paid_source_is_preserved_without_overlapping_grant(self):
        with self.factory.Session.begin() as session:
            session.add(Subscription(user_id=self.actor,plan="PRO",estado="ACTIVA",source_type="SUBSCRIPTION",
                started_at=self.now+timedelta(days=1),expires_at=self.now+timedelta(days=31)))
        self.service.apply_evidence(self.evidence())
        self.assertEqual(self.count(Grant),0)
        self.assertEqual(self.balance(),Decimal("100.00"))
        self.assertEqual(self.service.consume_credit(self.professional),"PENDING_REVIEW")

    def test_concurrent_consumption_at_expiry_grants_only_one_period(self):
        self.subscription("TRANSACTIONAL",days=1)
        self.service.apply_evidence(self.evidence("200.00"))
        self.now+=timedelta(days=1)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(self.service.consume_credit,[self.professional,self.professional]))
        self.assertCountEqual(results,["GRANTED","ACTIVE_PERIOD"])
        self.assertEqual(self.count(Grant),1)
        self.assertEqual(self.balance(),Decimal("100.00"))

    def test_new_contribution_does_not_rejuvenate_older_lot(self):
        first=self.evidence("60.00")
        self.service.apply_evidence(first)
        old_expiry=self.now+timedelta(days=40)
        self.now+=timedelta(days=1)
        second=self.evidence("10.00")
        self.service.apply_evidence(second)
        with self.factory.Session() as session:
            lots=session.query(Lot).order_by(Lot.id).all()
            self.assertEqual(lots[0].expires_at,old_expiry)
            self.assertEqual(lots[1].expires_at,old_expiry+timedelta(days=1))
        self.now=old_expiry
        self.assertEqual(self.service.consume_credit(self.professional),"INSUFFICIENT_CREDITS")

    def test_quarantine_after_accrual_blocks_consumption(self):
        identity=self.evidence("60.00")
        self.service.apply_evidence(identity)
        self.receive("evidence-1",digest="b"*64,resource=self.context.external_order_id)
        self.assertEqual(self.service.apply_evidence(identity),"PENDING_REVIEW")
        self.assertEqual(self.service.consume_credit(self.professional),"PENDING_REVIEW")
        self.assertEqual(self.balance(),Decimal("60.00"))

    def test_commit_failure_rolls_back_every_effect_and_can_resume(self):
        identity=self.evidence()
        from sqlalchemy.orm import SessionTransaction
        original=SessionTransaction.commit
        def fail(transaction,*args,**kwargs):
            if transaction.session.new:
                raise RuntimeError("PRIVATE-COMMIT")
            return original(transaction,*args,**kwargs)
        with patch.object(SessionTransaction,"commit",side_effect=fail,autospec=True),self.assertRaises(PaymentEffectUnavailableError) as caught:
            self.service.apply_evidence(identity)
        self.assertIsNone(caught.exception.__context__)
        self.assertIsNone(caught.exception.__cause__)
        self.assertNotIn("PRIVATE",repr(caught.exception))
        self.assertEqual(self.count(Grant),0)
        self.assertEqual(self.count(Lot),0)
        self.assertEqual(self.service.apply_evidence(identity),"ACCRUED")

    def test_effective_commission_date_does_not_replace_payment_date(self):
        identity=self.evidence()
        self.now+=timedelta(days=4)
        self.proofs[identity]=replace(self.proofs[identity],effective_at=self.now)
        self.assertEqual(self.service.apply_evidence(identity),"ACCRUED")
        self.assertEqual(self.count(Grant),1)

    def test_commission_contradiction_is_durable_and_replay_cannot_clear_review(self):
        identity=self.evidence("200.00")
        self.service.apply_evidence(identity)
        original=self.proofs[identity]
        self.proofs[identity]=replace(original,net_amount=Decimal("201.00"))
        self.assertEqual(self.service.apply_evidence(identity),"PENDING_REVIEW")
        self.proofs[identity]=original
        self.assertEqual(self.service.apply_evidence(identity),"PENDING_REVIEW")
        self.now+=timedelta(days=30)
        self.assertEqual(self.service.consume_credit(self.professional),"PENDING_REVIEW")
        self.assertEqual(self.balance(),Decimal("100.00"))
        self.assertEqual(self.count(Grant),1)

    def test_financial_payment_identity_cannot_fund_another_order(self):
        self.service.apply_evidence(self.evidence("60.00"))
        second=self.evidence("60.00",payment_id="PAY123")
        self.assertEqual(self.service.apply_evidence(second),"PENDING_REVIEW")
        self.assertEqual(self.balance(),Decimal("60.00"))
        self.assertEqual(self.count(Lot),1)

    def test_trusted_late_payment_date_is_reviewed_not_converted(self):
        identity=self.evidence()
        self.now+=timedelta(days=4)
        self.proofs[identity]=replace(self.proofs[identity],paid_at=self.now,effective_at=self.now)
        self.assertEqual(self.service.apply_evidence(identity),"PENDING_REVIEW")
        self.assertEqual(self.count(Lot),0)

    def test_hash_tampering_and_incomplete_payment_cannot_authorize_credit(self):
        identity=self.evidence()
        with self.factory.Session.begin() as session:
            evidence=session.get(Evidence,identity)
            changed=dict(evidence.snapshot)
            changed["total_paid_amount"]="1.00"
            evidence.snapshot=changed
        self.assertEqual(self.service.apply_evidence(identity),"PENDING_REVIEW")
        self.assertEqual(self.count(Lot),0)

    def test_backdated_paid_source_reviews_prior_credit_without_reversing_it(self):
        identity=self.evidence("200.00")
        self.service.apply_evidence(identity)
        self.subscription()
        self.assertEqual(self.service.apply_evidence(identity),"PENDING_REVIEW")
        self.assertEqual(self.count(Grant),1)
        self.assertEqual(self.balance(),Decimal("100.00"))

    def test_populated_ledger_downgrade_preserves_grants_and_provenance(self):
        self.service.apply_evidence(self.evidence())
        from alembic import command
        from alembic.config import Config as AlembicConfig
        from pathlib import Path
        import os
        config=AlembicConfig(str(Path(__file__).resolve().parents[1]/"alembic.ini"))
        with patch.dict(os.environ,{"DATABASE_URL":str(self.engine.url)}):
            command.stamp(config,"20260917_03")
            with self.assertRaisesRegex(RuntimeError,"preservation plan"):
                command.downgrade(config,"20260917_02")
        self.assertEqual(self.count(Grant),1)
        self.assertEqual(self.count(Lot),1)

    def test_quarantine_lock_wait_cannot_finish_after_4e_lease_expiry(self):
        work_id=self.receive("invalid-response")
        token=self.processor.claim(work_id)
        from app.services import payment_order_reconciliation_service as reconciliation
        original=reconciliation.quarantine
        def delayed(*args):
            original(*args)
            self.now+=timedelta(seconds=61)
        with patch.object(reconciliation,"quarantine",side_effect=delayed):
            self.assertEqual(self.processor._finish(work_id,token,self.context,None,"INVALID_RESPONSE"),"LEASE_LOST")
        self.assertEqual(self.count(fixtures.Quarantine),0)
        self.assertEqual(self.count(Evidence),0)
        with self.factory.Session() as session:
            self.assertEqual(session.get(fixtures.Work,work_id).status,"PROCESSING")

    def _during_order_lock_wait(self, action, order_id, later):
        """Deterministic two-thread schedule equivalent to a blocked PG order lock.

        SQLite cannot reproduce independent row locks. Pause the actual order
        write fence, after lot selection, then advance the clock before release.
        """
        waiting, release = Event(), Event()
        def block(connection, cursor, statement, parameters, context, executemany):
            if statement.lower().startswith("update payment_orders") and parameters == (order_id,):
                waiting.set()
                if not release.wait(10):
                    raise RuntimeError("test order lock wait timed out")
        sql_event.listen(self.engine, "before_cursor_execute", block)
        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(action)
                try:
                    self.assertTrue(waiting.wait(10), "worker must reach the order fence")
                    self.assertFalse(future.done())
                    self.now = later
                finally:
                    release.set()
                return future.result(timeout=10)
        finally:
            sql_event.remove(self.engine, "before_cursor_execute", block)

    def test_lot_expiring_during_concurrent_order_lock_wait_never_grants(self):
        self.subscription(source="TRANSACTIONAL", days=1)
        self.service.apply_evidence(self.evidence())
        with self.factory.Session() as session:
            lot = session.query(Lot).one()
            deadline = lot.expires_at
            order_id = session.query(Commission).one().payment_order_id
        self.now = deadline - timedelta(seconds=1)
        result = self._during_order_lock_wait(
            lambda: self.service.consume_credit(self.professional), order_id, deadline)
        self.assertEqual(result, "INSUFFICIENT_CREDITS")
        self.assertEqual(self.count(Grant), 0)
        self.assertEqual(self.count(Allocation), 0)
        self.assertEqual(self.balance(), Decimal("100.00"))
        with self.factory.Session() as session:
            self.assertEqual(session.query(Subscription).count(), 1)
            self.assertFalse(session.query(Audit).filter_by(operation="CREDIT_CONSUMED_30_DAYS").count())

    def test_successful_consumption_uses_one_post_lock_timestamp(self):
        self.subscription(source="TRANSACTIONAL", days=1)
        self.service.apply_evidence(self.evidence())
        with self.factory.Session() as session:
            deadline = session.query(Lot).one().expires_at
            order_id = session.query(Commission).one().payment_order_id
        self.now = deadline - timedelta(seconds=10)
        later = deadline - timedelta(seconds=1)
        self.assertEqual(self._during_order_lock_wait(
            lambda: self.service.consume_credit(self.professional), order_id, later), "GRANTED")
        with self.factory.Session() as session:
            grant = session.query(Grant).one()
            subscription = session.get(Subscription, grant.subscription_id)
            audit = session.query(Audit).filter_by(operation="CREDIT_CONSUMED_30_DAYS").one()
            self.assertEqual(grant.starts_at, later)
            self.assertEqual(subscription.started_at, later)
            self.assertEqual(audit.occurred_at, later)
            self.assertEqual(grant.expires_at, later + timedelta(days=30))
        self.assertEqual(self.balance(), Decimal("0.00"))

    def test_apply_revalidates_old_lot_after_concurrent_lock_wait(self):
        self.service.apply_evidence(self.evidence("50.00"))
        with self.factory.Session() as session:
            old = session.query(Lot).one()
            deadline, old_lot_id = old.expires_at, old.id
            old_order_id = session.query(Commission).one().payment_order_id
        identity = self.evidence("50.00")
        self.service._commission = lambda eid: self.proofs[eid]
        self.now = deadline - timedelta(seconds=1)
        self.assertEqual(self._during_order_lock_wait(
            lambda: self.service.apply_evidence(identity), old_order_id, deadline), "ACCRUED")
        self.assertEqual(self.count(Grant), 0)
        self.assertEqual(self.count(Allocation), 0)
        with self.factory.Session() as session:
            self.assertEqual(session.get(Lot, old_lot_id).remaining_amount, Decimal("50.00"))
            decision = session.query(Decision).filter_by(evidence_id=identity).one()
            audit = session.query(Audit).filter_by(evidence_id=identity).one()
            self.assertEqual(decision.observed_at, deadline)
            self.assertEqual(audit.occurred_at, deadline)
