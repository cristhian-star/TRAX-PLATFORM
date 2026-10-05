"""Short-lived recovery, never authorization or business persistence.

Data stays in private temporary files, not Flask's client-side session cookie.
The recovery proof binds the original CSRF token, browser, actor and form nonce.
"""
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import tempfile
import time

from flask import current_app, request, session
from flask_wtf.csrf import generate_csrf
from itsdangerous import BadData, URLSafeTimedSerializer

from app import db
from app.models.user import User
from app.services.user_service import is_user_active
from app.services.budget_creation_key_service import issue_budget_key, validate_budget_key
from app.services.operation_request_service import parse_date

COOKIE = "budget_navigation"
TTL = 900
LIMITS = {"titulo": 160, "categoria": 120, "zona": 120, "descripcion": 1200,
          "fecha_estimada": 10, "urgencia": 6}


def _digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def _signer():
    return URLSafeTimedSerializer(current_app.secret_key, salt="budget-draft-recovery-v1")


def navigation_cookie():
    value = request.cookies.get(COOKIE, "")
    return value if re.fullmatch(r"[a-f0-9]{64}", value) else None


def form_credentials(actor_id, key=None):
    key = key or issue_budget_key(actor_id)
    nonce = validate_budget_key(key, actor_id)
    browser = navigation_cookie() or secrets.token_hex(32)
    generate_csrf()
    proof = _signer().dumps(dict(actor=actor_id, nonce=nonce, browser=_digest(browser),
                               csrf=_digest(session["csrf_token"])))
    return key, proof, browser


def attach_navigation_cookie(response, browser):
    response.set_cookie(COOKIE, browser, max_age=1800, httponly=True,
                        secure=current_app.config["SESSION_COOKIE_SECURE"], samesite="Strict")
    response.headers["Cache-Control"] = "no-store"
    return response


def _directory():
    path = Path(current_app.config.get("BUDGET_DRAFT_DIRECTORY", Path(current_app.instance_path) / "budget_drafts"))
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    return path


def _path(browser, actor_id, nonce):
    if not re.fullmatch(r"[a-f0-9]{32}", nonce):
        raise ValueError("Invalid draft handle")
    return _directory() / f"{_digest(browser)}-{actor_id}-{nonce}.json"


def sanitize_draft(values):
    data = {name: str(values.get(name, "")).strip()[:limit] for name, limit in LIMITS.items()}
    if data["urgencia"] not in ("BAJA", "NORMAL", "ALTA"):
        data["urgencia"] = "NORMAL"
    try:
        parse_date(data["fecha_estimada"])
    except ValueError:
        data["fecha_estimada"] = ""
    return data


def preserve_expired_form():
    """Validate the original CSRF proof even after Flask's auth cookie expired.

    This only saves a draft and never creates a domain entity. No CSRF exemption.
    """
    browser = navigation_cookie()
    if not browser:
        return False
    try:
        proof = _signer().loads(request.form.get("draft_proof", ""), max_age=TTL)
        if not hmac.compare_digest(proof["browser"], _digest(browser)):
            return False
        token = URLSafeTimedSerializer(current_app.config.get("WTF_CSRF_SECRET_KEY") or current_app.secret_key,
                                       salt="wtf-csrf-token").loads(
            request.form.get("csrf_token", ""), max_age=TTL)
        if not hmac.compare_digest(proof["csrf"], _digest(token)):
            return False
        actor = db.session.get(User, proof["actor"])
        if not is_user_active(actor) or actor.rol != "CLIENTE":
            return False
        nonce = validate_budget_key(request.form.get("idempotency_key"), actor.id)
        if nonce != proof["nonce"]:
            return False
    except (BadData, KeyError, ValueError, TypeError):
        return False
    drafts = list_drafts(actor.id)
    if len(drafts) >= 5 and nonce not in [d["nonce"] for d in drafts]:
        return False
    record = dict(actor=actor.id, nonce=nonce, expires=time.time() + TTL,
                  data=sanitize_draft(request.form))
    path = _path(browser, actor.id, nonce)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".draft-")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(record, stream, ensure_ascii=False)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return True


def list_drafts(actor_id):
    browser = navigation_cookie()
    if not browser:
        return []
    drafts = []
    # Lazy expiry also removes abandoned drafts. The directory is dedicated to
    # recovery files; no user-controlled pathname can escape it.
    for path in _directory().glob("*.json"):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            if record["expires"] <= time.time():
                path.unlink(missing_ok=True)
                continue
            if path.name.startswith(f"{_digest(browser)}-{actor_id}-") and record["actor"] == actor_id:
                if path == _path(browser, actor_id, record["nonce"]):
                    record["data"] = sanitize_draft(record["data"])
                    drafts.append(record)
        except (ValueError, KeyError, TypeError):
            path.unlink(missing_ok=True)
    return sorted(drafts, key=lambda item: item["nonce"])


def delete_draft(actor_id, key):
    browser = navigation_cookie()
    nonce = validate_budget_key(key, actor_id)
    if browser:
        _path(browser, actor_id, nonce).unlink(missing_ok=True)
