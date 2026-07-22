import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace

from app.services.client_dashboard_service import (
    build_client_activity_rows,
    count_unique_awarded_professionals,
)
from app.services.professional_view_service import (
    calculate_private_profile_completion,
    get_professional_badges,
    sort_professionals_for_listing,
)


class ProfessionalViewServiceTest(unittest.TestCase):
    def test_profile_completion_returns_zero_without_profile(self):
        self.assertEqual(calculate_private_profile_completion(None), 0)

    def test_profile_completion_counts_existing_public_profile_data(self):
        professional = SimpleNamespace(
            nombre="Nexo Electrico",
            especialidad="Electricista",
            servicio="Electricidad",
            zona="CABA",
            descripcion="Servicios electricos",
            logo_url="https://example.com/logo.png",
            cover_url=None,
            gallery_urls=None,
            portfolio_urls="https://example.com",
            google_drive_url=None,
            website_url="https://example.com",
            instagram_url=None,
            tiktok_url=None,
            youtube_url=None,
            other_links=None,
            certificaciones_text="Matricula",
            anios_experiencia=8,
        )

        self.assertEqual(calculate_private_profile_completion(professional, is_verified=True), 83)

    def test_badges_default_to_work_for_orphan_public_profile(self):
        professional = SimpleNamespace(user_id=None)

        self.assertEqual(
            get_professional_badges(professional),
            {
                "work": True,
                "pro": False,
                "verified": False,
                "reputation_score": 0,
            },
        )

    def test_professional_listing_sort_prioritizes_coverage_then_plan_and_rating(self):
        inside = SimpleNamespace(id=1, nombre="Bravo")
        pro_outside = SimpleNamespace(id=2, nombre="Alfa")
        unknown = SimpleNamespace(id=3, nombre="Delta")
        professionals = [unknown, pro_outside, inside]

        sorted_professionals = sort_professionals_for_listing(
            professionals,
            badges={
                1: {"pro": False, "verified": False},
                2: {"pro": True, "verified": True},
                3: {"pro": False, "verified": False},
            },
            ratings={
                1: {"average": 3},
                2: {"average": 5},
                3: {"average": 4},
            },
            matching_results={
                1: {"sort_rank": 0, "distance_km": 8},
                2: {"sort_rank": 1, "distance_km": 2},
                3: {"sort_rank": 2, "distance_km": None},
            },
            coordinates=(-34.6, -58.4),
        )

        self.assertEqual([professional.id for professional in sorted_professionals], [1, 2, 3])


class ClientDashboardServiceTest(unittest.TestCase):
    def test_client_activity_rows_are_sorted_and_limited(self):
        now = datetime(2026, 7, 21, 12, 0, 0)
        budget_request = SimpleNamespace(
            id=10,
            titulo="Tablero electrico",
            estado="COTIZANDO",
            fecha_creacion=now - timedelta(days=2),
            offers=[],
        )
        proposal = SimpleNamespace(
            id=20,
            titulo="Mantenimiento",
            categoria="Electricidad",
            estado="PUBLICADA",
            created_at=now,
            applications=[],
        )

        rows = build_client_activity_rows(
            budget_rows=[(budget_request, 2)],
            emergency_requests=[],
            proposal_requests=[proposal],
            contracts=[],
        )

        self.assertEqual(rows[0]["kind"], "Propuesta")
        self.assertEqual(rows[1]["kind"], "Presupuesto")

    def test_unique_awarded_professionals_deduplicates_by_source(self):
        professional = SimpleNamespace(nombre="Nexo")
        awarded_offer = SimpleNamespace(
            estado="ADJUDICADO",
            professional_user_id=7,
            professional=professional,
        )
        budget_request = SimpleNamespace(offers=[awarded_offer])
        accepted_application = SimpleNamespace(
            estado="ACEPTADA",
            professional_user_id=7,
        )
        proposal = SimpleNamespace(applications=[accepted_application])
        contract = SimpleNamespace(professional_user_id=7, professional_id=None)

        self.assertEqual(
            count_unique_awarded_professionals(
                budget_rows=[(budget_request, 1)],
                proposal_requests=[proposal],
                contracts=[contract],
            ),
            3,
        )


if __name__ == "__main__":
    unittest.main()
