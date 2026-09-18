import os
from pathlib import Path
import unittest
from unittest.mock import patch

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text

from app import create_app, db
from app.config.config import DevelopmentConfig


class DockerContextTest(unittest.TestCase):
    def test_obsidian_is_excluded_recursively_without_excluding_markdown(self):
        patterns = (Path(__file__).resolve().parents[1] / ".dockerignore").read_text().splitlines()
        self.assertIn(".obsidian/", patterns)
        self.assertIn("**/.obsidian/", patterns)
        self.assertFalse(any("*.md" in pattern for pattern in patterns))

    @unittest.skipUnless(os.environ.get("DOCKER_IMAGE_CHECK_ROOT"), "Run explicitly inside the rebuilt image")
    def test_built_image_contains_no_obsidian_paths_and_preserves_docs(self):
        root = Path(os.environ["DOCKER_IMAGE_CHECK_ROOT"])
        self.assertTrue((root / "docs/HANDOFFS/ACTIVE_HANDOFF.md").is_file())
        self.assertTrue((root / "README.md").is_file())
        forbidden = []
        for directory, directories, files in os.walk(root):
            if ".obsidian" in directories or ".obsidian" in files:
                forbidden.append(str(Path(directory) / ".obsidian"))
        self.assertEqual(forbidden, [])
        for filename in ("app.json", "appearance.json", "core-plugins.json", "graph.json", "workspace.json"):
            self.assertFalse((root / "docs/.obsidian" / filename).exists())


class RuntimeHealthTest(unittest.TestCase):
    def setUp(self):
        with patch.dict(os.environ, {
            "APP_ENV": "development", "DATABASE_URL": "sqlite:///:memory:",
            "SECRET_KEY": "isolated-health-test", "PYTHON_DOTENV_DISABLED": "1",
        }, clear=True):
            self.app = create_app(config_class=DevelopmentConfig)
        self.client = self.app.test_client()
        self.head = ScriptDirectory.from_config(Config("alembic.ini")).get_current_head()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def applied(self, *versions):
        with self.app.app_context(), db.engine.begin() as connection:
            connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32))"))
            for version in versions:
                connection.execute(text("INSERT INTO alembic_version VALUES (:version)"), {"version": version})

    def assert_unavailable(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json, {"status": "unavailable"})
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_current_schema_is_ready_and_does_not_create_business_tables(self):
        self.applied(self.head)
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "ok"})
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        with self.app.app_context(), db.engine.connect() as connection:
            tables = list(connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).scalars())
        self.assertEqual(tables, ["alembic_version"])

    def test_missing_schema_is_unavailable(self):
        self.assert_unavailable()

    def test_old_revision_is_unavailable(self):
        self.applied("20260917_02")
        self.assert_unavailable()

    def test_empty_revision_is_unavailable(self):
        self.applied()
        self.assert_unavailable()

    def test_multiple_revisions_are_unavailable(self):
        self.applied(self.head, "20260917_02")
        self.assert_unavailable()

    def test_database_failure_is_generic_and_secret_free(self):
        with self.app.app_context(), patch.object(db.engine, "connect", side_effect=RuntimeError("PRIVATE-DSN-TOKEN")):
            self.assert_unavailable()

    def test_development_keeps_csrf_and_financial_flags_disabled(self):
        self.assertTrue(self.app.config["WTF_CSRF_ENABLED"])
        self.assertFalse(self.app.config["ALLOW_SCHEMA_CREATE_ALL"])
        for flag in ("CHECKOUT_PRO_DELIVERY_ENABLED", "MERCADOPAGO_ORDER_WEBHOOK_ENABLED",
                     "MERCADOPAGO_ORDER_RECONCILIATION_ENABLED", "PAYMENT_EFFECTS_ENABLED",
                     "TRANSACTIONAL_COMMISSION_ENABLED"):
            self.assertIs(self.app.config[flag], False)
