import os
import tempfile
import unittest
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory


ROOT = Path(__file__).resolve().parents[1]


class PSPEventInboxMigrationTest(unittest.TestCase):
    def test_upgrade_downgrade_upgrade(self):
        with tempfile.TemporaryDirectory() as temporary:
            url = f"sqlite:///{(Path(temporary) / 'events.db').as_posix()}"
            previous = os.environ.get("DATABASE_URL")
            os.environ["DATABASE_URL"] = url
            engine = sa.create_engine(url)
            config = Config(str(ROOT / "alembic.ini"))
            try:
                self.assertEqual(ScriptDirectory.from_config(config).get_heads(), ["20260911_01"])
                command.upgrade(config, "20260910_01")
                self.assertNotIn("psp_event_inbox", sa.inspect(engine).get_table_names())
                command.upgrade(config, "head")
                self.assertIn("psp_event_inbox", sa.inspect(engine).get_table_names())
                command.downgrade(config, "20260910_01")
                self.assertNotIn("psp_event_inbox", sa.inspect(engine).get_table_names())
                command.upgrade(config, "head")
                self.assertIn("psp_event_inbox", sa.inspect(engine).get_table_names())
            finally:
                engine.dispose()
                if previous is None:
                    os.environ.pop("DATABASE_URL", None)
                else:
                    os.environ["DATABASE_URL"] = previous


if __name__ == "__main__":
    unittest.main()
