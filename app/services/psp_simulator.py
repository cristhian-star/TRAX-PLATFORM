from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Callable


class AttemptStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"


class CreationOutcome(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"
    UNCERTAIN = "UNCERTAIN"


class AttemptNotFoundError(LookupError):
    pass


class IdempotencyConflictError(ValueError):
    pass


class UncertainResponseError(RuntimeError):
    pass


class SimulatorConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class SimulatedPaymentAttempt:
    attempt_id: str
    internal_reference: str
    amount: Decimal
    currency: str
    idempotency_key: str
    status: AttemptStatus
    created_at: datetime


class InMemoryPSPSimulator:
    """Deterministic, instance-local PSP contract simulator.

    Idempotency compares a canonical tuple containing the trimmed internal
    reference, the exact Decimal numeric value, and the trimmed uppercase
    currency. Amounts are never quantized or rounded.

    ``UNCERTAIN`` represents only the outcome observed by the caller. The
    stored attempt remains consultable with ``PENDING`` status and can be
    recovered by replaying the same idempotency key.
    """

    def __init__(
        self,
        *,
        id_factory: Callable[[], str],
        clock: Callable[[], datetime],
    ):
        if not callable(id_factory) or not callable(clock):
            raise SimulatorConfigurationError("id_factory and clock must be callable")

        self._id_factory = id_factory
        self._clock = clock
        self._attempts: dict[str, SimulatedPaymentAttempt] = {}
        self._attempt_ids_by_key: dict[str, str] = {}
        self._fingerprints_by_key: dict[str, tuple[str, Decimal, str]] = {}

    @property
    def attempt_count(self) -> int:
        return len(self._attempts)

    def create_attempt(
        self,
        *,
        internal_reference: str,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
        outcome: CreationOutcome,
    ) -> SimulatedPaymentAttempt:
        reference = self._required_text(internal_reference, "internal_reference")
        exact_amount = self._valid_amount(amount)
        normalized_currency = self._required_text(currency, "currency").upper()
        normalized_key = self._required_text(idempotency_key, "idempotency_key")
        if not isinstance(outcome, CreationOutcome):
            raise ValueError("outcome must be a CreationOutcome")

        fingerprint = (reference, exact_amount, normalized_currency)
        existing_id = self._attempt_ids_by_key.get(normalized_key)
        if existing_id is not None:
            if self._fingerprints_by_key[normalized_key] != fingerprint:
                raise IdempotencyConflictError(
                    "idempotency key already exists with different content"
                )
            return self._attempts[existing_id]

        attempt_id = self._required_text(self._id_factory(), "generated attempt_id")
        if attempt_id in self._attempts:
            raise SimulatorConfigurationError("id_factory produced a duplicate attempt_id")

        created_at = self._clock()
        if not isinstance(created_at, datetime):
            raise SimulatorConfigurationError("clock must return datetime values")

        status = (
            AttemptStatus.PENDING
            if outcome is CreationOutcome.UNCERTAIN
            else AttemptStatus(outcome.value)
        )
        attempt = SimulatedPaymentAttempt(
            attempt_id=attempt_id,
            internal_reference=reference,
            amount=exact_amount,
            currency=normalized_currency,
            idempotency_key=normalized_key,
            status=status,
            created_at=created_at,
        )
        self._attempts[attempt_id] = attempt
        self._attempt_ids_by_key[normalized_key] = attempt_id
        self._fingerprints_by_key[normalized_key] = fingerprint

        if outcome is CreationOutcome.UNCERTAIN:
            raise UncertainResponseError(
                "simulated transport response is uncertain; reconcile by idempotent replay"
            )

        return attempt

    def get_attempt(self, attempt_id: str) -> SimulatedPaymentAttempt:
        normalized_id = self._required_text(attempt_id, "attempt_id")
        try:
            return self._attempts[normalized_id]
        except KeyError as exc:
            raise AttemptNotFoundError("simulated payment attempt was not found") from exc

    @staticmethod
    def _required_text(value: str, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
        return value.strip()

    @staticmethod
    def _valid_amount(value: Decimal) -> Decimal:
        if isinstance(value, float):
            raise TypeError("amount must not be a float")
        if not isinstance(value, Decimal):
            raise TypeError("amount must be a Decimal")
        if not value.is_finite() or value <= 0:
            raise ValueError("amount must be finite and positive")
        return value
