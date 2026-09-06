"""Private snapshot of the legacy classification semantics shipped by _06.

This module intentionally knows nothing about professional ownership evidence:
revision 20260726_06 did not query it. It is not a domain API and no productive
caller is permitted by the dependency contract. Like any Python module it can
still be imported by arbitrary in-process code; this module is architectural
separation, not a security sandbox. Revision 20260726_07 performs the modern
fail-closed reconciliation.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class _HistoricalDecision:
    review_id: int
    classification_code: str
    contract_id: Optional[int]
    original_rating: object


def _positive_identifier(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _classify_one(review, contracts, competing_contract_ids=()):
    if not _positive_identifier(review["cliente_id"]) or not _positive_identifier(
        review["professional_id"]
    ):
        return "IDENTITY_INCONSISTENT", None
    rating = review["rating"]
    if (
        not isinstance(rating, int)
        or isinstance(rating, bool)
        or rating not in (1, 2, 3, 4, 5)
    ):
        return "INVALID_RATING", None

    identity_matches = tuple(
        contract
        for contract in contracts
        if contract["cliente_id"] == review["cliente_id"]
        and contract["professional_id"] == review["professional_id"]
    )
    if not identity_matches:
        partial = any(
            contract["cliente_id"] == review["cliente_id"]
            or contract["professional_id"] == review["professional_id"]
            for contract in contracts
        )
        return ("IDENTITY_INCONSISTENT" if partial else "NO_CANDIDATE"), None

    confirmed = tuple(
        contract for contract in identity_matches if contract["estado"] == "CONFIRMADA"
    )
    if not confirmed:
        return "NO_CANDIDATE", None
    if review["created_at"] is None:
        return "INSUFFICIENT_CONFIRMATION_EVIDENCE", None

    temporally_possible = tuple(
        contract
        for contract in confirmed
        if contract["fecha_creacion"] is not None
        and contract["fecha_creacion"] <= review["created_at"]
    )
    if not temporally_possible:
        code = (
            "INSUFFICIENT_CONFIRMATION_EVIDENCE"
            if any(contract["fecha_creacion"] is None for contract in confirmed)
            else "NO_CANDIDATE"
        )
        return code, None

    confirmed_before_review = tuple(
        contract
        for contract in temporally_possible
        if contract["confirmed_at"] is not None
        and contract["confirmed_at"] <= review["created_at"]
    )
    if any(contract["confirmed_at"] is None for contract in temporally_possible):
        return "INSUFFICIENT_CONFIRMATION_EVIDENCE", None
    if not confirmed_before_review:
        return "NO_CANDIDATE", None
    if len(confirmed_before_review) > 1:
        return "MULTIPLE_CANDIDATES", None

    contract_id = confirmed_before_review[0]["id"]
    if contract_id in competing_contract_ids:
        return "DUPLICATE_FOR_CONTRACT", None
    return "LINKED_UNIQUE", contract_id


def _classify_legacy_review_rows_20260726_06(review_rows, contract_rows):
    """Reproduce only the two-pass classification originally used by _06."""

    reviews = tuple(review_rows)
    contracts = tuple(contract_rows)
    preliminary = {
        review["id"]: _classify_one(review, contracts) for review in reviews
    }
    candidates_by_review = {
        review_id: contract_id
        for review_id, (code, contract_id) in preliminary.items()
        if code == "LINKED_UNIQUE"
    }

    decisions = []
    for review in reviews:
        competing = tuple(
            contract_id
            for review_id, contract_id in candidates_by_review.items()
            if review_id != review["id"]
        )
        code, contract_id = _classify_one(review, contracts, competing)
        decisions.append(
            _HistoricalDecision(
                review_id=review["id"],
                classification_code=code,
                contract_id=contract_id,
                original_rating=review["rating"],
            )
        )
    return tuple(decisions)


__all__ = ()
