# CHANGELOG TRAX

## 2026-07-14 - WhatsApp Integration Foundation v1

### Agregado

- Se creo el modelo `WhatsAppContactSession` para registrar aperturas de WhatsApp iniciadas desde TRAX.
- Se agrego la migracion Alembic `20260714_01_whatsapp_contact_sessions`.
- Se creo `app/services/whatsapp_contact_service.py` como servicio unico para validar operaciones, crear sesiones, generar URLs y actualizar estados.
- Se agrego la ruta central `POST /whatsapp/iniciar` con CSRF, consentimiento obligatorio y redireccion controlada.
- Se agrego modal de consentimiento previo a abrir WhatsApp.
- Se agregaron resumenes de contactos iniciados en Dashboard Cliente y oportunidades de contacto en Dashboard Profesional.

### Mejorado

- Se reemplazaron enlaces directos de WhatsApp en perfiles, tarjetas profesionales, emergencias, presupuestos adjudicados y propuestas aceptadas.
- Las aperturas de WhatsApp ahora generan notificaciones internas para cliente y profesional.
- El flujo queda preparado para futuras integraciones sin almacenar mensajes, archivos ni conversaciones.

### Corregido

- Se elimino la generacion dispersa de enlaces `wa.me` desde templates.

## 2026-07-13 - Cobertura Inteligente v2 Google Maps

### Agregado

- Se agrego soporte frontend para Google Maps JavaScript API en cobertura profesional.
- Se creo `app/static/js/professional-coverage-map.js` como modulo aislado del proveedor visual.
- Se agrego consentimiento explicito para uso de ubicacion de cobertura.
- Se agrego `coverage_location_consent_at` al modelo `Professional`.
- Se agrego la migracion Alembic `20260713_01_google_maps_coverage_v2`.
- Se documento `GOOGLE_MAPS_API_KEY` en `.env.example`.

### Mejorado

- El perfil privado puede persistir latitud, longitud y radio cuando existe consentimiento.
- El perfil publico usa centro aproximado para no exponer el punto exacto del profesional.
- Sin API key, la pantalla mantiene fallback visual y edicion textual.
- Se ajusto CSP para permitir la carga acotada de Google Maps JavaScript API.

### Corregido

- Se evita guardar coordenadas nuevas cuando el profesional no presta consentimiento.

## 2026-07-12 - Cobertura Inteligente v1

### Agregado

- Se agregaron campos de cobertura al modelo `Professional`.
- Se creo la migracion Alembic `20260712_02_smart_coverage_v1`.
- Se creo `app/services/coverage_service.py` para normalizar radios y describir cobertura profesional.
- Se agrego la seccion editable "Zona de cobertura" al perfil privado profesional.
- Se agrego visualizacion publica de cobertura con mapa placeholder y anillo representativo.
- Se agrego resumen operativo de cobertura al Dashboard Profesional.

### Mejorado

- El perfil publico informa zona principal, localidad/provincia, modalidad, radio y notas cuando existen.
- La cobertura queda preparada para futura integracion con mapas, geocoding y matching por distancia.

### Corregido

- Se reemplazo el placeholder estatico de cobertura por datos persistentes y validados.

## 2026-07-12 - Centro de Actividad + Notificaciones v1

### Agregado

- Se creo el modelo `ActivityNotification` para registrar actividad historica y notificaciones internas.
- Se agrego el servicio central `notification_service.py` con constantes, consultas y marcado de lectura.
- Se agregaron rutas `/notificaciones`, `/notificaciones/<id>/leer` y `/notificaciones/marcar-todas-leidas`.
- Se agrego campana de notificaciones en el navbar para usuarios autenticados.
- Se integraron eventos reales de presupuestos, propuestas y emergencias.

### Mejorado

- Dashboard Cliente y Dashboard Profesional muestran actividad reciente basada en notificaciones reales.
- El sistema queda preparado para canales futuros como Email, WhatsApp y Push sin implementarlos todavia.

### Corregido

- Sin correcciones registradas.

## 2026-07-12

### Agregado

- Se implemento el Dashboard Cliente v1 como centro de operaciones para solicitudes y contrataciones.
- Se agrego una hoja de estilos dedicada para el dashboard cliente basada en Design System v2.
- Se agregaron resumen, centro de actividad, accesos rapidos, mis solicitudes, recomendaciones y estado operativo del cliente.

### Mejorado

- Se reutilizaron datos reales de presupuestos, emergencias, propuestas y contrataciones existentes.
- Se incorporaron placeholders elegantes cuando todavia no hay actividad suficiente.

### Corregido

- Sin correcciones registradas.

## 2026-07-10

### Agregado

- Se creo `app/static/css/design-system-v2.css` como capa central de variables semanticas para temas Light y Dark.
- Se agregaron variables para fondos, superficies, cards, bordes, texto, marca, estados, sombras, radios, espaciados y transiciones.

### Mejorado

- Se conectaron tokens legacy globales con el Design System v2.
- Se adapto el comportamiento visual de Home publico, Home logueado, Perfil profesional, Perfil privado, Dashboard profesional, Presupuestos, Emergencias, Propuestas, Explorar rubros, Planes y formularios principales.
- Se mejoro la respuesta de cards, botones, inputs, selects, textareas, badges, alertas, links, focus y hover al cambio de tema.

### Corregido

- Se redujeron superficies e inputs hardcodeados que no respondian correctamente al modo oscuro.

## 2026-07-09

### Agregado

- Se incorporo la estructura permanente de documentacion del proyecto en `docs/`.
- Se agrego el registro de sprints en `docs/SPRINTS/`.
- Se agrego `docs/BACKLOG.md` para registrar funcionalidades pendientes, mejoras y deuda tecnica.
- Se agrego `docs/ESTANDARES_DESARROLLO.md` como manual permanente de desarrollo del proyecto.
- Se creo la politica de documentacion viva para cambios implementados, probados, documentados, versionados y mergeados.

### Mejorado

- Se formalizo el seguimiento de cambios, roadmap y decisiones importantes del proyecto.
- Se definio la convencion de nombres de sprint por fecha y nombre descriptivo, sin numeracion.
- Se incorporo el checklist obligatorio para cierre oficial de cada sprint.
- Se documentaron reglas permanentes de ramas, commits, flujo Git, estructura, UX/UI, seguridad, Docker, Alembic y Pull Requests.

### Corregido

- Sin correcciones registradas.
