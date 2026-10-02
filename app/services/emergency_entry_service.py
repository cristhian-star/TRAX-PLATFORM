"""Presentation/validation for the existing manual search, not a matcher."""

from app.services.taxonomy_service import obtener_categorias


MAX_DESCRIPTION_LENGTH = 600  # Existing textarea contract, now also server-side.
MAX_ZONE_LENGTH = 120  # Existing EmergencyRequest.zona column.


def emergency_entry_categories():
    categories = {item["slug"]: item for item in obtener_categorias()}
    # Reuse canonical IDs where available. The other values remain literal legacy
    # search terms, not new taxonomy IDs or emergency specialties.
    return (
        (categories["electricidad"]["slug"], "Electricidad"),
        (categories["plomeria"]["slug"], "Plomería"),
        ("Cerrajería", "Cerrajería"),
        ("Auxilio vehicular", "Auxilio vehicular"),
    )


def entry_context(values):
    data = {key: (values.get(key) or "").strip()
            for key in ("categoria", "zona", "descripcion")}
    categories = emergency_entry_categories()
    selected = next((value for value, label in categories
                     if data["categoria"].casefold() in (value.casefold(), label.casefold())), "")
    return dict(form_data=data, categories=categories, selected_category=selected,
                max_description_length=MAX_DESCRIPTION_LENGTH,
                max_zone_length=MAX_ZONE_LENGTH, errors={})


def entry_errors(context, mode="manual"):
    data = context["form_data"]
    errors = {}
    if mode != "manual":
        errors["modalidad"] = "La difusión todavía no está disponible. Elegí la búsqueda manual."
    if not context["selected_category"]:
        errors["categoria"] = "Seleccioná uno de los cuatro rubros disponibles."
    if not data["zona"] or len(data["zona"]) > MAX_ZONE_LENGTH:
        errors["zona"] = "Indicá una localidad de hasta 120 caracteres."
    if not data["descripcion"] or len(data["descripcion"]) > MAX_DESCRIPTION_LENGTH:
        errors["descripcion"] = "Describí la urgencia en hasta 600 caracteres."
    return errors
