"""Public error presentation, independent of session/database availability."""
from flask import g, render_template


ERROR_PAGES = {
    403: ("No tenés acceso a esta sección",
          "Tu cuenta no tiene permisos para realizar esta acción."),
    404: ("No encontramos esta página",
          "Es posible que el enlace haya cambiado o que la dirección no sea correcta."),
    500: ("Algo no salió como esperábamos",
          "Tuvimos un inconveniente y no pudimos completar la solicitud."),
    503: ("Estamos haciendo algunos ajustes",
          "El servicio no está disponible temporalmente. Probá nuevamente dentro de unos minutos."),
}


def render_error_page(code, *, preview=False):
    previous = getattr(g, "rendering_error_page", False)
    g.rendering_error_page = True
    try:
        title, message = ERROR_PAGES[code]
        return render_template("errors/base_error.html", code=code,
                               title=title, message=message, preview=preview)
    finally:
        g.rendering_error_page = previous
