"""Read-only Orders boundary with per-professional trusted account binding."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
import math
import re
import urllib.error
import urllib.request

from app.services import mercadopago_payment_query_http as http


class OrderQueryUnavailableError(RuntimeError):
    pass


class OrderQueryAuthenticationError(RuntimeError):
    pass


class OrderQueryResponseError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ProfessionalOrderQueryCredential:
    professional_id: int
    account_id: str
    access_token: str = field(repr=False)
    live_mode: bool
    currency: str = "ARS"


@dataclass(frozen=True, slots=True)
class OrderQueryContext:
    payment_order_id: int
    professional_id: int
    external_order_id: str
    external_reference: str
    amount: Decimal
    currency: str
    live_mode: bool
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class OrderSnapshot:
    content: dict
    digest: str
    remote_updated_at: datetime
    remote_created_at: datetime


_ID = re.compile(r"[A-Za-z0-9_-]{1,160}", re.ASCII)
_ACCOUNT = re.compile(r"[0-9]{1,32}", re.ASCII)
_MONEY = re.compile(r"(?:0|[1-9][0-9]{0,59})(?:\.[0-9]{1,2})?", re.ASCII)
_STATUSES = frozenset({"created", "processing", "processed", "action_required", "failed", "refunded", "canceled", "charged_back"})
_DETAILS = frozenset({"created", "accredited", "refunded", "partially_refunded", "waiting_capture", "pending_review_manual", "in_process", "settled", "reimbursed", "canceled", "bad_filled_card_data", "invalid_card_token", "high_risk", "rejected_by_issuer", "required_call_for_authorize", "max_attempts_exceeded", "card_disabled", "card_insufficient_amount", "amount_limit_exceeded", "invalid_installments", "processing_error"})
_CHARGEBACK_STATUSES = frozenset({"in_process", "settled", "reimbursed"})
_FAILED = object()


def _safe_call(function, *args, **kwargs):
    # Return only a non-sensitive sentinel, never the exception or its args.
    try:
        return function(*args, **kwargs)
    except Exception:
        return _FAILED


class UrllibMercadoPagoOrderQueryTransport(http.UrllibMercadoPagoTransport):
    def __call__(self, *, method, url, headers, timeout, allow_redirects, body):
        prefix = "https://api.mercadopago.com/v1/orders/"
        if (method != "GET" or not url.startswith(prefix)
                or _ID.fullmatch(url[len(prefix):]) is None
                or allow_redirects is not False or body is not None):
            raise ValueError("invalid order query request")
        request = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with self._opener.open(request, timeout=timeout) as response:
                return http._stdlib_response(response)
        except urllib.error.HTTPError as error:
            status = error.code
            http._close_http_error(error)
            return http.MercadoPagoHTTPResponse(status, (), b"")

    def __repr__(self):
        return "UrllibMercadoPagoOrderQueryTransport()"


@dataclass(frozen=True, slots=True, repr=False)
class MercadoPagoOrderQueryAdapter:
    oauth_provider: object = field(repr=False)
    transport: object = field(repr=False)
    timeout: float = 10.0

    def __post_init__(self):
        if (not callable(self.oauth_provider) or not callable(self.transport)
                or type(self.timeout) not in (int, float)
                or not math.isfinite(self.timeout) or not 0 < self.timeout <= 30):
            raise ValueError("invalid order query configuration")

    def __repr__(self):
        return "MercadoPagoOrderQueryAdapter(timeout=<configured>)"

    def query_order(self, context):
        if (type(context) is not OrderQueryContext
                or _ID.fullmatch(context.external_order_id) is None):
            raise OrderQueryResponseError("invalid order query context")
        credential = _safe_call(self.oauth_provider, context.professional_id)
        if credential is _FAILED:
            raise OrderQueryAuthenticationError("order provider authentication unavailable")
        valid = _safe_call(_validate_credential, credential, context)
        if valid is _FAILED:
            raise OrderQueryAuthenticationError("order provider authentication unavailable")
        response = _safe_call(
            self.transport, method="GET",
            url=f"https://api.mercadopago.com/v1/orders/{context.external_order_id}",
            headers={"Authorization": f"Bearer {credential.access_token}", "Accept": "application/json"},
            timeout=self.timeout, allow_redirects=False, body=None,
        )
        if response is _FAILED:
            raise OrderQueryUnavailableError("order provider temporarily unavailable")
        if type(response) is not http.MercadoPagoHTTPResponse or type(response.status_code) is not int:
            raise OrderQueryResponseError("invalid order provider response")
        if response.status_code in (401, 403):
            raise OrderQueryAuthenticationError("order provider authentication unavailable")
        if response.status_code in (404, 408, 429) or 500 <= response.status_code <= 599:
            raise OrderQueryUnavailableError("order provider temporarily unavailable")
        if response.status_code != 200:
            raise OrderQueryResponseError("invalid order provider response")
        payload = _safe_call(http._decode_json_response, response)
        if payload is _FAILED:
            raise OrderQueryResponseError("invalid order provider response")
        result = _safe_call(parse_order_snapshot, payload, context, credential.account_id)
        if result is _FAILED:
            raise OrderQueryResponseError("invalid order provider response")
        return result


def _validate_credential(credential, context):
    if (type(credential) is not ProfessionalOrderQueryCredential
            or type(credential.professional_id) is not int
            or credential.professional_id != context.professional_id
            or type(credential.live_mode) is not bool
            or credential.live_mode is not context.live_mode
            or credential.currency != context.currency or context.currency != "ARS"
            or type(credential.account_id) is not str
            or _ACCOUNT.fullmatch(credential.account_id) is None):
        raise ValueError("invalid credential binding")
    http._validate_access_token(credential.access_token)


def _money(value):
    if type(value) is not str or _MONEY.fullmatch(value) is None:
        raise ValueError("invalid amount")
    try:
        result = Decimal(value)
    except InvalidOperation:
        result = None
    if result is None or not result.is_finite():
        raise ValueError("invalid amount")
    return result


def _date(value):
    if type(value) is not str or len(value) > 64:
        raise ValueError("invalid date")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("invalid date")
    return parsed.astimezone(timezone.utc).replace(tzinfo=None)


def _id(value):
    if type(value) is not str or _ID.fullmatch(value) is None:
        raise ValueError("invalid resource identity")
    return value


def parse_order_snapshot(payload, context, account_id):
    """Allowlist only financial evidence; discard payer, tokens and metadata."""
    if (type(payload) is not dict or payload.get("id") != context.external_order_id
            or payload.get("external_reference") != context.external_reference
            or payload.get("currency") != "ARS" or payload.get("type") != "online"
            or payload.get("processing_mode") != "manual"
            or str(payload.get("user_id")) != account_id
            or _money(payload.get("total_amount")) != context.amount
            or ("live_mode" in payload and (type(payload["live_mode"]) is not bool or payload["live_mode"] is not context.live_mode))):
        raise ValueError("order correlation mismatch")
    status, detail = payload.get("status"), payload.get("status_detail")
    if status not in _STATUSES or detail not in _DETAILS:
        raise ValueError("unsupported order status")
    paid = _money(payload.get("total_paid_amount"))
    if paid > context.amount:
        raise ValueError("incoherent amount")
    created, updated = _date(payload.get("created_date")), _date(payload.get("last_updated_date"))
    if updated < created:
        raise ValueError("incoherent dates")
    transactions = payload.get("transactions", {})
    if type(transactions) is not dict:
        raise ValueError("invalid transactions")
    selected = {}
    payment_ids = set()
    for kind in ("payments", "refunds", "chargebacks"):
        rows = transactions.get(kind, [])
        if type(rows) is not list or len(rows) > 100:
            raise ValueError("invalid transactions")
        clean, seen = [], set()
        for row in rows:
            if type(row) is not dict:
                raise ValueError("invalid transaction")
            identity = _id(row.get("id"))
            if identity in seen and kind != "refunds":
                raise ValueError("duplicate transaction")
            seen.add(identity)
            item = {"id": identity}
            row_status = row.get("status")
            if row_status not in (_CHARGEBACK_STATUSES if kind == "chargebacks" else _STATUSES):
                raise ValueError("unsupported transaction status")
            item["status"] = row_status
            if kind == "payments":
                payment_ids.add(identity)
                if row.get("status_detail") not in _DETAILS:
                    raise ValueError("unsupported transaction detail")
                item["status_detail"] = row["status_detail"]
                for name in ("amount", "paid_amount"):
                    value = _money(row.get(name))
                    if value > context.amount:
                        raise ValueError("incoherent transaction amount")
                    item[name] = format(value, "f")
                if Decimal(item["paid_amount"]) > Decimal(item["amount"]):
                    raise ValueError("incoherent payment amount")
            else:
                item["transaction_id"] = _id(row.get("transaction_id"))
                if item["transaction_id"] not in payment_ids:
                    raise ValueError("unmatched reversal")
                if kind == "refunds":
                    value = _money(row.get("amount"))
                    if value <= 0:
                        raise ValueError("incoherent refund amount")
                    item["amount"] = format(value, "f")
            if kind == "refunds" and any(previous["id"] == identity for previous in clean):
                previous = next(previous for previous in clean if previous["id"] == identity)
                if previous["transaction_id"] != item["transaction_id"] or previous["amount"] != item["amount"]:
                    raise ValueError("contradictory refund identity")
                continue
            clean.append(item)
        selected[kind] = sorted(clean, key=lambda item: item["id"])
    content = {
        "id": context.external_order_id, "external_reference": context.external_reference,
        "user_id": account_id, "live_mode": context.live_mode, "currency": "ARS",
        "total_amount": format(_money(payload["total_amount"]), "f"),
        "total_paid_amount": format(paid, "f"), "status": status, "status_detail": detail,
        "created_date": created.isoformat(), "last_updated_date": updated.isoformat(),
        "transactions": selected,
    }
    if not refunds_are_consistent([content], context.amount):
        raise ValueError("incoherent refund amount")
    encoded = json.dumps(content, sort_keys=True, separators=(",", ":")).encode()
    return OrderSnapshot(content, hashlib.sha256(encoded).hexdigest(), updated, created)


def refunds_are_consistent(snapshots, order_amount):
    """Deduplicate financial identities across snapshots using exact Decimal sums."""
    payments, refunds = {}, {}
    for snapshot in snapshots:
        transactions = snapshot["transactions"]
        for payment in transactions["payments"]:
            amount = Decimal(payment["amount"])
            if payment["id"] in payments and payments[payment["id"]] != amount:
                return False
            payments[payment["id"]] = amount
        for refund in transactions["refunds"]:
            identity = refund["id"]
            fact = (refund["transaction_id"], Decimal(refund["amount"]))
            if identity in refunds and refunds[identity] != fact:
                return False
            refunds[identity] = fact
    totals = {}
    with localcontext() as context:
        context.prec = 128
        total = Decimal(0)
        for payment_id, amount in refunds.values():
            if amount <= 0 or payment_id not in payments:
                return False
            totals[payment_id] = totals.get(payment_id, Decimal(0)) + amount
            total += amount
        return total <= order_amount and all(amount <= payments[identity] for identity, amount in totals.items())
