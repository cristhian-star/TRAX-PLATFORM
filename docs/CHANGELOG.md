# CHANGELOG TRAX

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
