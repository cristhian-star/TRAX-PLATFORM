from datetime import datetime, timedelta

from app.domain.legacy_review_classifier import (
    CandidateContractData,
    CompetingLegacyReviewData,
    LegacyReviewClassificationCode,
    LegacyReviewData,
)


REVIEW_TIME = datetime(2026, 7, 20, 15, 0, 0)


def legacy_review(**overrides):
    values = {
        "id": 100,
        "cliente_id": 10,
        "professional_id": 20,
        "rating": 5,
        "created_at": REVIEW_TIME,
    }
    values.update(overrides)
    return LegacyReviewData(**values)


def confirmed_contract(**overrides):
    values = {
        "id": 200,
        "cliente_id": 10,
        "professional_id": 20,
        "estado": "CONFIRMADA",
        "created_at": REVIEW_TIME - timedelta(days=10),
        "confirmed_at": REVIEW_TIME - timedelta(days=1),
    }
    values.update(overrides)
    return CandidateContractData(**values)


CLASSIFICATION_CASES = (
    (
        "unique_candidate",
        legacy_review(),
        (confirmed_contract(),),
        (),
        LegacyReviewClassificationCode.LINKED_UNIQUE,
    ),
    (
        "multiple_candidates",
        legacy_review(),
        (
            confirmed_contract(id=200),
            confirmed_contract(
                id=201,
                created_at=REVIEW_TIME - timedelta(days=30),
                confirmed_at=REVIEW_TIME - timedelta(days=20),
            ),
        ),
        (),
        LegacyReviewClassificationCode.MULTIPLE_CANDIDATES,
    ),
    (
        "no_candidate",
        legacy_review(),
        (),
        (),
        LegacyReviewClassificationCode.NO_CANDIDATE,
    ),
    (
        "duplicate_reviews_for_contract",
        legacy_review(),
        (confirmed_contract(),),
        (
            CompetingLegacyReviewData(
                review_id=101,
                candidate_contract_ids=(200,),
            ),
        ),
        LegacyReviewClassificationCode.DUPLICATE_FOR_CONTRACT,
    ),
    (
        "rating_zero",
        legacy_review(rating=0),
        (confirmed_contract(),),
        (),
        LegacyReviewClassificationCode.INVALID_RATING,
    ),
    (
        "rating_six",
        legacy_review(rating=6),
        (confirmed_contract(),),
        (),
        LegacyReviewClassificationCode.INVALID_RATING,
    ),
    (
        "wrong_client",
        legacy_review(cliente_id=999),
        (confirmed_contract(),),
        (),
        LegacyReviewClassificationCode.IDENTITY_INCONSISTENT,
    ),
    (
        "wrong_professional",
        legacy_review(professional_id=999),
        (confirmed_contract(),),
        (),
        LegacyReviewClassificationCode.IDENTITY_INCONSISTENT,
    ),
    (
        "contract_not_confirmed",
        legacy_review(),
        (confirmed_contract(estado="COMPLETADA", confirmed_at=None),),
        (),
        LegacyReviewClassificationCode.NO_CANDIDATE,
    ),
    (
        "contract_created_after_review",
        legacy_review(),
        (
            confirmed_contract(
                created_at=REVIEW_TIME + timedelta(days=1),
                confirmed_at=REVIEW_TIME + timedelta(days=2),
            ),
        ),
        (),
        LegacyReviewClassificationCode.NO_CANDIDATE,
    ),
    (
        "missing_confirmation_evidence",
        legacy_review(),
        (confirmed_contract(confirmed_at=None),),
        (),
        LegacyReviewClassificationCode.INSUFFICIENT_CONFIRMATION_EVIDENCE,
    ),
    (
        "valid_legacy_unambiguous_contract",
        legacy_review(id=102, rating=4),
        (confirmed_contract(id=202),),
        (),
        LegacyReviewClassificationCode.LINKED_UNIQUE,
    ),
)


__all__ = (
    "CLASSIFICATION_CASES",
    "REVIEW_TIME",
    "confirmed_contract",
    "legacy_review",
)
