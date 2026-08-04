from dataclasses import dataclass
from typing import Mapping, Optional, Sequence, Tuple

from app.domain.legacy_review_classifier import (
    CandidateContractData,
    CompetingLegacyReviewData,
    LegacyReviewClassificationCode,
    LegacyReviewData,
    classify_legacy_review,
)


@dataclass(frozen=True)
class LegacyReviewMigrationDecision:
    review_id: int
    classification_code: str
    contract_id: Optional[int]
    original_rating: object


def _review_data(row: Mapping):
    return LegacyReviewData(
        id=row["id"],
        cliente_id=row["cliente_id"],
        professional_id=row["professional_id"],
        rating=row["rating"],
        created_at=row["created_at"],
    )


def _contract_data(row: Mapping):
    return CandidateContractData(
        id=row["id"],
        cliente_id=row["cliente_id"],
        professional_id=row["professional_id"],
        estado=row["estado"],
        created_at=row["fecha_creacion"],
        confirmed_at=row["confirmed_at"],
    )


def classify_legacy_review_rows(
    review_rows: Sequence[Mapping],
    contract_rows: Sequence[Mapping],
) -> Tuple[LegacyReviewMigrationDecision, ...]:
    """Adapt database-shaped rows to the closed, pure legacy classifier.

    Classification is deliberately two-pass. The first pass discovers only
    individually unambiguous candidates. The second pass supplies those
    candidates as competition evidence, so every review competing for one
    contract is left unlinked.
    """

    reviews = tuple(_review_data(row) for row in review_rows)
    contracts = tuple(_contract_data(row) for row in contract_rows)
    preliminary = {
        review.id: classify_legacy_review(review, contracts)
        for review in reviews
    }
    competition = tuple(
        CompetingLegacyReviewData(
            review_id=review.id,
            candidate_contract_ids=(preliminary[review.id].contract_id,),
        )
        for review in reviews
        if preliminary[review.id].code
        == LegacyReviewClassificationCode.LINKED_UNIQUE
    )

    decisions = []
    rows_by_id = {row["id"]: row for row in review_rows}
    for review in reviews:
        classification = classify_legacy_review(
            review,
            contracts,
            competition,
        )
        decisions.append(
            LegacyReviewMigrationDecision(
                review_id=review.id,
                classification_code=classification.code.value,
                contract_id=classification.contract_id,
                original_rating=rows_by_id[review.id]["rating"],
            )
        )
    return tuple(decisions)


__all__ = (
    "LegacyReviewMigrationDecision",
    "classify_legacy_review_rows",
)
