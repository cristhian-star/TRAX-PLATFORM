# DECISIONES DE ARQUITECTURA TRAX

## 2026-07-26

Se decidio refactorizar `ContractRequest` como nucleo canonico de contratacion en lugar de crear un segundo modelo de contrato.

Motivo:

Presupuestos y Propuestas tienen origenes diferentes, pero ambos deben producir una contratacion comun para ejecucion, conformidad, reputacion y futuras integraciones de facturacion o pagos.

Alcance:

- `BudgetOffer` adjudicada crea un `ContractRequest` en estado `CREADA`.
- `ProposalApplication` aceptada crea un `ContractRequest` en estado `CREADA`.
- La creacion derivada es idempotente por `budget_offer_id` o `proposal_application_id`.
- En reintentos no se duplican `ContractEvent`, `AuditLog` ni `ActivityNotification`.
- `source_id` debe coincidir con la entidad origen concreta: `budget_offer_id` para Presupuestos y `proposal_application_id` para Propuestas.
- Propuestas adopta `hiring_mode = SINGLE` por defecto hasta definir reglas de contratacion multiple.
- `ContractEvent` conserva historial de dominio.
- `AuditLog` conserva trazabilidad administrativa y de seguridad.
- Las contrataciones directas existentes quedan como `source_type = DIRECT`.

Criterio:

Presupuestos y Propuestas seguiran siendo dominios separados. Ningun modulo externo, WhatsApp, MCP, IA, pagos o facturacion debe controlar directamente la logica de contratacion.

## 2026-07-24

Se decidio cargar `design-system-v2.css` de forma explicita desde `base.html`, despues de `design-tokens.css` y antes de `styles.css`.

Motivo:

El Design System v2 es la capa canonica actual y debe tener una jerarquia visible, testeable y sin dependencia de `@import` dentro de CSS legacy.

Alcance:

- `design-tokens.css` permanece como compatibilidad v1.
- `design-system-v2.css` define tokens `--trax-ds-*` y componentes `.trax-*`.
- `styles.css` queda como capa legacy posterior.
- Los CSS por modulo solo deben resolver composicion especifica.

Criterio:

Las futuras migraciones deben consumir primero componentes `.trax-*` y reducir duplicacion legacy por superficie, sin eliminar CSS historico de forma masiva.

## 2026-07-24

Se decidio rediseñar login y registro manteniendo las URLs actuales y adoptando un flujo de cuenta basica primero.

Motivo:

TRAX necesita reducir friccion inicial sin pedir datos profesionales avanzados antes de tiempo. El profesional puede completar rubro, cobertura, verificacion y portfolio despues de crear la cuenta.

Alcance:

- Mantener `POST /login`, `POST /register` y `POST /logout`.
- Centralizar validacion de autenticacion en `auth_service.py`.
- Registrar `TermsAcceptance` en la misma transaccion de creacion de usuario.
- Iniciar sesion inmediatamente despues del registro.
- Redirigir clientes a `next` seguro o inicio.
- Redirigir profesionales a `/profesional/perfil/completar`.
- No crear `Professional` automaticamente en el alta inicial.
- Rechazar usuarios suspendidos o inactivos antes de crear sesion.
- Usar mensaje neutral ante email duplicado para reducir enumeracion.
- No simular recuperacion de contraseña ni login social sin backend real.

Criterio:

Las futuras mejoras de auth deberan sumar recuperacion de contraseña, verificacion de email o login social como capacidades reales de backend, no como enlaces o botones ficticios.

## 2026-07-23

Se decidio modelar la identidad visual y portfolio profesional con una tabla separada `ProfessionalMedia`, manteniendo los campos legacy de `Professional` solo como fallback de compatibilidad.

Motivo:

Avatar, portada y galeria requieren metadatos, orden, estados de moderacion, auditoria, storage externo y borrado logico. Guardar nuevas URLs directamente en `Professional` no escala para portfolio ni moderacion.

Alcance:

- Usar `ProfessionalMedia` para avatar, portada y galeria.
- Procesar imagenes en backend para validar formato real, MIME, tamano, dimensiones y eliminar EXIF/GPS.
- Guardar archivos en storage local para desarrollo/testing y preparar Cloudinary por variables de entorno.
- No almacenar binarios ni base64 en PostgreSQL.
- Usar estados de moderacion antes de exponer imagenes publicamente.
- Mantener campos legacy como fallback hasta una migracion funcional posterior.
- No crear `PortfolioItem`, videos ni moderacion automatica en esta fase.

Criterio:

Las futuras mejoras del portfolio deberan extender el servicio de media o crear un modelo de trabajos solo si el producto necesita agrupar varias imagenes, descripciones avanzadas y orden editorial.

## 2026-07-22

Se decidio cerrar el flujo de WhatsApp con una estrategia mixta: `POST /whatsapp/iniciar` sigue siendo la autoridad del backend y el frontend solicita una respuesta JSON segura para abrir la URL autorizada desde la interaccion del usuario.

Motivo:

El redirect backend tradicional era correcto para validacion y auditoria, pero podia ser menos confiable para abrir WhatsApp despues del consentimiento en ciertos navegadores. La URL final no debe estar en templates ni generarse en HTML publico.

Alcance:

- Mantener `POST /whatsapp/iniciar` como punto unico de validacion, CSRF, ownership, rate limit, sesion y notificacion.
- Responder `whatsapp_url` por JSON solo despues de validar y registrar la sesion.
- Mantener redirect HTML como fallback compatible.
- Reservar la apertura externa desde la accion confirmada del usuario.
- Evitar dobles envios desde el frontend.
- No almacenar conversaciones, mensajes ni archivos.
- No exponer telefonos completos en HTML, DOM ni logs.

Criterio:

Las futuras integraciones con WhatsApp Business Cloud API o webhooks deberan extender el servicio central, sin volver a generar enlaces directos desde templates.

## 2026-07-22

Se decidio centralizar la disponibilidad de Google Maps y tratar la API key como configuracion de entorno con fallback obligatorio.

Motivo:

TRAX debe poder operar sin Google Maps en desarrollo, testing o entornos sin key real, y no debe activar scripts externos con placeholders ni exponer claves hardcodeadas.

Alcance:

- Centralizar validacion de `GOOGLE_MAPS_API_KEY`.
- Rechazar placeholders como `tu_clave_real`.
- Exponer la variable en Docker Compose sin valor hardcodeado.
- Mantener fallback visual si falta la key, falla la carga del script o Google informa error de autenticacion.
- Conservar la privacidad del perfil publico usando coordenadas aproximadas.

Criterio:

La key real debera restringirse por dominio/referrer, Maps JavaScript API, cuotas y alertas antes de staging. Geocoding, Places y PostGIS quedan fuera de este cierre.

## 2026-07-22

Se decidio incorporar una base de seguridad transversal sin cambiar URLs, modelos ni experiencia visible.

Motivo:

TRAX ya cuenta con flujos operativos sensibles: autenticacion, presupuestos, propuestas, contratos, WhatsApp, cobertura geografica y administracion. La plataforma necesita controles preventivos de abuso, errores seguros y criterios productivos antes de escalar.

Alcance:

- Aplicar rate limits especificos por endpoint usando Flask-Limiter.
- Usar claves por IP, usuario o combinacion IP+usuario segun sensibilidad.
- Mantener almacenamiento en memoria solo para desarrollo/testing y preparar `RATELIMIT_STORAGE_URI` para Redis futuro.
- Agregar limites configurables de request y formularios.
- Responder errores `400`, `403`, `404`, `413`, `429` y `500` sin detalles internos.
- Reforzar CSP, headers de seguridad y HSTS solo en produccion HTTPS.
- Evitar placeholders inseguros de `SECRET_KEY` en produccion.
- Reducir precision de coordenadas publicas aproximadas.
- Usar `TermsAcceptance` como base versionada inicial de aceptacion.

Criterio:

La seguridad base debe ser incremental y compatible con el monolito modular existente. Redis, WSGI, Cloudflare/WAF y revision legal quedan como requisitos productivos, no como dependencias de esta fase.

## 2026-07-21

Se decidio consolidar TRAX como monolito modular con servicios internos concretos para reglas de negocio, view models, permisos operativos y notificaciones.

Motivo:

`main_routes.py` y `operation_routes.py` concentraban demasiada logica de aplicacion. Separar responsabilidades mejora mantenibilidad sin cambiar URLs, templates ni comportamiento visible.

Alcance:

- Extraer construccion de view models hacia servicios de vista.
- Centralizar permisos y ownership de presupuestos, propuestas y contratos en helpers reutilizables.
- Separar validacion y normalizacion de formularios operativos.
- Concentrar notificaciones operativas fuera de las rutas.
- Mantener Alembic como autoridad del esquema fuera de tests.
- Validar configuracion por entorno con reglas especificas para desarrollo, testing y produccion.

Criterio:

Las rutas deben quedar limitadas a recibir la peticion, validar acceso, invocar servicios, manejar redirects y renderizar templates. No se creara una capa generica si un servicio concreto resuelve mejor el problema.

## 2026-07-15

Se decidio implementar un esquema hibrido para contacto por WhatsApp: username como preferencia de privacidad y telefono como fallback tecnico.

Motivo:

Los usernames de WhatsApp mejoran la privacidad del profesional, pero no existe una URL publica estable y universal para abrir chats por username desde TRAX sin APIs avanzadas.

Alcance:

- Guardar `whatsapp_username` y `whatsapp_contact_preference` en el perfil profesional.
- Priorizar username de forma conceptual cuando la preferencia sea `AUTO` o `USERNAME`.
- Usar telefono como mecanismo tecnico de apertura mientras WhatsApp no ofrezca una URL publica estable por username.
- Registrar en sesiones solo tipo de identificador y valor enmascarado.
- No exponer telefono ni username completo en HTML publico.
- Mantener el flujo central `POST /whatsapp/iniciar`.

Criterio:

No se inventaran URLs no documentadas para usernames de WhatsApp. Cualquier futura apertura directa por username debera integrarse en `whatsapp_contact_service.py`.

## 2026-07-15

Se decidio rediseñar la cobertura del perfil publico como una experiencia visual de mapa aproximado, no como ficha textual.

Motivo:

El cliente debe entender rapidamente el area de trabajo del profesional, pero TRAX debe proteger la ubicacion exacta y evitar que el mapa parezca una direccion precisa.

Alcance:

- Mostrar centro aproximado, anillo de cobertura y radio declarado.
- Usar un marcador propio TRAX con concepto de trabajador de oficio.
- Reducir la informacion textual a cobertura aproximada, zona base y aviso de privacidad.
- Agregar modal no editable para ver la cobertura ampliada.
- Mantener intactas la logica de matching, Cobertura Inteligente, Google Maps v2, dashboards y rutas.

Criterio:

Las futuras mejoras visuales del mapa publico deberan sostener privacidad por defecto y no exponer domicilio, coordenadas ni punto base exacto del profesional.

## 2026-07-15

Se decidio implementar el matching geografico inicial con formula Haversine en backend.

Motivo:

TRAX necesita determinar si un profesional cubre una ubicacion de trabajo usando coordenadas y radio ya persistidos, sin depender de APIs externas ni exponer ubicaciones profesionales exactas.

Alcance:

- Crear `geographic_matching_service.py` como servicio aislado y reutilizable.
- Calcular distancia en linea recta con Haversine.
- Validar latitud, longitud y radio antes de calcular.
- Priorizar profesionales dentro de cobertura cuando la solicitud tenga coordenadas.
- Mantener fallback textual por servicio y zona cuando no existan coordenadas validas.
- Mostrar solo estado de cobertura y distancia aproximada en cards publicas.
- No exponer latitud, longitud ni punto base profesional en HTML publico.

Criterio:

El orden inicial con coordenadas es: dentro de cobertura, PRO, verificado, rating, menor distancia y nombre. En emergencias se reserva el lugar de disponibilidad/guardia para cuando exista un dato real.

Limitacion:

La distancia Haversine no representa rutas, transito ni tiempos de viaje. Las futuras mejoras podran evolucionar hacia PostGIS, poligonos o proveedores de rutas si el producto lo requiere.

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
