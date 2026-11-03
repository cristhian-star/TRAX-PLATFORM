"""Prepared billing destinations; intentionally no financial queries or commands."""


def prepared_page(section):
    pages = {
        "factura": {
            "title": "Crear una factura",
            "description": "Estamos preparando la emisión de facturas con ARCA y la identidad de tu negocio.",
            "detail": "Cuando esté disponible, podrás revisar un borrador antes de emitir. Por ahora no necesitás cargar datos fiscales.",
        },
        "cobro": {
            "title": "Cobrar un servicio",
            "description": "Estamos preparando los cobros mediante un enlace de Mercado Pago.",
            "detail": "Podrás compartir el enlace o un QR que abra ese mismo pago. Esta opción todavía no genera órdenes ni recibe dinero.",
        },
        "configuracion": {
            "title": "Marca y cuentas",
            "description": "Tu marca comercial y la cuenta para recibir tus cobros tendrán su propio espacio.",
            "detail": "La configuración estará disponible próximamente. No necesitás cargar un logo ni conectar una cuenta todavía.",
        },
    }
    return pages[section].copy()
