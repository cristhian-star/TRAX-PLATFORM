from dataclasses import FrozenInstanceError
import json
import traceback
import unittest

from app.services.mercadopago_payment_query_http import (
    MercadoPagoHTTPResponse,
    MercadoPagoPaymentAuthenticationError,
    MercadoPagoPaymentNotFoundError,
    MercadoPagoPaymentQueryHTTPClient,
    MercadoPagoPaymentRecoverableError,
    MercadoPagoPaymentResponseError,
)
from app.services.mercadopago_psp_adapter import MercadoPagoPSPAdapter
from app.services.psp_event_reconciliation import PSPEventReconciliationProcessor
from app.services.psp_contract import (
    PSPPaymentQueryAdapter,
    PSPPaymentQueryError,
    PSPPaymentQueryUncertainError,
    PaymentAttemptStatus,
)


class StubClient:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def get_payment(self, payment_id, *, expected_live_mode):
        self.calls.append((payment_id, expected_live_mode))
        if self.error is not None:
            raise self.error
        return self.result


class Transport:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def __call__(self, **request):
        self.calls.append(request)
        return self.response


class MercadoPagoPSPAdapterTest(unittest.TestCase):
    @staticmethod
    def _query_result(status):
        from app.services.mercadopago_payment_query import (
            MercadoPagoPaymentQueryResult,
        )
        return MercadoPagoPaymentQueryResult("123456", status, False)

    def test_implements_only_neutral_query_capability_with_fixed_context(self):
        client = StubClient(self._query_result(PaymentAttemptStatus.APPROVED))
        adapter = MercadoPagoPSPAdapter(client=client, live_mode=False)
        self.assertIsInstance(adapter, PSPPaymentQueryAdapter)
        self.assertEqual(adapter.provider, "mercadopago")
        self.assertIs(adapter.live_mode, False)
        self.assertFalse(hasattr(adapter, "create_attempt"))
        self.assertFalse(hasattr(adapter, "get_attempt"))

    def test_adapter_and_client_context_cannot_be_reassigned(self):
        client = StubClient(self._query_result(PaymentAttemptStatus.APPROVED))
        adapter = MercadoPagoPSPAdapter(client=client, live_mode=False)
        replacements = {
            "provider": "other-provider",
            "live_mode": True,
            "_live_mode": True,
            "_client": StubClient(),
        }
        for attribute, value in replacements.items():
            with self.subTest(attribute=attribute), self.assertRaises(
                (FrozenInstanceError, AttributeError, TypeError)
            ):
                setattr(adapter, attribute, value)
        self.assertEqual(adapter.provider, "mercadopago")
        self.assertIs(adapter.live_mode, False)
        self.assertIs(adapter._client, client)
        processor = PSPEventReconciliationProcessor(
            session_factory=lambda: None,
            adapter=adapter,
            provider="mercadopago",
            live_mode=False,
            payment_topics=("payment",),
        )
        self.assertIs(processor._adapter, adapter)
        with self.assertRaises(ValueError):
            PSPEventReconciliationProcessor(
                session_factory=lambda: None,
                adapter=adapter,
                provider="mercadopago",
                live_mode=True,
                payment_topics=("payment",),
            )

    def test_authoritative_statuses_map_to_minimal_immutable_result(self):
        for status in PaymentAttemptStatus:
            client = StubClient(self._query_result(status))
            adapter = MercadoPagoPSPAdapter(client=client, live_mode=False)
            result = adapter.query_payment("123456")
            self.assertEqual(result.external_attempt_id, "123456")
            self.assertEqual(result.status, status)
            self.assertEqual(client.calls, [("123456", False)])
            with self.assertRaises(AttributeError):
                result.status = PaymentAttemptStatus.REJECTED

    def test_invalid_id_and_configuration_fail_before_client_call(self):
        client = StubClient()
        adapter = MercadoPagoPSPAdapter(client=client, live_mode=False)
        for value in ("../123", "123/456", "", True):
            with self.subTest(value=value), self.assertRaises(
                PSPPaymentQueryError
            ):
                adapter.query_payment(value)
        self.assertEqual(client.calls, [])
        with self.assertRaises(TypeError):
            MercadoPagoPSPAdapter(client=client, live_mode=0)

    def test_recoverable_not_found_and_nonrepresentable_are_uncertain(self):
        from app.services.mercadopago_payment_query import (
            MercadoPagoPaymentStatusNotRepresentableError,
        )
        errors = (
            MercadoPagoPaymentNotFoundError("private"),
            MercadoPagoPaymentRecoverableError("private"),
            MercadoPagoPaymentStatusNotRepresentableError("private"),
        )
        for error in errors:
            client = StubClient(error=error)
            adapter = MercadoPagoPSPAdapter(client=client, live_mode=False)
            with self.subTest(error=type(error)), self.assertRaises(
                PSPPaymentQueryUncertainError
            ) as ctx:
                adapter.query_payment("123456")
            self.assertEqual(ctx.exception.external_attempt_id, "123456")
            self.assertEqual(client.calls, [("123456", False)])

    def test_authentication_and_contract_failures_are_explicit_neutral_errors(self):
        errors = (
            MercadoPagoPaymentAuthenticationError("private"),
            MercadoPagoPaymentResponseError("private"),
            ValueError("private"),
        )
        for error in errors:
            client = StubClient(error=error)
            adapter = MercadoPagoPSPAdapter(client=client, live_mode=True)
            with self.subTest(error=type(error)), self.assertRaises(
                PSPPaymentQueryError
            ) as ctx:
                adapter.query_payment("123456")
            self.assertNotIn("private", str(ctx.exception))
            self.assertIsNone(ctx.exception.__cause__)
            self.assertIsNone(ctx.exception.__context__)

    def test_actual_http_client_and_simulated_transport_make_one_query(self):
        body = json.dumps({
            "id": 123456,
            "status": "pending",
            "live_mode": False,
        }).encode()
        transport = Transport(MercadoPagoHTTPResponse(
            200, (("Content-Type", "application/json"),), body
        ))
        client = MercadoPagoPaymentQueryHTTPClient(
            access_token="APP_USR-fake-token",
            transport=transport,
            timeout=5,
        )
        adapter = MercadoPagoPSPAdapter(client=client, live_mode=False)
        result = adapter.query_payment("123456")
        self.assertEqual(result.status, PaymentAttemptStatus.PENDING)
        self.assertEqual(len(transport.calls), 1)

    def test_secret_and_provider_errors_do_not_leak(self):
        token = "APP_USR-PRIVATE_TOKEN"
        marker = "PRIVATE_PROVIDER_MARKER"

        class FailingTransport:
            def __call__(self, **_request):
                raise OSError(marker)

        client = MercadoPagoPaymentQueryHTTPClient(
            access_token=token, transport=FailingTransport(), timeout=5
        )
        adapter = MercadoPagoPSPAdapter(client=client, live_mode=False)
        try:
            adapter.query_payment("123456")
        except PSPPaymentQueryUncertainError as exc:
            captured = exc
            exposed = " ".join((str(exc), repr(exc), repr(exc.args),
                                repr(vars(exc)), repr(adapter),
                                "".join(traceback.format_exception(exc))))
        else:
            self.fail("transport failure was accepted")
        self.assertNotIn(token, exposed)
        self.assertNotIn(marker, exposed)
        self.assertIsNone(captured.__cause__)
        self.assertIsNone(captured.__context__)


if __name__ == "__main__":
    unittest.main()
