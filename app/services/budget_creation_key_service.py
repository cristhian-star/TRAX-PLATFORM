"""Server-issued, actor-bound keys for the canonical OperationCommand ledger."""
import hashlib
import hmac
import re
import secrets

from flask import current_app

OPERATION = "BUDGET_REQUEST_CREATE"
KEY_PATTERN = re.compile(r"b1\.([1-9][0-9]{0,18})\.([a-f0-9]{32})\.([a-f0-9]{64})")


def issue_budget_key(actor_id, nonce=None):
    prefix = f"b1.{actor_id}.{nonce or secrets.token_hex(16)}"
    signature = hmac.new(
        current_app.config["SECRET_KEY"].encode(),
        f"{OPERATION}:{prefix}".encode(), hashlib.sha256,
    ).hexdigest()
    return f"{prefix}.{signature}"


def validate_budget_key(key, actor_id):
    match = KEY_PATTERN.fullmatch(key or "") if isinstance(key, str) and len(key) <= 160 else None
    if not match or int(match[1]) != actor_id or not hmac.compare_digest(key, issue_budget_key(actor_id, match[2])):
        raise ValueError("El formulario ya no es válido. Abrí una nueva solicitud.")
    return match[2]
