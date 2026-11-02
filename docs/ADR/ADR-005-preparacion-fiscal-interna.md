# ADR-005 — Preparación fiscal interna separada de autorización

Timestamp: 2026-11-01T21:15:58-03:00.
Estado: decisión técnica local del incremento autorizado; pendiente de QA independiente.
Rama: `feature/professional-workspace-ux`; base `2e552f2`.

## Contexto

REQ-002 aprueba Factura C opcional para persona humana monotributista con PRO
vigente. Canal, inscripción, custodia y retención están pendientes. La solicitud
actual autoriza componentes internos y mantiene toda conexión deshabilitada.

## Decisión

Persistir declaraciones y borradores en tablas distintas de órdenes de cobro,
contratos, trabajos y futuros comprobantes autorizados. Ninguna fila de este
incremento puede tomar estado fiscal autorizado; constraints limitan estados a
`DECLARED_UNVERIFIED` y `INTERNAL_DRAFT`.

La política de acceso fiscal reutiliza `has_pro_access`, sin conceder beneficios.
Los servicios verifican actor activo persistido antes de escribir o resolver replay.
Toda consulta privada filtra dueño. Entidad y auditoría comparten transacción;
la capa llamadora decide commit/rollback. Auditoría registra identificadores y
acciones, nunca CUIT, domicilio, receptor ni descripción.

Un perfil por dueño, CUIT inmutable en el servicio, versión optimista y una clave
única por dueño/borrador limitan duplicaciones y escrituras concurrentes. El esquema
no define exclusión de numeración fiscal: no existen intentos externos todavía.

La inicialización solo registra modelos para mantener coherente metadata/Alembic.
No agrega rutas, servicios externos, flags, paquetes ni cambios comerciales.

## Consecuencias

La entrega es backend interno, sin captura pública de datos reales. Un borrador
puede estar incompleto y no es un snapshot confirmado. Debe diseñarse el snapshot
futuro antes de emitir, incluyendo emisor, receptor, contenido y vigencia.
La futura exclusión por emisor/ambiente/punto/tipo, numeración y reconciliación
requiere otro incremento y pruebas específicas. No reutilizar la clave de borrador
como si ya fuera un protocolo de idempotencia fiscal externo.

No se decide integración directa/intermediada, custodia, política de retención,
proveedor IA ni comisiones. ARS y los límites internos son la preparación propuesta,
sin fijar límites fiscales. La operación real sigue bloqueada por dependencias.

Detalle y evidencia: [FACTURACION-INTERNA-001](../REQUISITOS/FACTURACION_INTERNA_001.md).
