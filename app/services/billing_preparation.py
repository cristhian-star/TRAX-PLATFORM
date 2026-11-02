"""Internal preparation only. These values are never an ARCA authorization.

No transport, credentials, numbering or financial effects belong in this module.
The caller must authorize the actor before loading private data or persisting it.
"""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import re


class BillingValidationError(ValueError):
    """Field identifiers only: never echo private input into an exception."""

    def __init__(self, field_name):
        self.field_name = field_name
        super().__init__(f"Revisá el campo {field_name}.")


def _text(value, name, maximum, *, optional=False):
    if not isinstance(value, str) or len(value) > maximum:
        raise BillingValidationError(name)
    if value != value.strip() or (not value and not optional):
        raise BillingValidationError(name)
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise BillingValidationError(name)
    return value


def validate_cuit(value):
    """Syntax and checksum only; does not establish identity or tax status."""
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{11}", value):
        raise BillingValidationError("cuit")
    checksum = 11 - sum(int(n) * w for n, w in zip(value[:10], (5, 4, 3, 2, 7, 6, 5, 4, 3, 2))) % 11
    checksum = 0 if checksum == 11 else 9 if checksum == 10 else checksum
    if len(set(value)) == 1 or checksum != int(value[-1]):
        raise BillingValidationError("cuit")
    return value


def validate_amount(value):
    """Canonical positive ARS amount; explicit HALF_UP to two decimal places.

    The storage bound is technical, not a fiscal/commercial emission limit.
    Binary floating point, exponent notation and non-finite inputs are refused.
    """
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{1,12}(\.[0-9]{1,6})?", value):
        raise BillingValidationError("amount")
    try:
        with localcontext() as context:
            context.prec = 28
            amount = Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except InvalidOperation:
        raise BillingValidationError("amount") from None
    if not amount.is_finite() or not Decimal("0") < amount <= Decimal("999999999999.99"):
        raise BillingValidationError("amount")
    return amount


def _date(value, name):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise BillingValidationError(name)
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise BillingValidationError(name) from None


@dataclass(frozen=True, slots=True, repr=False)
class DeclaredFiscalProfile:
    cuit: str = field(repr=False)
    legal_name: str = field(repr=False)
    fiscal_address: str = field(repr=False)
    # Fixed scope. Nothing here claims verification by ARCA.
    person_type: str = field(default="HUMAN", init=False)
    tax_regime: str = field(default="MONOTRIBUTO", init=False)
    verification_status: str = field(default="DECLARED_UNVERIFIED", init=False)


def prepare_profile(*, cuit, legal_name, fiscal_address, human_monotributo_declared):
    if human_monotributo_declared is not True:
        raise BillingValidationError("human_monotributo_declared")
    return DeclaredFiscalProfile(
        validate_cuit(cuit), _text(legal_name, "legal_name", 200),
        _text(fiscal_address, "fiscal_address", 300),
    )


@dataclass(frozen=True, slots=True, repr=False)
class InternalBillingDraft:
    description: str = field(repr=False)
    amount: Decimal
    recipient_name: str = field(repr=False)
    service_from: date
    service_to: date
    currency: str = field(default="ARS", init=False)
    voucher_type: str = field(default="C", init=False)
    status: str = field(default="INTERNAL_DRAFT", init=False)


def prepare_draft(*, description, amount, recipient_name, service_from, service_to, currency="ARS"):
    """Minimal internal data, deliberately insufficient for fiscal submission.

    No receiver category, document, point of sale or tax date is inferred.
    Receiver details and official catalogs must be resolved before review/emission.
    """
    if currency != "ARS":
        raise BillingValidationError("currency")
    start, end = _date(service_from, "service_from"), _date(service_to, "service_to")
    if start > end:
        raise BillingValidationError("service_to")
    return InternalBillingDraft(
        _text(description, "description", 1000), validate_amount(amount),
        _text(recipient_name, "recipient_name", 200, optional=True), start, end,
    )
