import unittest
from types import SimpleNamespace

from app.services.whatsapp_contact_service import (
    IDENTIFIER_PHONE,
    IDENTIFIER_USERNAME,
    normalizar_whatsapp_username,
    resolver_identificador_contacto,
    validar_whatsapp_username,
)


class WhatsAppContactPrivacyServiceTest(unittest.TestCase):
    def test_username_with_at_is_normalized(self):
        self.assertEqual(normalizar_whatsapp_username(" @NombreProfesional "), "nombreprofesional")

    def test_username_url_is_rejected(self):
        with self.assertRaises(ValueError):
            normalizar_whatsapp_username("https://wa.me/nombre")

    def test_invalid_username_is_false(self):
        self.assertFalse(validar_whatsapp_username("nombre profesional"))

    def test_auto_with_username_prioritizes_username_conceptually(self):
        professional = SimpleNamespace(
            telefono="+54 9 11 0000-1001",
            whatsapp_username="@NexoElectrico",
            whatsapp_contact_preference="AUTO",
        )

        result = resolver_identificador_contacto(professional)

        self.assertEqual(result["type"], IDENTIFIER_USERNAME)
        self.assertEqual(result["technical_type"], IDENTIFIER_PHONE)
        self.assertEqual(result["technical_identifier"], "5491100001001")
        self.assertNotIn("5491100001001", result["masked"])

    def test_auto_without_username_uses_phone(self):
        professional = SimpleNamespace(
            telefono="+54 9 11 0000-1001",
            whatsapp_username=None,
            whatsapp_contact_preference="AUTO",
        )

        result = resolver_identificador_contacto(professional)

        self.assertEqual(result["type"], IDENTIFIER_PHONE)
        self.assertEqual(result["masked"], "*********1001")

    def test_phone_preference_uses_phone_even_with_username(self):
        professional = SimpleNamespace(
            telefono="+54 9 11 0000-1001",
            whatsapp_username="@NexoElectrico",
            whatsapp_contact_preference="PHONE",
        )

        result = resolver_identificador_contacto(professional)

        self.assertEqual(result["type"], IDENTIFIER_PHONE)

    def test_username_preference_without_username_uses_safe_phone_fallback(self):
        professional = SimpleNamespace(
            telefono="+54 9 11 0000-1001",
            whatsapp_username=None,
            whatsapp_contact_preference="USERNAME",
        )

        result = resolver_identificador_contacto(professional)

        self.assertEqual(result["type"], IDENTIFIER_PHONE)
        self.assertIn("fallback", result["fallback_reason"].lower())


if __name__ == "__main__":
    unittest.main()
