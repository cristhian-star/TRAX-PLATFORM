from math import asin, cos, radians, sin, sqrt


EARTH_RADIUS_KM = 6371.0088
MIN_LATITUDE = -90
MAX_LATITUDE = 90
MIN_LONGITUDE = -180
MAX_LONGITUDE = 180
MIN_COVERAGE_RADIUS_KM = 1
MAX_COVERAGE_RADIUS_KM = 200

COVERAGE_STATUS_WITHIN = "DENTRO_COBERTURA"
COVERAGE_STATUS_OUTSIDE = "FUERA_COBERTURA"
COVERAGE_STATUS_UNKNOWN = "NO_VERIFICABLE"


def _parse_float(value):
    if value is None or value == "":
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _validar_latitud(latitude):
    parsed = _parse_float(latitude)
    if parsed is None or not MIN_LATITUDE <= parsed <= MAX_LATITUDE:
        return None

    return parsed


def _validar_longitud(longitude):
    parsed = _parse_float(longitude)
    if parsed is None or not MIN_LONGITUDE <= parsed <= MAX_LONGITUDE:
        return None

    return parsed


def normalizar_coordenadas(latitude, longitude):
    parsed_latitude = _validar_latitud(latitude)
    parsed_longitude = _validar_longitud(longitude)

    if parsed_latitude is None or parsed_longitude is None:
        return None

    return parsed_latitude, parsed_longitude


def normalizar_radio_profesional(professional):
    if professional is None:
        return None

    try:
        radius = int(professional.coverage_radius_km)
    except (TypeError, ValueError):
        return None

    if not MIN_COVERAGE_RADIUS_KM <= radius <= MAX_COVERAGE_RADIUS_KM:
        return None

    return radius


def calcular_distancia_km(lat1, lng1, lat2, lng2):
    origin = normalizar_coordenadas(lat1, lng1)
    destination = normalizar_coordenadas(lat2, lng2)

    if origin is None or destination is None:
        raise ValueError("Coordenadas invalidas para calcular distancia")

    origin_lat, origin_lng = origin
    destination_lat, destination_lng = destination
    delta_lat = radians(destination_lat - origin_lat)
    delta_lng = radians(destination_lng - origin_lng)
    origin_lat_rad = radians(origin_lat)
    destination_lat_rad = radians(destination_lat)

    haversine = (
        sin(delta_lat / 2) ** 2
        + cos(origin_lat_rad) * cos(destination_lat_rad) * sin(delta_lng / 2) ** 2
    )
    distance = 2 * EARTH_RADIUS_KM * asin(sqrt(haversine))
    return max(distance, 0)


def formatear_distancia_publica(distance_km):
    if distance_km is None:
        return None

    if distance_km < 1:
        return "Aproximadamente a menos de 1 km"
    if distance_km < 10:
        return f"Aproximadamente a {round(distance_km, 1)} km"

    return f"Aproximadamente a {round(distance_km)} km"


def obtener_resultado_cobertura(professional, latitude, longitude):
    request_coordinates = normalizar_coordenadas(latitude, longitude)
    professional_coordinates = normalizar_coordenadas(
        getattr(professional, "latitude", None),
        getattr(professional, "longitude", None),
    )
    radius = normalizar_radio_profesional(professional)

    if request_coordinates is None or professional_coordinates is None or radius is None:
        return {
            "status": COVERAGE_STATUS_UNKNOWN,
            "status_label": "Cobertura no verificable",
            "within_coverage": None,
            "distance_km": None,
            "distance_label": None,
            "sort_rank": 2,
        }

    distance = calcular_distancia_km(
        professional_coordinates[0],
        professional_coordinates[1],
        request_coordinates[0],
        request_coordinates[1],
    )
    within_coverage = distance <= radius

    return {
        "status": COVERAGE_STATUS_WITHIN if within_coverage else COVERAGE_STATUS_OUTSIDE,
        "status_label": "Dentro de cobertura" if within_coverage else "Fuera de cobertura",
        "within_coverage": within_coverage,
        "distance_km": distance,
        "distance_label": formatear_distancia_publica(distance),
        "sort_rank": 0 if within_coverage else 1,
    }


def profesional_cubre_ubicacion(professional, latitude, longitude):
    return obtener_resultado_cobertura(professional, latitude, longitude)["within_coverage"] is True


def ordenar_profesionales_por_distancia(professionals, latitude, longitude):
    rows = [
        {
            "professional": professional,
            "coverage": obtener_resultado_cobertura(professional, latitude, longitude),
        }
        for professional in professionals
    ]

    return sorted(
        rows,
        key=lambda row: (
            row["coverage"]["sort_rank"],
            row["coverage"]["distance_km"]
            if row["coverage"]["distance_km"] is not None
            else float("inf"),
            (row["professional"].nombre or "").casefold(),
        ),
    )
