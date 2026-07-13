# Cobertura Inteligente v1

## Objetivo

Crear la primera version funcional de zona de cobertura para profesionales, visible en perfil privado, perfil publico y Dashboard Profesional.

## Resumen

Se agrego persistencia de cobertura en `Professional`, un servicio central de normalizacion y visualizaciones sin APIs externas. La version queda preparada para Google Maps, geocoding y matching futuro.

## Cambios implementados

- Campos de cobertura profesional persistentes.
- Seccion "Zona de cobertura" editable en perfil privado.
- Mapa placeholder con anillo representativo del radio seleccionado.
- Visualizacion publica de cobertura y estado vacio.
- Resumen operativo de cobertura en Dashboard Profesional.
- Helper `coverage_service.py` para normalizacion y descripcion.

## Archivos creados

- `app/services/coverage_service.py`
- `migrations/versions/20260712_02_smart_coverage_v1.py`
- `docs/SPRINTS/2026-07-12_Cobertura_Inteligente_v1.md`

## Archivos modificados

- `app/models/professional.py`
- `app/routes/main_routes.py`
- `app/services/professional_service.py`
- `app/templates/completar_perfil_profesional.html`
- `app/templates/components/_professional_work_area.html`
- `app/templates/profesional_dashboard.html`
- `app/static/css/professional-media-form.css`
- `app/static/css/professional-profile-v2.css`
- `app/static/css/professional-dashboard-v1.css`
- `app/static/js/profile-private-ux-a.js`
- `docs/CHANGELOG.md`
- `docs/ROADMAP.md`
- `docs/DECISIONES_ARQUITECTURA.md`
- `docs/BACKLOG.md`

## Rutas agregadas

- No se agregaron rutas nuevas.

## Rutas afectadas

- `/profesional/perfil/completar`
- `/profesional/dashboard`
- `/profesional/<id>`

## Migraciones realizadas

- `20260712_02_smart_coverage_v1`: agrega campos de cobertura y coordenadas nullable a `professionals`.

## Validaciones ejecutadas

- `python -m compileall app scripts`
- `git diff --check`
- `docker compose down`
- `docker compose up --build -d`
- `docker compose ps`
- `docker compose logs trax-web --tail=100`
- `docker compose exec -T trax-web alembic upgrade head`
- `docker compose exec -T trax-web alembic current`
- Prueba funcional Flask: radio 10 km, recarga, perfil publico, cambio a 30 km, ownership, dashboard y estado vacio.
- Validacion visual desktop/mobile en claro/oscuro.

## Capturas

- `docs/SPRINTS/captures/cobertura_privada_desktop_light.png`
- `docs/SPRINTS/captures/cobertura_privada_desktop_dark.png`
- `docs/SPRINTS/captures/cobertura_publica_desktop_dark.png`
- `docs/SPRINTS/captures/cobertura_publica_mobile_dark.png`
- `docs/SPRINTS/captures/cobertura_dashboard_mobile_dark.png`

## Riesgos pendientes

- Falta integracion Google Maps.
- Falta geocoding.
- Falta matching por distancia.
- Falta soporte de poligonos avanzados.

## Problemas encontrados

- La pantalla privada ya tenia un placeholder de cobertura sin persistencia. Se reemplazo por campos reales manteniendo el formulario y CSRF existentes.

## Decisiones tomadas

- No integrar APIs externas en esta fase.
- Guardar coordenadas nullable para habilitar integraciones futuras sin bloquear la version actual.
- Centralizar validaciones y descripcion de cobertura en un servicio.

## Resultado final

La cobertura profesional queda configurable por el propietario, persistida en base de datos y visible para clientes en el perfil publico.

## Proximo Sprint recomendado

Google Maps + Geocoding v1 o Matching por Distancia v1, segun prioridad de producto.
