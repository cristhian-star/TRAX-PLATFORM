# Incremento PRO entitlement foundation

Timestamp: 2026-09-04T09:56:46-03:00
Estado: IMPLEMENTACION_PARCIAL_VALIDADA
Rama: `feature/pro-entitlement-foundation`
Commit base: `18e46fd6bf6d05b73884b7ba3fdbb335f66d7d7e`

## Objetivo

Implementar la primera fase de REQ-001 sin PSP ni proveedores: evaluacion
calculada, fuentes reconocidas, vencimiento obligatorio, UTC, bloqueo de
concesiones manuales y un unico usuario PRO en el seed QA local.

## Implementado

- `Subscription.source_type` nullable con TRANSACTIONAL y SUBSCRIPTION.
- `has_pro_access()` exige profesional activo, verificacion aprobada, PRO
  ACTIVA, fuente reconocida y `expires_at` futuro.
- Registros legacy y ENTERPRISE no conceden acceso.
- Rutas y UI ya no activan PRO por puntos, verificacion o administracion.
- Seed QA idempotente con un unico entitlement demo valido.

## Fuera de alcance

PSP, cobros, prueba transaccional, extensiones, suscripciones comerciales,
webhooks, Facturacion, ARCA, IA y ENTERPRISE operativo.

## Validacion

- Baseline previo: 266 tests, 261 aprobados, 5 omitidos, 0 fallidos.
- Pruebas focalizadas finales: 14/14.
- Gate PostgreSQL exclusivo: 1/1, con upgrade/downgrade/re-upgrade.
- Suite final: 280 ejecutados, 275 aprobados, 5 omitidos y 0 fallidos.
- `compileall`, `alembic heads` y `git diff --check`: aprobados al cierre.

## Correcciones posteriores a auditoria

Timestamp: 2026-09-04T10:29:16-03:00

- La revocacion se restringio a fuentes PRO reconocidas y todavia vigentes, y
  ahora se confirma atomicamente junto con su auditoria.
- El gate PostgreSQL exige una base `trax_pro_entitlement_test` o con ese
  prefijo antes de crear el engine o ejecutar migraciones.
- El seed conserva `expires_at` mientras la fuente QA siga vigente y reutiliza
  la misma fila al renovarla una vez vencida. Los 365 dias son datos sinteticos
  de QA, no una regla comercial.
- El downgrade es solo estructuralmente reversible: pierde la clasificacion de
  `source_type`, que vuelve como NULL tras un re-upgrade.
- Validacion posterior: 20/20 pruebas focalizadas; suite completa de 286 tests,
  281 aprobados, 5 omitidos y 0 fallidos; gate PostgreSQL 1/1.
- Durante el cierre se observaron dos fallos intermitentes de aislamiento por
  orden; ambos pasaron aislados y la corrida final completa fue satisfactoria.

## Cierre focal del guard PostgreSQL

Timestamp: 2026-09-04T13:19:30-03:00

- El nombre descartable se valida con `fullmatch()` contra
  `^trax_pro_entitlement_test(?:_[a-z0-9]+(?:_[a-z0-9]+)*)?$`, sin parametros
  y con un maximo de 63 bytes.
- Nombres invalidos se rechazan antes de `create_engine()` y antes de upgrade,
  downgrade o limpieza.
- Tests del guard: 5 ejecutados, 5 aprobados, 0 fallidos, 0 omitidos.
- Suite focal PRO: 21 ejecutados, 21 aprobados, 0 fallidos, 0 omitidos.
- Suite completa: 287 ejecutados, 282 aprobados, 0 fallidos, 5 omitidos.
- Gate PostgreSQL real: 1 ejecutado, 1 aprobado, 0 fallidos, 0 omitidos sobre
  `trax_pro_entitlement_test_finalaudit_20260904`.
- `compileall`, Alembic head `20260904_01` y `git diff --check`: PASS.
- El P1 del guard queda cerrado. REQ-001 permanece en implementacion parcial.
