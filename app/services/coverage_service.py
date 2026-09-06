from datetime import datetime


COVERAGE_MODE_RADIO = "RADIO"
COVERAGE_MODE_LOCALIDAD = "LOCALIDAD"
COVERAGE_MODE_PROVINCIA = "PROVINCIA"
COVERAGE_MODE_PERSONALIZADA = "PERSONALIZADA"

COVERAGE_MODES = (
    COVERAGE_MODE_RADIO,
    COVERAGE_MODE_LOCALIDAD,
    COVERAGE_MODE_PROVINCIA,
    COVERAGE_MODE_PERSONALIZADA,
)

DEFAULT_RADIUS_OPTIONS = (5, 10, 20, 30, 50)
MAX_COVERAGE_RADIUS_KM = 200
DEFAULT_COVERAGE_CENTER = {
    "lat": -34.603722,
    "lng": -58.381592,
}


def _clean_text(value, max_length, field_label):
    if value is None:
        return None

    cleaned = value.strip()
    if not cleaned:
        return None

    if len(cleaned) > max_length:
        raise ValueError(f"{field_label} admite hasta {max_length} caracteres")

    return cleaned


def normalizar_radio(value, custom_value=None):
    raw_value = custom_value if value == "PERSONALIZADO" else value
    if raw_value is None or str(raw_value).strip() == "":
        return None

    try:
        radius = int(raw_value)
    except (TypeError, ValueError):
        raise ValueError("El radio de cobertura debe ser un numero entero") from None

    if radius < 1:
        raise ValueError("El radio de cobertura debe ser de al menos 1 km")
    if radius > MAX_COVERAGE_RADIUS_KM:
        raise ValueError(f"El radio de cobertura no puede superar {MAX_COVERAGE_RADIUS_KM} km")

    return radius


def validar_coordenadas(latitude, longitude):
    if latitude is None or longitude is None:
        return None, None

    try:
        parsed_latitude = float(latitude)
        parsed_longitude = float(longitude)
    except (TypeError, ValueError):
        raise ValueError("Las coordenadas de cobertura son invalidas") from None

    if not -90 <= parsed_latitude <= 90:
        raise ValueError("La latitud debe estar entre -90 y 90")
    if not -180 <= parsed_longitude <= 180:
        raise ValueError("La longitud debe estar entre -180 y 180")

    return parsed_latitude, parsed_longitude


def _coverage_has_text_data(coverage_data):
    return bool(
        coverage_data["coverage_location"]
        or coverage_data["coverage_city"]
        or coverage_data["coverage_province"]
        or coverage_data["coverage_radius_km"] is not None
        or coverage_data["coverage_notes"]
    )


def normalizar_cobertura(form):
    mode = _clean_text(form.get("coverage_mode"), 50, "Modalidad de cobertura") or COVERAGE_MODE_RADIO
    if mode not in COVERAGE_MODES:
        raise ValueError("Modalidad de cobertura invalida")

    coverage_data = {
        "coverage_location": _clean_text(form.get("coverage_location"), 160, "Ubicacion base"),
        "coverage_city": _clean_text(form.get("coverage_city"), 120, "Localidad"),
        "coverage_province": _clean_text(form.get("coverage_province"), 120, "Provincia"),
        "coverage_mode": mode,
        "coverage_radius_km": normalizar_radio(
            form.get("coverage_radius_km"),
            form.get("coverage_radius_custom"),
        ),
        "coverage_notes": _clean_text(form.get("coverage_notes"), 600, "Notas de cobertura"),
        "latitude": None,
        "longitude": None,
        "coverage_location_consent_at": None,
    }

    has_consent = form.get("coverage_location_consent") == "on"
    latitude = form.get("latitude")
    longitude = form.get("longitude")

    if has_consent and latitude and longitude:
        coverage_data["latitude"], coverage_data["longitude"] = validar_coordenadas(latitude, longitude)
        coverage_data["coverage_location_consent_at"] = datetime.utcnow()
    elif has_consent and _coverage_has_text_data(coverage_data):
        coverage_data["coverage_location_consent_at"] = datetime.utcnow()

    return coverage_data


def profesional_tiene_cobertura(professional):
    return bool(
        professional
        and (
            professional.coverage_location
            or professional.coverage_city
            or professional.coverage_province
            or professional.coverage_radius_km is not None
            or professional.coverage_mode
            or professional.coverage_notes
            or professional.latitude is not None
            or professional.longitude is not None
        )
    )


def obtener_cobertura_profesional(professional):
    if not professional:
        return {
            "configured": False,
            "radius_scale": 0.2,
            "description": "Zona de cobertura no informada.",
            "has_coordinates": False,
            "latitude": None,
            "longitude": None,
            "public_latitude": None,
            "public_longitude": None,
            "default_center": DEFAULT_COVERAGE_CENTER,
        }

    radius = professional.coverage_radius_km
    radius_scale = min(max((radius or 10) / MAX_COVERAGE_RADIUS_KM, 0.08), 1)
    return {
        "configured": profesional_tiene_cobertura(professional),
        "location": professional.coverage_location,
        "city": professional.coverage_city,
        "province": professional.coverage_province,
        "radius_km": radius,
        "mode": professional.coverage_mode,
        "notes": professional.coverage_notes,
        "latitude": professional.latitude,
        "longitude": professional.longitude,
        "has_coordinates": professional.latitude is not None and professional.longitude is not None,
        "public_latitude": obtener_centro_publico_aproximado(professional)[0],
        "public_longitude": obtener_centro_publico_aproximado(professional)[1],
        "default_center": DEFAULT_COVERAGE_CENTER,
        "has_location_consent": bool(professional.coverage_location_consent_at),
        "radius_scale": radius_scale,
        "description": descripcion_cobertura(professional),
    }


def descripcion_cobertura(professional):
    if not profesional_tiene_cobertura(professional):
        return "Zona de cobertura no informada."

    parts = []
    if professional.coverage_location:
        parts.append(professional.coverage_location)
    if professional.coverage_city:
        parts.append(professional.coverage_city)
    if professional.coverage_province:
        parts.append(professional.coverage_province)

    location = ", ".join(parts) if parts else professional.zona
    mode = (professional.coverage_mode or COVERAGE_MODE_RADIO).replace("_", " ").title()
    radius = (
        f"Radio de {professional.coverage_radius_km} km"
        if professional.coverage_radius_km is not None
        else "Radio a coordinar"
    )
    return f"{location} - {mode} - {radius}"


def obtener_opciones_radio():
    return DEFAULT_RADIUS_OPTIONS


def obtener_centro_publico_aproximado(professional):
    if not professional or professional.latitude is None or professional.longitude is None:
        return None, None

    return round(professional.latitude + 0.004, 2), round(professional.longitude - 0.004, 2)
