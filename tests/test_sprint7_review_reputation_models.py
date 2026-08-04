import unittest

from app import create_app, db
from app.config.config import TestingConfig
from app.models.contract_request import ContractRequest
from app.models.professional import Professional
from app.models.reputation_event import ReputationEvent
from app.models.review import Review
from app.models.user import User


class ReviewReputationModelPreparationTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestingConfig, initialize_schema=True)

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_review_exposes_only_preparatory_block_one_fields(self):
        expected = {
            "contract_id",
            "comment_public",
            "origin",
            "verification_status",
            "comment_visibility_status",
            "rating_eligibility_status",
            "correlation_id",
            "payload_hash",
            "legacy_metadata_json",
            "moderated_by_user_id",
            "moderated_at",
            "moderation_reason",
        }
        self.assertTrue(expected.issubset(Review.__table__.columns.keys()))
        self.assertNotIn("operation_command_id", Review.__table__.columns)
        self.assertTrue(Review.__table__.columns.contract_id.nullable)
        self.assertTrue(Review.__table__.columns.rating.nullable)

    def test_review_foreign_keys_use_canonical_identifiers(self):
        targets = {
            foreign_key.target_fullname
            for foreign_key in Review.__table__.foreign_keys
        }
        self.assertIn("contract_requests.id", targets)
        self.assertIn("users.id", targets)
        self.assertIn("professionals.id", targets)

    def test_reputation_event_keeps_user_target_and_adds_neutral_fact_fields(self):
        expected = {
            "review_id",
            "contract_id",
            "source_type",
            "event_type",
            "event_value",
            "origin",
            "correlation_id",
        }
        self.assertTrue(expected.issubset(ReputationEvent.__table__.columns.keys()))
        self.assertTrue(ReputationEvent.__table__.columns.puntos.nullable)
        targets = {
            foreign_key.target_fullname
            for foreign_key in ReputationEvent.__table__.foreign_keys
        }
        self.assertIn("users.id", targets)
        self.assertIn("reviews.id", targets)
        self.assertIn("contract_requests.id", targets)

    def test_legacy_constructors_remain_compatible(self):
        with self.app.app_context():
            client = User(
                nombre="Cliente legacy",
                email="legacy-client@review.test",
                password="hash",
                rol="CLIENTE",
            )
            professional_user = User(
                nombre="Profesional legacy",
                email="legacy-professional@review.test",
                password="hash",
                rol="PROFESIONAL",
            )
            db.session.add_all((client, professional_user))
            db.session.flush()
            professional = Professional(
                user_id=professional_user.id,
                nombre="Perfil legacy",
                servicio="Electricidad",
                zona="CABA",
            )
            db.session.add(professional)
            db.session.flush()
            review = Review(
                cliente_id=client.id,
                professional_id=professional.id,
                rating=5,
                comentario="Review anterior al bloque contractual",
            )
            event = ReputationEvent(
                user_id=professional_user.id,
                tipo_evento="REVIEW_POSITIVA",
                puntos=10,
                descripcion="Evento legacy preservado",
            )
            db.session.add_all((review, event))
            db.session.commit()
            self.assertIsNone(review.contract_id)
            self.assertIsNone(event.review_id)
            self.assertEqual(event.puntos, 10)

    def test_new_neutral_event_can_store_rating_without_points(self):
        with self.app.app_context():
            client = User(
                nombre="Cliente contractual",
                email="contract-client@review.test",
                password="hash",
                rol="CLIENTE",
            )
            professional_user = User(
                nombre="Profesional contractual",
                email="contract-professional@review.test",
                password="hash",
                rol="PROFESIONAL",
            )
            db.session.add_all((client, professional_user))
            db.session.flush()
            professional = Professional(
                user_id=professional_user.id,
                nombre="Perfil contractual",
                servicio="Plomeria",
                zona="CABA",
            )
            db.session.add(professional)
            db.session.flush()
            contract = ContractRequest(
                cliente_id=client.id,
                professional_id=professional.id,
                professional_user_id=professional_user.id,
                servicio="Reparacion",
                estado="CONFIRMADA",
            )
            db.session.add(contract)
            db.session.flush()
            review = Review(
                contract_id=contract.id,
                cliente_id=client.id,
                professional_id=professional.id,
                rating=4,
                comentario="Original",
                comment_public="Original",
                origin=Review.ORIGIN_CONTRACTUAL,
                verification_status=Review.VERIFICATION_VERIFIED,
                comment_visibility_status=Review.COMMENT_VISIBLE,
                rating_eligibility_status=Review.RATING_ELIGIBLE,
                correlation_id="00000000-0000-0000-0000-000000000001",
                payload_hash="a" * 64,
            )
            db.session.add(review)
            db.session.flush()
            event = ReputationEvent(
                user_id=professional_user.id,
                review_id=review.id,
                contract_id=contract.id,
                source_type=ReputationEvent.SOURCE_CONTRACT_REVIEW,
                event_type=ReputationEvent.EVENT_REVIEW_RECORDED,
                event_value=4,
                origin=ReputationEvent.ORIGIN_CONTRACTUAL,
                correlation_id=review.correlation_id,
                tipo_evento="REVIEW_RECORDED",
                puntos=None,
            )
            db.session.add(event)
            db.session.commit()
            self.assertIsNone(event.puntos)
            self.assertEqual(event.event_value, review.rating)


if __name__ == "__main__":
    unittest.main()
