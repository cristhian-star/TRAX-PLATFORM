# Cierre de WhatsApp y Geolocalizacion

## Objetivo

Cerrar el flujo operativo de WhatsApp y dejar Google Maps configurable y tolerante a fallos, sin cambiar UX/UI, URLs, modelos ni migraciones.

## Resumen

Se reforzo la apertura de WhatsApp posterior al consentimiento usando respuesta JSON segura desde el backend y apertura autorizada desde el frontend. Google Maps quedo centralizado por configuracion, con rechazo de placeholders y fallback robusto ante ausencia o falla de la key.

## Cambios implementados

- `POST /whatsapp/iniciar` responde JSON seguro cuando el frontend lo solicita.
- Se mantiene redirect HTML como fallback compatible.
- El modal de WhatsApp solicita la URL autorizada por `fetch` y evita dobles envios.
- Se agrego fallback accesible si el navegador no soporta `<dialog>`.
- Se valido longitud razonable del telefono tecnico usado por WhatsApp.
- Se centralizo la lectura y validacion de `GOOGLE_MAPS_API_KEY`.
- Docker Compose expone `GOOGLE_MAPS_API_KEY` sin hardcodear claves.
- El mapa cae a fallback si falta la key, es placeholder, falla el script o Google informa error de autenticacion.
- Se agregaron pruebas de cierre para WhatsApp, Google Maps, cobertura y privacidad.

## Archivos creados

- `app/services/google_maps_config_service.py`
- `tests/test_whatsapp_geolocation_completion_phase2.py`
- `docs/SPRINTS/2026-07-22_Cierre_WhatsApp_Geolocalizacion.md`

## Archivos modificados

- `README.md`
- `app/routes/main_routes.py`
- `app/routes/whatsapp_routes.py`
- `app/services/whatsapp_contact_service.py`
- `app/static/js/whatsapp-consent-v1.js`
- `app/static/js/professional-coverage-map.js`
- `docker-compose.yml`
- `docs/CHANGELOG.md`
- `docs/ROADMAP.md`
- `docs/BACKLOG.md`
- `docs/DECISIONES_ARQUITECTURA.md`

## Rutas agregadas

- No se agregaron rutas.

## Migraciones realizadas

- No se realizaron migraciones.

## Validaciones ejecutadas

- `python -m unittest discover tests`: 67 tests OK.
- `python -m compileall app scripts tests`.
- `git diff --check`.
- `docker compose up --build -d`.
- `docker compose ps`.
- Tests dentro del contenedor: 67 tests OK.
- Smoke tests HTTP de `/`, `/login`, `/buscar`, `/explorar` y `/profesional/1`.
- Validacion manual en navegador integrado de perfil publico, modal WhatsApp, apertura externa sin envio, fallback de mapa, desktop, mobile y tema oscuro.

## Validaciones manuales reales

- El consentimiento de WhatsApp se exige antes de continuar.
- El boton Continuar inicia deshabilitado hasta aceptar.
- La apertura externa llego a WhatsApp Web/API sin enviar mensaje real.
- La prueba manual creo una sola sesion nueva.
- La ultima sesion quedo en `CONTACTO_ABIERTO`.
- Los logs de Flask no expusieron telefono ni URL externa.
- El HTML/DOM del perfil publico no expuso `wa.me` ni telefono completo.
- Sin key real de Google Maps, el perfil publico uso fallback visual sin errores de consola.

## Limitaciones de validacion

- No se valido Chrome escritorio mediante conector dedicado porque no estuvo disponible en el entorno de ejecucion.
- No se valido dispositivo movil fisico.
- No se valido carga real de Google Maps porque no habia `GOOGLE_MAPS_API_KEY` de staging disponible en Docker.

## Riesgos pendientes

- Validar Google Maps en staging con key real restringida por dominio/referrer, API y cuota.
- Confirmar apertura WhatsApp en Chrome escritorio y dispositivo movil fisico.
- Implementar WhatsApp Business Cloud API y webhooks si producto lo aprueba.
- Implementar Geocoding y Places Autocomplete cuando se defina UX de ubicacion.
- Evaluar PostGIS cuando el volumen requiera indices espaciales.
- Reemplazar usos legacy de `Query.get()`.
- Reemplazar `datetime.utcnow()` por timestamps timezone-aware.

## Problemas encontrados

- No habia key real de Google Maps configurada, por lo que solo se valido fallback.
- El entorno no expuso herramienta Chrome dedicada.

## Decisiones tomadas

- Mantener el backend como autoridad del flujo WhatsApp y entregar la URL autorizada por JSON al frontend.
- Conservar redirect HTML como fallback.
- No generar enlaces `wa.me` en templates.
- Tratar Google Maps como proveedor opcional por entorno, nunca como dependencia obligatoria de la pantalla.

## Resultado final

El sprint queda cerrado a nivel de implementacion, pruebas automatizadas, Docker y documentacion. La rama queda lista para revision y merge, con validaciones de staging pendientes para Google Maps real y dispositivos fisicos.

## Proximo Sprint recomendado

Staging Readiness v1: validar Google Maps con key restringida, Chrome escritorio, dispositivo movil fisico, checklist productivo, WSGI, Redis y monitoreo.
