import unittest
from unittest.mock import patch

from app import create_app, db
from app.config.config import TestingConfig
from app.models.activity_notification import ActivityNotification
from app.models.audit_log import AuditLog
from app.models.contract_event import ContractEvent
from app.models.contract_request import ContractRequest
from app.models.operation_command import OperationCommand
from app.models.professional import Professional
from app.models.reputation_event import ReputationEvent
from app.models.review import Review
from app.models.user import User
from app.services.contract_review_moderation_service import (
    ACTION_HIDE,
    ACTION_REDACT,
    REASON_FRAUD_CONFIRMED,
    REASON_OFFENSIVE_CONTENT,
    exclude_contract_review_rating,
    get_pending_contract_review_moderation,
    moderate_contract_review_comment,
    report_contract_review,
)
from app.services.contract_review_service import create_contract_review
from app.services.review_service import (
    get_professional_reputation_metrics,
    get_professional_reviews,
)


class ContractReviewRoutesUiModerationTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestingConfig, initialize_schema=True)
        self.client = self.app.test_client()
        with self.app.app_context():
            self.owner = self._user("Owner", "route-owner@test.local", "CLIENTE")
            self.other = self._user("Other", "route-other@test.local", "CLIENTE")
            self.prof_user = self._user(
                "Professional", "route-prof@test.local", "PROFESIONAL"
            )
            self.admin = self._user("Admin", "route-admin@test.local", "SUPER_ADMIN")
            self.profile = Professional(
                user_id=self.prof_user.id,
                nombre="Profesional de prueba",
                servicio="Electricidad",
                especialidad="Electricidad",
                zona="CABA",
                descripcion="Perfil publico",
                perfil_completo=True,
            )
            db.session.add(self.profile)
            db.session.flush()
            self.contract = self._contract("CONFIRMADA")
            self.pending_contract = self._contract("COMPLETADA")
            db.session.commit()
            self.owner_id = self.owner.id
            self.other_id = self.other.id
            self.prof_user_id = self.prof_user.id
            self.admin_id = self.admin.id
            self.profile_id = self.profile.id
            self.contract_id = self.contract.id
            self.pending_contract_id = self.pending_contract.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _user(self, name, email, role, state="ACTIVO"):
        user = User(
            nombre=name,
            email=email,
            password="hash",
            rol=role,
            estado=state,
        )
        db.session.add(user)
        db.session.flush()
        return user

    def _contract(self, state):
        contract = ContractRequest(
            cliente_id=self.owner.id,
            professional_id=self.profile.id,
            professional_user_id=self.prof_user.id,
            source_type=ContractRequest.SOURCE_DIRECT,
            servicio="Trabajo confirmado",
            estado=state,
            contracting_mode=ContractRequest.CONTRACTING_MODE_EXTERNAL,
        )
        db.session.add(contract)
        db.session.flush()
        return contract

    def _login(self, user_id):
        with self.client.session_transaction() as session:
            session["user_id"] = user_id

    def _create_review(self, key="route-review-key", comment="Original seguro"):
        return create_contract_review(
            actor_user_id=self.owner_id,
            contract_id=self.contract_id,
            rating=5,
            comment=comment,
            idempotency_key=key,
        )

    def test_route_rejects_visitor_professional_other_client_and_previous_state(self):
        self.assertEqual(
            self.client.get(f"/contratacion/{self.contract_id}/review").status_code,
            302,
        )
        self._login(self.prof_user_id)
        self.assertEqual(
            self.client.get(f"/contratacion/{self.contract_id}/review").status_code,
            403,
        )
        self._login(self.other_id)
        self.assertEqual(
            self.client.get(f"/contratacion/{self.contract_id}/review").status_code,
            403,
        )
        self._login(self.owner_id)
        self.assertEqual(
            self.client.get(
                f"/contratacion/{self.pending_contract_id}/review"
            ).status_code,
            400,
        )

    def test_owner_form_has_stable_hidden_key_and_no_identity_inputs(self):
        self._login(self.owner_id)
        response = self.client.get(f"/contratacion/{self.contract_id}/review")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('name="idempotency_key"', body)
        self.assertIn('name="csrf_token"', body)
        self.assertNotIn('name="cliente_id"', body)
        self.assertNotIn('name="professional_id"', body)
        self.assertNotIn('name="contract_id"', body)

    def test_create_replay_payload_conflict_and_exact_effects(self):
        self._login(self.owner_id)
        payload = {
            "rating": "5",
            "comment": "  Excelente  ",
            "idempotency_key": "route-stable-review-key",
        }
        first = self.client.post(
            f"/contratacion/{self.contract_id}/review", data=payload
        )
        second = self.client.post(
            f"/contratacion/{self.contract_id}/review", data=payload
        )
        conflict = self.client.post(
            f"/contratacion/{self.contract_id}/review",
            data={**payload, "rating": "4"},
        )
        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        self.assertEqual(conflict.status_code, 409)
        with self.app.app_context():
            self.assertEqual(Review.query.count(), 1)
            self.assertEqual(OperationCommand.query.count(), 1)
            self.assertEqual(ReputationEvent.query.count(), 1)
            self.assertEqual(AuditLog.query.count(), 1)
            self.assertEqual(ActivityNotification.query.count(), 1)
            self.assertEqual(ContractEvent.query.count(), 0)
            self.assertIsNone(ReputationEvent.query.one().puntos)

    def test_route_surfaces_invalid_rating_existing_review_and_service_error(self):
        self._login(self.owner_id)
        invalid = self.client.post(
            f"/contratacion/{self.contract_id}/review",
            data={"rating": "0", "comment": "x", "idempotency_key": "invalid-key"},
        )
        self.assertEqual(invalid.status_code, 400)
        with patch(
            "app.routes.operation_routes.create_contract_review",
            side_effect=RuntimeError("injected transactional error"),
        ):
            service_error = self.client.post(
                f"/contratacion/{self.contract_id}/review",
                data={
                    "rating": "5",
                    "comment": "x",
                    "idempotency_key": "service-error-key",
                },
            )
            self.assertEqual(service_error.status_code, 500)
        with self.app.app_context():
            self.assertEqual(Review.query.count(), 0)
            self._create_review()
        existing = self.client.get(f"/contratacion/{self.contract_id}/review")
        self.assertEqual(existing.status_code, 409)

    def test_contract_detail_button_visibility_and_existing_review_link(self):
        self._login(self.owner_id)
        confirmed = self.client.get(f"/contratacion/{self.contract_id}")
        pending = self.client.get(f"/contratacion/{self.pending_contract_id}")
        self.assertIn("Calificar trabajo realizado", confirmed.get_data(as_text=True))
        self.assertNotIn("Calificar trabajo realizado", pending.get_data(as_text=True))
        self._login(self.prof_user_id)
        professional_view = self.client.get(f"/contratacion/{self.contract_id}")
        self.assertNotIn(
            "Calificar trabajo realizado",
            professional_view.get_data(as_text=True),
        )
        self._login(self.owner_id)
        with self.app.app_context():
            review = self._create_review()
            review_id = review.id
        reviewed = self.client.get(f"/contratacion/{self.contract_id}")
        body = reviewed.get_data(as_text=True)
        self.assertNotIn("Calificar trabajo realizado", body)
        self.assertIn(f"#review-{review_id}", body)
        duplicate = self.client.post(
            f"/contratacion/{self.contract_id}/review",
            data={
                "rating": "5",
                "comment": "Otro intento",
                "idempotency_key": "different-key-existing-review",
            },
        )
        self.assertEqual(duplicate.status_code, 409)

    def test_public_profile_uses_only_public_comment_and_neutral_metrics(self):
        with self.app.app_context():
            review = self._create_review(comment="ORIGINAL_PRIVATE_MARKER")
            review.comment_public = "PUBLIC_SAFE_MARKER"
            legacy_contract = self._contract("CONFIRMADA")
            legacy = Review(
                contract_id=legacy_contract.id,
                cliente_id=self.owner_id,
                professional_id=self.profile_id,
                rating=4,
                comentario="LEGACY_ORIGINAL_PRIVATE",
                comment_public="LEGACY_PUBLIC_SAFE",
                origin=Review.ORIGIN_LEGACY,
                verification_status=Review.VERIFICATION_VERIFIED,
                comment_visibility_status=Review.COMMENT_VISIBLE,
                rating_eligibility_status=Review.RATING_ELIGIBLE,
                estado="VISIBLE",
            )
            excluded_contract = self._contract("CONFIRMADA")
            excluded = Review(
                contract_id=excluded_contract.id,
                cliente_id=self.owner_id,
                professional_id=self.profile_id,
                rating=1,
                comentario="EXCLUDED_ORIGINAL_PRIVATE",
                comment_public="EXCLUDED_PUBLIC_MARKER",
                origin=Review.ORIGIN_LEGACY,
                verification_status=Review.VERIFICATION_VERIFIED,
                comment_visibility_status=Review.COMMENT_VISIBLE,
                rating_eligibility_status=Review.RATING_EXCLUDED,
                estado="VISIBLE",
            )
            db.session.add_all((legacy, excluded))
            db.session.commit()
        response = self.client.get(f"/profesional/{self.profile_id}")
        body = response.get_data(as_text=True)
        self.assertIn("PUBLIC_SAFE_MARKER", body)
        self.assertIn("LEGACY_PUBLIC_SAFE", body)
        self.assertIn("Review contractual verificada", body)
        self.assertIn("Review legacy verificada", body)
        self.assertNotIn("ORIGINAL_PRIVATE_MARKER", body)
        self.assertNotIn("LEGACY_ORIGINAL_PRIVATE", body)
        self.assertNotIn("EXCLUDED_PUBLIC_MARKER", body)
        self.assertNotIn("Reputacion TRAX", body)
        with self.app.app_context():
            metrics = get_professional_reputation_metrics(self.profile_id)
            self.assertEqual(metrics.eligible_rating_count, 2)
            self.assertEqual(metrics.average_eligible_rating, 4.5)
            self.assertEqual(dict(metrics.star_distribution)[1], 0)

    def test_report_by_both_parties_third_party_rejected_and_rating_stays_eligible(self):
        with self.app.app_context():
            first = self._create_review()
            original = first.comentario
            report_contract_review(first.id, actor_user_id=self.owner_id)
            self.assertEqual(
                first.comment_visibility_status,
                Review.COMMENT_PENDING_MODERATION,
            )
            self.assertEqual(first.rating_eligibility_status, Review.RATING_ELIGIBLE)
            self.assertEqual(first.comentario, original)
            self.assertEqual(
                AuditLog.query.filter_by(action="CONTRACT_REVIEW_REPORTED").count(),
                1,
            )

            second_contract = self._contract("CONFIRMADA")
            db.session.commit()
            second = create_contract_review(
                actor_user_id=self.owner_id,
                contract_id=second_contract.id,
                rating=4,
                comment="Segundo",
                idempotency_key="second-report-key",
            )
            report_contract_review(second.id, actor_user_id=self.prof_user_id)
            with self.assertRaises(PermissionError):
                report_contract_review(second.id, actor_user_id=self.other_id)
            self.assertEqual(second.comentario, "Segundo")

    def test_only_admin_can_moderate_redact_hide_and_exclude_with_reason(self):
        with self.app.app_context():
            review = self._create_review(comment="Original inmutable")
            original = review.comentario
            with self.assertRaises(PermissionError):
                moderate_contract_review_comment(
                    review.id,
                    actor_user_id=self.owner_id,
                    action=ACTION_HIDE,
                    reason=REASON_OFFENSIVE_CONTENT,
                )
            moderate_contract_review_comment(
                review.id,
                actor_user_id=self.admin_id,
                action=ACTION_HIDE,
                reason=REASON_OFFENSIVE_CONTENT,
            )
            self.assertEqual(review.comment_visibility_status, Review.COMMENT_HIDDEN)
            self.assertEqual(review.rating_eligibility_status, Review.RATING_ELIGIBLE)
            moderate_contract_review_comment(
                review.id,
                actor_user_id=self.admin_id,
                action=ACTION_REDACT,
                reason=REASON_OFFENSIVE_CONTENT,
                redacted_comment=" Version publica segura ",
            )
            self.assertEqual(review.comment_public, "Version publica segura")
            self.assertEqual(review.comentario, original)
            with self.assertRaises(ValueError):
                exclude_contract_review_rating(
                    review.id,
                    actor_user_id=self.admin_id,
                    reason=None,
                )
            exclude_contract_review_rating(
                review.id,
                actor_user_id=self.admin_id,
                reason=REASON_FRAUD_CONFIRMED,
            )
            self.assertEqual(review.rating_eligibility_status, Review.RATING_EXCLUDED)
            self.assertEqual(review.comentario, original)
            self.assertEqual(
                AuditLog.query.filter(
                    AuditLog.action.in_((
                        "CONTRACT_REVIEW_COMMENT_MODERATED",
                        "CONTRACT_REVIEW_RATING_EXCLUDED",
                    ))
                ).count(),
                3,
            )

    def test_original_comment_reader_requires_active_super_admin(self):
        with self.app.app_context():
            review = self._create_review(comment="Original restringido")
            report_contract_review(review.id, actor_user_id=self.owner_id)
            with self.assertRaises(PermissionError):
                get_pending_contract_review_moderation(
                    actor_user_id=self.owner_id
                )
            pending = get_pending_contract_review_moderation(
                actor_user_id=self.admin_id
            )
            self.assertEqual([item.id for item in pending], [review.id])

    def test_legacy_route_is_gone_and_historical_events_remain_readable(self):
        visitor_response = self.client.get(
            f"/profesional/{self.profile_id}/review"
        )
        self.assertEqual(visitor_response.status_code, 410)
        self._login(self.owner_id)
        response = self.client.post(
            f"/profesional/{self.profile_id}/review",
            data={"rating": "5", "comentario": "legacy"},
        )
        self.assertEqual(response.status_code, 410)
        with self.app.app_context():
            historical = ReputationEvent(
                user_id=self.prof_user_id,
                source_type=ReputationEvent.SOURCE_LEGACY_EVENT,
                origin=ReputationEvent.ORIGIN_LEGACY,
                tipo_evento="REVIEW_POSITIVA",
                puntos=10,
                descripcion="Historico",
            )
            db.session.add(historical)
            db.session.commit()
            self.assertEqual(ReputationEvent.query.filter_by(puntos=10).count(), 1)
            self.assertEqual(Review.query.count(), 0)

    def test_end_to_end_review_notification_profile_metrics_and_no_points(self):
        self._login(self.owner_id)
        response = self.client.post(
            f"/contratacion/{self.contract_id}/review",
            data={
                "rating": "5",
                "comment": "Trabajo documentado",
                "idempotency_key": "route-e2e-review-key",
            },
        )
        self.assertEqual(response.status_code, 302)
        profile = self.client.get(response.headers["Location"])
        self.assertIn("Trabajo documentado", profile.get_data(as_text=True))
        with self.app.app_context():
            self.assertEqual(ActivityNotification.query.count(), 1)
            self.assertEqual(
                ActivityNotification.query.one().user_id,
                self.prof_user_id,
            )
            metrics = get_professional_reputation_metrics(self.profile_id)
            self.assertEqual(metrics.eligible_rating_count, 1)
            self.assertEqual(metrics.average_eligible_rating, 5.0)
            self.assertEqual(ContractEvent.query.count(), 0)
            self.assertEqual(ReputationEvent.query.filter(ReputationEvent.puntos.isnot(None)).count(), 0)


if __name__ == "__main__":
    unittest.main()
