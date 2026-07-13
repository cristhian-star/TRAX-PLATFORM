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

    if radius < 0:
        raise ValueError("El radio de cobertura no puede ser negativo")
    if radius > MAX_COVERAGE_RADIUS_KM:
        raise ValueError(f"El radio de cobertura no puede superar {MAX_COVERAGE_RADIUS_KM} km")

    return radius


def normalizar_cobertura(form):
    mode = _clean_text(form.get("coverage_mode"), 50, "Modalidad de cobertura") or COVERAGE_MODE_RADIO
    if mode not in COVERAGE_MODES:
        raise ValueError("Modalidad de cobertura invalida")

    return {
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
    }


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
        )
    )


def obtener_cobertura_profesional(professional):
    if not professional:
        return {
            "configured": False,
            "radius_scale": 0.2,
            "description": "Zona de cobertura no informada.",
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
