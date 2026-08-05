from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.models.contract_request import ContractRequest
from app.models.review import Review
from app.domain.reputation_metrics import (
    ContractMetricFact,
    ReviewMetricFact,
    build_neutral_reputation_metrics,
)


@dataclass(frozen=True)
class PublicReviewView:
    id: int
    rating: int
    comment_public: Optional[str]
    origin: str
    label: str
    comment_visibility_status: str
    created_at: Optional[datetime]


def _verified_review_query(professional_id):
    return Review.query.filter(
        Review.professional_id == professional_id,
        Review.contract_id.isnot(None),
        Review.origin.in_((Review.ORIGIN_CONTRACTUAL, Review.ORIGIN_LEGACY)),
        Review.verification_status == Review.VERIFICATION_VERIFIED,
        Review.rating_eligibility_status == Review.RATING_ELIGIBLE,
        Review.rating.in_((1, 2, 3, 4, 5)),
    )


def get_professional_reviews(professional_id):
    reviews = _verified_review_query(professional_id).order_by(
        Review.created_at.desc(),
        Review.id.desc(),
    ).all()
    public_statuses = (Review.COMMENT_VISIBLE, Review.COMMENT_REDACTED)
    labels = {
        Review.ORIGIN_CONTRACTUAL: "Review contractual verificada",
        Review.ORIGIN_LEGACY: "Review legacy verificada",
    }
    return [
        PublicReviewView(
            id=review.id,
            rating=review.rating,
            comment_public=(
                review.comment_public
                if review.comment_visibility_status in public_statuses
                else None
            ),
            origin=review.origin,
            label=labels[review.origin],
            comment_visibility_status=review.comment_visibility_status,
            created_at=review.created_at,
        )
        for review in reviews
    ]


def get_professional_reputation_metrics(professional_id):
    reviews = Review.query.filter(
        Review.professional_id == professional_id,
        Review.origin.in_((Review.ORIGIN_CONTRACTUAL, Review.ORIGIN_LEGACY)),
    ).all()
    contracts = ContractRequest.query.filter_by(
        professional_id=professional_id
    ).all()
    return build_neutral_reputation_metrics(
        professional_id,
        tuple(
            ReviewMetricFact(
                id=review.id,
                professional_id=review.professional_id,
                contract_id=review.contract_id,
                origin=review.origin,
                verification_status=review.verification_status,
                rating_eligibility_status=review.rating_eligibility_status,
                rating=review.rating,
            )
            for review in reviews
        ),
        tuple(
            ContractMetricFact(
                id=contract.id,
                professional_id=contract.professional_id,
                estado=contract.estado,
            )
            for contract in contracts
        ),
    )


def get_professional_average_rating(professional_id):
    return get_professional_reputation_metrics(
        professional_id
    ).average_eligible_rating


__all__ = (
    "PublicReviewView",
    "get_professional_average_rating",
    "get_professional_reputation_metrics",
    "get_professional_reviews",
)
