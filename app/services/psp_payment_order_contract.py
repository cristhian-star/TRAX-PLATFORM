from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Context, Decimal, DecimalException
import ipaddress
import re
from typing import Protocol, runtime_checkable
import unicodedata
from urllib.parse import SplitResult, urlsplit


class InvalidPaymentOrderCreationRequestError(ValueError):
    pass


class InvalidPaymentOrderCreationResultError(ValueError):
    pass


class PaymentOrderIdempotencyConflictError(ValueError):
    pass


class PaymentOrderCreationUncertainError(RuntimeError):
    pass


_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,159}", re.ASCII)
_IDEMPOTENCY_KEY = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9._:-]{15,159}", re.ASCII
)
_PROVIDER = re.compile(r"[a-z][a-z0-9_-]{0,63}", re.ASCII)
_HOST_LABEL = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", re.ASCII)
_PERCENT_ESCAPE = re.compile(r"%[0-9A-Fa-f]{2}", re.ASCII)
_MAX_CONCEPT_LENGTH = 200
_ORDER_LIFETIME = timedelta(hours=72)
_CENT = Decimal("0.01")
_MAX_CANONICAL_DECIMAL_DIGITS = 64
_DECIMAL_CONTEXT = Context(prec=_MAX_CANONICAL_DECIMAL_DIGITS)
_PARSE_FAILURE = object()

# Percent-encoded delimiters can change URL structure after a later decode.
_ENCODED_PATH_SEPARATOR = 0x2F  # /
_ENCODED_BACKSLASH = 0x5C  # \
_ENCODED_QUERY_SEPARATOR = 0x3F  # ?
_ENCODED_FRAGMENT_SEPARATOR = 0x23  # #
_ENCODED_AUTHORITY_SEPARATOR = 0x40  # @
_ENCODED_SCHEME_SEPARATOR = 0x3A  # :
_ENCODED_PERCENT = 0x25  # %
_FORBIDDEN_ENCODED_SEPARATORS = frozenset({
    _ENCODED_PATH_SEPARATOR,
    _ENCODED_BACKSLASH,
    _ENCODED_QUERY_SEPARATOR,
    _ENCODED_FRAGMENT_SEPARATOR,
    _ENCODED_AUTHORITY_SEPARATOR,
    _ENCODED_SCHEME_SEPARATOR,
    _ENCODED_PERCENT,
})


@dataclass(frozen=True, slots=True)
class PaymentOrderCreationCommand:
    local_order_id: str
    obligation_reference: str
    professional_id: int
    amount: Decimal
    currency: str
    concept: str
    external_reference: str
    idempotency_key: str
    created_at: datetime
    expires_at: datetime

    def __post_init__(self):
        try:
            _validate_command_fields(self)
        except InvalidPaymentOrderCreationRequestError:
            raise
        except (DecimalException, OverflowError, TypeError, ValueError):
            raise InvalidPaymentOrderCreationRequestError(
                "invalid payment order creation request"
            ) from None
        amount = _canonical_amount(self.amount)
        if amount is _PARSE_FAILURE:
            _invalid_request()
        object.__setattr__(self, "amount", amount)
        created_at, expires_at = _canonical_dates(self.created_at, self.expires_at)
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "expires_at", expires_at)


@dataclass(frozen=True, slots=True)
class PaymentOrderCreationResult:
    local_order_id: str
    obligation_reference: str
    external_reference: str
    amount: Decimal
    currency: str
    concept: str
    idempotency_key: str
    created_at: datetime
    expires_at: datetime
    external_order_id: str
    checkout_url: str = field(repr=False)
    provider: str
    live_mode: bool

    def __post_init__(self):
        try:
            _validate_result_fields(self)
        except InvalidPaymentOrderCreationResultError:
            raise
        except (DecimalException, OverflowError, TypeError, ValueError):
            raise InvalidPaymentOrderCreationResultError(
                "invalid payment order creation result"
            ) from None
        amount = _canonical_amount(self.amount)
        if amount is _PARSE_FAILURE:
            _invalid_result()
        object.__setattr__(self, "amount", amount)
        created_at, expires_at = _canonical_dates(self.created_at, self.expires_at)
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "expires_at", expires_at)


@runtime_checkable
class PSPPaymentOrderCreationAdapter(Protocol):
    def create_payment_order(
        self, command: PaymentOrderCreationCommand
    ) -> PaymentOrderCreationResult: ...


def validate_payment_order_creation_result(
    command: PaymentOrderCreationCommand,
    result: PaymentOrderCreationResult,
) -> PaymentOrderCreationResult:
    if type(command) is not PaymentOrderCreationCommand:
        raise InvalidPaymentOrderCreationRequestError(
            "invalid payment order creation request"
        )
    if type(result) is not PaymentOrderCreationResult:
        raise InvalidPaymentOrderCreationResultError(
            "invalid payment order creation result"
        )
    shared_fields = (
        "local_order_id",
        "obligation_reference",
        "external_reference",
        "amount",
        "currency",
        "concept",
        "idempotency_key",
        "created_at",
        "expires_at",
    )
    if any(getattr(command, name) != getattr(result, name) for name in shared_fields):
        raise InvalidPaymentOrderCreationResultError(
            "payment order creation result does not match request"
        )
    return result


def _validate_command_fields(command):
    _request_token(command.local_order_id)
    _request_token(command.obligation_reference)
    if type(command.professional_id) is not int or command.professional_id <= 0:
        _invalid_request()
    _request_amount(command.amount)
    if command.currency != "ARS":
        _invalid_request()
    _request_concept(command.concept)
    _request_token(command.external_reference)
    if (
        type(command.idempotency_key) is not str
        or _IDEMPOTENCY_KEY.fullmatch(command.idempotency_key) is None
    ):
        _invalid_request()
    _request_dates(command.created_at, command.expires_at)


def _validate_result_fields(result):
    for value in (
        result.local_order_id,
        result.obligation_reference,
        result.external_reference,
        result.external_order_id,
    ):
        _result_token(value)
    _result_amount(result.amount)
    if result.currency != "ARS":
        _invalid_result()
    _result_concept(result.concept)
    if (
        type(result.idempotency_key) is not str
        or _IDEMPOTENCY_KEY.fullmatch(result.idempotency_key) is None
    ):
        _invalid_result()
    _result_dates(result.created_at, result.expires_at)
    provider = _normalized_provider(result.provider)
    if provider is None:
        _invalid_result()
    object.__setattr__(result, "provider", provider)
    if type(result.live_mode) is not bool:
        _invalid_result()
    if not _is_structurally_safe_checkout_url(result.checkout_url):
        _invalid_result()


def _request_token(value):
    if type(value) is not str or _TOKEN.fullmatch(value) is None:
        _invalid_request()


def _result_token(value):
    if type(value) is not str or _TOKEN.fullmatch(value) is None:
        _invalid_result()


def _request_amount(value):
    if not _is_valid_amount(value):
        _invalid_request()


def _result_amount(value):
    if not _is_valid_amount(value):
        _invalid_result()


def _is_valid_amount(value):
    if type(value) is not Decimal:
        return False
    try:
        return (
            value.is_finite()
            and value > 0
            and value.as_tuple().exponent >= -2
        )
    except (DecimalException, OverflowError, ValueError):
        return False


def _canonical_amount(value):
    try:
        value_tuple = value.as_tuple()
        canonical_digits = len(value_tuple.digits) + max(value_tuple.exponent + 2, 0)
        if canonical_digits > _MAX_CANONICAL_DECIMAL_DIGITS:
            return _PARSE_FAILURE
        return value.quantize(_CENT, context=_DECIMAL_CONTEXT.copy())
    except (DecimalException, OverflowError, ValueError):
        return _PARSE_FAILURE


def _request_concept(value):
    if not _is_safe_concept(value):
        _invalid_request()


def _result_concept(value):
    if not _is_safe_concept(value):
        _invalid_result()


def _is_safe_concept(value):
    return (
        type(value) is str
        and 0 < len(value) <= _MAX_CONCEPT_LENGTH
        and value == value.strip()
        and all(
            character == " " or not _is_unsafe_character(character)
            for character in value
        )
    )


def _request_dates(created_at, expires_at):
    if not _valid_dates(created_at, expires_at):
        _invalid_request()


def _result_dates(created_at, expires_at):
    if not _valid_dates(created_at, expires_at):
        _invalid_result()


def _valid_dates(created_at, expires_at):
    if not (_is_aware_datetime(created_at) and _is_aware_datetime(expires_at)):
        return False
    canonical_created_at, canonical_expires_at = _canonical_dates(
        created_at, expires_at
    )
    return canonical_expires_at == canonical_created_at + _ORDER_LIFETIME


def _canonical_dates(created_at, expires_at):
    return (
        created_at.astimezone(timezone.utc),
        expires_at.astimezone(timezone.utc),
    )


def _is_aware_datetime(value):
    return (
        type(value) is datetime
        and value.tzinfo is not None
        and value.utcoffset() is not None
    )


def _is_structurally_safe_checkout_url(value):
    if (
        type(value) is not str
        or not value
        or not value.isascii()
        or any(_is_unsafe_character(character) for character in value)
        or "\\" in value
        or not _has_safe_percent_escapes(value)
    ):
        return False
    parsed = _safe_urlsplit(value)
    if parsed is _PARSE_FAILURE:
        return False
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        return False
    if _safe_port(parsed) is _PARSE_FAILURE:
        return False
    return _is_valid_hostname(parsed.hostname)


def _normalized_provider(value):
    if type(value) is not str or not value:
        return None
    normalized = value.strip().lower()
    if _PROVIDER.fullmatch(normalized) is None:
        return None
    return normalized


def _has_safe_percent_escapes(value):
    index = 0
    while index < len(value):
        if value[index] != "%":
            index += 1
            continue
        escape = value[index:index + 3]
        if _PERCENT_ESCAPE.fullmatch(escape) is None:
            return False
        decoded = int(escape[1:], 16)
        if (
            decoded <= 32
            or decoded == 127
            or decoded >= 128
            or decoded in _FORBIDDEN_ENCODED_SEPARATORS
        ):
            return False
        index += 3
    return True


def _safe_urlsplit(value):
    try:
        return urlsplit(value)
    except (TypeError, ValueError):
        return _PARSE_FAILURE


def _safe_port(parsed: SplitResult):
    try:
        return parsed.port
    except ValueError:
        return _PARSE_FAILURE


def _is_valid_hostname(hostname):
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        pass
    if len(hostname) > 253 or hostname.endswith("."):
        return False
    labels = hostname.split(".")
    return bool(labels) and all(_HOST_LABEL.fullmatch(label) for label in labels)


def _is_unsafe_character(character):
    return character.isspace() or unicodedata.category(character).startswith("C")


def _invalid_request():
    raise InvalidPaymentOrderCreationRequestError(
        "invalid payment order creation request"
    )


def _invalid_result():
    raise InvalidPaymentOrderCreationResultError(
        "invalid payment order creation result"
    )
