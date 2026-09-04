import os
import re
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.config.config import TestingConfig
from app.services.subscription_service import has_pro_access


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

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def _revision(self):
        with self.engine.connect() as connection:
            return connection.execute(
                sa.text("SELECT version_num FROM alembic_version")
            ).scalar_one()

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
        self.assertEqual(self._revision(), "20260904_01")
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
