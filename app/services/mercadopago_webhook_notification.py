import hashlib
import json
import re
from collections.abc import Mapping
from datetime import datetime, timezone

from app.services.mercadopago_webhook_signature import (
    verify_mercadopago_webhook_signature,
)
from app.services.psp_event_contract import PSPEvent


_TOKEN = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
_INVALID_DATETIME = object()
_REQUIRED_BODY_FIELDS = frozenset(
    {"id", "type", "action", "data", "live_mode", "date_created", "api_version"}
)
_ALLOWED_BODY_FIELDS = _REQUIRED_BODY_FIELDS | {"application_id", "user_id"}


class MercadoPagoWebhookNotificationError(ValueError):
    """Raised when a decoded Mercado Pago notification is not canonical."""


def parse_mercadopago_webhook_notification(
    *, query_params, headers, body, secret, received_at
):
    """Verify and transform one decoded Mercado Pago notification into PSPEvent.

    This boundary is intentionally pure: it does not receive a database session,
    call Mercado Pago, or interpret the financial meaning of ``action``.
    """
    query = _collect_fields(query_params, "query parameters")
    request_headers = _collect_fields(headers, "headers", case_insensitive=True)

    signed_data_id = _required_field(query, "data.id", "query parameters")
    query_topic = _required_field(query, "type", "query parameters")
    x_signature = _required_field(request_headers, "x-signature", "headers")
    x_request_id = _required_field(request_headers, "x-request-id", "headers")

    verification = verify_mercadopago_webhook_signature(
        x_signature=x_signature,
        x_request_id=x_request_id,
        data_id=signed_data_id,
        secret=secret,
    )

    content = _validated_body(body)
    resource_id = _identifier(verification.data_id, "query data.id")
    body_resource_id = _identifier(content["data"]["id"], "body data.id")
    if resource_id != body_resource_id:
        raise MercadoPagoWebhookNotificationError(
            "signed data.id does not match body data.id"
        )

    topic = _token(query_topic, "query type")
    body_topic = _token(content["type"], "body type")
    if topic != body_topic:
        raise MercadoPagoWebhookNotificationError(
            "query type does not match body type"
        )

    action = _token(content["action"], "body action")
    external_event_id = _identifier(content["id"], "body id")
    live_mode = content["live_mode"]
    if type(live_mode) is not bool:
        raise MercadoPagoWebhookNotificationError("body live_mode must be a boolean")

    api_version = _token(content["api_version"], "body api_version")
    if api_version != "v1":
        raise MercadoPagoWebhookNotificationError("unsupported body api_version")

    optional_identifiers = {
        optional_id: _identifier(content[optional_id], f"body {optional_id}")
        for optional_id in ("application_id", "user_id")
        if optional_id in content
    }

    occurred_at = _aware_datetime(content["date_created"], "body date_created")
    received_at = _aware_datetime(received_at, "received_at", decoded=True)
    test_mode = not live_mode
    payload_hash = _canonical_payload_hash(
        external_event_id=external_event_id,
        topic=topic,
        action=action,
        external_resource_id=resource_id,
        test_mode=test_mode,
        occurred_at=occurred_at,
        api_version=api_version,
        optional_identifiers=optional_identifiers,
    )

    return PSPEvent(
        provider="mercadopago",
        external_event_id=external_event_id,
        topic=topic,
        action=action,
        external_resource_id=resource_id,
        test_mode=test_mode,
        occurred_at=occurred_at,
        received_at=received_at,
        payload_hash=payload_hash,
    )


def _collect_fields(value, label, *, case_insensitive=False):
    if isinstance(value, Mapping):
        try:
            pairs = list(value.items(multi=True))
        except TypeError:
            pairs = list(value.items())
    elif isinstance(value, (list, tuple)):
        pairs = list(value)
    else:
        raise MercadoPagoWebhookNotificationError(f"{label} must be key-value pairs")

    found = {}
    for pair in pairs:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise MercadoPagoWebhookNotificationError(
                f"{label} contain an invalid structure"
            )
        key, field_value = pair
        if not isinstance(key, str) or not key.strip():
            raise MercadoPagoWebhookNotificationError(f"{label} contain an invalid key")
        canonical_key = key.strip().lower() if case_insensitive else key
        if canonical_key in found:
            raise MercadoPagoWebhookNotificationError(
                f"{label} contain a duplicate parameter"
            )
        if not isinstance(field_value, str):
            raise MercadoPagoWebhookNotificationError(
                f"{label} contain a non-string value"
            )
        found[canonical_key] = field_value
    return found


def _required_field(fields, name, label):
    value = fields.get(name)
    if not isinstance(value, str) or not value.strip():
        raise MercadoPagoWebhookNotificationError(
            f"missing required {label} field: {name}"
        )
    return value


def _validated_body(body):
    if type(body) is not dict:
        raise MercadoPagoWebhookNotificationError("body must be a JSON object")
    keys = set(body)
    if any(not isinstance(key, str) for key in keys):
        raise MercadoPagoWebhookNotificationError("body contains an invalid field name")
    missing = _REQUIRED_BODY_FIELDS - keys
    if missing:
        raise MercadoPagoWebhookNotificationError("body is missing required fields")
    if keys - _ALLOWED_BODY_FIELDS:
        raise MercadoPagoWebhookNotificationError("body contains unexpected fields")
    data = body["data"]
    if type(data) is not dict or set(data) != {"id"}:
        raise MercadoPagoWebhookNotificationError(
            "body data must contain exactly one id field"
        )
    return body


def _identifier(value, label):
    if type(value) is int:
        if value < 0:
            raise MercadoPagoWebhookNotificationError(f"{label} must be non-negative")
        return str(value)
    if not isinstance(value, str) or not value or value != value.strip():
        raise MercadoPagoWebhookNotificationError(
            f"{label} must be an exact non-empty identifier"
        )
    return value


def _token(value, label):
    if not isinstance(value, str) or not value.strip():
        raise MercadoPagoWebhookNotificationError(f"{label} must be a non-empty string")
    normalized = value.strip().lower()
    if _TOKEN.fullmatch(normalized) is None:
        raise MercadoPagoWebhookNotificationError(f"{label} has an invalid format")
    return normalized


def _aware_datetime(value, label, *, decoded=False):
    if decoded:
        parsed = value
    else:
        if not isinstance(value, str) or not value.strip():
            raise MercadoPagoWebhookNotificationError(
                f"{label} must be an ISO 8601 timestamp"
            )
        candidate = value.strip()
        if candidate.endswith("Z"):
            candidate = candidate[:-1] + "+00:00"
        parsed = _parse_iso_datetime(candidate)
        if parsed is _INVALID_DATETIME:
            raise MercadoPagoWebhookNotificationError(
                f"{label} must be an ISO 8601 timestamp"
            )
    if not isinstance(parsed, datetime) or parsed.tzinfo is None or parsed.utcoffset() is None:
        raise MercadoPagoWebhookNotificationError(f"{label} must be timezone-aware")
    return parsed


def _parse_iso_datetime(value):
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return _INVALID_DATETIME


def _canonical_payload_hash(
    *,
    external_event_id,
    topic,
    action,
    external_resource_id,
    test_mode,
    occurred_at,
    api_version,
    optional_identifiers,
):
    canonical = {
        "action": action,
        "api_version": api_version,
        "external_event_id": external_event_id,
        "external_resource_id": external_resource_id,
        "occurred_at": occurred_at.astimezone(timezone.utc).isoformat(),
        "provider": "mercadopago",
        "test_mode": test_mode,
        "topic": topic,
    }
    canonical.update(optional_identifiers)
    encoded = json.dumps(
        canonical, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
