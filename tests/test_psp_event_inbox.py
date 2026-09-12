import inspect
import unittest
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError

from app import create_app, db
from app.config.config import TestingConfig
from app.models.psp_event import PSPEventRecord
from app.services.psp_event_contract import PSPEvent
from app.services.psp_event_inbox import (
    PSPEventConflictError,
    get_event,
    get_event_by_identity,
    register_or_get_event,
)


class PSPEventInboxTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestingConfig)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.event = PSPEvent(
            provider="provider-A", external_event_id="evt/opaque?1", topic="payment",
            action="payment.updated", external_resource_id="000-RESOURCE",
            test_mode=True,
            occurred_at=datetime(2026, 9, 11, 20, tzinfo=timezone.utc),
            received_at=datetime(2026, 9, 11, 20, 1, tzinfo=timezone.utc),
            payload_hash="a" * 64,
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def test_contract_is_immutable_and_has_no_financial_state(self):
        with self.assertRaises(FrozenInstanceError):
            self.event.action = "changed"
        self.assertFalse(hasattr(self.event, "financial_status"))

    def test_contract_rejects_invalid_values(self):
        for field, value in (
            ("provider", " "), ("external_event_id", None), ("topic", ""),
            ("action", 1), ("external_resource_id", "\t"),
            ("test_mode", 1), ("received_at", datetime(2026, 9, 11)),
            ("occurred_at", datetime(2026, 9, 11)), ("payload_hash", "x" * 64),
        ):
            with self.subTest(field=field), self.assertRaises(ValueError):
                replace(self.event, **{field: value})

    def test_register_query_and_identical_replay(self):
        first = register_or_get_event(db.session, self.event)
        replay = register_or_get_event(db.session, self.event)
        self.assertEqual(first.id, replay.id)
        self.assertEqual(get_event(db.session, first.id).id, first.id)
        self.assertEqual(
            get_event_by_identity(db.session, "provider-A", True, "evt/opaque?1").id,
            first.id,
        )

    def test_each_canonical_field_change_conflicts(self):
        register_or_get_event(db.session, self.event)
        changes = {
            "topic": "merchant_order", "action": "payment.created",
            "external_resource_id": "other", "occurred_at": self.event.occurred_at + timedelta(seconds=1),
            "payload_hash": "b" * 64,
        }
        for field, value in changes.items():
            with self.subTest(field=field), self.assertRaises(PSPEventConflictError):
                register_or_get_event(db.session, replace(self.event, **{field: value}))

    def test_redelivery_keeps_first_received_at_without_updating_row(self):
        first = register_or_get_event(db.session, self.event)
        original_received_at = first.received_at
        replay = register_or_get_event(
            db.session,
            replace(self.event, received_at=self.event.received_at + timedelta(hours=2)),
        )
        self.assertEqual(replay.id, first.id)
        self.assertEqual(replay.received_at, original_received_at)
        self.assertFalse(db.session.is_modified(replay))

    def test_payload_hash_is_canonical_lowercase_for_replay_and_storage(self):
        uppercase = replace(self.event, payload_hash="ABCDEF" * 10 + "ABCD")
        self.assertEqual(uppercase.payload_hash, ("abcdef" * 10 + "abcd"))
        first = register_or_get_event(db.session, uppercase)
        replay = register_or_get_event(
            db.session, replace(uppercase, payload_hash=uppercase.payload_hash.upper())
        )
        self.assertEqual(replay.id, first.id)
        self.assertEqual(replay.payload_hash, uppercase.payload_hash)

        with self.assertRaises(PSPEventConflictError):
            register_or_get_event(
                db.session, replace(uppercase, payload_hash="b" * 64)
            )

    def test_mode_is_part_of_identity_and_same_resource_accepts_distinct_events(self):
        first = register_or_get_event(db.session, self.event)
        production = register_or_get_event(db.session, replace(self.event, test_mode=False))
        second = register_or_get_event(
            db.session, replace(self.event, external_event_id="second-event")
        )
        self.assertEqual({first.id, production.id, second.id}, {1, 2, 3})

    def test_occurred_at_is_optional_and_received_at_is_not_a_substitute(self):
        event = replace(self.event, occurred_at=None)
        record = register_or_get_event(db.session, event)
        self.assertIsNone(record.occurred_at)
        self.assertEqual(record.received_at, event.received_at)

    def test_helper_never_commits_or_calls_provider(self):
        import app.services.psp_event_inbox as service
        source = inspect.getsource(service)
        self.assertNotIn(".commit(", source)
        self.assertNotIn("create_attempt(", source)
        self.assertNotIn("get_attempt(", source)

    def test_unrelated_integrity_error_is_preserved(self):
        invalid = PSPEventRecord(
            provider="provider", external_event_id="invalid", topic="topic",
            action="action", external_resource_id="resource", test_mode=True,
            occurred_at=None, received_at=self.event.received_at, payload_hash="short",
        )
        db.session.add(invalid)
        with self.assertRaises(IntegrityError):
            db.session.flush()


if __name__ == "__main__":
    unittest.main()
