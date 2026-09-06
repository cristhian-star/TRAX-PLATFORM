# ADR-001 - Nucleo calculado de entitlement PRO

Timestamp: 2026-09-04T09:56:46-03:00
Estado: ACEPTADA_IMPLEMENTACION_PARCIAL
Rama: `feature/pro-entitlement-foundation`
Commit base: `18e46fd6bf6d05b73884b7ba3fdbb335f66d7d7e`

## Contexto

El lector legacy concedia capacidades por una fila activa PRO o ENTERPRISE, sin
validar rol, estado de cuenta, verificacion, fuente ni vencimiento. Las rutas
tambien permitian nuevas concesiones por puntos, verificacion o administracion.

## Decision

El entitlement se calcula en `has_pro_access()` y requiere simultaneamente:
usuario PROFESIONAL ACTIVO, verificacion PROFESIONAL APROBADA y una fila PRO
ACTIVA con `source_type` TRANSACTIONAL o SUBSCRIPTION y `expires_at` posterior
al instante UTC evaluado.

Se reutiliza `Subscription` incrementalmente. `source_type=NULL` conserva la
evidencia legacy pero nunca concede acceso. ENTERPRISE sigue persistible por
compatibilidad y no habilita capacidades. La frontera con columnas `DateTime`
legacy normaliza timestamps aware a UTC naive en un unico helper documentado.

Las concesiones manuales quedan deshabilitadas. El unico usuario QA PRO se crea
mediante el seed bloqueado en production/prod, con una fila SUBSCRIPTION
temporal, y atraviesa el mismo evaluador productivo sin excepciones por email o
ID.

## Alternativas consideradas

- Crear un modelo nuevo: descartado en este incremento por duplicar
  persistencia antes de definir PSP y eventos comerciales.
- Convertir filas legacy: descartado porque inventaria una fuente valida.
- Crear fuentes QA, ADMINISTRATIVE o LEGACY: descartado para evitar permisos no
  aprobados.
- Mantener activacion por puntos o verificacion: descartado por contradecir
  REQ-001.

## Consecuencias

- Los accesos legacy se reevaluan inmediatamente y pasan funcionalmente a FREE.
- Toda fuente valida debe vencer; el instante exacto de expiracion ya no concede.
- PSP, prueba, extensiones, pagos y renovaciones siguen pendientes.
- La migracion `20260904_01` agrega el discriminador nullable y su constraint.

## Correccion posterior a revision tecnica

Timestamp: 2026-09-04T10:29:16-03:00

- La frontera temporal PRO usa UTC aware para representar instantes y convierte
  mediante un helper unico a UTC naive al persistir o consultar columnas
  legacy `DateTime` sin zona horaria.
- La revocacion solo selecciona fuentes PRO reconocidas, activas, no nulas y
  vigentes; la mutacion y su auditoria se confirman en una unica transaccion.
- El downgrade es reversible estructuralmente, pero no respecto de los valores
  `TRANSACTIONAL` y `SUBSCRIPTION`: eliminar `source_type` pierde esa
  clasificacion y un re-upgrade devuelve las filas con `source_type=NULL`.
- No debe ejecutarse ese downgrade sobre datos cuya clasificacion deba
  conservarse sin respaldo y autorizacion explicita.
