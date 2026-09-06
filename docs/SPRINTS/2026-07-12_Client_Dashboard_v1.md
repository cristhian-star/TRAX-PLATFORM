# Client Dashboard v1

## Objetivo

Crear el Dashboard del Cliente como centro de operaciones para entender el estado de sus solicitudes y contrataciones dentro de TRAX.

## Resumen

Se implemento una version inicial del Dashboard Cliente con datos reales existentes y placeholders cuando la cuenta todavia no tiene actividad suficiente.

## Cambios implementados

- Bienvenida con nombre del usuario, estado de cuenta, ultimo acceso y mensaje operativo.
- Centro de actividad con presupuestos, emergencias, propuestas, adjudicaciones y contrataciones.
- Resumen con indicadores de presupuestos activos, emergencias activas, propuestas activas, profesionales adjudicados e historial.
- Accesos rapidos a nuevo presupuesto, nueva emergencia, nueva propuesta, busqueda de profesionales y solicitudes.
- Seccion Mis Solicitudes con resumen de presupuestos, emergencias y propuestas.
- Recomendaciones operativas para completar los primeros pasos del cliente.
- Estado de cuenta con cantidad de solicitudes y ultima actividad.

## Archivos creados

- `app/static/css/client-dashboard-v1.css`
- `docs/SPRINTS/2026-07-12_Client_Dashboard_v1.md`

## Archivos modificados

- `app/routes/main_routes.py`
- `app/templates/cliente_dashboard.html`
- `docs/CHANGELOG.md`
- `docs/ROADMAP.md`
- `docs/DECISIONES_ARQUITECTURA.md`
- `docs/BACKLOG.md`

## Rutas agregadas

- No se agregaron rutas nuevas.
- Se completo la ruta existente `/cliente/dashboard`.

## Migraciones realizadas

- No se realizaron migraciones.

## Validaciones ejecutadas

- `python -m compileall app scripts` ejecutado correctamente.
- `git diff --check` ejecutado correctamente.
- Validacion visual ejecutada en Docker sobre `http://localhost:5000/cliente/dashboard`.
- Desktop claro, desktop oscuro y mobile oscuro sin overflow horizontal ni errores de consola.

## Riesgos pendientes

- No existe campo persistente de ultimo acceso del usuario; se muestra placeholder `No registrado`.
- No existe listado dedicado de emergencias del cliente; el dashboard enlaza al flujo disponible de emergencias.
- No existe vista consolidada de todas las solicitudes del cliente; se reutilizan rutas actuales por modulo.

## Problemas encontrados

- Las contrataciones utilizan la ruta existente `/contratacion/<id>`, por lo que se evito crear una ruta nueva.

## Decisiones tomadas

- El Dashboard Cliente se mantiene como tablero operativo y no incorpora edicion de perfil ni configuracion personal.
- La UI consume Design System v2 y mantiene identidad visual compatible con Dashboard Profesional.

## Resultado final

Dashboard Cliente v1 implementado como centro de operaciones con datos reales, placeholders y layout responsive.

## Proximo Sprint recomendado

Crear vista consolidada de solicitudes del cliente con presupuestos, emergencias y propuestas en un unico historial filtrable.
