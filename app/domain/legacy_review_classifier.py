from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Sequence, Tuple


class LegacyReviewClassificationCode(str, Enum):
    LINKED_UNIQUE = "LINKED_UNIQUE"
    NO_CANDIDATE = "NO_CANDIDATE"
    MULTIPLE_CANDIDATES = "MULTIPLE_CANDIDATES"
    DUPLICATE_FOR_CONTRACT = "DUPLICATE_FOR_CONTRACT"
    INVALID_RATING = "INVALID_RATING"
    IDENTITY_INCONSISTENT = "IDENTITY_INCONSISTENT"
    INSUFFICIENT_CONFIRMATION_EVIDENCE = (
        "INSUFFICIENT_CONFIRMATION_EVIDENCE"
    )


@dataclass(frozen=True)
class LegacyReviewData:
    id: int
    cliente_id: Optional[int]
    professional_id: Optional[int]
    rating: Optional[int]
    created_at: Optional[datetime]


@dataclass(frozen=True)
class CandidateContractData:
    id: int
    cliente_id: Optional[int]
    professional_id: Optional[int]
    estado: str
    created_at: Optional[datetime]
    confirmed_at: Optional[datetime]


@dataclass(frozen=True)
class CompetingLegacyReviewData:
    review_id: int
    candidate_contract_ids: Tuple[int, ...]


@dataclass(frozen=True)
class LegacyReviewClassification:
    code: LegacyReviewClassificationCode
    contract_id: Optional[int] = None


def _is_positive_identifier(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def classify_legacy_review(
    review: LegacyReviewData,
    candidate_contracts: Sequence[CandidateContractData],
    competing_reviews: Sequence[CompetingLegacyReviewData] = (),
):
    """Classify normalized legacy data without querying or mutating it.

    Priority is deliberate: invalid identities, invalid rating, candidate
    ambiguity, duplicate ownership, and finally a unique safe link.
    Dates only reject impossible links; they never rank candidates.
    """

    if not _is_positive_identifier(review.cliente_id) or not _is_positive_identifier(
        review.professional_id
    ):
        return LegacyReviewClassification(
            LegacyReviewClassificationCode.IDENTITY_INCONSISTENT
        )

    if (
        not isinstance(review.rating, int)
        or isinstance(review.rating, bool)
        or review.rating not in (1, 2, 3, 4, 5)
    ):
        return LegacyReviewClassification(
            LegacyReviewClassificationCode.INVALID_RATING
        )

    identity_matches = tuple(
        contract
        for contract in candidate_contracts
        if contract.cliente_id == review.cliente_id
        and contract.professional_id == review.professional_id
    )
    if not identity_matches:
        partial_identity_match = any(
            contract.cliente_id == review.cliente_id
            or contract.professional_id == review.professional_id
            for contract in candidate_contracts
        )
        return LegacyReviewClassification(
            LegacyReviewClassificationCode.IDENTITY_INCONSISTENT
            if partial_identity_match
            else LegacyReviewClassificationCode.NO_CANDIDATE
        )

    confirmed_matches = tuple(
        contract
        for contract in identity_matches
        if contract.estado == "CONFIRMADA"
    )
    if not confirmed_matches:
        return LegacyReviewClassification(
            LegacyReviewClassificationCode.NO_CANDIDATE
        )

    if review.created_at is None:
        return LegacyReviewClassification(
            LegacyReviewClassificationCode.INSUFFICIENT_CONFIRMATION_EVIDENCE
        )

    temporally_possible = tuple(
        contract
        for contract in confirmed_matches
        if contract.created_at is not None
        and contract.created_at <= review.created_at
    )
    missing_creation_evidence = any(
        contract.created_at is None for contract in confirmed_matches
    )
    if not temporally_possible:
        return LegacyReviewClassification(
            LegacyReviewClassificationCode.INSUFFICIENT_CONFIRMATION_EVIDENCE
            if missing_creation_evidence
            else LegacyReviewClassificationCode.NO_CANDIDATE
        )

    confirmed_before_review = tuple(
        contract
        for contract in temporally_possible
        if contract.confirmed_at is not None
        and contract.confirmed_at <= review.created_at
    )
    missing_confirmation_evidence = any(
        contract.confirmed_at is None for contract in temporally_possible
    )
    if missing_confirmation_evidence:
        return LegacyReviewClassification(
            LegacyReviewClassificationCode.INSUFFICIENT_CONFIRMATION_EVIDENCE
        )
    if not confirmed_before_review:
        return LegacyReviewClassification(
            LegacyReviewClassificationCode.NO_CANDIDATE
        )
    if len(confirmed_before_review) > 1:
        return LegacyReviewClassification(
            LegacyReviewClassificationCode.MULTIPLE_CANDIDATES
        )

    contract_id = confirmed_before_review[0].id
    has_competitor = any(
        competing.review_id != review.id
        and contract_id in competing.candidate_contract_ids
        for competing in competing_reviews
    )
    if has_competitor:
        return LegacyReviewClassification(
            LegacyReviewClassificationCode.DUPLICATE_FOR_CONTRACT
        )

    return LegacyReviewClassification(
        LegacyReviewClassificationCode.LINKED_UNIQUE,
        contract_id=contract_id,
    )


__all__ = (
    "CandidateContractData",
    "CompetingLegacyReviewData",
    "LegacyReviewClassification",
    "LegacyReviewClassificationCode",
    "LegacyReviewData",
    "classify_legacy_review",
)
