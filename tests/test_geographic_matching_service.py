import unittest
from types import SimpleNamespace

from app.services.geographic_matching_service import (
    COVERAGE_STATUS_UNKNOWN,
    calcular_distancia_km,
    obtener_resultado_cobertura,
    profesional_cubre_ubicacion,
)


class GeographicMatchingServiceTest(unittest.TestCase):
    def test_same_location_is_zero_km(self):
        distance = calcular_distancia_km(-34.603722, -58.381592, -34.603722, -58.381592)

        self.assertEqual(round(distance, 6), 0)

    def test_known_points_distance(self):
        distance = calcular_distancia_km(-34.603722, -58.381592, -34.92145, -57.95453)

        self.assertGreater(distance, 45)
        self.assertLess(distance, 60)

    def test_professional_inside_radius(self):
        professional = SimpleNamespace(
            latitude=-34.603722,
            longitude=-58.381592,
            coverage_radius_km=20,
        )

        self.assertTrue(profesional_cubre_ubicacion(professional, -34.694, -58.381592))

    def test_professional_outside_radius(self):
        professional = SimpleNamespace(
            latitude=-34.603722,
            longitude=-58.381592,
            coverage_radius_km=20,
        )

        self.assertFalse(profesional_cubre_ubicacion(professional, -34.873, -58.381592))

    def test_missing_coordinates_are_not_verifiable(self):
        professional = SimpleNamespace(
            latitude=None,
            longitude=None,
            coverage_radius_km=20,
        )

        result = obtener_resultado_cobertura(professional, -34.603722, -58.381592)

        self.assertEqual(result["status"], COVERAGE_STATUS_UNKNOWN)
        self.assertIsNone(result["within_coverage"])

    def test_invalid_coordinates_are_safe(self):
        professional = SimpleNamespace(
            latitude=-34.603722,
            longitude=-58.381592,
            coverage_radius_km=20,
        )

        result = obtener_resultado_cobertura(professional, -120, -58.381592)

        self.assertEqual(result["status"], COVERAGE_STATUS_UNKNOWN)
        self.assertIsNone(result["distance_km"])

    def test_distance_rejects_invalid_coordinates(self):
        with self.assertRaises(ValueError):
            calcular_distancia_km(-34.603722, -58.381592, -120, -58.381592)


if __name__ == "__main__":
    unittest.main()
