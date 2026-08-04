import ast
import copy
import inspect
import unittest
from datetime import timedelta

from app.domain import legacy_review_classifier
from app.domain.legacy_review_classifier import (
    CompetingLegacyReviewData,
    LegacyReviewClassificationCode,
    LegacyReviewData,
    classify_legacy_review,
)
from tests.fixtures.legacy_review_cases import (
    CLASSIFICATION_CASES,
    REVIEW_TIME,
    confirmed_contract,
    legacy_review,
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


if __name__ == "__main__":
    unittest.main()
