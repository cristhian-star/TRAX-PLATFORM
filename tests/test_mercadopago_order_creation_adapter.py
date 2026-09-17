from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal, localcontext
import io
import json
import traceback
import unittest
import urllib.error
from unittest.mock import Mock, patch

from app.services import mercadopago_payment_query_http as http
from app.services.mercadopago_order_creation_adapter import (
    MercadoPagoOrderAuthenticationError, MercadoPagoOrderConfiguration,
    MercadoPagoOrderConfigurationError, MercadoPagoOrderCreationAdapter,
    MercadoPagoOrderRejectedError, ProfessionalOAuthCredential,
    UrllibMercadoPagoOrderTransport,
)
from app.services.psp_payment_order_contract import (
    InvalidPaymentOrderCreationRequestError, InvalidPaymentOrderCreationResultError,
    PaymentOrderCreationCommand, PaymentOrderCreationUncertainError,
)


NOW = datetime(2026, 9, 17, 16, 0, tzinfo=timezone.utc)
TOKEN = "OAUTH_PROFESSIONAL_SECRET_123"
URL = "https://www.mercadopago.com.ar/checkout/v1/redirect?order_id=ORD123"


def command():
    return PaymentOrderCreationCommand(
        local_order_id="order-local-0001", obligation_reference="obligation-0001",
        professional_id=7, amount=Decimal("1250.50"), currency="ARS",
        concept="Cobro de servicio acordado", external_reference="reference-0001",
        idempotency_key="creation-key-0001", created_at=NOW,
        expires_at=NOW + timedelta(hours=72),
    )


def response(cmd=None, **changes):
    cmd = cmd or command()
    payload = {
        "id": "ORD123", "checkout_url": URL,
        "external_reference": cmd.external_reference, "currency": "ARS",
        "total_amount": format(cmd.amount, ".2f"),
    }
    payload.update(changes)
    return http.MercadoPagoHTTPResponse(
        201, (("Content-Type", "application/json; charset=utf-8"),),
        json.dumps(payload).encode(),
    )


class OrderAdapterTest(unittest.TestCase):
    def setUp(self):
        self.command = command()
        self.oauth = Mock(return_value=ProfessionalOAuthCredential(7, TOKEN, False, "ARS"))
        self.fee = Mock(return_value=Decimal("25.01"))
        self.transport = Mock(return_value=response())
        self.adapter = MercadoPagoOrderCreationAdapter(
            MercadoPagoOrderConfiguration(enabled=True), self.oauth, self.fee,
            self.transport, clock=lambda: NOW,
        )

    def test_exact_request_and_result(self):
        result = self.adapter.create_payment_order(self.command)
        request = self.transport.call_args.kwargs
        self.assertEqual(request, {
            "method": "POST", "url": "https://api.mercadopago.com/v1/orders",
            "headers": {"Authorization": f"Bearer {TOKEN}",
                        "X-Idempotency-Key": self.command.idempotency_key,
                        "Accept": "application/json", "Content-Type": "application/json"},
            "timeout": 10.0, "allow_redirects": False,
            "body": b'{"type":"online","processing_mode":"manual","total_amount":"1250.50","external_reference":"reference-0001","marketplace_fee":"25.01","expiration_time":"PT72H","items":[{"title":"Cobro de servicio acordado","quantity":1,"unit_price":"1250.50"}]}',
        })
        self.oauth.assert_called_once_with(7)
        self.fee.assert_called_once_with(self.command)
        self.transport.assert_called_once()
        self.assertEqual(result.external_order_id, "ORD123")
        self.assertEqual(result.checkout_url, URL)
        self.assertEqual(result.expires_at, NOW + timedelta(hours=72))
        self.assertEqual((result.provider, result.live_mode), ("mercadopago", False))

    def test_decimal_is_exact_even_under_low_precision_context(self):
        cmd = replace(self.command, amount=Decimal("12345678901234567890.12"))
        self.transport.return_value = response(cmd)
        with localcontext() as context:
            context.prec = 2
            result = self.adapter.create_payment_order(cmd)
        self.assertEqual(result.amount, cmd.amount)
        self.assertEqual(json.loads(self.transport.call_args.kwargs["body"])["total_amount"],
                         "12345678901234567890.12")

    def test_each_professional_gets_own_oauth_without_shared_prepared_state(self):
        tokens = {7: TOKEN, 8: "OAUTH_OTHER_PROFESSIONAL"}
        self.oauth.side_effect = lambda professional: ProfessionalOAuthCredential(
            professional, tokens[professional], False, "ARS"
        )
        first = self.adapter.prepare_payment_order(self.command)
        second_command = replace(self.command, professional_id=8, idempotency_key="creation-key-0002")
        second = self.adapter.prepare_payment_order(second_command)
        first.create_payment_order(self.command)
        second.create_payment_order(second_command)
        self.assertEqual(
            [call.kwargs["headers"]["Authorization"] for call in self.transport.call_args_list],
            [f"Bearer {tokens[7]}", f"Bearer {tokens[8]}"],
        )
        self.assertEqual([call.args[0] for call in self.oauth.call_args_list], [7, 8])

    def test_currency_and_dates_are_not_relaxed(self):
        for changes in ({"currency": "USD"}, {"amount": 1.2},
                        {"expires_at": NOW + timedelta(hours=71)}):
            with self.subTest(changes=changes), self.assertRaises(InvalidPaymentOrderCreationRequestError):
                replace(self.command, **changes)
        self.transport.assert_not_called()

    def test_key_limits_without_truncation_or_regeneration(self):
        for length in (128, 129, 160):
            cmd = replace(self.command, idempotency_key="x" * length)
            with self.subTest(length=length):
                if length > 128:
                    with self.assertRaises(InvalidPaymentOrderCreationRequestError):
                        self.adapter.prepare_payment_order(cmd)
                else:
                    self.adapter.create_payment_order(cmd)
                    self.assertEqual(self.transport.call_args.kwargs["headers"]["X-Idempotency-Key"],
                                     cmd.idempotency_key)
        self.assertEqual(self.transport.call_count, 1)

    def test_reference_limits_and_remote_alphabet(self):
        for reference in ("x" * 65, "reference.with.dot", "reference:123"):
            with self.subTest(reference=reference), self.assertRaises(InvalidPaymentOrderCreationRequestError):
                self.adapter.prepare_payment_order(replace(self.command, external_reference=reference))
        self.oauth.assert_not_called()

    def test_disabled_and_invalid_configuration(self):
        disabled = replace(self.adapter, configuration=MercadoPagoOrderConfiguration())
        with self.assertRaises(MercadoPagoOrderConfigurationError):
            disabled.create_payment_order(self.command)
        for timeout in (True, 0, -1, 31, float("nan"), float("inf"), "10"):
            with self.subTest(timeout=timeout), self.assertRaises(MercadoPagoOrderConfigurationError):
                MercadoPagoOrderConfiguration(enabled=True, timeout=timeout)
        for field in ("enabled", "live_mode"):
            with self.assertRaises(MercadoPagoOrderConfigurationError):
                MercadoPagoOrderConfiguration(**{field: 1})
        self.oauth.assert_not_called()
        self.transport.assert_not_called()

    def test_oauth_receiver_currency_and_environment_must_match(self):
        for credential in (
            None, TOKEN, ProfessionalOAuthCredential(8, TOKEN, False, "ARS"),
            ProfessionalOAuthCredential(7, TOKEN, True, "ARS"),
            ProfessionalOAuthCredential(7, TOKEN, False, "USD"),
            ProfessionalOAuthCredential(7, "", False, "ARS"),
            ProfessionalOAuthCredential(7, "bad\ntoken", False, "ARS"),
        ):
            self.oauth.return_value = credential
            with self.subTest(credential=repr(credential)), self.assertRaises(MercadoPagoOrderConfigurationError):
                self.adapter.prepare_payment_order(self.command)
        self.transport.assert_not_called()

    def test_explicit_fee_has_no_default_and_zero_is_allowed_only_explicitly(self):
        for fee in (None, 0, 1.1, "25", Decimal("-1"), Decimal("1250.51"),
                    Decimal("0.001"), Decimal("NaN"), Decimal("Infinity")):
            self.fee.return_value = fee
            with self.subTest(fee=fee), self.assertRaises(MercadoPagoOrderConfigurationError):
                self.adapter.prepare_payment_order(self.command)
        self.fee.return_value = Decimal("0")
        self.adapter.create_payment_order(self.command)
        self.assertEqual(json.loads(self.transport.call_args.kwargs["body"])["marketplace_fee"], "0.00")
        self.assertEqual(self.transport.call_count, 1)

    def test_prepared_values_are_immutable_and_do_not_reresolve_providers(self):
        prepared = self.adapter.prepare_payment_order(self.command)
        with self.assertRaises(FrozenInstanceError):
            prepared.token = "different"
        self.oauth.side_effect = AssertionError("must not resolve again")
        self.fee.side_effect = AssertionError("must not resolve again")
        prepared.create_payment_order(self.command)
        with self.assertRaises(InvalidPaymentOrderCreationRequestError):
            prepared.create_payment_order(replace(self.command, concept="Different"))
        self.assertEqual(self.transport.call_count, 1)

    def test_http_errors_classified_without_retries(self):
        cases = {
            200: PaymentOrderCreationUncertainError, 302: PaymentOrderCreationUncertainError,
            400: MercadoPagoOrderRejectedError, 401: MercadoPagoOrderAuthenticationError,
            403: MercadoPagoOrderAuthenticationError, 404: MercadoPagoOrderRejectedError,
            409: PaymentOrderCreationUncertainError, 422: MercadoPagoOrderRejectedError,
            423: PaymentOrderCreationUncertainError, 429: PaymentOrderCreationUncertainError,
            500: PaymentOrderCreationUncertainError, 503: PaymentOrderCreationUncertainError,
        }
        for status, error in cases.items():
            self.transport.reset_mock()
            self.transport.return_value = http.MercadoPagoHTTPResponse(status, (), TOKEN.encode())
            with self.subTest(status=status), self.assertRaises(error):
                self.adapter.create_payment_order(self.command)
            self.transport.assert_called_once()

    def test_timeout_and_provider_exceptions_never_expose_secrets(self):
        for provider in (self.transport, self.oauth, self.fee):
            provider.side_effect = RuntimeError(TOKEN)
            try:
                self.adapter.create_payment_order(self.command)
            except (PaymentOrderCreationUncertainError, MercadoPagoOrderConfigurationError):
                self.assertNotIn(TOKEN, traceback.format_exc())
            else:
                self.fail("expected neutral error")
            provider.side_effect = None
        self.transport.reset_mock()
        self.transport.side_effect = TimeoutError(TOKEN)
        with self.assertRaises(PaymentOrderCreationUncertainError):
            self.adapter.create_payment_order(self.command)
        self.transport.assert_called_once()
        for value in (self.adapter, self.oauth.return_value,
                      self.adapter.prepare_payment_order(self.command)):
            self.assertNotIn(TOKEN, repr(value))

    def test_hostile_checkout_urls(self):
        for url in (
            "https://evil.test/checkout", "https://www.mercadopago.com.ar.evil.test/",
            "https://evil.test@www.mercadopago.com.ar/", "http://www.mercadopago.com.ar/",
            "https://www.mercadopago.com.ar:444/", "https://www.mercadopago.com.ar/#token",
            "https://www.mercadopago.com.ar/\n", "https://www.mercadopago.com.ar./",
        ):
            self.transport.return_value = response(checkout_url=url)
            with self.subTest(url=url), self.assertRaises(InvalidPaymentOrderCreationResultError):
                self.adapter.create_payment_order(self.command)

    def assert_neutral_error(self, error_type, message, marker):
        with self.assertRaises(error_type) as caught:
            self.adapter.create_payment_order(self.command)
        error = caught.exception
        self.assertIs(type(error), error_type)
        self.assertEqual(str(error), message)
        self.assertIsNone(error.__context__)
        self.assertIsNone(error.__cause__)
        self.assertNotIn(marker, repr(error))
        self.assertNotIn(marker, repr(error.args))
        self.assertNotIn(marker, str(error))
        self.assertNotIn(marker, "".join(traceback.format_exception(error)))

    def test_oauth_failure_discards_sensitive_exception_context(self):
        marker = "SENSITIVE_OAUTH_FAILURE"
        self.oauth.side_effect = RuntimeError(marker)
        self.assert_neutral_error(MercadoPagoOrderConfigurationError,
                                  "order prerequisites unavailable", marker)
        self.oauth.assert_called_once_with(7)
        self.fee.assert_not_called()
        self.transport.assert_not_called()

    def test_commission_failure_discards_sensitive_exception_context(self):
        marker = "SENSITIVE_COMMISSION_FAILURE"
        self.fee.side_effect = RuntimeError(marker)
        self.assert_neutral_error(MercadoPagoOrderConfigurationError,
                                  "order prerequisites unavailable", marker)
        self.oauth.assert_called_once_with(7)
        self.fee.assert_called_once_with(self.command)
        self.transport.assert_not_called()

    def test_token_validation_discards_sensitive_exception_context(self):
        marker = "SENSITIVE_TOKEN_VALIDATION"
        with patch.object(http, "_validate_access_token", side_effect=ValueError(marker)) as validator:
            self.assert_neutral_error(MercadoPagoOrderConfigurationError,
                                      "invalid receiver configuration", marker)
        validator.assert_called_once_with(TOKEN)
        self.oauth.assert_called_once_with(7)
        self.fee.assert_not_called()
        self.transport.assert_not_called()

    def test_transport_failures_discard_sensitive_exception_context(self):
        marker = "SENSITIVE_TRANSPORT_FAILURE"
        for error_type in (RuntimeError, TimeoutError):
            with self.subTest(error_type=error_type):
                self.transport.reset_mock()
                self.oauth.reset_mock()
                self.fee.reset_mock()
                self.transport.side_effect = error_type(marker)
                self.assert_neutral_error(PaymentOrderCreationUncertainError,
                                          "order creation is uncertain", marker)
                self.transport.assert_called_once()
                self.oauth.assert_called_once_with(7)
                self.fee.assert_called_once_with(self.command)

    def test_response_validation_discards_sensitive_exception_context(self):
        marker = "SENSITIVE_RESPONSE_VALIDATION"
        with patch.object(http, "_decode_json_response", side_effect=ValueError(marker)) as decoder:
            self.assert_neutral_error(InvalidPaymentOrderCreationResultError,
                                      "invalid order response", marker)
        decoder.assert_called_once_with(self.transport.return_value)
        self.transport.assert_called_once()
        self.oauth.assert_called_once_with(7)
        self.fee.assert_called_once_with(self.command)

    def test_url_validation_discards_sensitive_exception_context(self):
        marker = "SENSITIVE_URL_PORT"
        self.transport.return_value = response(
            checkout_url=f"https://www.mercadopago.com.ar:{marker}/checkout",
        )
        self.assert_neutral_error(InvalidPaymentOrderCreationResultError,
                                  "invalid order response", marker)
        self.transport.assert_called_once()
        self.oauth.assert_called_once_with(7)
        self.fee.assert_called_once_with(self.command)

    def test_invalid_response_identity_amount_currency_and_reference(self):
        for changes in ({"id": None}, {"id": " "}, {"checkout_url": None},
                        {"currency": "USD"}, {"external_reference": "other"},
                        {"total_amount": "1250.51"}, {"total_amount": 1250.5},
                        {"total_amount": "NaN"}):
            self.transport.return_value = response(**changes)
            with self.subTest(changes=changes), self.assertRaises(InvalidPaymentOrderCreationResultError):
                self.adapter.create_payment_order(self.command)

    def test_strict_json_and_response_limits(self):
        for body in (b"", b"[]", b"{", b'{"id":1,"id":2}', b'{"id":NaN}',
                     b"\xff", b"x" * (http._MAX_RESPONSE_BYTES + 1)):
            self.transport.return_value = http.MercadoPagoHTTPResponse(
                201, (("Content-Type", "application/json"),), body,
            )
            with self.subTest(body_size=len(body)), self.assertRaises(InvalidPaymentOrderCreationResultError):
                self.adapter.create_payment_order(self.command)
        self.transport.return_value = replace(response(), headers=(("Content-Type", "text/html"),))
        with self.assertRaises(InvalidPaymentOrderCreationResultError):
            self.adapter.create_payment_order(self.command)

    def test_malformed_transport_response_is_uncertain_and_single_call(self):
        for value in (None, {}, replace(response(), status_code=True)):
            self.transport.reset_mock()
            self.transport.return_value = value
            with self.assertRaises(PaymentOrderCreationUncertainError):
                self.adapter.create_payment_order(self.command)
            self.transport.assert_called_once()

    def test_expired_preparation_and_expired_prepared_request_make_no_call(self):
        adapter = replace(self.adapter, clock=lambda: self.command.expires_at)
        with self.assertRaises(InvalidPaymentOrderCreationRequestError):
            adapter.prepare_payment_order(self.command)
        now = [NOW]
        prepared = replace(self.adapter, clock=lambda: now[0]).prepare_payment_order(self.command)
        now[0] = self.command.expires_at
        with self.assertRaises(InvalidPaymentOrderCreationRequestError):
            prepared.create_payment_order(self.command)
        self.transport.assert_not_called()

    def test_post_transport_reuses_tls_no_redirect_and_read_limit(self):
        with patch.object(http.ssl, "create_default_context") as tls, \
             patch.object(http.urllib.request, "build_opener") as opener:
            transport = UrllibMercadoPagoOrderTransport()
            tls.assert_called_once()
            self.assertIsInstance(opener.call_args.args[1], http._NoRedirectHandler)
        fake = Mock()
        fake.status = 201
        fake.headers.items.return_value = [("Content-Type", "application/json")]
        fake.read.return_value = response().body
        fake.__enter__ = Mock(return_value=fake)
        fake.__exit__ = Mock(return_value=False)
        transport._opener = Mock()
        transport._opener.open.return_value = fake
        transport(method="POST", url="https://api.mercadopago.com/v1/orders",
                  headers={}, timeout=10, allow_redirects=False, body=b"{}")
        fake.read.assert_called_once_with(http._MAX_RESPONSE_BYTES + 1)
        request = transport._opener.open.call_args.args[0]
        self.assertEqual((request.method, request.data), ("POST", b"{}"))

    def test_post_http_error_closes_without_reading_sensitive_body(self):
        transport = UrllibMercadoPagoOrderTransport()
        body = io.BytesIO(TOKEN.encode())
        error = urllib.error.HTTPError("https://api.mercadopago.com/v1/orders", 401, TOKEN, {}, body)
        transport._opener = Mock()
        transport._opener.open.side_effect = error
        result = transport(method="POST", url="https://api.mercadopago.com/v1/orders",
                           headers={}, timeout=10, allow_redirects=False, body=b"{}")
        self.assertEqual(result, http.MercadoPagoHTTPResponse(401, (), b""))
        self.assertTrue(body.closed)
        transport._opener.open.assert_called_once()


if __name__ == "__main__":
    unittest.main()
