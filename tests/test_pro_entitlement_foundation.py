import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from flask import session
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from app import create_app, db, limiter
from app.config.config import TestingConfig
from app.models.audit_log import AuditLog
from app.models.professional import Professional
from app.models.subscription import Subscription
from app.models.user import User
from app.models.verification_request import VerificationRequest
from app.services.subscription_service import cancel_subscription, has_pro_access
from scripts import dev_seed_professionals
from tests.postgresql_pro_entitlement_e2e import (
    _create_guarded_engine,
    _validate_postgresql_test_url,
)


class IsolatedTestingConfig(TestingConfig):
    @classmethod
    def apply_runtime_config(cls, app_config):
        super().apply_runtime_config(app_config)
        app_config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"


class ProEntitlementFoundationTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=IsolatedTestingConfig, initialize_schema=True)
        self.app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,
            RATELIMIT_ENABLED=False,
        )
        self.http = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        limiter.reset()

    def _user(self, suffix, role="PROFESIONAL", state="ACTIVO", verified=True):
        user = User(
            nombre=f"User {suffix}",
            email=f"{suffix}@pro.test",
            password=generate_password_hash("ProTest123!"),
            rol=role,
            estado=state,
        )
        db.session.add(user)
        db.session.flush()
        if role == "PROFESIONAL":
            db.session.add(
                Professional(
                    user_id=user.id,
                    nombre=f"Professional {suffix}",
                    servicio="Electricidad",
                    zona="CABA",
                    perfil_completo=True,
                    estado_perfil="VERIFICADO",
                )
            )
        if verified:
            db.session.add(
                VerificationRequest(
                    user_id=user.id,
                    tipo_usuario="PROFESIONAL",
                    estado="APROBADO",
                )
            )
        db.session.commit()
        return user

    def _subscription(
        self,
        user_id,
        *,
        source="SUBSCRIPTION",
        plan="PRO",
        state="ACTIVA",
        expires_at=None,
    ):
        expires_at = expires_at or datetime(2030, 1, 1, tzinfo=timezone.utc)
        item = Subscription(
            user_id=user_id,
            plan=plan,
            estado=state,
            source_type=source,
            started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            expires_at=expires_at,
        )
        db.session.add(item)
        db.session.commit()
        return item

    def test_valid_subscription_and_transactional_sources_grant_access(self):
        with self.app.app_context():
            for source in Subscription.SOURCE_TYPES:
                user = self._user(source.lower())
                self._subscription(user.id, source=source)
                self.assertTrue(
                    has_pro_access(user.id, now=datetime(2029, 1, 1, tzinfo=timezone.utc))
                )

    def test_points_or_verification_without_valid_source_do_not_grant_access(self):
        with self.app.app_context():
            verified = self._user("verified")
            points = self._user("points")
            self.assertFalse(has_pro_access(verified.id))
            self.assertFalse(has_pro_access(points.id))

    def test_legacy_null_source_and_missing_expiry_do_not_grant_access(self):
        with self.app.app_context():
            legacy = self._user("legacy")
            self._subscription(legacy.id, source=None)
            no_expiry = self._user("no-expiry")
            self._subscription(no_expiry.id, expires_at=None)
            Subscription.query.filter_by(user_id=no_expiry.id).update({"expires_at": None})
            db.session.commit()
            self.assertFalse(has_pro_access(legacy.id))
            self.assertFalse(has_pro_access(no_expiry.id))

    def test_expired_boundary_and_non_active_states_do_not_grant_access(self):
        boundary = datetime(2026, 9, 4, 12, 0, tzinfo=timezone.utc)
        with self.app.app_context():
            expired = self._user("expired")
            self._subscription(expired.id, expires_at=boundary - timedelta(seconds=1))
            exact = self._user("exact")
            self._subscription(exact.id, expires_at=boundary)
            self.assertFalse(has_pro_access(expired.id, now=boundary))
            self.assertFalse(has_pro_access(exact.id, now=boundary))
            for state in ("CANCELADA", "EXPIRADA", "PENDIENTE"):
                user = self._user(state.lower())
                self._subscription(user.id, state=state)
                self.assertFalse(has_pro_access(user.id, now=boundary))

    def test_role_account_state_and_enterprise_are_enforced(self):
        with self.app.app_context():
            for state in ("SUSPENDIDO", "BANEADO"):
                user = self._user(state.lower(), state=state)
                self._subscription(user.id)
                self.assertFalse(has_pro_access(user.id))
            client = self._user("client", role="CLIENTE")
            self._subscription(client.id)
            self.assertFalse(has_pro_access(client.id))
            enterprise = self._user("enterprise")
            self._subscription(enterprise.id, plan="ENTERPRISE")
            self.assertFalse(has_pro_access(enterprise.id))

    def test_one_current_source_wins_and_other_users_are_isolated(self):
        boundary = datetime(2026, 9, 4, 12, 0, tzinfo=timezone.utc)
        with self.app.app_context():
            user = self._user("multi")
            self._subscription(user.id, expires_at=boundary - timedelta(days=1))
            self._subscription(user.id, source="TRANSACTIONAL", expires_at=boundary + timedelta(days=1))
            other = self._user("other")
            self.assertTrue(has_pro_access(user.id, now=boundary))
            self.assertFalse(has_pro_access(other.id, now=boundary))

    def test_revocation_only_cancels_current_valid_pro_sources(self):
        boundary = datetime(2026, 9, 4, 12, 0, tzinfo=timezone.utc)
        with self.app.app_context():
            user = self._user("revoke")
            affected = [
                self._subscription(user.id, source="SUBSCRIPTION"),
                self._subscription(user.id, source="TRANSACTIONAL"),
            ]
            untouched = [
                self._subscription(user.id, source=None),
                self._subscription(user.id, expires_at=boundary),
                self._subscription(user.id, plan="FREE", source=None),
                self._subscription(user.id, plan="ENTERPRISE"),
                self._subscription(user.id, state="CANCELADA"),
                self._subscription(user.id, state="EXPIRADA"),
                self._subscription(user.id, state="PENDIENTE"),
            ]
            other = self._user("revoke-other")
            other_row = self._subscription(other.id)
            affected_ids = [item.id for item in affected]
            untouched_states = {item.id: item.estado for item in untouched + [other_row]}

            self.assertIsNotNone(cancel_subscription(user.id, now=boundary))
            db.session.commit()
            db.session.expire_all()

            self.assertTrue(all(db.session.get(Subscription, item_id).estado == "CANCELADA" for item_id in affected_ids))
            self.assertEqual(
                {item_id: db.session.get(Subscription, item_id).estado for item_id in untouched_states},
                untouched_states,
            )

    def test_revocation_and_audit_roll_back_together_on_audit_failure(self):
        with self.app.app_context():
            admin = self._user("revoke-admin", role="SUPER_ADMIN", verified=False)
            target = self._user("revoke-target")
            subscription = self._subscription(target.id)
            admin_id, target_id, subscription_id = admin.id, target.id, subscription.id
        with self.app.test_request_context(
            f"/admin/usuarios/{target_id}/quitar-pro",
            method="POST",
        ):
            session["user_id"] = admin_id
            session["user_role"] = "SUPER_ADMIN"
            with patch(
                "app.routes.main_routes._add_audit_log",
                side_effect=RuntimeError("forced audit failure"),
            ):
                with self.assertRaisesRegex(RuntimeError, "forced audit failure"):
                    self.app.view_functions["main.admin_usuario_quitar_pro"](target_id)

        with self.app.app_context():
            db.session.expire_all()
            self.assertEqual(db.session.get(Subscription, subscription_id).estado, "ACTIVA")
            self.assertEqual(AuditLog.query.filter_by(target_user_id=target_id).count(), 0)

    def test_successful_revocation_persists_entitlement_and_audit_together(self):
        with self.app.app_context():
            admin = self._user("revoke-success-admin", role="SUPER_ADMIN", verified=False)
            target = self._user("revoke-success-target")
            subscription = self._subscription(target.id)
            admin_id, target_id, subscription_id = admin.id, target.id, subscription.id
        with self.http.session_transaction() as browser_session:
            browser_session["user_id"] = admin_id
            browser_session["user_role"] = "SUPER_ADMIN"

        response = self.http.post(f"/admin/usuarios/{target_id}/quitar-pro")
        self.assertEqual(response.status_code, 302)

        with self.app.app_context():
            db.session.expire_all()
            self.assertEqual(db.session.get(Subscription, subscription_id).estado, "CANCELADA")
            self.assertEqual(
                AuditLog.query.filter_by(
                    target_user_id=target_id,
                    action="USER_PRO_REMOVED",
                ).count(),
                1,
            )

    def test_unknown_source_is_rejected_but_null_legacy_is_allowed(self):
        with self.app.app_context():
            user = self._user("constraint")
            db.session.add(
                Subscription(
                    user_id=user.id,
                    plan="PRO",
                    estado="ACTIVA",
                    source_type="ADMINISTRATIVE",
                    expires_at=datetime(2030, 1, 1, tzinfo=timezone.utc),
                )
            )
            with self.assertRaises(IntegrityError):
                db.session.commit()
            db.session.rollback()
            self._subscription(user.id, source=None)

    def test_professional_upgrade_post_does_not_mutate_subscriptions(self):
        with self.app.app_context():
            user = self._user("route")
            user_id = user.id
        with self.http.session_transaction() as browser_session:
            browser_session["user_id"] = user_id
            browser_session["user_role"] = "PROFESIONAL"
        response = self.http.post("/profesional/pro/upgrade")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"todavia no esta disponible", response.data)
        with self.app.app_context():
            self.assertEqual(Subscription.query.filter_by(user_id=user_id).count(), 0)

    def test_admin_activation_post_does_not_mutate_subscriptions(self):
        with self.app.app_context():
            admin = self._user("admin", role="SUPER_ADMIN", verified=False)
            target = self._user("target")
            admin_id, target_id = admin.id, target.id
        with self.http.session_transaction() as browser_session:
            browser_session["user_id"] = admin_id
            browser_session["user_role"] = "SUPER_ADMIN"
        response = self.http.post(f"/admin/usuarios/{target_id}/activar-pro")
        self.assertEqual(response.status_code, 409)
        with self.app.app_context():
            self.assertEqual(Subscription.query.filter_by(user_id=target_id).count(), 0)

    def test_seed_creates_one_valid_pro_and_is_idempotent(self):
        first_now = datetime(2026, 9, 4, 12, 0, tzinfo=timezone.utc)
        with self.app.app_context():
            first = dev_seed_professionals.seed_professionals(now=first_now)
            qa_user = User.query.filter_by(email=dev_seed_professionals.QA_PRO_EMAIL).one()
            source = Subscription.query.filter_by(user_id=qa_user.id, source_type="SUBSCRIPTION").one()
            source_id = source.id
            first_expiry = source.expires_at
            second = dev_seed_professionals.seed_professionals(now=first_now + timedelta(hours=1))
            self.assertEqual(first["subscriptions_created"], 1)
            self.assertEqual(second["subscriptions_created"], 0)
            self.assertEqual(db.session.get(Subscription, source_id).expires_at, first_expiry)
            demo_users = User.query.filter(User.email.like("%@demo.trax.local")).all()
            pro_users = [user for user in demo_users if has_pro_access(user.id, now=first_now)]
            self.assertEqual([user.email for user in pro_users], [dev_seed_professionals.QA_PRO_EMAIL])
            valid_rows = Subscription.query.filter_by(
                plan="PRO", estado="ACTIVA", source_type="SUBSCRIPTION"
            ).all()
            self.assertEqual(len(valid_rows), 1)

            renewed_at = first_now + timedelta(days=366)
            third = dev_seed_professionals.seed_professionals(now=renewed_at)
            db.session.expire_all()
            renewed = db.session.get(Subscription, source_id)
            self.assertEqual(third["subscriptions_created"], 0)
            self.assertEqual(renewed.expires_at, renewed_at.replace(tzinfo=None) + timedelta(days=365))
            self.assertEqual(
                Subscription.query.filter_by(user_id=qa_user.id, source_type="SUBSCRIPTION").count(),
                1,
            )

    def test_seed_neutralizes_prior_demo_pro_without_touching_other_users(self):
        with self.app.app_context():
            dev_seed_professionals.seed_professionals()
            plumbing = User.query.filter_by(email="plomeria.work@demo.trax.local").one()
            refrigeration = User.query.filter_by(email="refrigeracion.pro@demo.trax.local").one()
            outsider = self._user("outsider")
            for user in (plumbing, refrigeration, outsider):
                self._subscription(user.id)
            dev_seed_professionals.seed_professionals()
            self.assertFalse(has_pro_access(plumbing.id))
            self.assertFalse(has_pro_access(refrigeration.id))
            self.assertTrue(has_pro_access(outsider.id))

    def test_seed_main_remains_blocked_in_production_aliases(self):
        for environment in ("production", "prod"):
            with self.subTest(environment=environment), patch.dict(
                os.environ,
                {"APP_ENV": environment},
                clear=True,
            ):
                with self.assertRaisesRegex(SystemExit, "bloqueado en produccion"):
                    dev_seed_professionals.main()


class PostgreSQLGateGuardTest(unittest.TestCase):
    INVALID_DATABASES = (
        "trax_db",
        "postgres",
        "template0",
        "template1",
        "arbitrary",
        "trax_pro_entitlement_test_",
        "TRAX_PRO_ENTITLEMENT_TEST",
        "trax_pro_entitlement_test_A1",
        "trax_pro_entitlement_test-a1",
        "trax_pro_entitlement_test.a1",
        "trax_pro_entitlement_test a1",
        "trax_pro_entitlement_test_%20",
        "trax_pro_entitlement_test_%2Fa1",
        "trax_pro_entitlement_test/a1",
        "trax_pro_entitlement_test\\a1",
        "trax_pro_entitlement_test;a1",
        "trax_pro_entitlement_test#a1",
        "trax_pro_entitlement_test_á",
        "trax_pro_entitlement_test_a1_",
        "trax_pro_entitlement_test_a1__b2",
        "trax_pro_entitlement_testx",
        "prefix_trax_pro_entitlement_test",
        "trax_pro_entitlement_test_" + "a" * 39,
    )

    def test_accepts_reserved_database_names(self):
        for database in (
            "trax_pro_entitlement_test",
            "trax_pro_entitlement_test_a1",
            "trax_pro_entitlement_test_finalaudit_20260904",
        ):
            parsed = _validate_postgresql_test_url(
                f"postgresql://user:password@localhost/{database}",
                "1",
            )
            self.assertEqual(parsed.database, database)

    def test_rejects_unsafe_database_names_and_empty_name(self):
        for database in self.INVALID_DATABASES:
            with self.subTest(database=database), self.assertRaisesRegex(RuntimeError, "nombre reservado"):
                _validate_postgresql_test_url(
                    f"postgresql://user:password@localhost/{database}",
                    "1",
                )
        with self.assertRaisesRegex(RuntimeError, "nombre reservado"):
            _validate_postgresql_test_url("postgresql://user:password@localhost", "1")

        for url in (None, "", 123):
            with self.subTest(url=url), self.assertRaises(RuntimeError):
                _validate_postgresql_test_url(url, "1")

        for marker in ("?option=value", "?options=-csearch_path%3Dpublic"):
            with self.subTest(marker=marker), self.assertRaisesRegex(RuntimeError, "nombre reservado"):
                _validate_postgresql_test_url(
                    f"postgresql://user:password@localhost/trax_pro_entitlement_test{marker}",
                    "1",
                )

    def test_every_invalid_name_stops_before_engine_or_migrations(self):
        invalid_urls = tuple(
            f"postgresql://user:password@localhost/{database}"
            for database in self.INVALID_DATABASES
        ) + (
            "postgresql://user:password@localhost/trax_pro_entitlement_test?option=value",
            "postgresql://user:password@localhost/trax_pro_entitlement_test?options=-csearch_path%3Dpublic",
            "postgresql://user:password@localhost",
            "sqlite:///trax_pro_entitlement_test",
            None,
            "",
            123,
        )
        with (
            patch("tests.postgresql_pro_entitlement_e2e.sa.create_engine") as create_engine,
            patch("tests.postgresql_pro_entitlement_e2e.command.upgrade") as upgrade,
            patch("tests.postgresql_pro_entitlement_e2e.command.downgrade") as downgrade,
        ):
            for url in invalid_urls:
                with self.subTest(url=url), self.assertRaises(RuntimeError):
                    _create_guarded_engine(url, "1")
            create_engine.assert_not_called()
            upgrade.assert_not_called()
            downgrade.assert_not_called()

    def test_rejects_missing_authorization_before_engine_creation(self):
        with patch("tests.postgresql_pro_entitlement_e2e.sa.create_engine") as create_engine:
            with self.assertRaisesRegex(RuntimeError, "autorizacion explicita"):
                _create_guarded_engine(
                    "postgresql://user:password@localhost/trax_pro_entitlement_test",
                    None,
                )
            create_engine.assert_not_called()
    def test_rejects_trax_db_before_engine_creation(self):
        with patch("tests.postgresql_pro_entitlement_e2e.sa.create_engine") as create_engine:
            with self.assertRaisesRegex(RuntimeError, "nombre reservado"):
                _create_guarded_engine(
                    "postgresql://user:password@localhost/trax_db",
                    "1",
                )
            create_engine.assert_not_called()


if __name__ == "__main__":
    unittest.main()
