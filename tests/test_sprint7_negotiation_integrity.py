import os
import unittest
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError


os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "negotiation-integrity-test"

from app import create_app, db
from app.models.activity_notification import ActivityNotification
from app.models.audit_log import AuditLog
from app.models.contract_event import ContractEvent
from app.models.contract_negotiation import ContractNegotiation
from app.models.contract_negotiation_version import ContractNegotiationVersion
from app.models.contract_request import ContractRequest
from app.models.negotiation_acceptance import NegotiationAcceptance
from app.models.negotiation_event import NegotiationEvent
from app.models.operation_command import OperationCommand
from app.models.professional import Professional
from app.models.user import User
from app.services.negotiation_service import (
    NegotiationConflictError,
    accept_negotiation_terms,
    finalize_negotiation_contract,
    initiate_direct_negotiation,
    propose_negotiation_terms,
)


class Sprint7NegotiationIntegrityTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(initialize_schema=False)
        self.app.config.update(TESTING=True)
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            client = User(
                nombre="Integrity Client",
                email="integrity-client@test.local",
                password="hash",
                rol="CLIENTE",
                estado="ACTIVO",
            )
            professional_user = User(
                nombre="Integrity Professional",
                email="integrity-professional@test.local",
                password="hash",
                rol="PROFESIONAL",
                estado="ACTIVO",
            )
            db.session.add_all([client, professional_user])
            db.session.flush()
            professional = Professional(
                user_id=professional_user.id,
                nombre="Integrity Professional",
                servicio="Electricidad",
                zona="CABA",
                perfil_completo=True,
            )
            db.session.add(professional)
            db.session.commit()
            self.client_id = client.id
            self.professional_user_id = professional_user.id
            self.professional_id = professional.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _initiate(self, key="negotiation-integrity-init-0001"):
        return initiate_direct_negotiation(
            cliente_id=self.client_id,
            professional_id=self.professional_id,
            servicio="Servicio integro",
            description="Descripcion integra",
            scope="Alcance integro",
            external_price="250000.00",
            estimated_start_at=datetime(2026, 8, 1, 10, 0),
            estimated_end_at=datetime(2026, 8, 3, 18, 0),
            observations="Observaciones integras",
            actor_user_id=self.client_id,
            idempotency_key=key,
        )

    def _agree(self):
        negotiation = self._initiate()
        negotiation = accept_negotiation_terms(
            negotiation.id,
            actor_user_id=self.client_id,
            expected_version=negotiation.version,
            terms_version=negotiation.current_terms_version,
            idempotency_key="negotiation-integrity-client-accept",
        )
        return accept_negotiation_terms(
            negotiation.id,
            actor_user_id=self.professional_user_id,
            expected_version=negotiation.version,
            terms_version=negotiation.current_terms_version,
            idempotency_key="negotiation-integrity-professional-accept",
        )

    def _counts(self):
        return {
            "contracts": ContractRequest.query.count(),
            "contract_events": ContractEvent.query.count(),
            "commands": OperationCommand.query.count(),
            "negotiation_events": NegotiationEvent.query.count(),
            "audits": AuditLog.query.count(),
            "notifications": ActivityNotification.query.count(),
        }

    def _assert_no_new_effects(self, baseline):
        self.assertEqual(self._counts(), baseline)
        self.assertEqual(ContractRequest.query.count(), 0)
        self.assertEqual(ContractEvent.query.count(), 0)

    def test_snapshot_columns_are_orm_immutable_after_acceptance(self):
        protected_changes = {
            "description": "Descripcion mutada",
            "scope": "Alcance mutado",
            "external_price": 1,
            "estimated_start_at": datetime(2026, 9, 1),
            "estimated_end_at": datetime(2026, 9, 2),
            "observations": "Observacion mutada",
            "payload_hash": "0" * 64,
        }
        with self.app.app_context():
            negotiation = self._agree()
            terms_id = ContractNegotiationVersion.query.filter_by(
                negotiation_id=negotiation.id,
                version_no=1,
            ).one().id
            baseline = self._counts()
            for attribute, value in protected_changes.items():
                with self.subTest(attribute=attribute):
                    terms = db.session.get(
                        ContractNegotiationVersion,
                        terms_id,
                    )
                    setattr(terms, attribute, value)
                    with self.assertRaisesRegex(ValueError, "inmutable"):
                        db.session.flush()
                    db.session.rollback()
                    self._assert_no_new_effects(baseline)

    def test_corrupted_hash_is_rejected_before_acceptance_command(self):
        with self.app.app_context():
            negotiation = self._initiate()
            terms = ContractNegotiationVersion.query.filter_by(
                negotiation_id=negotiation.id
            ).one()
            db.session.execute(
                sa.text(
                    "UPDATE contract_negotiation_versions "
                    "SET payload_hash = :hash WHERE id = :id"
                ),
                {"hash": "f" * 64, "id": terms.id},
            )
            db.session.commit()
            baseline = self._counts()
            with self.assertRaises(NegotiationConflictError):
                accept_negotiation_terms(
                    negotiation.id,
                    actor_user_id=self.client_id,
                    expected_version=1,
                    terms_version=1,
                    idempotency_key="negotiation-corrupt-hash-accept",
                )
            self._assert_no_new_effects(baseline)

    def test_content_changed_without_hash_is_rejected_before_acceptance(self):
        corruptions = (
            ("description", "Descripcion adulterada"),
            ("scope", "Alcance adulterado"),
            ("estimated_start_at", datetime(2026, 8, 2)),
            ("estimated_end_at", datetime(2026, 8, 4)),
        )
        with self.app.app_context():
            for index, (column, value) in enumerate(corruptions):
                with self.subTest(column=column):
                    negotiation = self._initiate(
                        f"negotiation-content-corruption-{index:04d}"
                    )
                    terms = ContractNegotiationVersion.query.filter_by(
                        negotiation_id=negotiation.id
                    ).one()
                    db.session.execute(
                        sa.text(
                            f"UPDATE contract_negotiation_versions "
                            f"SET {column} = :value WHERE id = :id"
                        ),
                        {"value": value, "id": terms.id},
                    )
                    db.session.commit()
                    baseline = self._counts()
                    with self.assertRaises(NegotiationConflictError):
                        accept_negotiation_terms(
                            negotiation.id,
                            actor_user_id=self.client_id,
                            expected_version=1,
                            terms_version=1,
                            idempotency_key=(
                                f"negotiation-corrupt-content-{index:04d}"
                            ),
                        )
                    self._assert_no_new_effects(baseline)

    def test_price_changed_after_two_acceptances_blocks_finalization(self):
        with self.app.app_context():
            negotiation = self._agree()
            terms = ContractNegotiationVersion.query.filter_by(
                negotiation_id=negotiation.id
            ).one()
            db.session.execute(
                sa.text(
                    "UPDATE contract_negotiation_versions "
                    "SET external_price = 1 WHERE id = :id"
                ),
                {"id": terms.id},
            )
            db.session.commit()
            baseline = self._counts()
            with self.assertRaises(NegotiationConflictError):
                finalize_negotiation_contract(
                    negotiation.id,
                    actor_user_id=self.client_id,
                    expected_version=negotiation.version,
                    terms_version=1,
                    idempotency_key="negotiation-corrupt-price-finalize",
                )
            self._assert_no_new_effects(baseline)

    def test_swapped_acceptance_identities_block_finalization(self):
        with self.app.app_context():
            negotiation = self._agree()
            baseline = self._counts()
            corruptions = (
                ("PROFESSIONAL", self.client_id),
                ("CLIENT", self.professional_user_id),
            )
            for party, actor_id in corruptions:
                with self.subTest(party=party):
                    correct_actor_id = (
                        self.professional_user_id
                        if party == "PROFESSIONAL"
                        else self.client_id
                    )
                    db.session.execute(
                        sa.text(
                            "UPDATE negotiation_acceptances "
                            "SET actor_user_id = :actor_id "
                            "WHERE negotiation_id = :negotiation_id "
                            "AND party = :party"
                        ),
                        {
                            "actor_id": actor_id,
                            "negotiation_id": negotiation.id,
                            "party": party,
                        },
                    )
                    db.session.commit()
                    with self.assertRaises(NegotiationConflictError):
                        finalize_negotiation_contract(
                            negotiation.id,
                            actor_user_id=self.client_id,
                            expected_version=negotiation.version,
                            terms_version=1,
                            idempotency_key=(
                                f"negotiation-swapped-{party.lower()}"
                            ),
                        )
                    self._assert_no_new_effects(baseline)
                    db.session.execute(
                        sa.text(
                            "UPDATE negotiation_acceptances "
                            "SET actor_user_id = :actor_id "
                            "WHERE negotiation_id = :negotiation_id "
                            "AND party = :party"
                        ),
                        {
                            "actor_id": correct_actor_id,
                            "negotiation_id": negotiation.id,
                            "party": party,
                        },
                    )
                    db.session.commit()

    def test_incoherent_orm_acceptances_are_rejected_before_insert(self):
        with self.app.app_context():
            negotiation = self._initiate()
            terms = ContractNegotiationVersion.query.filter_by(
                negotiation_id=negotiation.id
            ).one()
            invalid_rows = (
                NegotiationAcceptance(
                    negotiation_id=negotiation.id,
                    negotiation_version_id=terms.id,
                    actor_user_id=self.client_id,
                    party=NegotiationAcceptance.PARTY_PROFESSIONAL,
                ),
                NegotiationAcceptance(
                    negotiation_id=negotiation.id,
                    negotiation_version_id=terms.id,
                    actor_user_id=self.professional_user_id,
                    party=NegotiationAcceptance.PARTY_CLIENT,
                ),
            )
            for row in invalid_rows:
                with self.subTest(party=row.party):
                    db.session.add(row)
                    with self.assertRaises(ValueError):
                        db.session.flush()
                    db.session.rollback()
                    self.assertEqual(NegotiationAcceptance.query.count(), 0)

    def test_cross_negotiation_and_stale_version_acceptances_are_rejected(self):
        with self.app.app_context():
            first = self._initiate("negotiation-integrity-first-0001")
            second = self._initiate("negotiation-integrity-second-0001")
            first_terms = ContractNegotiationVersion.query.filter_by(
                negotiation_id=first.id
            ).one()
            second_terms = ContractNegotiationVersion.query.filter_by(
                negotiation_id=second.id
            ).one()
            cross = NegotiationAcceptance(
                negotiation_id=first.id,
                negotiation_version_id=second_terms.id,
                actor_user_id=self.client_id,
                party=NegotiationAcceptance.PARTY_CLIENT,
            )
            db.session.add(cross)
            with self.assertRaises(ValueError):
                db.session.flush()
            db.session.rollback()

            first = propose_negotiation_terms(
                first.id,
                description="Version dos",
                scope="Alcance version dos",
                external_price="260000",
                actor_user_id=self.client_id,
                expected_version=first.version,
                idempotency_key="negotiation-integrity-propose-v2",
            )
            stale = NegotiationAcceptance(
                negotiation_id=first.id,
                negotiation_version_id=first_terms.id,
                actor_user_id=self.client_id,
                party=NegotiationAcceptance.PARTY_CLIENT,
            )
            db.session.add(stale)
            with self.assertRaises(ValueError):
                db.session.flush()
            db.session.rollback()
            self.assertEqual(NegotiationAcceptance.query.count(), 0)

    def test_suspended_acceptance_actor_blocks_agreed_and_finalize(self):
        with self.app.app_context():
            negotiation = self._initiate()
            negotiation = accept_negotiation_terms(
                negotiation.id,
                actor_user_id=self.client_id,
                expected_version=negotiation.version,
                terms_version=1,
                idempotency_key="negotiation-suspend-client-accept",
            )
            client = db.session.get(User, self.client_id)
            client.estado = "SUSPENDIDO"
            db.session.commit()
            baseline = self._counts()
            with self.assertRaises(PermissionError):
                accept_negotiation_terms(
                    negotiation.id,
                    actor_user_id=self.professional_user_id,
                    expected_version=negotiation.version,
                    terms_version=1,
                    idempotency_key="negotiation-suspend-professional-accept",
                )
            self._assert_no_new_effects(baseline)
            self.assertEqual(
                db.session.get(ContractNegotiation, negotiation.id).state,
                ContractNegotiation.STATE_OPEN,
            )

        with self.app.app_context():
            db.session.remove()
            client = db.session.get(User, self.client_id)
            client.estado = "ACTIVO"
            db.session.commit()
            negotiation = self._initiate(
                "negotiation-suspended-professional-init"
            )
            negotiation = accept_negotiation_terms(
                negotiation.id,
                actor_user_id=self.client_id,
                expected_version=negotiation.version,
                terms_version=1,
                idempotency_key="negotiation-suspended-pro-client-accept",
            )
            negotiation = accept_negotiation_terms(
                negotiation.id,
                actor_user_id=self.professional_user_id,
                expected_version=negotiation.version,
                terms_version=1,
                idempotency_key="negotiation-suspended-pro-accept",
            )
            professional = db.session.get(User, self.professional_user_id)
            professional.estado = "SUSPENDIDO"
            db.session.commit()
            baseline = self._counts()
            with self.assertRaises(PermissionError):
                finalize_negotiation_contract(
                    negotiation.id,
                    actor_user_id=self.client_id,
                    expected_version=negotiation.version,
                    terms_version=1,
                    idempotency_key="negotiation-suspended-pro-finalize",
                )
            self._assert_no_new_effects(baseline)

    def test_integrity_happy_path_still_materializes_one_contract(self):
        with self.app.app_context():
            negotiation = self._agree()
            contract = finalize_negotiation_contract(
                negotiation.id,
                actor_user_id=self.client_id,
                expected_version=negotiation.version,
                terms_version=1,
                idempotency_key="negotiation-integrity-happy-finalize",
            )
            self.assertEqual(contract.estado, "CREADA")
            self.assertEqual(ContractRequest.query.count(), 1)
            self.assertEqual(ContractEvent.query.count(), 1)
            self.assertEqual(NegotiationAcceptance.query.count(), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
