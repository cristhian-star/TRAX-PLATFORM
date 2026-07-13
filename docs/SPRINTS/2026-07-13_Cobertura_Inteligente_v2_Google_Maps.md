# Cobertura Inteligente v2 Google Maps

## Objetivo

Reemplazar el placeholder de cobertura por integracion preparada para Google Maps JavaScript API, manteniendo fallback seguro sin API key.

## Resumen

Se agrego un modulo frontend aislado para mapas de cobertura, persistencia de consentimiento y validacion de coordenadas. El perfil privado queda preparado para marcador movible y circulo de radio. El perfil publico muestra cobertura aproximada sin revelar coordenadas exactas.

## Cambios implementados

- Modulo `professional-coverage-map.js` para Google Maps.
- Inputs ocultos `latitude` y `longitude` en perfil privado.
- Consentimiento explicito para uso de ubicacion.
- Fallback visual cuando no existe `GOOGLE_MAPS_API_KEY`.
- Centro publico aproximado calculado sin modificar datos persistidos.
- CSP ajustado para permitir Maps JavaScript API.

## Archivos creados

- `app/static/js/professional-coverage-map.js`
- `migrations/versions/20260713_01_google_maps_coverage_v2.py`
- `docs/SPRINTS/2026-07-13_Cobertura_Inteligente_v2_Google_Maps.md`

## Archivos modificados

- `.env.example`
- `app/__init__.py`
- `app/models/professional.py`
- `app/routes/main_routes.py`
- `app/services/coverage_service.py`
- `app/services/professional_service.py`
- `app/templates/completar_perfil_profesional.html`
- `app/templates/components/_professional_work_area.html`
- `app/templates/perfil_profesional.html`
- `app/static/css/professional-media-form.css`
- `app/static/css/professional-profile-v2.css`
- `docs/CHANGELOG.md`
- `docs/ROADMAP.md`
- `docs/DECISIONES_ARQUITECTURA.md`
- `docs/BACKLOG.md`

## Rutas agregadas

- No se agregaron rutas nuevas.

## Rutas afectadas

- `/profesional/perfil/completar`
- `/profesional/<id>`

## Migraciones realizadas

- `20260713_01_google_maps_coverage_v2`: agrega `coverage_location_consent_at` nullable en `professionals`.

## Configuracion requerida

- Variable `GOOGLE_MAPS_API_KEY` en entorno.
- La clave debe restringirse por origen autorizado, Maps JavaScript API y cuotas de uso.
- No se debe commitear una clave real.

## Validaciones ejecutadas

- `python -m compileall app scripts`
- `git diff --check`
- `node --check app/static/js/professional-coverage-map.js` usando Node empaquetado por Codex.
- `docker compose up --build -d`
- `docker compose ps`
- `docker compose logs trax-web --tail=100`
- `docker compose exec -T trax-web alembic upgrade head`
- `docker compose exec -T trax-web alembic current`
- Prueba funcional Flask: consentimiento, persistencia de coordenadas, radio, ownership, fallback y privacidad publica.
- Validacion visual fallback desktop/mobile sin API key.

## Capturas

- `docs/SPRINTS/captures/cobertura_v2_privada_fallback_desktop.png`
- `docs/SPRINTS/captures/cobertura_v2_publica_fallback_desktop.png`
- `docs/SPRINTS/captures/cobertura_v2_publica_fallback_mobile.png`

## Riesgos pendientes

- Falta validar con una API key real de Google Maps.
- Falta restringir la clave en Google Cloud.
- Falta geocoding.
- Falta Places Autocomplete.
- Falta matching por distancia.
- Falta soporte de poligonos avanzados.

## Problemas encontrados

- La CSP existente bloqueaba scripts externos. Se habilito solo `https://maps.googleapis.com` para scripts y endpoints de Maps en `connect-src`.

## Decisiones tomadas

- Google Maps queda como proveedor frontend encapsulado.
- Python no importa librerias de Google.
- Las coordenadas exactas solo se usan en perfil privado y persistencia autorizada.
- El perfil publico usa centro aproximado y no muestra texto con coordenadas exactas.

## Resultado final

TRAX queda preparado para mapa interactivo real de cobertura profesional con fallback seguro cuando no hay API key.

## Proximo Sprint recomendado

Geocoding + Places Autocomplete v1 o Matching Geografico v1.
