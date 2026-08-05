import copy
import unittest

from app.domain.reputation_metrics import (
    ContractMetricFact,
    ReviewMetricFact,
    build_neutral_reputation_metrics,
)


class NeutralReputationMetricsTest(unittest.TestCase):
    def test_builds_neutral_metrics_without_points_or_ranking(self):
        reviews = (
            ReviewMetricFact(1, 10, 101, "CONTRACTUAL", "VERIFIED", "ELIGIBLE", 5),
            ReviewMetricFact(2, 10, 102, "LEGACY", "VERIFIED", "ELIGIBLE", 3),
            ReviewMetricFact(3, 10, 103, "CONTRACTUAL", "VERIFIED", "EXCLUDED", 1),
            ReviewMetricFact(4, 10, None, "LEGACY", "UNVERIFIED", "EXCLUDED", 4),
            ReviewMetricFact(5, 99, 901, "CONTRACTUAL", "VERIFIED", "ELIGIBLE", 5),
        )
        contracts = (
            ContractMetricFact(101, 10, "CONFIRMADA"),
            ContractMetricFact(102, 10, "CONFIRMADA"),
            ContractMetricFact(103, 10, "CONFIRMADA"),
            ContractMetricFact(104, 10, "COMPLETADA"),
            ContractMetricFact(901, 99, "CONFIRMADA"),
        )

        metrics = build_neutral_reputation_metrics(10, reviews, contracts)

        self.assertEqual(metrics.contractual_verified_reviews, 2)
        self.assertEqual(metrics.legacy_verified_reviews, 1)
        self.assertEqual(metrics.eligible_rating_count, 2)
        self.assertEqual(metrics.average_eligible_rating, 4.0)
        self.assertEqual(
            metrics.star_distribution,
            ((1, 0), (2, 0), (3, 1), (4, 0), (5, 1)),
        )
        self.assertEqual(metrics.confirmed_contracts, 3)
        self.assertEqual(metrics.confirmed_contracts_with_review, 3)
        self.assertEqual(metrics.review_coverage, 1.0)
        self.assertFalse(hasattr(metrics, "score"))
        self.assertFalse(hasattr(metrics, "ranking"))

    def test_invalid_and_unverified_ratings_are_excluded(self):
        reviews = (
            ReviewMetricFact(1, 10, 101, "LEGACY", "VERIFIED", "ELIGIBLE", 0),
            ReviewMetricFact(2, 10, 102, "LEGACY", "VERIFIED", "ELIGIBLE", 6),
            ReviewMetricFact(3, 10, None, "LEGACY", "UNVERIFIED", "ELIGIBLE", 5),
        )
        metrics = build_neutral_reputation_metrics(
            10,
            reviews,
            (ContractMetricFact(101, 10, "CONFIRMADA"),),
        )
        self.assertEqual(metrics.eligible_rating_count, 0)
        self.assertIsNone(metrics.average_eligible_rating)
        self.assertEqual(
            metrics.star_distribution,
            ((1, 0), (2, 0), (3, 0), (4, 0), (5, 0)),
        )

    def test_no_confirmed_contracts_produces_zero_coverage(self):
        metrics = build_neutral_reputation_metrics(10, (), ())
        self.assertEqual(metrics.confirmed_contracts, 0)
        self.assertEqual(metrics.confirmed_contracts_with_review, 0)
        self.assertEqual(metrics.review_coverage, 0.0)

    def test_null_and_unknown_origins_never_enter_public_metrics(self):
        reviews = (
            ReviewMetricFact(1, 10, 101, None, "VERIFIED", "ELIGIBLE", 5),
            ReviewMetricFact(2, 10, 102, "UNKNOWN", "VERIFIED", "ELIGIBLE", 4),
            ReviewMetricFact(3, 10, 103, "LEGACY_EVENT", "VERIFIED", "ELIGIBLE", 3),
        )
        contracts = tuple(
            ContractMetricFact(identifier, 10, "CONFIRMADA")
            for identifier in (101, 102, 103)
        )
        metrics = build_neutral_reputation_metrics(10, reviews, contracts)
        self.assertEqual(metrics.contractual_verified_reviews, 0)
        self.assertEqual(metrics.legacy_verified_reviews, 0)
        self.assertEqual(metrics.eligible_rating_count, 0)
        self.assertIsNone(metrics.average_eligible_rating)
        self.assertEqual(
            metrics.star_distribution,
            ((1, 0), (2, 0), (3, 0), (4, 0), (5, 0)),
        )
        self.assertEqual(metrics.confirmed_contracts_with_review, 0)

    def test_metrics_are_deterministic_and_do_not_mutate_inputs(self):
        reviews = (
            ReviewMetricFact(1, 10, 101, "CONTRACTUAL", "VERIFIED", "ELIGIBLE", 4),
        )
        contracts = (ContractMetricFact(101, 10, "CONFIRMADA"),)
        original = copy.deepcopy((reviews, contracts))
        first = build_neutral_reputation_metrics(10, reviews, contracts)
        second = build_neutral_reputation_metrics(10, reviews, contracts)
        self.assertEqual(first, second)
        self.assertEqual((reviews, contracts), original)


if __name__ == "__main__":
    unittest.main()
