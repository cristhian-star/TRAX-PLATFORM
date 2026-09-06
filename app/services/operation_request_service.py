from datetime import datetime

from app.services.geographic_matching_service import normalizar_coordenadas


def empty_to_none(value):
    if value is None:
        return None

    value = value.strip()
    return value or None


def parse_datetime(value):
    value = empty_to_none(value)

    if value is None:
        return None

    return datetime.fromisoformat(value)


def parse_date(value):
    value = empty_to_none(value)

    if value is None:
        return None

    return datetime.strptime(value, "%Y-%m-%d").date()


def get_request_coordinates(source):
    latitude = source.get("latitude") or source.get("latitud") or source.get("lat")
    longitude = source.get("longitude") or source.get("longitud") or source.get("lng")
    return normalizar_coordenadas(latitude, longitude)


def get_query_prefill(source, *field_names):
    return {
        field_name: empty_to_none(source.get(field_name)) or ""
        for field_name in field_names
    }


def build_budget_form_data(form):
    return {
        "categoria": empty_to_none(form.get("categoria")) or "",
        "zona": empty_to_none(form.get("zona")) or "",
        "titulo": empty_to_none(form.get("titulo")) or "",
        "descripcion": empty_to_none(form.get("descripcion")) or "",
        "fecha_estimada": empty_to_none(form.get("fecha_estimada")) or "",
        "urgencia": empty_to_none(form.get("urgencia")) or "NORMAL",
    }


def validate_budget_form_data(form_data):
    if not all(
        form_data[field]
        for field in ("categoria", "zona", "titulo", "descripcion")
    ):
        return "Completa categoria, zona, titulo y descripcion."

    if form_data["urgencia"] not in ("BAJA", "NORMAL", "ALTA"):
        return "Selecciona una urgencia valida."

    return None


def build_proposal_form_data(form):
    required_fields = ("industria", "categoria", "rubro", "titulo", "descripcion", "ubicacion", "modalidad")
    form_data = {field: empty_to_none(form.get(field)) or "" for field in required_fields}
    form_data.update({
        "especialidad": empty_to_none(form.get("especialidad")) or "",
        "cantidad_profesionales": empty_to_none(form.get("cantidad_profesionales")) or "1",
        "presupuesto_estimado": empty_to_none(form.get("presupuesto_estimado")) or "",
        "fecha_inicio_estimada": empty_to_none(form.get("fecha_inicio_estimada")) or "",
        "fecha_limite_postulacion": empty_to_none(form.get("fecha_limite_postulacion")) or "",
    })
    return form_data


def validate_proposal_form_data(form_data):
    required_fields = ("industria", "categoria", "rubro", "titulo", "descripcion", "ubicacion", "modalidad")
    if any(not form_data[field] for field in required_fields):
        return "Completa industria, categoria, rubro, titulo, descripcion, ubicacion y modalidad."

    return None
