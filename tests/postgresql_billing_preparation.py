"""Explicit disposable-only gate. Never points at the ordinary application DB."""
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy.engine import make_url
from alembic import command
from alembic.config import Config

from app import create_app, db
from app.models.user import User
from app.models.billing_preparation import BillingDraft
from app.services.billing_preparation_service import BillingConflict
import tests.test_billing_preparation_service as base


class BillingPreparationPostgresTest(base.BillingPreparationServiceTest):
    @classmethod
    def setUpClass(cls):
        url = make_url(os.environ["TRAX_BILLING_TEST_URL"])
        if ((url.host, url.port, url.database, url.username) != ("127.0.0.1", 55591, "billing_qa", "billing_qa")
                or os.environ.get("TRAX_BILLING_ALLOW_RESET") != "billing-01a19993"):
            raise RuntimeError("Exclusive disposable billing PostgreSQL required")
        os.environ.update(DATABASE_URL=url.render_as_string(hide_password=False), APP_ENV="testing",
                          SECRET_KEY="billing-exclusive-fixture-secret")
        cls.migration_config = Config("alembic.ini")
        command.upgrade(cls.migration_config, "20261101_01")
        cls.app = create_app()

    def setUp(self):
        with self.app.app_context():
            names = [n for n in sa.inspect(db.engine).get_table_names() if n != "alembic_version"]
            quoted = ", ".join(db.engine.dialect.identifier_preparer.quote(n) for n in names)
            db.session.execute(sa.text("TRUNCATE TABLE " + quoted + " RESTART IDENTITY CASCADE"))
            db.session.add_all([User(id=i, nombre="QA", email=f"billing-{i}@qa.invalid", password="x",
                                    rol="CLIENTE" if i == 30 else "PROFESIONAL", estado="ACTIVO")
                                for i in (10, 20, 30)])
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()

    def race(self, action):
        barrier = Barrier(2)
        def run(index):
            with self.app.app_context():
                barrier.wait(timeout=10)
                try:
                    result = action(index)
                    db.session.commit()
                    return result
                except (IntegrityError, StaleDataError, BillingConflict):
                    db.session.rollback()
                    return "conflict"
                finally:
                    db.session.remove()
        with ThreadPoolExecutor(max_workers=2) as workers:
            return list(workers.map(run, (0, 1)))

    def test_concurrent_profile_updates_preserve_version(self):
        with self.app.app_context():
            self.grant()
            self.profile()
            db.session.commit()
        results = self.race(lambda i: self.profile(expected_version=1, legal_name=f"Emisor {i}"))
        self.assertEqual(results.count("conflict"), 1)

    def test_concurrent_draft_creation_and_same_key_recovery(self):
        with self.app.app_context():
            self.grant()
            self.profile()
            db.session.commit()
        key = str(uuid4())
        results = self.race(lambda i: self.draft(request_key=key))
        successful = [r for r in results if r != "conflict"]
        self.assertGreaterEqual(len(successful), 1)
        with self.app.app_context():
            recovered = self.draft(request_key=key)
            self.assertTrue(all(r == recovered for r in successful))
            self.assertEqual(BillingDraft.query.count(), 1)
            db.session.rollback()

    def test_migration_roundtrip_preserves_legacy_users(self):
        with self.app.app_context():
            db.session.remove()
        command.downgrade(self.migration_config, "20261030_01")
        with self.app.app_context():
            self.assertEqual(db.session.query(User).count(), 3)
            self.assertNotIn("billing_drafts", sa.inspect(db.engine).get_table_names())
            db.session.remove()
        command.upgrade(self.migration_config, "20261101_01")
        with self.app.app_context():
            self.assertIn("billing_drafts", sa.inspect(db.engine).get_table_names())


if __name__ == "__main__":
    unittest.main()
