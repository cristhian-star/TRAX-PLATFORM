# Security & Compliance Foundation v1

## Objetivo

Fortalecer la base tecnica de seguridad y cumplimiento de TRAX sin cambiar UX/UI, URLs, modelos ni migraciones.

## Resumen

Se implementaron rate limits por endpoint, limites de recursos, errores seguros, headers reforzados, auditoria de secretos y controles de exposicion publica de datos sensibles.

## Cambios implementados

- Rate limiting para autenticacion, registro, busquedas, WhatsApp, solicitudes, propuestas, reportes y POST administrativos.
- Claves reutilizables por IP, usuario e IP+usuario.
- `MAX_CONTENT_LENGTH` y limite de memoria de formularios configurables por entorno.
- Handlers seguros para `400`, `403`, `404`, `413`, `429` y `500`.
- HSTS condicionado a produccion HTTPS.
- CSP compatible con Google Maps y restringida contra objetos embebidos.
- Rechazo de placeholders inseguros de `SECRET_KEY` en produccion.
- `.gitignore` ampliado para artefactos sensibles.
- Coordenadas publicas aproximadas con menor precision.
- Pruebas para seguridad, privacidad, rate limits, headers y consentimientos versionados.

## Archivos creados

- `app/utils/security.py`
- `tests/test_security_controls.py`
- `tests/test_security_compliance_phase3.py`
- `docs/SPRINTS/2026-07-22_Security_Compliance_Foundation_v1.md`

## Archivos modificados

- `.env.example`
- `.gitignore`
- `README.md`
- `app/__init__.py`
- `app/config/config.py`
- `app/routes/auth_routes.py`
- `app/routes/main_routes.py`
- `app/routes/operation_routes.py`
- `app/routes/whatsapp_routes.py`
- `app/services/coverage_service.py`
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

- `python -m unittest discover tests`
- `python -m compileall app scripts tests`
- `git diff --check`
- `docker compose up --build -d`
- `docker compose ps`
- Tests dentro del contenedor.
- Smoke tests de auth, busquedas, perfiles, WhatsApp, presupuestos, propuestas y administracion.

## Riesgos pendientes

- Redis productivo para Flask-Limiter.
- Servidor WSGI productivo.
- Cloudflare/WAF o equivalente.
- Revision legal profesional de terminos, privacidad, cookies y consentimientos.
- Campo `source` explicito para consentimientos si se requiere trazabilidad separada.
- Reemplazo de `Query.get()`.
- Reemplazo de `datetime.utcnow()`.

## Problemas encontrados

- Docker Compose conserva credenciales locales de desarrollo. Quedaron documentadas como no reutilizables en produccion.
- El servidor Flask de desarrollo sigue siendo usado por el entorno local Docker.

## Decisiones tomadas

- Mantener Redis como configuracion futura, sin agregar dependencia ni servicio en este sprint.
- Mantener `TermsAcceptance` sin migracion porque cubre usuario, tipo, version, fecha, IP y user agent.
- Reducir precision de coordenadas publicas en lugar de retirar el mapa.

## Resultado final

Rama lista para revision tecnica y merge, sujeta a aprobacion del equipo.

## Proximo Sprint recomendado

Production Readiness v1: Redis, WSGI, checklist de staging, backups, monitoreo, escaneo de secretos/dependencias y WAF.
