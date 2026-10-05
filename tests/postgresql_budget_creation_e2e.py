"""Explicit, destructive gate: reserved disposable PostgreSQL database only."""
import os
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from tests.postgresql_payment_persistence_e2e import _validate_postgresql_test_url
from tests.alembic_head_validation import assert_database_at_repository_head
from app import create_app, db
from app.models.user import User
from app.models.budget_request import BudgetRequest
from app.models.activity_notification import ActivityNotification
from app.models.operation_command import OperationCommand
from app.services.budget_creation_key_service import issue_budget_key
from app.services.budget_service import create_budget_request, BudgetCreationConflict
from app.services.operation_notification_service import notify_budget_created


class PostgreSQLBudgetCreationGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        url = os.environ.get('TRAX_POSTGRES_TEST_URL')
        _validate_postgresql_test_url(url, os.environ.get('TRAX_POSTGRES_TEST_ALLOW_RESET'))
        if os.environ.get('DATABASE_URL') != url:
            raise RuntimeError('Application and gate database must match exactly')
        config = Config('alembic.ini')
        command.upgrade(config, 'head')
        cls.app = create_app(initialize_schema=False)
        cls.app.config.update(TESTING=True)
        with cls.app.app_context():
            if db.engine.dialect.name != 'postgresql':
                raise RuntimeError('PostgreSQL required')
            assert_database_at_repository_head(config, db.session.execute(sa.text('SELECT version_num FROM alembic_version')).scalars().all())
            cls.engine = db.engine

    def setUp(self):
        with self.app.app_context():
            names = ', '.join(db.engine.dialect.identifier_preparer.quote(t.name) for t in db.metadata.sorted_tables)
            db.session.execute(sa.text(f'TRUNCATE TABLE {names} RESTART IDENTITY CASCADE'))
            actor = User(nombre='Budget PG', email='budget-pg@test.local', password='hash', rol='CLIENTE', estado='ACTIVO')
            db.session.add(actor)
            db.session.commit()
            self.actor = actor.id
            self.key = issue_budget_key(actor.id)
        self.data = dict(titulo='PG concurrency', categoria='Plomería', zona='CABA', descripcion='Prueba aislada')

    def create(self, title=None):
        with self.app.app_context():
            try:
                result = create_budget_request(self.actor, **{**self.data, **({'titulo': title} if title else {})}, idempotency_key=self.key)
                return ('ok', result.id)
            except BudgetCreationConflict:
                return ('conflict', None)
            finally:
                db.session.remove()

    def assert_facts(self, count):
        with self.app.app_context():
            self.assertEqual(tuple(m.query.count() for m in (BudgetRequest, ActivityNotification, OperationCommand)), (count,) * 3)
            if count:
                command_row = OperationCommand.query.one()
                self.assertEqual(command_row.status, 'SUCCEEDED')
                self.assertEqual(command_row.result_entity_id, BudgetRequest.query.one().id)

    def race(self, different=False):
        barrier = threading.Barrier(2, timeout=15)
        connections = set()
        def synchronize_insert(connection, cursor, statement, parameters, context, executemany):
            if statement.startswith('INSERT INTO operation_commands'):
                connections.add(id(connection.connection))
                barrier.wait()
        sa.event.listen(self.engine, 'before_cursor_execute', synchronize_insert)
        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(self.create, 'Changed payload' if different and i else None) for i in range(2)]
                results = [f.result(timeout=30) for f in futures]
        finally:
            sa.event.remove(self.engine, 'before_cursor_execute', synchronize_insert)
        self.assertEqual(len(connections), 2)
        return results

    def test_concurrent_unique_same_key_same_result(self):
        results = self.race()
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[0][0], 'ok')
        self.assert_facts(1)

    def test_concurrent_payload_conflict(self):
        results = self.race(different=True)
        self.assertEqual(sorted(r[0] for r in results), ['conflict', 'ok'])
        self.assert_facts(1)

    def test_notification_failure_rollback_and_same_session_retry(self):
        with self.app.app_context():
            def fail(budget):
                notify_budget_created(budget)
                db.session.flush()
                raise RuntimeError('notification failure after flush')
            with patch('app.services.budget_service.notify_budget_created', side_effect=fail):
                with self.assertRaises(RuntimeError):
                    create_budget_request(self.actor, **self.data, idempotency_key=self.key)
            self.assertEqual(tuple(m.query.count() for m in (BudgetRequest, ActivityNotification, OperationCommand)), (0, 0, 0))
            first = create_budget_request(self.actor, **self.data, idempotency_key=self.key)
            self.assertEqual(create_budget_request(self.actor, **self.data, idempotency_key=self.key).id, first.id)
        self.assert_facts(1)

    def test_racing_waiter_succeeds_when_first_transaction_rolls_back(self):
        first_notifying = threading.Event()
        waiter_inserting = threading.Event()
        def signal_waiter(connection, cursor, statement, parameters, context, executemany):
            if statement.startswith('INSERT INTO operation_commands') and first_notifying.is_set():
                waiter_inserting.set()
        def notify_or_fail(budget):
            notify_budget_created(budget)
            db.session.flush()
            if not first_notifying.is_set():
                first_notifying.set()
                if not waiter_inserting.wait(15):
                    raise AssertionError('waiter did not reach PostgreSQL insert')
                raise RuntimeError('first transaction fails')
        sa.event.listen(self.engine, 'before_cursor_execute', signal_waiter)
        try:
            with patch('app.services.budget_service.notify_budget_created', side_effect=notify_or_fail):
                with ThreadPoolExecutor(max_workers=2) as executor:
                    first = executor.submit(self.create)
                    self.assertTrue(first_notifying.wait(15))
                    second = executor.submit(self.create)
                    with self.assertRaises(RuntimeError):
                        first.result(timeout=30)
                    self.assertEqual(second.result(timeout=30)[0], 'ok')
        finally:
            sa.event.remove(self.engine, 'before_cursor_execute', signal_waiter)
        self.assert_facts(1)


if __name__ == '__main__':
    unittest.main()
