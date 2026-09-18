import hashlib
import hmac
import re
from dataclasses import dataclass
from datetime import datetime, timezone


_SHA256_HEX = re.compile(r"[0-9a-fA-F]{64}")


class MercadoPagoWebhookSignatureError(ValueError):
    """Raised when a webhook signature cannot be accepted safely."""


@dataclass(frozen=True, slots=True)
class MercadoPagoWebhookSignatureVerification:
    verified: bool
    data_id: str
    timestamp: str


def verify_mercadopago_webhook_signature(
    *, x_signature, x_request_id, data_id, secret
):
    """Validate Mercado Pago's HMAC-SHA256 webhook signature.

    MANDOBRA applies a stricter fail-closed policy than the provider template:
    every manifest component is mandatory. ``data_id`` retains its exact case.
    Temporal acceptance is evaluated separately after cryptographic verification.
    """
    signature = _required_text(x_signature, "x-signature")
    request_id = _required_text(x_request_id, "x-request-id", preserve=True)
    original_data_id = _required_text(data_id, "data.id", preserve=True)
    secret_value = _required_text(secret, "secret", preserve=True)
    if (len(signature) > 1024 or len(request_id) > 256 or len(original_data_id) > 160
            or len(secret_value) > 2048):
        raise MercadoPagoWebhookSignatureError("webhook signature fields exceed limit")
    components = _signature_components(signature)
    timestamp = components["ts"]
    received_signature = components["v1"]

    if len(timestamp) > 13 or not timestamp.isascii() or not timestamp.isdecimal():
        raise MercadoPagoWebhookSignatureError("invalid webhook signature timestamp")
    if _SHA256_HEX.fullmatch(received_signature) is None:
        raise MercadoPagoWebhookSignatureError("invalid webhook signature digest")

    manifest = (
        f"id:{original_data_id};"
        f"request-id:{request_id};"
        f"ts:{timestamp};"
    )
    expected_signature = hmac.new(
        secret_value.encode("utf-8"),
        manifest.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected_signature, received_signature):
        raise MercadoPagoWebhookSignatureError("invalid webhook signature")
    return MercadoPagoWebhookSignatureVerification(
        verified=True,
        data_id=original_data_id,
        timestamp=timestamp,
    )


def _signature_components(value):
    found = {}
    for raw_component in value.split(","):
        component = raw_component.strip()
        key, separator, raw_value = component.partition("=")
        key = key.strip().lower()
        component_value = raw_value.strip()
        if not separator or not key or not component_value:
            raise MercadoPagoWebhookSignatureError("malformed x-signature header")
        if key in found:
            raise MercadoPagoWebhookSignatureError(
                "ambiguous x-signature header components"
            )
        found[key] = component_value
    if "ts" not in found or "v1" not in found:
        raise MercadoPagoWebhookSignatureError(
            "missing required x-signature components"
        )
    return found


def _required_text(value, field_name, *, preserve=False):
    if not isinstance(value, str) or not value.strip():
        raise MercadoPagoWebhookSignatureError(
            f"missing required webhook field: {field_name}"
        )
    return value if preserve else value.strip()


def webhook_timestamp_in_window(verification, received_at):
    """Temporal policy only; never replace cryptographic verification."""
    if (type(verification) is not MercadoPagoWebhookSignatureVerification
            or not verification.verified or not isinstance(received_at, datetime)
            or received_at.tzinfo is None or received_at.utcoffset() is None):
        raise ValueError("invalid webhook receipt timestamp")
    received_ms = int(received_at.astimezone(timezone.utc).timestamp() * 1000)
    return abs(received_ms - int(verification.timestamp)) <= 600_000
