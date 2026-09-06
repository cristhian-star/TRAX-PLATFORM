import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from alembic.config import Config
from alembic.script import ScriptDirectory

from tests.alembic_head_validation import assert_database_at_repository_head


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class _FakeRevisionMap:
    def __init__(self, lineage):
        self.lineage = lineage

    def iterate_revisions(self, _head, _ancestor, **_kwargs):
        return iter(SimpleNamespace(revision=value) for value in self.lineage)


class _FakeScriptDirectory:
    def __init__(self, heads, known_revisions, lineage):
        self._heads = heads
        self._known_revisions = known_revisions
        self.revision_map = _FakeRevisionMap(lineage)

    def get_heads(self):
        return self._heads

    def get_revision(self, revision):
        if revision not in self._known_revisions:
            return None
        return SimpleNamespace(revision=revision)


class AlembicHeadValidationTest(unittest.TestCase):
    def _assert_with(self, script, applied):
        with patch(
            "tests.alembic_head_validation.ScriptDirectory.from_config",
            return_value=script,
        ):
            return assert_database_at_repository_head(object(), applied)

    def test_real_repository_has_one_current_head_with_required_ancestor(self):
        config = Config(str(PROJECT_ROOT / "alembic.ini"))
        heads = tuple(ScriptDirectory.from_config(config).get_heads())
        self.assertEqual(len(heads), 1)
        expected_head = heads[0]
        self.assertEqual(
            assert_database_at_repository_head(config, [expected_head]),
            expected_head,
        )

    def test_multiple_heads_fail(self):
        script = _FakeScriptDirectory(
            ("head_a", "head_b"),
            {"head_a", "head_b", "20260726_07"},
            ("head_a", "20260726_07"),
        )
        with self.assertRaisesRegex(RuntimeError, "exactamente un head"):
            self._assert_with(script, ["head_a"])

    def test_database_without_applied_revision_fails(self):
        script = _FakeScriptDirectory(
            ("new_head",),
            {"new_head", "20260726_07"},
            ("new_head", "20260726_07"),
        )
        with self.assertRaisesRegex(RuntimeError, "exactamente una revision"):
            self._assert_with(script, [])

    def test_database_at_historical_revision_fails_when_head_is_newer(self):
        script = _FakeScriptDirectory(
            ("new_head",),
            {"new_head", "20260726_07"},
            ("new_head", "20260726_07"),
        )
        with self.assertRaisesRegex(RuntimeError, "no esta en el head vigente"):
            self._assert_with(script, ["20260726_07"])

    def test_unknown_database_revision_fails(self):
        script = _FakeScriptDirectory(
            ("new_head",),
            {"new_head", "20260726_07"},
            ("new_head", "20260726_07"),
        )
        with self.assertRaisesRegex(RuntimeError, "aplicada desconocida"):
            self._assert_with(script, ["unknown_revision"])

    def test_missing_required_ancestor_fails(self):
        script = _FakeScriptDirectory(
            ("new_head",),
            {"new_head", "20260726_07"},
            ("new_head",),
        )
        with self.assertRaisesRegex(RuntimeError, "no es ancestro"):
            self._assert_with(script, ["new_head"])


if __name__ == "__main__":
    unittest.main()
