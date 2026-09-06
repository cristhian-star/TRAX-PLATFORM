import os
import re
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app, db
from app.config.config import TestingConfig
from app.models.audit_log import AuditLog
from app.models.subscription import Subscription
from app.models.user import User
from app.models.verification_request import VerificationRequest
from app.services.subscription_service import has_pro_access
from tests.alembic_head_validation import assert_database_at_repository_head


RESERVED_DATABASE = "trax_pro_entitlement_test"
POSTGRESQL_IDENTIFIER_MAX_BYTES = 63
RESERVED_DATABASE_PATTERN = re.compile(
    rf"{RESERVED_DATABASE}(?:_[a-z0-9]+(?:_[a-z0-9]+)*)?"
)


def _validate_postgresql_test_url(url, allow_reset):
    if allow_reset != "1":
        raise RuntimeError("Gate bloqueado: falta autorizacion explicita")
    if not isinstance(url, str) or not url:
        raise RuntimeError("Gate bloqueado: falta URL PostgreSQL descartable")

    parsed = make_url(url)
    database = parsed.database
    if parsed.get_backend_name() != "postgresql":
        raise RuntimeError("Gate bloqueado: el motor no es PostgreSQL")
    if (
        not isinstance(database, str)
        or len(database.encode("utf-8")) > POSTGRESQL_IDENTIFIER_MAX_BYTES
        or RESERVED_DATABASE_PATTERN.fullmatch(database) is None
        or bool(parsed.query)
    ):
        raise RuntimeError(
            "Gate bloqueado: la base debe usar el nombre reservado "
            f"{RESERVED_DATABASE} o {RESERVED_DATABASE}_<segmentos_ascii>, "
            f"sin parametros y con hasta {POSTGRESQL_IDENTIFIER_MAX_BYTES} bytes"
        )
    return parsed


def _create_guarded_engine(url, allow_reset):
    parsed = _validate_postgresql_test_url(url, allow_reset)
    engine = sa.create_engine(parsed)
    if engine.dialect.name != "postgresql":
        engine.dispose()
        raise RuntimeError("Gate bloqueado: el dialecto efectivo no es PostgreSQL")
    return engine


class PostgreSQLProEntitlementGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = os.environ.get("TRAX_POSTGRES_PRO_ENTITLEMENT_TEST_URL")
        cls.engine = _create_guarded_engine(
            cls.url,
            os.environ.get("TRAX_POSTGRES_TEST_ALLOW_RESET"),
        )
        os.environ["DATABASE_URL"] = cls.url
        os.environ["SECRET_KEY"] = "pro-entitlement-postgresql-gate"
        cls.config = Config(str(PROJECT_ROOT / "alembic.ini"))
        cls.app = create_app(config_class=TestingConfig)

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.session.remove()
            db.engine.dispose()
        cls.engine.dispose()

    def _revision(self):
        with self.engine.connect() as connection:
            return connection.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).scalar_one()

    def test_z_admin_revocation_and_audit_roll_back_and_recover_on_postgresql(self):
        command.upgrade(self.config, "head")
        with self.engine.begin() as connection:
            connection.execute(sa.text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        suffix = str(int(datetime.now(timezone.utc).timestamp() * 1_000_000))
        with self.app.app_context():
            admin = User(
                nombre="PRO rollback admin",
                email=f"pro-rollback-admin-{suffix}@test.local",
                password="hash",
                rol="SUPER_ADMIN",
                estado="ACTIVO",
            )
            target = User(
                nombre="PRO rollback target",
                email=f"pro-rollback-target-{suffix}@test.local",
                password="hash",
                rol="PROFESIONAL",
                estado="ACTIVO",
            )
            other = User(
                nombre="PRO rollback other",
                email=f"pro-rollback-other-{suffix}@test.local",
                password="hash",
                rol="PROFESIONAL",
                estado="ACTIVO",
            )
            db.session.add_all((admin, target, other))
            db.session.flush()
            db.session.add(
                VerificationRequest(
                    user_id=target.id,
                    tipo_usuario="PROFESIONAL",
                    estado="APROBADO",
                )
            )
            subscriptions = (
                Subscription(
                    user_id=target.id,
                    plan="PRO",
                    estado="ACTIVA",
                    source_type="TRANSACTIONAL",
                    started_at=now,
                    expires_at=now + timedelta(days=1),
                ),
                Subscription(
                    user_id=target.id,
                    plan="PRO",
                    estado="ACTIVA",
                    source_type="SUBSCRIPTION",
                    started_at=now,
                    expires_at=now + timedelta(days=2),
                ),
                Subscription(
                    user_id=target.id,
                    plan="PRO",
                    estado="ACTIVA",
                    source_type=None,
                    started_at=now,
                    expires_at=now + timedelta(days=3),
                ),
                Subscription(
                    user_id=target.id,
                    plan="PRO",
                    estado="ACTIVA",
                    source_type="SUBSCRIPTION",
                    started_at=now - timedelta(days=2),
                    expires_at=now - timedelta(days=1),
                ),
                Subscription(
                    user_id=target.id,
                    plan="FREE",
                    estado="ACTIVA",
                    started_at=now,
                ),
                Subscription(
                    user_id=target.id,
                    plan="ENTERPRISE",
                    estado="ACTIVA",
                    started_at=now,
                ),
                Subscription(
                    user_id=other.id,
                    plan="PRO",
                    estado="ACTIVA",
                    source_type="SUBSCRIPTION",
                    started_at=now,
                    expires_at=now + timedelta(days=1),
                ),
            )
            db.session.add_all(subscriptions)
            db.session.commit()
            admin_id = admin.id
            target_id = target.id
            protected_ids = [subscription.id for subscription in subscriptions[2:]]

        self.app.config["WTF_CSRF_ENABLED"] = True
        client = self.app.test_client()
        with client.session_transaction() as browser_session:
            browser_session["user_id"] = admin_id
            browser_session["user_role"] = "SUPER_ADMIN"

        def csrf_token():
            response = client.get("/admin/usuarios")
            self.assertEqual(response.status_code, 200)
            match = re.search(
                r'name="csrf_token" value="([^"]+)"',
                response.get_data(as_text=True),
            )
            self.assertIsNotNone(match)
            return match.group(1)

        def add_invalid_audit(**values):
            invalid = AuditLog(**values)
            invalid.actor_user_id = 2_147_483_647
            db.session.add(invalid)
            return invalid

        with patch(
            "app.routes.main_routes._add_audit_log",
            side_effect=add_invalid_audit,
        ):
            failed_response = client.post(
                f"/admin/usuarios/{target_id}/quitar-pro",
                data={"csrf_token": csrf_token()},
            )
            self.assertEqual(failed_response.status_code, 500)

        with self.engine.connect() as independent:
            active_sources = independent.execute(
                sa.text(
                    "SELECT source_type FROM subscriptions "
                    "WHERE user_id=:target AND plan='PRO' AND estado='ACTIVA' "
                    "AND source_type IN ('TRANSACTIONAL','SUBSCRIPTION') "
                    "AND expires_at > :now "
                    "ORDER BY source_type"
                ),
                {"target": target_id, "now": now},
            ).scalars().all()
            self.assertEqual(active_sources, ["SUBSCRIPTION", "TRANSACTIONAL"])
            self.assertEqual(
                independent.execute(
                    sa.text(
                        "SELECT COUNT(*) FROM audit_logs "
                        "WHERE target_user_id=:target AND action='USER_PRO_REMOVED'"
                    ),
                    {"target": target_id},
                ).scalar_one(),
                0,
            )

        with self.app.app_context():
            self.assertEqual(db.session.execute(sa.text("SELECT 1")).scalar_one(), 1)

        response = client.post(
            f"/admin/usuarios/{target_id}/quitar-pro",
            data={"csrf_token": csrf_token()},
        )
        self.assertEqual(response.status_code, 302)

        with self.engine.connect() as independent:
            self.assertEqual(
                independent.execute(
                    sa.text(
                        "SELECT COUNT(*) FROM subscriptions "
                        "WHERE user_id=:target AND plan='PRO' AND estado='CANCELADA' "
                        "AND source_type IN ('TRANSACTIONAL','SUBSCRIPTION')"
                    ),
                    {"target": target_id},
                ).scalar_one(),
                2,
            )
            self.assertEqual(
                independent.execute(
                    sa.text(
                        "SELECT COUNT(*) FROM audit_logs "
                        "WHERE target_user_id=:target AND action='USER_PRO_REMOVED'"
                    ),
                    {"target": target_id},
                ).scalar_one(),
                1,
            )
            protected_states = independent.execute(
                sa.text(
                    "SELECT id, estado FROM subscriptions WHERE id = ANY(:ids) ORDER BY id"
                ),
                {"ids": protected_ids},
            ).all()
            self.assertTrue(all(row.estado == "ACTIVA" for row in protected_states))
            self.assertEqual(independent.execute(sa.text("SELECT 1")).scalar_one(), 1)

    def test_postgresql_migration_constraint_and_entitlement(self):
        command.upgrade(self.config, "20260726_07")
        with self.engine.begin() as connection:
            legacy_user = connection.execute(
                sa.text(
                    "INSERT INTO users (nombre,email,password,rol,estado) "
                    "VALUES ('Legacy','legacy@pro-gate.test','hash','PROFESIONAL','ACTIVO') RETURNING id"
                )
            ).scalar_one()
            connection.execute(
                sa.text(
                    "INSERT INTO subscriptions "
                    "(user_id,plan,estado,started_at,expires_at,auto_renew) "
                    "VALUES (:user,'PRO','ACTIVA',:started,:expires,false)"
                ),
                {
                    "user": legacy_user,
                    "started": datetime(2026, 1, 1),
                    "expires": datetime(2030, 1, 1),
                },
            )

        command.upgrade(self.config, "head")
        assert_database_at_repository_head(self.config, [self._revision()])
        with self.engine.begin() as connection:
            self.assertIsNone(
                connection.execute(sa.text("SELECT source_type FROM subscriptions")).scalar_one()
            )
            connection.execute(
                sa.text("UPDATE subscriptions SET source_type='TRANSACTIONAL'")
            )
        command.downgrade(self.config, "20260726_07")
        self.assertEqual(self._revision(), "20260726_07")
        command.upgrade(self.config, "head")
        with self.engine.begin() as connection:
            self.assertIsNone(
                connection.execute(sa.text("SELECT source_type FROM subscriptions")).scalar_one()
            )

        now = datetime.now(timezone.utc)
        with self.engine.begin() as connection:
            valid_user = connection.execute(
                sa.text(
                    "INSERT INTO users (nombre,email,password,rol,estado) "
                    "VALUES ('Valid','valid@pro-gate.test','hash','PROFESIONAL','ACTIVO') RETURNING id"
                )
            ).scalar_one()
            other_user = connection.execute(
                sa.text(
                    "INSERT INTO users (nombre,email,password,rol,estado) "
                    "VALUES ('Other','other@pro-gate.test','hash','PROFESIONAL','ACTIVO') RETURNING id"
                )
            ).scalar_one()
            for user_id in (legacy_user, valid_user, other_user):
                connection.execute(
                    sa.text(
                        "INSERT INTO verification_requests "
                        "(user_id,tipo_usuario,estado,created_at) "
                        "VALUES (:user,'PROFESIONAL','APROBADO',:now)"
                    ),
                    {"user": user_id, "now": now},
                )
            connection.execute(
                sa.text(
                    "INSERT INTO subscriptions "
                    "(user_id,plan,estado,source_type,started_at,expires_at,auto_renew) "
                    "VALUES (:user,'PRO','ACTIVA','SUBSCRIPTION',:now,:expires,false)"
                ),
                {"user": valid_user, "now": now, "expires": now + timedelta(days=1)},
            )

        with self.assertRaises(IntegrityError):
            with self.engine.begin() as connection:
                connection.execute(
                    sa.text(
                        "INSERT INTO subscriptions "
                        "(user_id,plan,estado,source_type,started_at,expires_at,auto_renew) "
                        "VALUES (:user,'PRO','ACTIVA','ADMINISTRATIVE',:now,:expires,false)"
                    ),
                    {"user": other_user, "now": now, "expires": now + timedelta(days=1)},
                )

        app = create_app(config_class=TestingConfig)
        with app.app_context():
            self.assertFalse(has_pro_access(legacy_user, now=now))
            self.assertTrue(has_pro_access(valid_user, now=now))
            self.assertFalse(has_pro_access(other_user, now=now))


if __name__ == "__main__":
    unittest.main()
