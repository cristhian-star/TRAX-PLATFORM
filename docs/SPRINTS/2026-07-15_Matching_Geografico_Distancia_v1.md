# Matching Geografico por Distancia v1

## Objetivo

Crear un motor reutilizable para determinar si un profesional cubre geograficamente una ubicacion de trabajo.

## Resumen

Se implemento un servicio backend con formula Haversine que compara la distancia entre profesional y trabajo contra el radio de cobertura declarado. La integracion inicial aplica en Resultados de profesionales y Directorio de Emergencias.

## Cambios implementados

- Servicio `geographic_matching_service.py` con validacion de coordenadas, radios y calculo de distancia.
- Resultado normalizado de cobertura: dentro, fuera o no verificable.
- Orden geografico inicial cuando la busqueda trae coordenadas.
- Fallback textual cuando no hay coordenadas validas.
- Distancia publica aproximada en cards compatibles.
- Pruebas unitarias con `unittest`.

## Archivos creados

- `app/services/geographic_matching_service.py`
- `tests/test_geographic_matching_service.py`
- `docs/SPRINTS/2026-07-15_Matching_Geografico_Distancia_v1.md`

## Archivos modificados

- `app/routes/main_routes.py`
- `app/routes/operation_routes.py`
- `app/templates/resultados.html`
- `app/templates/components/_professional_card.html`
- `app/templates/components/_emergency_professional_card.html`
- `app/static/css/professional-cards-v1.css`
- `app/static/css/emergency-directory-v1.css`
- `docs/CHANGELOG.md`
- `docs/ROADMAP.md`
- `docs/DECISIONES_ARQUITECTURA.md`
- `docs/BACKLOG.md`

## Rutas agregadas

- No se agregaron rutas nuevas.

## Migraciones realizadas

- No se agregaron migraciones. Se reutilizan coordenadas y radio de `Professional`.

## Formula utilizada

Se utiliza Haversine en backend con radio terrestre medio `6371.0088 km`.

Regla de cobertura:

`distancia_profesional_trabajo <= coverage_radius_km`

## Orden de resultados

Cuando hay coordenadas validas:

1. Dentro de cobertura.
2. PRO.
3. Verificado.
4. Rating.
5. Menor distancia.
6. Nombre.

En Emergencias queda reservado el criterio de guardia/disponibilidad para cuando exista un dato real.

## Privacidad

- No se exponen coordenadas profesionales en HTML publico.
- No se renderiza punto base profesional.
- Solo se muestra estado de cobertura y distancia aproximada.
- Las busquedas sin coordenadas no fuerzan geolocalizacion.

## Fallback textual

Si la solicitud no tiene coordenadas validas, se mantiene el matching actual por servicio, rubro y zona declarada.

## Validaciones ejecutadas

- `python -m compileall app scripts tests`
- `python -m unittest tests.test_geographic_matching_service` dentro de Docker.
- `git diff --check`
- Pruebas funcionales en Docker sobre `/resultados` y `/emergencias/directorio`.
- Validacion visual en navegador: desktop, mobile, tema claro, tema oscuro y ausencia de overflow horizontal.

## Capturas

- `C:/Users/Usuario/.codex/visualizations/2026/07/10/019f495b-0a05-7271-aaf8-b0014c25503a/geographic-matching-v1/resultados_matching_desktop_dark.png`
- `C:/Users/Usuario/.codex/visualizations/2026/07/10/019f495b-0a05-7271-aaf8-b0014c25503a/geographic-matching-v1/emergencias_matching_mobile_dark.png`

## Riesgos pendientes

- Haversine calcula distancia en linea recta, no rutas reales.
- No hay geocoding automatico de zonas textuales.
- No se implementan poligonos, multiples zonas ni PostGIS.

## Problemas encontrados

- El entorno host no tiene Flask instalado para ejecutar tests locales; las pruebas se ejecutaron dentro de Docker.

## Decisiones tomadas

- No integrar Google Distance Matrix, Routes API ni geocoding.
- No persistir coordenadas de solicitudes en esta fase.
- No agregar coordenadas profesionales en atributos publicos.

## Resultado final

TRAX cuenta con un motor inicial de matching geografico reutilizable, seguro y compatible con el fallback textual existente.

## Proximo Sprint recomendado

Agregar captura controlada de coordenadas de solicitudes o geocoding opt-in para mejorar el matching sin romper privacidad.
