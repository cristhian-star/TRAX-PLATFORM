import os
import unittest
from unittest.mock import patch

from app import create_app, db
from app.config.config import DevelopmentConfig, ProductionConfig, TestingConfig
from app.models.user import User


class AppConfigurationTest(unittest.TestCase):
    def test_production_requires_secret_key(self):
        with patch.dict(os.environ, {"APP_ENV": "production", "DATABASE_URL": "sqlite:///:memory:"}, clear=True):
            with self.assertRaises(RuntimeError) as context:
                create_app()

        self.assertIn("SECRET_KEY", str(context.exception))

    def test_production_rejects_development_secret_key(self):
        with patch.dict(
            os.environ,
            {
                "APP_ENV": "production",
                "SECRET_KEY": "dev-only-insecure-secret-key",
                "DATABASE_URL": "sqlite:///:memory:",
            },
            clear=True,
        ):
            with self.assertRaises(RuntimeError) as context:
                create_app()

        self.assertIn("desarrollo", str(context.exception))

    def test_dev_routes_are_registered_only_in_development(self):
        with patch.dict(
            os.environ,
            {"APP_ENV": "development", "SECRET_KEY": "dev", "DATABASE_URL": "sqlite:///:memory:"},
            clear=True,
        ):
            development_app = create_app()

        with patch.dict(
            os.environ,
            {"APP_ENV": "testing", "SECRET_KEY": "test", "DATABASE_URL": "sqlite:///:memory:"},
            clear=True,
        ):
            testing_app = create_app()

        self.assertIn("dev", development_app.blueprints)
        self.assertNotIn("dev", testing_app.blueprints)

    def test_create_all_requires_allowed_environment(self):
        with patch.dict(
            os.environ,
            {
                "APP_ENV": "production",
                "SECRET_KEY": "prod-secret",
                "DATABASE_URL": "sqlite:///:memory:",
            },
            clear=True,
        ):
            with self.assertRaises(RuntimeError) as context:
                create_app(config_class=ProductionConfig, initialize_schema=True)

        self.assertIn("Alembic", str(context.exception))

    def test_create_all_is_allowed_in_testing(self):
        with patch.dict(
            os.environ,
            {"APP_ENV": "testing", "SECRET_KEY": "test", "DATABASE_URL": "sqlite:///:memory:"},
            clear=True,
        ):
            app = create_app(config_class=TestingConfig, initialize_schema=True)

        with app.app_context():
            db.session.add(User(nombre="Cliente", email="cliente@trax.test", password="hash"))
            db.session.commit()
            self.assertEqual(User.query.count(), 1)
            db.session.remove()
            db.drop_all()

    def test_development_create_all_requires_explicit_flag(self):
        with patch.dict(
            os.environ,
            {"APP_ENV": "development", "SECRET_KEY": "dev", "DATABASE_URL": "sqlite:///:memory:"},
            clear=True,
        ):
            with self.assertRaises(RuntimeError):
                create_app(config_class=DevelopmentConfig, initialize_schema=True)

        with patch.dict(
            os.environ,
            {
                "APP_ENV": "development",
                "SECRET_KEY": "dev",
                "DATABASE_URL": "sqlite:///:memory:",
                "ALLOW_DEV_CREATE_ALL": "true",
            },
            clear=True,
        ):
            app = create_app(config_class=DevelopmentConfig, initialize_schema=True)

        with app.app_context():
            db.session.remove()
            db.drop_all()


if __name__ == "__main__":
    unittest.main()
