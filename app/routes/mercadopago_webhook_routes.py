import json
import re
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request

from app import csrf, db
from app.services.mercadopago_webhook_notification import (
    MercadoPagoWebhookNotificationError,
    parse_mercadopago_webhook_notification,
)
from app.services.mercadopago_webhook_signature import (
    MercadoPagoWebhookSignatureError,
    verify_mercadopago_webhook_signature, webhook_timestamp_in_window,
)
from app.services.payment_order_reconciliation_service import receive_order_event


mercadopago_webhooks = Blueprint("mercadopago_webhooks", __name__)
_INVALID_JSON = object()


class _StrictJSONError(ValueError):
    pass


def _pairs(collection, *, multiple=False):
    if multiple:
        return list(collection.items(multi=True))
    return list(collection.items())


def _unique_value(pairs, name, *, case_insensitive=False):
    expected = name.lower() if case_insensitive else name
    values = []
    for key, value in pairs:
        candidate = key.lower() if case_insensitive and isinstance(key, str) else key
        if candidate == expected:
            values.append(value)
    if len(values) != 1 or not isinstance(values[0], str) or not values[0].strip():
        raise MercadoPagoWebhookNotificationError("malformed webhook metadata")
    return values[0]


def _unique_request_id(pairs):
    values = [
        value
        for key, value in pairs
        if isinstance(key, str) and key.strip().lower() == "x-request-id"
    ]
    if (
        len(values) != 1
        or not isinstance(values[0], str)
        or not values[0]
        or values[0] != values[0].strip()
        or "," in values[0]
    ):
        raise MercadoPagoWebhookNotificationError("malformed webhook metadata")
    return values[0]


def _strict_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise _StrictJSONError()
        result[key] = value
    return result


def _reject_json_constant(value):
    raise _StrictJSONError()


def _decode_json_body(raw_body):
    try:
        decoded = raw_body.decode("utf-8")
        return json.loads(
            decoded,
            object_pairs_hook=_strict_json_object,
            parse_constant=_reject_json_constant,
        )
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError, _StrictJSONError):
        return _INVALID_JSON


def _utc_now():
    return datetime.now(timezone.utc)


@mercadopago_webhooks.post("/api/webhooks/mercadopago")
@csrf.exempt
def receive_mercadopago_webhook():
    if current_app.config.get("MERCADOPAGO_ORDER_WEBHOOK_ENABLED") is not True:
        return jsonify({"error": "service unavailable"}), 503
    secret = current_app.config.get("MERCADOPAGO_WEBHOOK_SECRET")
    if not isinstance(secret, str) or not secret.strip():
        return jsonify({"error": "service unavailable"}), 503

    query_pairs = _pairs(request.args, multiple=True)
    header_pairs = _pairs(request.headers)
    received_at = _utc_now()
    try:
        signed_data_id = _unique_value(query_pairs, "data.id")
        if _unique_value(query_pairs, "type") != "order":
            raise MercadoPagoWebhookNotificationError("unsupported order notification")
    except MercadoPagoWebhookNotificationError:
        return jsonify({"error": "bad request"}), 400
    try:
        x_signature = _unique_value(
            header_pairs, "x-signature", case_insensitive=True
        )
        x_request_id = _unique_request_id(header_pairs)
        if len(x_request_id) > 256 or any(char in x_request_id for char in "\r\n;"):
            raise MercadoPagoWebhookNotificationError("malformed webhook metadata")
    except MercadoPagoWebhookNotificationError:
        return jsonify({"error": "bad request"}), 400
    try:
        verification = verify_mercadopago_webhook_signature(
            x_signature=x_signature,
            x_request_id=x_request_id,
            data_id=signed_data_id,
            secret=secret,
        )
    except MercadoPagoWebhookSignatureError:
        return jsonify({"error": "unauthorized"}), 401

    if not request.is_json:
        return jsonify({"error": "bad request"}), 400
    if request.content_length is not None and request.content_length > 65536:
        return jsonify({"error": "payload too large"}), 413
    raw_body = request.stream.read(65537)
    if len(raw_body) > 65536:
        return jsonify({"error": "payload too large"}), 413
    body = _decode_json_body(raw_body)
    if body is _INVALID_JSON:
        return jsonify({"error": "bad request"}), 400
    if type(body) is not dict or body.get("type") != "order" or body.get("api_version") != "v1":
        return jsonify({"error": "bad request"}), 400

    try:
        event = parse_mercadopago_webhook_notification(
            query_params=query_pairs,
            headers=header_pairs,
            body=body,
            secret=secret,
            received_at=received_at,
        )
        if (event.topic != "order" or re.fullmatch(r"ORD[A-Za-z0-9_-]{1,157}", event.external_resource_id, re.ASCII) is None
                or len(event.external_event_id) > 160
                or not event.action.startswith("order.")):
            raise MercadoPagoWebhookNotificationError("unsupported order notification")
    except MercadoPagoWebhookSignatureError:
        return jsonify({"error": "unauthorized"}), 401
    except MercadoPagoWebhookNotificationError:
        return jsonify({"error": "bad request"}), 400

    try:
        receive_order_event(db.session, event, quarantine_reason=(
            None if webhook_timestamp_in_window(verification, received_at)
            else "TIMESTAMP_OUTSIDE_WINDOW"
        ))
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "internal error"}), 500

    return jsonify({"status": "accepted"}), 200
