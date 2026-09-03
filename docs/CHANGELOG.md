# CHANGELOG MANDOBRA

## 2026-09-02 - Consolidacion documental de trazabilidad

Timestamp: 2026-09-02T21:18:48-03:00
Estado: DOCUMENTACION_VALIDADA
Documento: documentacion canonica de MANDOBRA
Motivo: registrar el contraste estatico de `develop` contra Master Spec,
decisiones, Roadmap y Backlog.
Evidencia: rama `docs/documentation-traceability-consolidation`, commit base
`f63c8db` y auditoria tecnica del 2026-09-02.
Responsable: Codex / Documentation Engineer Senior
Rama: `docs/documentation-traceability-consolidation`
Commit base: `f63c8db`

### Aclarado

- El check de Emergencias cubre solicitud y directorio, no asignacion
  persistente, resolucion operativa completa ni contrato `EMERGENCY`.
- Design System v2 es la capa canonica, pero la migracion visual total sigue
  pendiente.
- La ausencia de P0/P1/P2 documentada corresponde al cierre historico de
  Sprint 7 y no acredita preparacion productiva general.

### Trazabilidad

- Se registro una revision posterior del Master Spec sin alterar su revision
  historica `d07d95`.
- Se incorporo la auditoria tecnica estatica de `f63c8db` al indice.
- Se consolidaron pendientes de Planes/PRO, Emergencias, cobertura de pruebas
  e identificadores internos TRAX sin convertirlos en requisitos aprobados.
- Se eliminaron duplicados no rastreados bajo `docs/RUNBOOKS/` despues de
  verificar contenido y preservar las fuentes canonicas en
  `docs/DECISIONES_ARQUITECTURA.md` y `docs/PLANTILLAS/`.
- Tests de aplicacion: NO EJECUTADOS - no aplican al alcance documental.

## 2026-08-04 - Sprint 7 Contractual Trust Fases 2E-2F (cierre aprobado)

Estado: la auditoría independiente de integración fue aprobada. Sprint 7 está
técnicamente cerrado y aprobado para PR hacia `develop`. Esta aprobación no
autoriza publicación ni despliegue productivo.

### Agregado

- Se vincularon las reviews nuevas a un único `ContractRequest` confirmado.
- Se agregó `create_contract_review()` como operación cerrada, atómica e idempotente.
- Se agregó `ReputationEvent` neutral con rating observado y `puntos = NULL`.
- Se agregaron visibilidad pública separada, elegibilidad del rating y moderación cerrada.
- Se agregó la migración Alembic `20260726_06` con constraints y triggers físicos para reviews y reputación.
- Se agregó `20260726_07` como head para exigir discriminadores explícitos,
  reparar ownership profesional legacy y preservar `_06` sin reescribirla.
- Se agregaron gates PostgreSQL para concurrencia, rutas, CSRF, privacidad, moderación y rollback.

### Mejorado

- El perfil público consume exclusivamente `comment_public` y métricas neutrales reconstruibles.
- Las reviews contractuales y legacy verificadas se distinguen explícitamente.
- La lectura de comentarios originales pendientes exige `SUPER_ADMIN` activo también dentro del servicio.
- PostgreSQL y SQLite impiden nuevas filas reputacionales con puntos, preservando las filas históricas existentes.

### Corregido

- Se bloqueó con `410` la ruta legacy de creación de reviews.
- Se retiró `add_reputation_event()` como API pública y no quedan callers productivos.
- Se eliminó la presentación pública del score histórico como reputación contractual.
- Se verificó que el flujo nuevo no crea `ContractEvent` ni puntos arbitrarios.
- Se cerró el bypass de `NULL`/orígenes desconocidos en `Review` y
  `ReputationEvent` mediante checks requeridos y triggers `v2` de inserción
  y actualización en PostgreSQL y SQLite.
- Las métricas admiten sólo `CONTRACTUAL` y `LEGACY` verificada; ningún
  origen nulo o desconocido se interpreta como legacy.
- El seed de desarrollo dejó de fabricar eventos reputacionales legacy con puntos.
- `20260726_06` conserva su clasificación histórica mediante un snapshot
  migratorio versionado y autocontenido. No es una API productiva: su
  aislamiento es un contrato arquitectónico verificado por dependencias, no
  una frontera contra imports de Python arbitrarios. El adaptador vigente
  exige ambos IDs de ownership y falla ante payloads incompletos.
  `20260726_07` usa exclusivamente esa API fail-closed y es el
  único estado operativo soportado. Un downgrade a `_06`
  reinstala defensas históricas más débiles y no equivale a `_07` para
  operación normal.

### Validación

- Auditoría independiente de integración: aprobada.
- Hallazgos abiertos: P0/P1/P2 ninguno. P3 no bloqueante: contraseña demo
  predecible pendiente de endurecimiento futuro.
- PostgreSQL 16.14, Alembic `20260726_07`: 59/59 pruebas finales aprobadas.
- Gate contractual 8/8; negociación 8/8; reviews 10/10; rutas/moderación 8/8; migración parcial 21/21; legacy 4/4.
- Suite Sprint 7 con PostgreSQL habilitado: 165 ejecutadas, 164 aprobadas y 1 omisión deliberada; cero fallos.
- Suite completa con PostgreSQL habilitado: 266 ejecutadas, 265 aprobadas y la misma omisión deliberada; cero fallos.
- Los warnings por `Query.get()` y `datetime.utcnow()` quedan como deuda no bloqueante.
- `20260726_07` es el único estado operativo soportado. Un downgrade a `_06`
  restaura defensas históricas más débiles.

## 2026-07-26 - Sprint 7 Contracting Core Fase 2A

### Agregado

- Se agrego `OperationCommand` como fuente canonica de idempotencia para comandos contractuales sensibles.
- Se agregaron `contracting_mode = EXTERNAL` y `version` a `ContractRequest`.
- Se agregaron secuencia, correlacion, causacion e idempotencia a `ContractEvent`.
- Se agrego correlacion estructurada a `AuditLog` y `ActivityNotification`.
- Se agrego la migracion Alembic `20260726_02_sprint7_contracting_foundations`.
- Se agrego la migracion Alembic `20260726_03_sprint7_single_hiring_mode`.
- Se agregaron pruebas de estados, ownership, idempotencia, rollback y
  constraints; la validacion de locks reales queda pendiente de PostgreSQL.
- Se agrego un gate PostgreSQL E2E explicito para carreras de comandos,
  transiciones y creaciones derivadas con dos sesiones independientes.
- Se agregaron pruebas integradas de reparacion y bloqueo de esquemas parciales
  de `operation_commands`.
- Se valido el gate contra PostgreSQL 16: 8 escenarios E2E, 4 pruebas
  legacy y 21 escenarios de migracion parcial aprobados sin omisiones.
- Se agregaron pruebas negativas para impedir la fabricacion externa de
  eventos contractuales y para validar o reparar el generador PostgreSQL de
  `operation_commands.id`.

### Mejorado

- `CONFIRMADA` es el unico estado terminal exitoso para contratos nuevos.
- `CERRADA` contractual se migra a `CONFIRMADA` y deja de ser un estado valido de escritura.
- Las transiciones contractuales usan operaciones explicitas, lock pesimista y version esperada.
- Evento, auditoria, notificacion interna y resultado idempotente se confirman en una unica transaccion.
- Las notificaciones contractuales obligatorias quedan listas para una futura outbox sin implementar canales externos.
- La creacion derivada de contratos conserva correlacion comun entre eventos, auditoria y notificaciones.
- Las creaciones derivadas autorizan al actor owner antes del replay y recuperan
  colisiones unicas mediante savepoint sin commits internos.
- `hiring_mode = MULTIPLE` queda bloqueado tambien por constraint hasta Fase 2C.
- La migracion ya no considera completa una `operation_commands` solo porque
  exista la tabla: valida estructura, datos, constraints e indices antes de
  reparar.
- El preflight PostgreSQL valida identity/default, ownership y permisos de la
  secuencia de `operation_commands.id`; sincroniza el generador por encima de
  `MAX(id)` o bloquea antes de otras mutaciones si no puede repararlo.
- La validacion del generador incluye incremento ascendente, `NO CYCLE`,
  limites compatibles con `INTEGER`, siguiente valor efectivo y ausencia de
  consumidores compartidos. Las secuencias propias reparables se normalizan a
  incremento 1 y se reinician en `MAX(id) + 1`.
- Las secuencias creadas por la migracion quedan marcadas; el downgrade
  preserva secuencias preexistentes o ajenas.

### Corregido

- Se retiro el mutador generico `update_contract_status`.
- Se elimino la transicion posterior `CONFIRMADA -> CERRADA`.
- Los servicios validan rol y ownership sin depender exclusivamente de las rutas.
- Los actores ausentes, inexistentes, suspendidos, inactivos, con rol incorrecto
  o sin ownership no pueden crear ni consultar por replay un contrato derivado.
- Se elimino la API generica publica `create_contract_event`: los eventos
  iniciales de presupuesto y propuesta solo se emiten dentro de sus operaciones
  cerradas, junto con auditoria y notificacion correlacionadas.

## 2026-07-26 - Sprint 7 Contracting Core Fase 1

### Agregado

- Se agrego `ContractEvent` como historial de dominio para contrataciones.
- Se agrego `contracting_core_service.py` como puerta central para crear contratos desde presupuestos y propuestas.
- Se agrego trazabilidad de origen en `ContractRequest` para `DIRECT`, `BUDGET` y `PROPOSAL`.
- Se agrego migracion Alembic `20260726_01_sprint7_contracting_core`.
- Se agregaron pruebas de contratacion directa, presupuesto a contrato y propuesta a contrato.

### Mejorado

- Una `BudgetOffer` adjudicada crea un `ContractRequest` canonico en estado `CREADA`.
- Una `ProposalApplication` aceptada crea un `ContractRequest` canonico en estado `CREADA`.
- Las creaciones derivadas son idempotentes y conservan referencias a la entidad origen.
- Los reintentos de adjudicacion o aceptacion no duplican eventos, auditorias ni notificaciones.
- Las propuestas usan `hiring_mode = SINGLE` por defecto: la primera postulacion aceptada cierra la propuesta y descarta otras activas.
- La migracion incorpora checks de consistencia de origen y bloqueo seguro de downgrade si ya existe trazabilidad contractual.
- Las transiciones de contrato generan eventos de dominio.

### Corregido

- Se corrigio el contrato de estados de `BudgetRequest` para incluir `CANCELADA` y estados canonicos de publicacion.
- Se normaliza el estado legacy `CERRADO` de presupuestos a `CERRADA`.

## 2026-07-24 - UX/UI General & Design System v2

### Agregado

- Se agrego carga explicita de `design-system-v2.css` desde `base.html`.
- Se agrego `design-system-v2.js` para cierre accesible de alertas globales.
- Se agregaron componentes canonicos para flashes, estados vacios, layout utilities y modal compartido.
- Se creo la documentacion de cierre del sprint en `docs/SPRINTS/2026-07-24_UX_UI_General_Design_System_v2.md`.

### Mejorado

- Login, registro, rubro solicitado, notificaciones, flashes globales y modal WhatsApp quedaron alineados al contrato `.trax-*`.
- `styles.css` dejo de importar el Design System v2 y queda como capa legacy posterior.
- `DESIGN_SYSTEM_V2.md` documenta jerarquia CSS, mapa de impacto, deuda pendiente y estrategia de migracion futura.

### Corregido

- Se redujo duplicacion visual en notificaciones y modal WhatsApp sin cambiar rutas ni logica de negocio.
- Se protegio por tests la carga del Design System v2 antes de estilos legacy.

## 2026-07-24 - Rediseño de Login y Registro

### Agregado

- Se agrego una experiencia dedicada de autenticacion con `auth-ux-v1.css` y `auth-ux-v1.js`.
- Se agregaron labels visibles, errores inline accesibles, toggle de contraseña, estado de carga y feedback de fortaleza.
- Se agrego validacion centralizada de login y registro en `auth_service.py`.
- Se conecto `TermsAcceptance` al registro con version centralizada.
- Se agregaron pruebas de login, registro, CSRF, rate limiting, redirects, roles, terminos y accesibilidad basica.

### Mejorado

- `auth_routes.py` quedo orientado a request, servicio, sesion y redirect.
- El registro crea cuenta basica y redirige por rol: cliente al destino seguro, profesional a completar perfil.
- El login rechaza usuarios suspendidos o inactivos antes de crear sesion.
- Los mensajes de registro evitan confirmar explicitamente si un email ya existe.

### Corregido

- Se evita dejar una cuenta parcialmente creada si falla el registro de consentimiento.
- Se bloqueo `next` externo tambien en el flujo de registro con sesion inmediata.

## 2026-07-23 - Identidad y Portfolio Profesional

### Agregado

- Se agrego el modelo `ProfessionalMedia` para gestionar avatar, portada y galeria profesional.
- Se creo la migracion Alembic `20260723_01_professional_media_v1`.
- Se agregaron servicios para procesar imagenes, almacenar archivos y administrar media profesional.
- Se agregaron rutas privadas para subir, reemplazar, editar, reordenar, marcar principal y eliminar media.
- Se agregaron acciones de moderacion administrativa para publicar, rechazar, ocultar y restaurar imagenes.
- Se agregaron pruebas de validacion de imagenes, ownership, CSRF, moderacion, fallback legacy y almacenamiento.

### Mejorado

- El perfil privado profesional incorpora gestion basica de identidad visual y portfolio sin redisenar la UX general.
- El perfil publico, galeria y cards profesionales priorizan media publicada y mantienen campos legacy como fallback.
- Las imagenes se reprocesan para eliminar EXIF/GPS y generar miniaturas.
- El almacenamiento local queda validado para desarrollo y Cloudinary queda configurable por entorno sin secretos versionados.

### Corregido

- Se evita exponer imagenes rechazadas, ocultas o eliminadas en el perfil publico.
- Se rechazan archivos corruptos, MIME falso, extensiones no permitidas, tamanos excesivos y dimensiones invalidas.

## 2026-07-22 - Cierre de WhatsApp y Geolocalizacion

### Agregado

- Se agrego respuesta JSON segura en `POST /whatsapp/iniciar` para abrir la URL autorizada desde la interaccion del usuario.
- Se agrego validacion central de disponibilidad de `GOOGLE_MAPS_API_KEY`.
- Se agregaron pruebas de cierre para WhatsApp, Google Maps, privacidad, CSRF, ownership, radios y coordenadas.
- Se documento el cierre operativo de WhatsApp y Geolocalizacion.

### Mejorado

- El modal de WhatsApp ya no depende exclusivamente de submit programatico y redirect backend.
- El flujo conserva redirect HTML como fallback compatible.
- El fallback del modal funciona en navegadores sin soporte de `<dialog>`.
- Google Maps ignora placeholders y cae a fallback si falta la key, falla la carga o Google informa error de autenticacion.
- Docker Compose expone `GOOGLE_MAPS_API_KEY` sin hardcodear claves.

### Corregido

- Se evita que una key placeholder active el mapa interactivo.
- Se evita aceptar telefonos tecnicamente invalidos para construir URLs de WhatsApp.
- Se redujo el riesgo de dobles envios desde el frontend mediante bloqueo de submit en curso.

## 2026-07-22 - Security & Compliance Foundation v1

### Agregado

- Se agregaron claves reutilizables de rate limiting por IP, usuario e IP+usuario.
- Se agregaron limites especificos para login, registro, busquedas, WhatsApp, solicitudes, propuestas, reportes y POST administrativos.
- Se agregaron handlers seguros para `400`, `403`, `404`, `413`, `429` y `500`.
- Se agregaron limites configurables de tamano de request y memoria de formularios.
- Se agregaron pruebas de seguridad, privacidad publica, headers, errores seguros y consentimientos versionados.

### Mejorado

- Se reforzaron cookies de sesion, headers de seguridad, CSP y HSTS condicionado a produccion HTTPS.
- Se amplio `.gitignore` para artefactos locales sensibles.
- Se documento Docker Compose como entorno local con credenciales no reutilizables en produccion.
- Se redujo la precision de coordenadas publicas aproximadas de cobertura.

### Corregido

- Produccion ya no acepta placeholders inseguros de `SECRET_KEY`.
- Los errores internos no exponen detalles ni payloads sensibles al usuario.

## 2026-07-21 - Consolidacion Arquitectonica v1

### Agregado

- Se agregaron servicios internos para separar view models, permisos, formularios y notificaciones operativas de las rutas principales.
- Se agregaron pruebas de configuracion por entorno, ownership y servicios extraidos.

### Mejorado

- `main_routes.py` y `operation_routes.py` redujeron responsabilidades y quedaron orientados a request, permisos, servicios y render.
- Se consolidaron `DevelopmentConfig`, `TestingConfig` y `ProductionConfig`.
- Se establecio Alembic como autoridad del esquema fuera de tests.
- Se documento Docker como flujo principal de ejecucion local.

### Corregido

- Se elimino el fallback inseguro de `SECRET_KEY` para produccion.
- Se restringio `db.create_all()` a tests o desarrollo explicitamente habilitado.

## 2026-07-15 - WhatsApp Contact Privacy v1

### Agregado

- Se agregaron `whatsapp_username` y `whatsapp_contact_preference` al modelo `Professional`.
- Se agregaron `contact_identifier_type` y `contact_identifier_masked` a `WhatsAppContactSession`.
- Se creo la migracion Alembic `20260715_01_whatsapp_contact_privacy_v1`.
- Se agregaron helpers para normalizar, validar y resolver identificadores de contacto por WhatsApp.
- Se agregaron campos de username y preferencia en el perfil privado profesional.
- Se agregaron pruebas unitarias para el esquema hibrido de contacto.

### Mejorado

- El flujo central de WhatsApp prioriza username de forma conceptual cuando existe y la preferencia lo permite.
- Mientras no exista URL publica estable por username, el telefono se mantiene como fallback tecnico de apertura.
- Las sesiones registran solo tipo de identificador y valor enmascarado.
- El perfil publico informa contacto protegido sin exponer telefono ni username completo.

### Corregido

- Se evita duplicar telefonos completos en nuevas sesiones de contacto.

## 2026-07-15 - Public Profile Map UX v1

### Agregado

- Se agrego el marcador SVG reutilizable `trax-worker-marker.svg` para mapas publicos de cobertura.
- Se agrego modal "Ver cobertura ampliada" en el perfil publico profesional.
- Se agrego card vacia para profesionales sin zona de cobertura configurada.

### Mejorado

- Se rediseño la seccion publica "Zona de cobertura" con experiencia visual tipo marketplace.
- El perfil publico muestra mapa, anillo de cobertura, centro aproximado, radio y zona base sin exponer direccion exacta.
- El mapa publico usa marcador TRAX personalizado en lugar del pin clasico de Google.
- La seccion queda adaptada a claro, oscuro, desktop, tablet y mobile.

### Corregido

- Se reemplazo el bloque textual largo por un resumen breve orientado a privacidad.

## 2026-07-15 - Matching Geografico por Distancia v1

### Agregado

- Se creo `app/services/geographic_matching_service.py` con calculo Haversine en backend.
- Se agregaron pruebas unitarias para distancia, cobertura, coordenadas ausentes e invalidas.
- Se integro el resultado de cobertura en Resultados de profesionales y Directorio de Emergencias.
- Se agrego visualizacion publica de estado de cobertura y distancia aproximada en cards compatibles.

### Mejorado

- Los resultados con coordenadas validas priorizan profesionales dentro de cobertura.
- Las busquedas sin coordenadas conservan el matching textual actual por servicio y zona.
- La interfaz informa cobertura sin exponer coordenadas ni punto base profesional.

### Corregido

- Sin correcciones registradas.

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
