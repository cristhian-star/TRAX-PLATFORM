# BACKLOG TRAX

## Alta prioridad

- Sustituir almacenamiento en memoria de Flask-Limiter por Redis u otro backend compartido.
- Definir WSGI productivo para despliegues fuera del servidor Flask de desarrollo.
- Revisar politicas legales con profesional: terminos, privacidad, cookies y consentimientos.
- Configurar Cloudflare/WAF o equivalente antes de exposicion publica.
- Implementar checklist productivo en staging con secretos reales, HTTPS, backups, monitoreo y prueba de restauracion.

## Media prioridad

- Revisar uso del servidor Flask de desarrollo dentro de Docker y separar perfil local de perfil productivo.
- Reemplazar usos legacy de `Query.get()` por `db.session.get()`.
- Reemplazar `datetime.utcnow()` deprecated por timestamps timezone-aware.
- Agregar `source` explicito al modelo de consentimientos si producto requiere trazabilidad separada del contexto tecnico.
- Incorporar escaneo automatizado de dependencias y secretos en CI.
- Evaluar Redis futuro para rate limiting, cache o colas cuando el volumen lo justifique.
- Restringir la clave de Google Maps por origen autorizado, API permitida y cuotas.
- Validar Google Maps con una API key real en entorno controlado.
- Implementar geocoding de ubicaciones base.
- Evolucionar matching geografico hacia PostGIS o indices espaciales cuando escale el volumen.
- Implementar rutas, tiempos de viaje o distancia real por calle solo si producto lo requiere.
- Incorporar poligonos avanzados y zonas personalizadas multiples.
- Evaluar estilos avanzados de Google Maps si TRAX define un mapa de marca propio.
- Crear listado dedicado de emergencias del cliente para reemplazar enlaces operativos provisorios.
- Crear vista consolidada de solicitudes del cliente que incluya presupuestos, emergencias y propuestas.
- Realizar auditoria visual completa de pantallas secundarias para Design System v2 Fase 2.
- Implementar Agenda.
- Implementar canal Email para notificaciones transaccionales.
- Integrar WhatsApp Business API cuando exista definicion de producto y proveedor.
- Validar apertura directa por username si WhatsApp publica una URL estable para esa capacidad.
- Evaluar grupos automaticos de WhatsApp solo con una API oficial y consentimiento explicito.
- Implementar webhooks de WhatsApp solo si se aprueba lectura de eventos externos.
- Evaluar Push notifications cuando exista estrategia mobile/browser.
- Evaluar polling moderado o WebSockets solo cuando el producto requiera tiempo real.

## Baja prioridad

- Incorporar Mercados.
- Incorporar funcionalidades de IA.
