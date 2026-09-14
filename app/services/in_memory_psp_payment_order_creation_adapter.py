from hashlib import sha256
from threading import RLock

from app.services.psp_payment_order_contract import (
    InvalidPaymentOrderCreationRequestError,
    PaymentOrderCreationCommand,
    PaymentOrderCreationResult,
    PaymentOrderIdempotencyConflictError,
    validate_payment_order_creation_result,
)


class InMemoryPSPPaymentOrderCreationAdapter:
    """Deterministic, instance-local implementation of the creation port."""

    def __init__(self):
        self._lock = RLock()
        self._orders_by_key: dict[
            str, tuple[PaymentOrderCreationCommand, PaymentOrderCreationResult]
        ] = {}

    def create_payment_order(
        self, command: PaymentOrderCreationCommand
    ) -> PaymentOrderCreationResult:
        if type(command) is not PaymentOrderCreationCommand:
            raise InvalidPaymentOrderCreationRequestError(
                "invalid payment order creation request"
            )

        with self._lock:
            existing = self._orders_by_key.get(command.idempotency_key)
            if existing is not None:
                stored_command, stored_result = existing
                if stored_command != command:
                    raise PaymentOrderIdempotencyConflictError(
                        "payment order idempotency conflict"
                    )
                return stored_result

            digest = sha256(command.idempotency_key.encode("utf-8")).hexdigest()
            result = PaymentOrderCreationResult(
                local_order_id=command.local_order_id,
                obligation_reference=command.obligation_reference,
                external_reference=command.external_reference,
                amount=command.amount,
                currency=command.currency,
                concept=command.concept,
                idempotency_key=command.idempotency_key,
                created_at=command.created_at,
                expires_at=command.expires_at,
                external_order_id=f"fake-order-{digest}",
                checkout_url=(
                    f"https://checkout.example.test/payment-orders/{digest}"
                ),
                provider="fake",
                live_mode=False,
            )
            validate_payment_order_creation_result(command, result)
            self._orders_by_key[command.idempotency_key] = (command, result)
            return result
