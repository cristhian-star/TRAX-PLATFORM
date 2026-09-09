from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Protocol, runtime_checkable


class PaymentAttemptStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"


class AttemptNotFoundError(LookupError):
    pass


class IdempotencyConflictError(ValueError):
    pass


class UncertainResponseError(RuntimeError):
    def __init__(self, message: str, *, attempt_id: str | None = None):
        if attempt_id is not None and (
            not isinstance(attempt_id, str) or not attempt_id.strip()
        ):
            raise ValueError("attempt_id must be a non-empty string or None")
        super().__init__(message)
        self.attempt_id = attempt_id


@dataclass(frozen=True, slots=True)
class PaymentAttempt:
    attempt_id: str
    internal_reference: str
    amount: Decimal
    currency: str
    idempotency_key: str
    status: PaymentAttemptStatus
    created_at: datetime


@runtime_checkable
class PSPAdapter(Protocol):
    def create_attempt(
        self,
        *,
        internal_reference: str,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
    ) -> PaymentAttempt: ...

    def get_attempt(self, attempt_id: str) -> PaymentAttempt: ...
