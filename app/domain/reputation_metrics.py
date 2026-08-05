from dataclasses import dataclass
from typing import Optional, Sequence, Tuple


@dataclass(frozen=True)
class ReviewMetricFact:
    id: int
    professional_id: int
    contract_id: Optional[int]
    origin: str
    verification_status: str
    rating_eligibility_status: str
    rating: Optional[int]


@dataclass(frozen=True)
class ContractMetricFact:
    id: int
    professional_id: int
    estado: str


@dataclass(frozen=True)
class NeutralReputationMetrics:
    contractual_verified_reviews: int
    legacy_verified_reviews: int
    eligible_rating_count: int
    average_eligible_rating: Optional[float]
    star_distribution: Tuple[Tuple[int, int], ...]
    confirmed_contracts: int
    confirmed_contracts_with_review: int
    review_coverage: float


def build_neutral_reputation_metrics(
    professional_id: int,
    reviews: Sequence[ReviewMetricFact],
    contracts: Sequence[ContractMetricFact],
):
    """Aggregate neutral, reconstructible facts without assigning a score."""

    professional_reviews = tuple(
        review for review in reviews if review.professional_id == professional_id
    )
    admitted_reviews = tuple(
        review
        for review in professional_reviews
        if review.origin in ("CONTRACTUAL", "LEGACY")
    )
    verified_reviews = tuple(
        review
        for review in admitted_reviews
        if review.verification_status == "VERIFIED"
        and review.contract_id is not None
    )
    contractual_verified = sum(
        review.origin == "CONTRACTUAL" for review in verified_reviews
    )
    legacy_verified = sum(review.origin == "LEGACY" for review in verified_reviews)

    eligible_ratings = tuple(
        review.rating
        for review in verified_reviews
        if review.rating_eligibility_status == "ELIGIBLE"
        and isinstance(review.rating, int)
        and not isinstance(review.rating, bool)
        and review.rating in (1, 2, 3, 4, 5)
    )
    distribution = tuple(
        (stars, eligible_ratings.count(stars)) for stars in range(1, 6)
    )
    average = (
        round(sum(eligible_ratings) / len(eligible_ratings), 2)
        if eligible_ratings
        else None
    )

    confirmed_contract_ids = {
        contract.id
        for contract in contracts
        if contract.professional_id == professional_id
        and contract.estado == "CONFIRMADA"
    }
    reviewed_contract_ids = {
        review.contract_id
        for review in verified_reviews
        if review.contract_id in confirmed_contract_ids
    }
    confirmed_count = len(confirmed_contract_ids)
    reviewed_count = len(reviewed_contract_ids)

    return NeutralReputationMetrics(
        contractual_verified_reviews=contractual_verified,
        legacy_verified_reviews=legacy_verified,
        eligible_rating_count=len(eligible_ratings),
        average_eligible_rating=average,
        star_distribution=distribution,
        confirmed_contracts=confirmed_count,
        confirmed_contracts_with_review=reviewed_count,
        review_coverage=(
            round(reviewed_count / confirmed_count, 4)
            if confirmed_count
            else 0.0
        ),
    )


__all__ = (
    "ContractMetricFact",
    "NeutralReputationMetrics",
    "ReviewMetricFact",
    "build_neutral_reputation_metrics",
)
