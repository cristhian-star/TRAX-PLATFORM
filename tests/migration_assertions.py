"""Assertions shared by tests that deliberately upgrade the complete history."""
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory


def assert_database_at_head(test, config, engine):
    heads = ScriptDirectory.from_config(config).get_heads()
    test.assertEqual(len(heads), 1, "Migration history must have exactly one head")
    with engine.connect() as connection:
        test.assertEqual(list(MigrationContext.configure(connection).get_current_heads()), heads)
