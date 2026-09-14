import json
import traceback
import unittest

from app.services.mercadopago_payment_query_http import (
    MercadoPagoHTTPResponse,
    MercadoPagoPaymentAuthenticationError,
    MercadoPagoPaymentNotFoundError,
    MercadoPagoPaymentQueryHTTPClient,
    MercadoPagoPaymentRecoverableError,
    MercadoPagoPaymentRequestRejectedError,
    MercadoPagoPaymentResponseError,
)
from app.services.psp_contract import PaymentAttemptStatus


class RecordingTransport:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def __call__(self, **request):
        self.calls.append(request)
        if self.error is not None:
            raise self.error
        return self.response


class MercadoPagoPaymentQueryHTTPClientTest(unittest.TestCase):
    TOKEN = "TEST_ACCESS_TOKEN_123"

    @staticmethod
    def _response(status_code=200, body=None, headers=None):
        if body is None:
            body = json.dumps({
                "id": 123456789,
                "status": "approved",
                "live_mode": False,
                "status_detail": "accredited",
            }).encode()
        return MercadoPagoHTTPResponse(
            status_code,
            headers if headers is not None else (
                ("Content-Type", "application/json; charset=utf-8"),
            ),
            body,
        )

    def _client(self, response=None, **overrides):
        transport = overrides.pop(
            "transport", RecordingTransport(response or self._response())
        )
        client = MercadoPagoPaymentQueryHTTPClient(
            access_token=overrides.pop("access_token", self.TOKEN),
            transport=transport,
            timeout=overrides.pop("timeout", 7),
            **overrides,
        )
        return client, transport

    def test_request_is_single_fixed_get_without_body_query_redirects_or_retries(self):
        client, transport = self._client()
        result = client.get_payment("123456789", expected_live_mode=False)
        self.assertEqual(result.status, PaymentAttemptStatus.APPROVED)
        self.assertEqual(len(transport.calls), 1)
        request = transport.calls[0]
        self.assertEqual(request["method"], "GET")
        self.assertEqual(
            request["url"],
            "https://api.mercadopago.com/v1/payments/123456789",
        )
        self.assertEqual(request["body"], None)
        self.assertEqual(request["timeout"], 7.0)
        self.assertIs(request["allow_redirects"], False)
        self.assertEqual(request["headers"], {
            "Authorization": f"Bearer {self.TOKEN}",
            "Accept": "application/json",
        })
        self.assertNotIn("params", request)

    def test_payment_id_is_validated_before_transport_or_url_construction(self):
        client, transport = self._client()
        for value in ("../123", "123?secret=true", "123/456", "", True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                client.get_payment(value, expected_live_mode=False)
        self.assertEqual(transport.calls, [])

    def test_token_uses_strict_ascii_b64token_allowlist(self):
        invalid = (
            None,
            "",
            " token",
            "token ",
            "to ken",
            "token\tvalue",
            "token\nvalue",
            "token\x00value",
            "token\x1fvalue",
            "token\x7fvalue",
            "token\x80value",
            "token\x9fvalue",
            "token\u200bvalue",
            "token\u00a0value",
            "token\u202evalue",
            "ＴEST_TOKEN",
            "token=value",
            "x" * 2049,
        )
        for value in invalid:
            transport = RecordingTransport(self._response())
            with self.subTest(value=repr(value)), self.assertRaises(ValueError):
                MercadoPagoPaymentQueryHTTPClient(
                    access_token=value,
                    transport=transport,
                )
            self.assertEqual(transport.calls, [])

        valid = (
            "APP_USR-1234567890-abcdef",
            "AbC09-._~+/",
            "AbC09-._~+/=",
            "AbC09==",
            "x" * 2048,
        )
        for value in valid:
            with self.subTest(value=value):
                client, _ = self._client(access_token=value)
                self.assertNotIn(value, repr(client))

    def test_invalid_token_is_not_exposed_by_configuration_error(self):
        token = "PRIVATE_TOKEN\u202eMARKER"
        transport = RecordingTransport(self._response())
        try:
            MercadoPagoPaymentQueryHTTPClient(
                access_token=token,
                transport=transport,
            )
        except ValueError as exc:
            captured_exc = exc
            rendered = " ".join((
                str(exc),
                repr(exc),
                "".join(traceback.format_exception(exc)),
                repr(exc.args),
                repr(vars(exc)),
            ))
        else:
            self.fail("invalid access token was accepted")
        self.assertNotIn(token, rendered)
        self.assertEqual(
            captured_exc.args,
            ("invalid access token configuration",),
        )
        self.assertEqual(vars(captured_exc), {})
        self.assertIsNone(captured_exc.__cause__)
        self.assertIsNone(captured_exc.__context__)
        self.assertEqual(transport.calls, [])

    def test_timeout_is_explicit_and_bounded(self):
        for value in (True, 0, -1, 31, None, "10"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self._client(timeout=value)

    def test_status_codes_have_neutral_classification_without_reading_body(self):
        cases = {
            401: MercadoPagoPaymentAuthenticationError,
            403: MercadoPagoPaymentAuthenticationError,
            404: MercadoPagoPaymentNotFoundError,
            429: MercadoPagoPaymentRecoverableError,
            500: MercadoPagoPaymentRecoverableError,
            503: MercadoPagoPaymentRecoverableError,
            400: MercadoPagoPaymentRequestRejectedError,
            422: MercadoPagoPaymentRequestRejectedError,
        }
        for status_code, expected in cases.items():
            marker = f"PRIVATE-BODY-{status_code}".encode()
            client, _ = self._client(self._response(status_code, marker))
            with self.subTest(status_code=status_code), self.assertRaises(expected) as ctx:
                client.get_payment("123456789", expected_live_mode=False)
            self.assertNotIn(marker.decode(), str(ctx.exception))

    def test_transport_timeout_network_and_other_failures_are_recoverable(self):
        for error in (TimeoutError("PRIVATE-TIMEOUT"), OSError("PRIVATE-NETWORK")):
            client, transport = self._client(transport=RecordingTransport(error=error))
            with self.subTest(error=type(error)), self.assertRaises(
                MercadoPagoPaymentRecoverableError
            ) as ctx:
                client.get_payment("123456789", expected_live_mode=False)
            self.assertEqual(len(transport.calls), 1)
            self.assertIsNone(ctx.exception.__cause__)
            self.assertIsNone(ctx.exception.__context__)
            self.assertNotIn(str(error), "".join(traceback.format_exception(ctx.exception)))

    def test_json_requires_utf8_object_and_supported_content_type(self):
        invalid = (
            self._response(body=b"not-json"),
            self._response(body=b"[]"),
            self._response(body=b"\xff"),
            self._response(body=b'{"id": NaN}'),
            self._response(headers=(("Content-Type", "text/json"),)),
            self._response(headers=(("Content-Type", "application/json; charset=latin-1"),)),
            self._response(headers=()),
        )
        for response in invalid:
            client, _ = self._client(response)
            with self.subTest(response=response), self.assertRaises(
                MercadoPagoPaymentResponseError
            ):
                client.get_payment("123456789", expected_live_mode=False)

    def test_duplicate_json_keys_are_rejected_at_any_object_level(self):
        bodies = (
            b'{"id":123456789,"id":123456789,"status":"approved","live_mode":false}',
            b'{"id":123456789,"status":"approved","live_mode":false,"extra":{"x":1,"x":1}}',
        )
        for body in bodies:
            client, _ = self._client(self._response(body=body))
            with self.subTest(body=body), self.assertRaises(
                MercadoPagoPaymentResponseError
            ):
                client.get_payment("123456789", expected_live_mode=False)

    def test_oversized_or_empty_response_is_rejected(self):
        for body in (b"", b"{" + b" " * (1024 * 1024) + b"}"):
            client, _ = self._client(self._response(body=body))
            with self.subTest(size=len(body)), self.assertRaises(
                MercadoPagoPaymentResponseError
            ):
                client.get_payment("123456789", expected_live_mode=False)

    def test_token_payload_url_and_transport_error_do_not_leak(self):
        token = "PRIVATE_ACCESS_TOKEN_MARKER"
        marker = "PRIVATE_PROVIDER_ERROR_MARKER"
        client, _ = self._client(
            access_token=token,
            transport=RecordingTransport(error=RuntimeError(marker)),
        )
        try:
            client.get_payment("123456789", expected_live_mode=False)
        except MercadoPagoPaymentRecoverableError as exc:
            captured_exc = exc
            rendered = " ".join((str(exc), repr(exc),
                                 "".join(traceback.format_exception(exc)),
                                 repr(exc.args), repr(vars(exc)), repr(client)))
        else:
            self.fail("transport failure was accepted")
        self.assertNotIn(token, rendered)
        self.assertNotIn(marker, rendered)
        self.assertNotIn("https://api.mercadopago.com/v1/payments/", rendered)
        self.assertIsNone(captured_exc.__cause__)
        self.assertIsNone(captured_exc.__context__)

    def test_success_reuses_approved_query_contract(self):
        client, _ = self._client(self._response(body=json.dumps({
            "id": 123456789,
            "status": "charged_back",
            "live_mode": False,
        }).encode()))
        with self.assertRaises(ValueError):
            client.get_payment("123456789", expected_live_mode=False)


if __name__ == "__main__":
    unittest.main()
