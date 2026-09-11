import unittest
from unittest.mock import patch

from tests.postgresql_payment_persistence_e2e import (
    POSTGRESQL_IDENTIFIER_MAX_BYTES,
    RESERVED_DATABASE,
    _create_guarded_engine,
    _validate_postgresql_test_url,
)


class PostgreSQLPaymentPersistenceGuardTest(unittest.TestCase):
    def test_accepts_only_reserved_safe_database_names(self):
        accepted = (
            RESERVED_DATABASE,
            f"{RESERVED_DATABASE}_a1",
            f"{RESERVED_DATABASE}_finalaudit_20260910",
        )
        for database in accepted:
            with self.subTest(database=database):
                parsed = _validate_postgresql_test_url(
                    f"postgresql://user:pass@postgres/{database}", "1"
                )
                self.assertEqual(parsed.database, database)

    def test_rejects_unsafe_names_and_missing_authorization(self):
        invalid = (
            "trax_db", "postgres", "template0", "template1", "arbitrary",
            f"{RESERVED_DATABASE}_", f"{RESERVED_DATABASE}__a",
            f"{RESERVED_DATABASE}_UPPER", f"{RESERVED_DATABASE}-a",
            f"{RESERVED_DATABASE}.a", f"{RESERVED_DATABASE}_á",
            f"{RESERVED_DATABASE}_a%20b", f"{RESERVED_DATABASE}_a/b",
            f"{RESERVED_DATABASE}_a\\b", f"{RESERVED_DATABASE}_a?x=1",
        )
        for database in invalid:
            with self.subTest(database=database):
                with self.assertRaises(RuntimeError):
                    _validate_postgresql_test_url(
                        f"postgresql://user:pass@postgres/{database}", "1"
                    )
        with self.assertRaises(RuntimeError):
            _validate_postgresql_test_url(
                f"postgresql://user:pass@postgres/{RESERVED_DATABASE}", None
            )

    def test_rejects_overlength_name_and_query_parameters(self):
        suffix_length = POSTGRESQL_IDENTIFIER_MAX_BYTES - len(RESERVED_DATABASE) + 1
        with self.assertRaises(RuntimeError):
            _validate_postgresql_test_url(
                f"postgresql://user:pass@postgres/{RESERVED_DATABASE}_{'a' * suffix_length}",
                "1",
            )
        with self.assertRaises(RuntimeError):
            _validate_postgresql_test_url(
                f"postgresql://user:pass@postgres/{RESERVED_DATABASE}?sslmode=disable",
                "1",
            )

    def test_invalid_input_never_creates_an_engine(self):
        with patch("tests.postgresql_payment_persistence_e2e.sa.create_engine") as create_engine:
            for url in (
                None,
                "sqlite:///:memory:",
                "postgresql://user:pass@postgres/trax_db",
            ):
                with self.subTest(url=url):
                    with self.assertRaises(RuntimeError):
                        _create_guarded_engine(url, "1")
            create_engine.assert_not_called()


if __name__ == "__main__":
    unittest.main()
