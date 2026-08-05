"""Mandatory PostgreSQL gate for contractual review routes and moderation.

This module is intentionally outside normal ``test_*.py`` discovery. It
requires an exclusive disposable PostgreSQL database because it migrates and
truncates that database.
"""

import io
import logging
import os
import re
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

POSTGRES_URL = os.environ.get("TRAX_POSTGRES_TEST_URL")
ALLOW_RESET = os.environ.get("TRAX_POSTGRES_TEST_ALLOW_RESET") == "1"
if POSTGRES_URL:
    os.environ["DATABASE_URL"] = POSTGRES_URL
os.environ.setdefault("SECRET_KEY", "postgres-review-moderation-e2e")
os.environ.setdefault("APP_ENV", "testing")

from app import create_app, db
from app.models.activity_notification import ActivityNotification
from app.models.audit_log import AuditLog
from app.models.contract_event import ContractEvent
from app.models.contract_request import ContractRequest
from app.models.operation_command import OperationCommand
from app.models.professional import Professional
from app.models.reputation_event import ReputationEvent
from app.models.review import Review
from app.models.user import User
from app.services import contract_review_moderation_service
from app.services.contract_review_moderation_service import (
    ACTION_HIDE,
    REASON_FRAUD_CONFIRMED,
    REASON_OFFENSIVE_CONTENT,
    get_pending_contract_review_moderation,
    moderate_contract_review_comment,
)


class ContractReviewRoutesModerationPostgreSQLGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not POSTGRES_URL:
            raise RuntimeError(
                "TRAX_POSTGRES_TEST_URL es obligatorio para el gate de moderacion"
            )
        if make_url(POSTGRES_URL).get_backend_name() not in (
            "postgresql",
            "postgres",
        ):
            raise RuntimeError("El gate requiere PostgreSQL")
        if not ALLOW_RESET:
            raise RuntimeError(
                "TRAX_POSTGRES_TEST_ALLOW_RESET=1 es obligatorio"
            )
        command.upgrade(Config(str(PROJECT_ROOT / "alembic.ini")), "head")
        cls.app = create_app(initialize_schema=False)
        cls.app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=True,
        )
        with cls.app.app_context():
            revision = db.session.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).scalar_one()
            version = db.session.execute(sa.text("SHOW server_version")).scalar_one()
            if revision != "20260726_07":
                raise RuntimeError(f"Revision inesperada: {revision}")
            print(
                f"PostgreSQL server_version={version} alembic={revision}",
                flush=True,
            )

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def _truncate(self):
        with self.app.app_context():
            names = [
                table.name
                for table in reversed(db.metadata.sorted_tables)
                if table.name != "alembic_version"
            ]
            quoted = ", ".join(
                db.engine.dialect.identifier_preparer.quote(name)
                for name in names
            )
            db.session.execute(
                sa.text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE")
            )
            db.session.commit()

    def setUp(self):
        self._truncate()
        self.client = self.app.test_client()
        with self.app.app_context():
            suffix = uuid4().hex
            owner = User(
                nombre="PG owner",
                email=f"pg-owner-{suffix}@test.local",
                password="hash",
                rol="CLIENTE",
                estado="ACTIVO",
            )
            other = User(
                nombre="PG other",
                email=f"pg-other-{suffix}@test.local",
                password="hash",
                rol="CLIENTE",
                estado="ACTIVO",
            )
            professional_user = User(
                nombre="PG professional",
                email=f"pg-prof-{suffix}@test.local",
                password="hash",
                rol="PROFESIONAL",
                estado="ACTIVO",
            )
            admin = User(
                nombre="PG admin",
                email=f"pg-admin-{suffix}@test.local",
                password="hash",
                rol="SUPER_ADMIN",
                estado="ACTIVO",
            )
            db.session.add_all((owner, other, professional_user, admin))
            db.session.flush()
            profile = Professional(
                user_id=professional_user.id,
                nombre="PG profile",
                servicio="Electricidad",
                especialidad="Electricidad",
                zona="CABA",
                descripcion="Perfil para gate",
                perfil_completo=True,
            )
            db.session.add(profile)
            db.session.flush()
            confirmed = ContractRequest(
                cliente_id=owner.id,
                professional_id=profile.id,
                professional_user_id=professional_user.id,
                source_type="DIRECT",
                servicio="Servicio confirmado",
                estado="CONFIRMADA",
                contracting_mode="EXTERNAL",
                version=5,
                confirmed_at=datetime(2026, 8, 4, 12, 0),
            )
            pending = ContractRequest(
                cliente_id=owner.id,
                professional_id=profile.id,
                professional_user_id=professional_user.id,
                source_type="DIRECT",
                servicio="Servicio pendiente",
                estado="COMPLETADA",
                contracting_mode="EXTERNAL",
                version=4,
            )
            db.session.add_all((confirmed, pending))
            db.session.commit()
            self.owner_id = owner.id
            self.other_id = other.id
            self.professional_user_id = professional_user.id
            self.admin_id = admin.id
            self.profile_id = profile.id
            self.contract_id = confirmed.id
            self.pending_contract_id = pending.id

    def tearDown(self):
        self._truncate()

    def _login(self, user_id):
        with self.client.session_transaction() as session:
            session.clear()
            session["user_id"] = user_id

    def _csrf_from(self, path):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        match = re.search(
            r'name="csrf_token" value="([^"]+)"',
            response.get_data(as_text=True),
        )
        self.assertIsNotNone(match)
        return match.group(1), response

    def _create_via_route(
        self,
        *,
        key="pg-route-review-key",
        rating="5",
        comment="PUBLIC_MARKER",
    ):
        self._login(self.owner_id)
        csrf_token, _ = self._csrf_from(
            f"/contratacion/{self.contract_id}/review"
        )
        return self.client.post(
            f"/contratacion/{self.contract_id}/review",
            data={
                "csrf_token": csrf_token,
                "idempotency_key": key,
                "rating": rating,
                "comment": comment,
            },
        )

    def _counts(self):
        return {
            "reviews": Review.query.count(),
            "commands": OperationCommand.query.count(),
            "events": ReputationEvent.query.count(),
            "audits": AuditLog.query.count(),
            "notifications": ActivityNotification.query.count(),
            "contract_events": ContractEvent.query.count(),
            "points": ReputationEvent.query.filter(
                ReputationEvent.puntos.isnot(None)
            ).count(),
        }

    def test_01_route_authorization_state_and_csrf(self):
        self.assertEqual(
            self.client.get(
                f"/contratacion/{self.contract_id}/review"
            ).status_code,
            302,
        )
        self._login(self.professional_user_id)
        self.assertEqual(
            self.client.get(
                f"/contratacion/{self.contract_id}/review"
            ).status_code,
            403,
        )
        self._login(self.other_id)
        self.assertEqual(
            self.client.get(
                f"/contratacion/{self.contract_id}/review"
            ).status_code,
            403,
        )
        self._login(self.owner_id)
        self.assertEqual(
            self.client.get(
                f"/contratacion/{self.pending_contract_id}/review"
            ).status_code,
            400,
        )
        missing_csrf = self.client.post(
            f"/contratacion/{self.contract_id}/review",
            data={
                "idempotency_key": "missing-csrf-key",
                "rating": "5",
            },
        )
        self.assertEqual(missing_csrf.status_code, 400)
        with self.app.app_context():
            self.assertEqual(self._counts()["reviews"], 0)

    def test_02_route_replay_conflicts_and_exact_physical_counts(self):
        first = self._create_via_route(comment="  PUBLIC_MARKER  ")
        self.assertEqual(first.status_code, 302)
        self._login(self.owner_id)
        token, _ = self._csrf_from(f"/contratacion/{self.contract_id}")
        payload = {
            "csrf_token": token,
            "idempotency_key": "pg-route-review-key",
            "rating": "5",
            "comment": "  PUBLIC_MARKER  ",
        }
        replay = self.client.post(
            f"/contratacion/{self.contract_id}/review", data=payload
        )
        different_payload = self.client.post(
            f"/contratacion/{self.contract_id}/review",
            data={**payload, "rating": "4"},
        )
        different_key = self.client.post(
            f"/contratacion/{self.contract_id}/review",
            data={
                **payload,
                "idempotency_key": "pg-different-existing-review-key",
            },
        )
        self.assertEqual(replay.status_code, 302)
        self.assertEqual(different_payload.status_code, 409)
        self.assertEqual(different_key.status_code, 409)
        with self.app.app_context():
            self.assertEqual(
                self._counts(),
                {
                    "reviews": 1,
                    "commands": 1,
                    "events": 1,
                    "audits": 1,
                    "notifications": 1,
                    "contract_events": 0,
                    "points": 0,
                },
            )

    def test_03_reporting_parties_third_party_and_audits(self):
        self.assertEqual(self._create_via_route().status_code, 302)
        with self.app.app_context():
            review_id = Review.query.one().id

        self._login(self.owner_id)
        token, _ = self._csrf_from(f"/contratacion/{self.contract_id}")
        owner_report = self.client.post(
            f"/reviews/{review_id}/reportar",
            data={"csrf_token": token},
        )
        self.assertEqual(owner_report.status_code, 302)

        self._login(self.admin_id)
        admin_token, admin_page = self._csrf_from("/admin/moderacion")
        self.assertIn("PUBLIC_MARKER", admin_page.get_data(as_text=True))
        show = self.client.post(
            f"/admin/reviews/{review_id}/comentario",
            data={
                "csrf_token": admin_token,
                "action": "SHOW",
                "reason": REASON_OFFENSIVE_CONTENT,
            },
        )
        self.assertEqual(show.status_code, 302)

        self._login(self.professional_user_id)
        professional_token, _ = self._csrf_from(
            f"/contratacion/{self.contract_id}"
        )
        professional_report = self.client.post(
            f"/reviews/{review_id}/reportar",
            data={"csrf_token": professional_token},
        )
        self.assertEqual(professional_report.status_code, 302)

        self._login(self.other_id)
        other_token, _ = self._csrf_from("/")
        third_party = self.client.post(
            f"/reviews/{review_id}/reportar",
            data={"csrf_token": other_token},
        )
        self.assertEqual(third_party.status_code, 403)
        with self.app.app_context():
            review = db.session.get(Review, review_id)
            self.assertEqual(
                review.comment_visibility_status,
                Review.COMMENT_PENDING_MODERATION,
            )
            self.assertEqual(review.rating_eligibility_status, Review.RATING_ELIGIBLE)
            self.assertEqual(
                AuditLog.query.filter_by(action="CONTRACT_REVIEW_REPORTED").count(),
                2,
            )

    def test_04_admin_moderation_privacy_original_immutability_and_exclusion(self):
        original_marker = "ORIGINAL_PRIVATE_MARKER"
        self.assertEqual(
            self._create_via_route(comment=original_marker).status_code,
            302,
        )
        with self.app.app_context():
            review = Review.query.one()
            review_id = review.id
            original = review.comentario

        self._login(self.owner_id)
        token, _ = self._csrf_from(f"/contratacion/{self.contract_id}")
        self.assertEqual(
            self.client.post(
                f"/reviews/{review_id}/reportar",
                data={"csrf_token": token},
            ).status_code,
            302,
        )
        profile = self.client.get(f"/profesional/{self.profile_id}")
        listing = self.client.get("/buscar")
        self.assertNotIn(original_marker, profile.get_data(as_text=True))
        self.assertNotIn(original_marker, listing.get_data(as_text=True))

        self._login(self.owner_id)
        with self.app.app_context():
            with self.assertRaises(PermissionError):
                get_pending_contract_review_moderation(
                    actor_user_id=self.owner_id
                )

        self._login(self.admin_id)
        admin_token, admin_page = self._csrf_from("/admin/moderacion")
        self.assertIn(original_marker, admin_page.get_data(as_text=True))
        redact = self.client.post(
            f"/admin/reviews/{review_id}/comentario",
            data={
                "csrf_token": admin_token,
                "action": "REDACT",
                "reason": REASON_OFFENSIVE_CONTENT,
                "redacted_comment": "PUBLIC_REDACTED_MARKER",
            },
        )
        self.assertEqual(redact.status_code, 302)
        admin_token, _ = self._csrf_from("/admin/moderacion")
        invalid_reason = self.client.post(
            f"/admin/reviews/{review_id}/rating/excluir",
            data={"csrf_token": admin_token, "reason": "FREE_TEXT"},
        )
        self.assertEqual(invalid_reason.status_code, 400)
        excluded = self.client.post(
            f"/admin/reviews/{review_id}/rating/excluir",
            data={
                "csrf_token": admin_token,
                "reason": REASON_FRAUD_CONFIRMED,
            },
        )
        self.assertEqual(excluded.status_code, 302)

        public_after = self.client.get(f"/profesional/{self.profile_id}")
        self.assertNotIn(original_marker, public_after.get_data(as_text=True))
        self.assertNotIn(
            "PUBLIC_REDACTED_MARKER",
            public_after.get_data(as_text=True),
        )
        with self.app.app_context():
            review = db.session.get(Review, review_id)
            self.assertEqual(review.comentario, original)
            self.assertEqual(review.comment_public, "PUBLIC_REDACTED_MARKER")
            self.assertEqual(review.rating_eligibility_status, Review.RATING_EXCLUDED)
            self.assertEqual(
                AuditLog.query.filter(
                    AuditLog.action.in_((
                        "CONTRACT_REVIEW_COMMENT_MODERATED",
                        "CONTRACT_REVIEW_RATING_EXCLUDED",
                    ))
                ).count(),
                2,
            )

    def test_05_common_user_cannot_moderate(self):
        self.assertEqual(self._create_via_route().status_code, 302)
        with self.app.app_context():
            review_id = Review.query.one().id
        self._login(self.owner_id)
        token, _ = self._csrf_from(f"/contratacion/{self.contract_id}")
        response = self.client.post(
            f"/admin/reviews/{review_id}/comentario",
            data={
                "csrf_token": token,
                "action": "HIDE",
                "reason": REASON_OFFENSIVE_CONTENT,
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_06_rollback_and_session_reuse_after_audit_failure(self):
        self.assertEqual(self._create_via_route().status_code, 302)
        with self.app.app_context():
            review = Review.query.one()
            review_id = review.id
            with patch.object(
                contract_review_moderation_service,
                "_add_audit",
                side_effect=RuntimeError("forced audit failure"),
            ):
                with self.assertRaises(RuntimeError):
                    moderate_contract_review_comment(
                        review_id,
                        actor_user_id=self.admin_id,
                        action=ACTION_HIDE,
                        reason=REASON_OFFENSIVE_CONTENT,
                    )
            review = db.session.get(Review, review_id)
            self.assertEqual(
                review.comment_visibility_status,
                Review.COMMENT_VISIBLE,
            )
            audit_count = AuditLog.query.count()
            moderate_contract_review_comment(
                review_id,
                actor_user_id=self.admin_id,
                action=ACTION_HIDE,
                reason=REASON_OFFENSIVE_CONTENT,
            )
            self.assertEqual(
                db.session.get(Review, review_id).comment_visibility_status,
                Review.COMMENT_HIDDEN,
            )
            self.assertEqual(AuditLog.query.count(), audit_count + 1)

    def test_07_physical_database_forbids_new_points(self):
        with self.app.app_context():
            with self.assertRaises(IntegrityError):
                db.session.execute(
                    sa.text(
                        "INSERT INTO reputation_events "
                        "(user_id, source_type, origin, tipo_evento, puntos, created_at) "
                        "VALUES (:user_id, NULL, NULL, 'ARBITRARY', 99, now())"
                    ),
                    {"user_id": self.professional_user_id},
                )
                db.session.commit()
            db.session.rollback()
            self.assertEqual(ReputationEvent.query.count(), 0)

    def test_08_successful_requests_do_not_log_original_comment(self):
        original_marker = "LOG_PRIVATE_MARKER"
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        self.app.logger.addHandler(handler)
        try:
            self.assertEqual(
                self._create_via_route(comment=original_marker).status_code,
                302,
            )
            self.client.get(f"/profesional/{self.profile_id}")
        finally:
            self.app.logger.removeHandler(handler)
        self.assertNotIn(original_marker, stream.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
