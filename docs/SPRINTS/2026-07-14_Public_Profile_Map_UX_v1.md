# Public Profile Map UX v1

## Objetivo

Rediseñar la seccion "Zona de cobertura" del perfil publico profesional con una experiencia visual moderna, clara y orientada a privacidad.

## Resumen

Se reemplazo el bloque textual de cobertura por un mapa visual con anillo, centro aproximado, marcador TRAX reutilizable y resumen minimo. Se agrego modal de cobertura ampliada no editable.

## Cambios implementados

- Nueva composicion visual de mapa publico en el perfil profesional.
- Marcador SVG propio de TRAX con concepto trabajador de oficio.
- Anillo de cobertura semitransparente.
- Resumen debajo del mapa: cobertura aproximada y zona base.
- Texto breve de privacidad.
- Modal "Ver cobertura ampliada".
- Estado vacio elegante para profesionales sin cobertura configurada.

## Archivos creados

- `app/static/img/trax-worker-marker.svg`
- `docs/SPRINTS/2026-07-14_Public_Profile_Map_UX_v1.md`

## Archivos modificados

- `app/templates/components/_professional_work_area.html`
- `app/static/css/professional-profile-v2.css`
- `app/static/js/professional-coverage-map.js`
- `docs/CHANGELOG.md`
- `docs/ROADMAP.md`
- `docs/DECISIONES_ARQUITECTURA.md`
- `docs/BACKLOG.md`

## Rutas agregadas

- No se agregaron rutas.

## Migraciones realizadas

- No se realizaron migraciones.

## Validaciones ejecutadas

- `python -m compileall app scripts`
- `git diff --check`
- `docker compose up --build -d`
- `docker compose ps`
- `docker compose logs trax-web --tail=80`
- Validacion visual desktop.
- Validacion visual tablet.
- Validacion visual mobile.
- Validacion theme claro y oscuro.
- Validacion de modal ampliado.
- Validacion de estado vacio sin cobertura.
- Validacion sin overflow horizontal.
- Validacion sin errores de consola en perfil publico.

## Capturas

- `C:/Users/Usuario/.codex/visualizations/2026/07/10/019f495b-0a05-7271-aaf8-b0014c25503a/public-profile-map-ux-v1/perfil_mapa_desktop_light.png`
- `C:/Users/Usuario/.codex/visualizations/2026/07/10/019f495b-0a05-7271-aaf8-b0014c25503a/public-profile-map-ux-v1/perfil_mapa_desktop_dark.png`
- `C:/Users/Usuario/.codex/visualizations/2026/07/10/019f495b-0a05-7271-aaf8-b0014c25503a/public-profile-map-ux-v1/perfil_mapa_modal_dark.png`
- `C:/Users/Usuario/.codex/visualizations/2026/07/10/019f495b-0a05-7271-aaf8-b0014c25503a/public-profile-map-ux-v1/perfil_mapa_mobile_dark.png`

## Riesgos pendientes

- Validar con `GOOGLE_MAPS_API_KEY` real para confirmar el marcador personalizado sobre Google Maps en entorno con API activa.
- El fallback visual no reemplaza al mapa real, solo preserva la experiencia cuando no hay API key.

## Problemas encontrados

- Sin problemas bloqueantes registrados.

## Decisiones tomadas

- Mantener el centro publico aproximado existente.
- No mostrar direccion, domicilio ni coordenadas en la interfaz.
- No modificar matching geografico, Cobertura Inteligente, Google Maps backend ni dashboards.

## Resultado final

El perfil publico comunica la zona de cobertura en menos tiempo, con una lectura visual mas moderna y una señal clara de privacidad.

## Proximo Sprint recomendado

Auditar estilos avanzados de mapa o mapa de marca TRAX cuando exista una estrategia visual final para mapas.
