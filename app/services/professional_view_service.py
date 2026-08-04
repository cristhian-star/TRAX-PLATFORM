from app.services.geographic_matching_service import obtener_resultado_cobertura
from app.services.review_service import (
    get_professional_average_rating,
    get_professional_reviews,
)
from app.services.subscription_service import has_pro_access
from app.services.verification_service import has_approved_verification


def entity_value(entity, key, default=None):
    if isinstance(entity, dict):
        return entity.get(key, default)

    return getattr(entity, key, default)


def professional_user_id(professional):
    return entity_value(professional, "user_id")


def get_professional_badges(professional):
    user_id = professional_user_id(professional)

    if not user_id:
        return {
            "work": True,
            "pro": False,
            "verified": False,
        }

    return {
        "work": True,
        "pro": has_pro_access(user_id),
        "verified": has_approved_verification(user_id),
    }


def get_professional_rating(professional_id):
    reviews = get_professional_reviews(professional_id)

    return {
        "average": get_professional_average_rating(professional_id),
        "count": len(reviews),
    }


def get_professionals_ratings(professionals):
    return {
        entity_value(professional, "id", index): get_professional_rating(
            entity_value(professional, "id", index)
        )
        for index, professional in enumerate(professionals, start=1)
    }


def get_professionals_badges(professionals):
    return {
        entity_value(professional, "id", index): get_professional_badges(professional)
        for index, professional in enumerate(professionals, start=1)
    }


def calculate_private_profile_completion(professional, is_verified=False):
    if professional is None:
        return 0

    checks = (
        bool(professional.nombre),
        bool(professional.especialidad or professional.servicio),
        bool(professional.zona),
        bool(professional.descripcion),
        bool(professional.logo_url),
        bool(professional.cover_url),
        bool(professional.gallery_urls),
        bool(professional.portfolio_urls),
        bool(
            professional.google_drive_url
            or professional.website_url
            or professional.instagram_url
            or professional.tiktok_url
            or professional.youtube_url
            or professional.other_links
        ),
        bool(professional.certificaciones_text),
        bool(professional.anios_experiencia is not None),
        bool(is_verified),
    )

    return round((sum(checks) / len(checks)) * 100)


def build_matching_results(professionals, coordinates):
    latitude = coordinates[0] if coordinates is not None else None
    longitude = coordinates[1] if coordinates is not None else None

    return {
        entity_value(professional, "id", index): obtener_resultado_cobertura(
            professional,
            latitude,
            longitude,
        )
        for index, professional in enumerate(professionals, start=1)
    }


def sort_professionals_for_listing(professionals, badges, ratings, matching_results, coordinates):
    if coordinates is None:
        return professionals

    return sorted(
        professionals,
        key=lambda professional: (
            matching_results.get(professional.id, {}).get("sort_rank", 2),
            -int(bool(badges.get(professional.id, {}).get("pro"))),
            -int(bool(badges.get(professional.id, {}).get("verified"))),
            -(ratings.get(professional.id, {}).get("average") or 0),
            matching_results.get(professional.id, {}).get("distance_km")
            if matching_results.get(professional.id, {}).get("distance_km") is not None
            else float("inf"),
            (professional.nombre or "").casefold(),
        ),
    )
