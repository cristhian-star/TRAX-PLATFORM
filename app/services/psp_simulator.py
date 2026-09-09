from collections import deque
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Callable, Iterable

from app.services.psp_contract import (
    AttemptNotFoundError,
    IdempotencyConflictError,
    PaymentAttempt,
    PaymentAttemptStatus,
    UncertainResponseError,
)


class SimulationScenario(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"
    UNCERTAIN = "UNCERTAIN"


class SimulatorConfigurationError(RuntimeError):
    pass


class ScenarioController:
    """Instance-local FIFO used only to configure simulator behavior."""

    def __init__(self, scenarios: Iterable[SimulationScenario] = ()):
        self._scenarios = deque(scenarios)
        if not all(isinstance(item, SimulationScenario) for item in self._scenarios):
            raise SimulatorConfigurationError(
                "all configured scenarios must be SimulationScenario values"
            )

    @property
    def remaining_count(self) -> int:
        return len(self._scenarios)

    def enqueue(self, scenario: SimulationScenario) -> None:
        if not isinstance(scenario, SimulationScenario):
            raise SimulatorConfigurationError(
                "scenario must be a SimulationScenario value"
            )
        self._scenarios.append(scenario)

    def consume(self) -> SimulationScenario:
        try:
            return self._scenarios.popleft()
        except IndexError as exc:
            raise SimulatorConfigurationError(
                "no simulation scenario is configured for the next new attempt"
            ) from exc


# Compatibility re-exports for the neutral types previously defined here.
AttemptStatus = PaymentAttemptStatus
SimulatedPaymentAttempt = PaymentAttempt
# Compatibility name for simulator-only scenario configuration.
CreationOutcome = SimulationScenario


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
        scenario_controller: ScenarioController,
    ):
        if (
            not callable(id_factory)
            or not callable(clock)
            or not isinstance(scenario_controller, ScenarioController)
        ):
            raise SimulatorConfigurationError(
                "id_factory and clock must be callable and scenario_controller valid"
            )

        self._id_factory = id_factory
        self._clock = clock
        self._scenario_controller = scenario_controller
        self._attempts: dict[str, PaymentAttempt] = {}
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
    ) -> PaymentAttempt:
        reference = self._required_text(internal_reference, "internal_reference")
        exact_amount = self._valid_amount(amount)
        normalized_currency = self._required_text(currency, "currency").upper()
        normalized_key = self._required_text(idempotency_key, "idempotency_key")
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

        scenario = self._scenario_controller.consume()
        status = (
            PaymentAttemptStatus.PENDING
            if scenario is SimulationScenario.UNCERTAIN
            else PaymentAttemptStatus(scenario.value)
        )
        attempt = PaymentAttempt(
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

        if scenario is SimulationScenario.UNCERTAIN:
            raise UncertainResponseError(
                "simulated transport response is uncertain; reconcile by idempotent replay",
                attempt_id=attempt_id,
            )

        return attempt

    def get_attempt(self, attempt_id: str) -> PaymentAttempt:
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
