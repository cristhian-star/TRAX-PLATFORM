import ast
import copy
import inspect
import re
import unittest
from dataclasses import fields
from datetime import timedelta
from pathlib import Path

from app.domain import legacy_review_classifier
from app.domain import legacy_review_migration_adapter
from app.domain.legacy_review_classifier import (
    CandidateContractData,
    CompetingLegacyReviewData,
    LegacyReviewClassificationCode,
    LegacyReviewData,
    classify_legacy_review,
)
from app.domain.legacy_review_migration_adapter import (
    classify_legacy_review_rows_fail_closed,
)
from tests.fixtures.legacy_review_cases import (
    CLASSIFICATION_CASES,
    REVIEW_TIME,
    confirmed_contract,
    legacy_review,
)
from migrations.compat._legacy_review_20260726_06_snapshot import (
    _classify_legacy_review_rows_20260726_06,
)


class LegacyReviewClassifierTest(unittest.TestCase):
    def test_all_synthetic_cases_have_expected_closed_result(self):
        for name, review, contracts, competitors, expected in CLASSIFICATION_CASES:
            with self.subTest(name=name):
                result = classify_legacy_review(review, contracts, competitors)
                self.assertEqual(result.code, expected)
                self.assertEqual(
                    result.contract_id is not None,
                    expected == LegacyReviewClassificationCode.LINKED_UNIQUE,
                )

    def test_classifier_is_deterministic_and_does_not_mutate_inputs(self):
        review = legacy_review()
        contracts = (
            confirmed_contract(id=200),
            confirmed_contract(id=201),
        )
        competitors = (
            CompetingLegacyReviewData(101, (200,)),
        )
        original = copy.deepcopy((review, contracts, competitors))

        first = classify_legacy_review(review, contracts, competitors)
        second = classify_legacy_review(review, contracts, competitors)

        self.assertEqual(first, second)
        self.assertEqual((review, contracts, competitors), original)

    def test_classifier_module_has_no_sql_orm_or_application_imports(self):
        source = inspect.getsource(legacy_review_classifier)
        tree = ast.parse(source)
        imported_roots = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported_roots.update(
            node.module.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        )
        self.assertTrue(
            imported_roots.isdisjoint(
                {"app", "flask", "flask_sqlalchemy", "sqlalchemy"}
            )
        )
        self.assertNotIn(".query", source)
        self.assertNotIn("commit(", source)

    def test_nearest_contract_is_never_selected_from_ambiguous_candidates(self):
        far_contract = confirmed_contract(
            id=301,
            created_at=REVIEW_TIME - timedelta(days=200),
            confirmed_at=REVIEW_TIME - timedelta(days=150),
        )
        near_contract = confirmed_contract(
            id=302,
            created_at=REVIEW_TIME - timedelta(days=2),
            confirmed_at=REVIEW_TIME - timedelta(hours=1),
        )
        result = classify_legacy_review(
            legacy_review(),
            (near_contract, far_contract),
        )
        reverse_result = classify_legacy_review(
            legacy_review(),
            (far_contract, near_contract),
        )
        self.assertEqual(
            result.code,
            LegacyReviewClassificationCode.MULTIPLE_CANDIDATES,
        )
        self.assertEqual(result, reverse_result)

    def test_unknown_confirmation_prevents_link_even_with_one_valid_candidate(self):
        result = classify_legacy_review(
            legacy_review(),
            (
                confirmed_contract(id=401),
                confirmed_contract(id=402, confirmed_at=None),
            ),
        )
        self.assertEqual(
            result.code,
            LegacyReviewClassificationCode.INSUFFICIENT_CONFIRMATION_EVIDENCE,
        )

    def test_error_priority_is_identity_then_rating_then_candidate_analysis(self):
        identity_and_rating_invalid = LegacyReviewData(
            id=500,
            cliente_id=None,
            professional_id=20,
            rating=0,
            created_at=REVIEW_TIME,
        )
        self.assertEqual(
            classify_legacy_review(
                identity_and_rating_invalid,
                (confirmed_contract(),),
            ).code,
            LegacyReviewClassificationCode.IDENTITY_INCONSISTENT,
        )
        self.assertEqual(
            classify_legacy_review(
                legacy_review(rating=0),
                (),
            ).code,
            LegacyReviewClassificationCode.INVALID_RATING,
        )

    def test_multiple_candidates_precede_duplicate_detection(self):
        result = classify_legacy_review(
            legacy_review(),
            (confirmed_contract(id=601), confirmed_contract(id=602)),
            (CompetingLegacyReviewData(101, (601,)),),
        )
        self.assertEqual(
            result.code,
            LegacyReviewClassificationCode.MULTIPLE_CANDIDATES,
        )

    def test_current_review_is_not_its_own_competitor(self):
        result = classify_legacy_review(
            legacy_review(id=700),
            (confirmed_contract(id=701),),
            (CompetingLegacyReviewData(700, (701,)),),
        )
        self.assertEqual(
            result.code,
            LegacyReviewClassificationCode.LINKED_UNIQUE,
        )

    def test_professional_ownership_mismatch_is_identity_inconsistent(self):
        result = classify_legacy_review(
            legacy_review(),
            (confirmed_contract(professional_user_id=30, profile_user_id=31),),
        )
        self.assertEqual(
            result.code,
            LegacyReviewClassificationCode.IDENTITY_INCONSISTENT,
        )

    def test_professional_profile_without_user_is_identity_inconsistent(self):
        result = classify_legacy_review(
            legacy_review(),
            (confirmed_contract(profile_user_id=None),),
        )
        self.assertEqual(
            result.code,
            LegacyReviewClassificationCode.IDENTITY_INCONSISTENT,
        )

    def test_contract_without_professional_user_is_identity_inconsistent(self):
        result = classify_legacy_review(
            legacy_review(),
            (confirmed_contract(professional_user_id=None),),
        )
        self.assertEqual(
            result.code,
            LegacyReviewClassificationCode.IDENTITY_INCONSISTENT,
        )

    def test_both_professional_user_ids_missing_is_identity_inconsistent(self):
        result = classify_legacy_review(
            legacy_review(),
            (
                confirmed_contract(
                    professional_user_id=None,
                    profile_user_id=None,
                ),
            ),
        )
        self.assertEqual(
            result.code,
            LegacyReviewClassificationCode.IDENTITY_INCONSISTENT,
        )

    def test_candidate_cannot_be_constructed_without_ownership_evidence(self):
        values = {
            "id": 900,
            "cliente_id": 10,
            "professional_id": 20,
            "estado": "CONFIRMADA",
            "created_at": REVIEW_TIME,
            "confirmed_at": REVIEW_TIME,
        }
        with self.assertRaises(TypeError):
            CandidateContractData(**values)

    def test_candidate_api_contains_only_current_required_fields(self):
        self.assertEqual(
            tuple(field.name for field in fields(CandidateContractData)),
            (
                "id",
                "cliente_id",
                "professional_id",
                "estado",
                "created_at",
                "confirmed_at",
                "professional_user_id",
                "profile_user_id",
            ),
        )

    def test_current_migration_adapter_rejects_rows_without_ownership_keys(self):
        review_row = {
            "id": 100,
            "cliente_id": 10,
            "professional_id": 20,
            "rating": 5,
            "created_at": REVIEW_TIME,
        }
        contract_row = {
            "id": 200,
            "cliente_id": 10,
            "professional_id": 20,
            "estado": "CONFIRMADA",
            "fecha_creacion": REVIEW_TIME,
            "confirmed_at": REVIEW_TIME,
        }
        with self.assertRaises(KeyError):
            classify_legacy_review_rows_fail_closed((review_row,), (contract_row,))

    def test_historical_alias_is_unexported_and_matches_snapshot(self):
        review_row = {
            "id": 100,
            "cliente_id": 10,
            "professional_id": 20,
            "rating": 5,
            "created_at": REVIEW_TIME,
        }
        contract_row = {
            "id": 200,
            "cliente_id": 10,
            "professional_id": 20,
            "estado": "CONFIRMADA",
            "fecha_creacion": REVIEW_TIME - timedelta(days=2),
            "confirmed_at": REVIEW_TIME - timedelta(days=1),
        }
        through_alias = legacy_review_migration_adapter.classify_legacy_review_rows(
            (review_row,),
            (contract_row,),
        )
        through_snapshot = _classify_legacy_review_rows_20260726_06(
            (review_row,),
            (contract_row,),
        )
        self.assertEqual(through_alias, through_snapshot)
        self.assertEqual(through_alias[0].classification_code, "LINKED_UNIQUE")
        self.assertNotIn(
            "classify_legacy_review_rows",
            legacy_review_migration_adapter.__all__,
        )

    def test_historical_snapshot_is_deterministic_pure_and_self_contained(self):
        review_rows = (
            {
                "id": 100,
                "cliente_id": 10,
                "professional_id": 20,
                "rating": 5,
                "created_at": REVIEW_TIME,
            },
        )
        contract_rows = (
            {
                "id": 200,
                "cliente_id": 10,
                "professional_id": 20,
                "estado": "CONFIRMADA",
                "fecha_creacion": REVIEW_TIME - timedelta(days=2),
                "confirmed_at": REVIEW_TIME - timedelta(days=1),
            },
        )
        original = copy.deepcopy((review_rows, contract_rows))
        first = _classify_legacy_review_rows_20260726_06(
            review_rows,
            contract_rows,
        )
        second = _classify_legacy_review_rows_20260726_06(
            review_rows,
            contract_rows,
        )
        self.assertEqual(first, second)
        self.assertEqual((review_rows, contract_rows), original)
        self.assertEqual(
            set(first[0].__dict__),
            {
                "review_id",
                "classification_code",
                "contract_id",
                "original_rating",
            },
        )

        snapshot_source = inspect.getsource(
            __import__(
                "migrations.compat._legacy_review_20260726_06_snapshot",
                fromlist=["*"],
            )
        )
        tree = ast.parse(snapshot_source)
        imported_roots = {
            node.module.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        self.assertTrue(imported_roots.isdisjoint({"app", "sqlalchemy", "flask"}))
        self.assertNotIn("commit(", snapshot_source)
        self.assertNotIn("execute(", snapshot_source)

    def test_historical_dependencies_are_confined_to_migrations_contract(self):
        project_root = Path(__file__).resolve().parents[1]
        exact_alias = re.compile(r"\bclassify_legacy_review_rows\b")
        production_references = []
        for root_name in ("app", "migrations", "scripts"):
            for path in (project_root / root_name).rglob("*.py"):
                relative = path.relative_to(project_root).as_posix()
                source = path.read_text(encoding="utf-8")
                if exact_alias.search(source):
                    production_references.append(relative)
        self.assertEqual(
            sorted(production_references),
            [
                "app/domain/legacy_review_migration_adapter.py",
                "migrations/versions/20260726_06_contract_reviews_reputation_integrity.py",
            ],
        )

        revision_07 = (
            project_root
            / "migrations/versions/20260726_07_contract_review_discriminator_hardening.py"
        ).read_text(encoding="utf-8")
        self.assertIn("classify_legacy_review_rows_fail_closed", revision_07)
        self.assertNotIn("_legacy_review_20260726_06_snapshot", revision_07)

    def test_migration_adapter_rejects_partial_ownership_payload(self):
        review_row = {
            "id": 100,
            "cliente_id": 10,
            "professional_id": 20,
            "rating": 5,
            "created_at": REVIEW_TIME,
        }
        base_contract = {
            "id": 200,
            "cliente_id": 10,
            "professional_id": 20,
            "estado": "CONFIRMADA",
            "fecha_creacion": REVIEW_TIME,
            "confirmed_at": REVIEW_TIME,
        }
        for partial in (
            {**base_contract, "professional_user_id": 30},
            {**base_contract, "profile_user_id": 30},
        ):
            with self.subTest(keys=tuple(sorted(partial))):
                with self.assertRaises(KeyError):
                    classify_legacy_review_rows_fail_closed(
                        (review_row,),
                        (partial,),
                    )

    def test_current_adapter_requires_complete_coherent_ownership(self):
        review_row = {
            "id": 100,
            "cliente_id": 10,
            "professional_id": 20,
            "rating": 5,
            "created_at": REVIEW_TIME,
        }
        base_contract = {
            "id": 200,
            "cliente_id": 10,
            "professional_id": 20,
            "estado": "CONFIRMADA",
            "fecha_creacion": REVIEW_TIME - timedelta(days=2),
            "confirmed_at": REVIEW_TIME - timedelta(days=1),
        }
        coherent = classify_legacy_review_rows_fail_closed(
            (review_row,),
            (
                {
                    **base_contract,
                    "professional_user_id": 30,
                    "profile_user_id": 30,
                },
            ),
        )[0]
        self.assertEqual(coherent.classification_code, "LINKED_UNIQUE")
        self.assertEqual(coherent.contract_id, 200)

        invalid_pairs = (
            (None, None),
            (30, None),
            (None, 30),
            (30, 31),
            (True, True),
            (0, 0),
            ("30", "30"),
        )
        for contract_owner, profile_owner in invalid_pairs:
            with self.subTest(
                contract_owner=contract_owner,
                profile_owner=profile_owner,
            ):
                decision = classify_legacy_review_rows_fail_closed(
                    (review_row,),
                    (
                        {
                            **base_contract,
                            "professional_user_id": contract_owner,
                            "profile_user_id": profile_owner,
                        },
                    ),
                )[0]
                self.assertEqual(
                    decision.classification_code,
                    "IDENTITY_INCONSISTENT",
                )
                self.assertIsNone(decision.contract_id)

    def test_invalid_professional_identifiers_are_always_inconsistent(self):
        invalid_values = (None, 0, -1, True, False, "1", "abc", 1.0)
        for field_name in ("professional_user_id", "profile_user_id"):
            for invalid_value in invalid_values:
                with self.subTest(field=field_name, value=invalid_value):
                    values = {
                        "professional_user_id": 30,
                        "profile_user_id": 30,
                        field_name: invalid_value,
                    }
                    result = classify_legacy_review(
                        legacy_review(),
                        (confirmed_contract(**values),),
                    )
                    self.assertEqual(
                        result.code,
                        LegacyReviewClassificationCode.IDENTITY_INCONSISTENT,
                    )

    def test_consistent_professional_ownership_remains_linkable(self):
        result = classify_legacy_review(
            legacy_review(),
            (confirmed_contract(professional_user_id=30, profile_user_id=30),),
        )
        self.assertEqual(
            result.code,
            LegacyReviewClassificationCode.LINKED_UNIQUE,
        )


if __name__ == "__main__":
    unittest.main()
