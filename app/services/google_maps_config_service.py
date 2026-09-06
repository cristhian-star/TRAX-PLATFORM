import os


GOOGLE_MAPS_API_KEY_ENV = "GOOGLE_MAPS_API_KEY"
_PLACEHOLDER_VALUES = {
    "",
    "tu_clave_real",
    "your_google_maps_api_key",
    "your_google_maps_api_key_here",
    "changeme",
    "change-me",
    "placeholder",
}


def normalizar_google_maps_api_key(value):
    if value is None:
        return None

    key = value.strip()
    if key.lower() in _PLACEHOLDER_VALUES:
        return None

    return key


def obtener_google_maps_api_key():
    return normalizar_google_maps_api_key(os.environ.get(GOOGLE_MAPS_API_KEY_ENV))


def google_maps_disponible():
    return obtener_google_maps_api_key() is not None
