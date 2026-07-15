# DECISIONES DE ARQUITECTURA TRAX

## 2026-07-14

Se decidio centralizar toda apertura de WhatsApp en un unico flujo interno de TRAX.

Motivo:

Los enlaces directos `wa.me` dispersos impiden auditar contactos, aplicar consentimiento, validar propiedad de operaciones y preparar futuras integraciones de forma segura.

Alcance:

- Crear `WhatsAppContactSession` como registro auditable de cada apertura.
- Generar URLs de WhatsApp solo desde `whatsapp_contact_service.py`.
- Usar `POST /whatsapp/iniciar` como unica entrada del flujo.
- Exigir consentimiento explicito antes de redireccionar fuera de TRAX.
- Registrar actividad interna sin enviar mensajes automaticos.
- No almacenar conversaciones, mensajes, archivos ni datos sensibles.
- Mantener fuera de esta fase WhatsApp Business API, webhooks, IA y lectura de conversaciones.

Criterio:

Las futuras capacidades de WhatsApp deberan extender este servicio y esta tabla, sin volver a generar enlaces directos desde templates ni exponer telefonos por APIs.

## 2026-07-13

Se decidio usar Google Maps Platform como proveedor inicial para el mapa interactivo de cobertura profesional.

Motivo:

La cobertura necesita un mapa real con marcador movible y circulo de radio, pero la logica de negocio debe permanecer independiente del proveedor visual.

Alcance:

- Usar Maps JavaScript API solo en perfil privado y perfil publico profesional.
- Encapsular la implementacion frontend en `professional-coverage-map.js`.
- Mantener `coverage_service.py` sin dependencias de Google.
- Guardar coordenadas solo con consentimiento explicito.
- Mostrar al publico un centro aproximado, sin exponer domicilio exacto ni coordenadas persistidas.
- Mantener fallback visual cuando no exista `GOOGLE_MAPS_API_KEY`.

Criterio:

Las futuras integraciones de geocoding, Places, rutas, matching por distancia o proveedores alternativos deberan agregarse sin distribuir logica de mapas en templates ni servicios de dominio.

## 2026-07-12

Se decidio modelar la cobertura profesional como datos persistentes del perfil `Professional`, sin integrar todavia APIs externas de mapas.

Motivo:

La cobertura es parte estructural de la oferta profesional y debe estar disponible para perfil privado, perfil publico, dashboard y futuro matching.

Alcance:

- Guardar ubicacion base, localidad, provincia, modalidad, radio, notas y coordenadas nullable.
- Centralizar normalizacion y descripcion en `coverage_service.py`.
- Mantener un mapa placeholder visual sin Google Maps, geocoding ni calculo real de distancia.
- Preparar `latitude` y `longitude` como campos nullable para una fase posterior.

Criterio:

Las futuras integraciones de mapas y matching deberan apoyarse en el servicio de cobertura, evitando logica geografica dispersa en rutas o templates.

## 2026-07-12

Se decidio crear un modelo central `ActivityNotification` para unificar actividad historica y notificaciones internas.

Motivo:

El mismo evento operativo debe poder alimentar dashboards, centro de notificaciones y canales futuros sin duplicar logica por pantalla.

Alcance:

- Registrar actividad y notificacion interna en una unica tabla.
- Usar strings controlados y constantes centralizadas en lugar de enums rigidos.
- Integrar solo eventos reales existentes de presupuestos, propuestas y emergencias.
- Mantener los canales Email, WhatsApp, Push y tiempo real fuera de esta version.
- Proteger lectura y modificacion por propietario de la notificacion.

Criterio:

Los nuevos eventos operativos deberan registrarse mediante el servicio central de notificaciones y no directamente desde templates o consultas ad hoc.

## 2026-07-12

Se decidio implementar el Dashboard Cliente como centro de operaciones y no como perfil personal.

Motivo:

El cliente necesita responder rapidamente que esta pasando con sus solicitudes, respuestas recibidas, emergencias, propuestas y contrataciones.

Alcance:

- Mostrar actividad operativa y resumen de estado.
- Reutilizar datos reales ya disponibles en presupuestos, emergencias, propuestas y contrataciones.
- Mantener fuera del dashboard la edicion de datos personales y la configuracion de perfil.
- Consumir Design System v2 para sostener consistencia Light/Dark con el Dashboard Profesional.

Criterio:

Las futuras mejoras del dashboard deberan priorizar seguimiento operativo, estado de solicitudes y acciones rapidas.

## 2026-07-09

Se decidio incorporar una documentacion permanente y viva dentro del repositorio como parte obligatoria del proceso oficial de desarrollo.

Motivo:

El proyecto TRAX necesita conservar el contexto tecnico, funcional y de UX sin depender de la memoria del equipo ni del historial de Git.

Alcance:

- Registrar cambios implementados y aceptados en `docs/CHANGELOG.md`.
- Mantener el estado general del producto en `docs/ROADMAP.md`.
- Documentar decisiones relevantes en `docs/DECISIONES_ARQUITECTURA.md`.
- Mantener pendientes, mejoras y deuda tecnica en `docs/BACKLOG.md`.
- Mantener las reglas permanentes de desarrollo en `docs/ESTANDARES_DESARROLLO.md`.
- Crear un documento independiente por sprint en `docs/SPRINTS/` con nombre `AAAA-MM-DD_Nombre_del_Sprint.md`.

Criterio:

Solo se documentaran funcionalidades implementadas, probadas y validadas. No se registraran experimentos descartados, codigo temporal ni ideas sin validar.

Condicion de cierre:

Un sprint solo se considerara cerrado cuando este implementado, probado, documentado, versionado y mergeado en `develop`.

## 2026-07-09

Se decidio crear `docs/ESTANDARES_DESARROLLO.md` como manual permanente de desarrollo de TRAX.

Motivo:

El crecimiento del proyecto requiere reglas explicitas y estables para ramas, commits, flujo Git, estructura, UX/UI, seguridad, Docker, Alembic y aceptacion de Pull Requests.

Criterio:

El documento se actualizara solo ante cambios de reglas permanentes del proyecto, no para registrar tareas diarias ni implementaciones puntuales.

## 2026-07-10

Se decidio consolidar el sistema visual de TRAX en una capa semantica de variables CSS v2.

Motivo:

El cambio de tema Light/Dark debe depender de variables globales y no de duplicacion de estilos por pantalla.

Alcance:

- Crear `app/static/css/design-system-v2.css`.
- Mantener compatibilidad con tokens existentes del Design System v1.
- Adaptar pantallas y componentes existentes sin redisenar la arquitectura visual.
- No modificar navbar, rutas, modelos, migraciones, Docker ni logica de negocio.

Criterio:

Las nuevas pantallas deberan consumir variables semanticas del Design System v2 para heredar automaticamente Light/Dark.
