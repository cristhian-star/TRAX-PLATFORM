# ADR-004 — Registro privado independiente del contrato

Fecha: 2026-10-30T15:48:41-03:00. Estado: decisión de implementación autorizada por el encargo
MIS-TRABAJOS-UX-001; pendiente de revisión independiente. Responsable: agente local.

## Contexto

El profesional necesita documentar también trabajos externos, sin inventar cuentas ni
contratos y sin convertir notas en estados canónicos. Mis trabajos ya mostraba contratos.

## Decisión

Persistir WorkRecord (propietario/versión), WorkFollowup (uno vigente) y WorkReminder
(historial de programación). Reutilizar OperationCommand, AuditLog y notificaciones.
Contrato opcional únicamente para verificar la contraparte de un recordatorio al cliente.
Ningún cambio de estado contractual deriva de guardar, editar o notificar un registro.
El listado privado ocupa la entrada Mis trabajos y ofrece acceso secundario a contratados.

Locks compartidos por propietario y versiones coordinan edición/despacho; cada notificación
se confirma con su resultado en una misma transacción. Ejecutor periódico explícito,
independiente del navegador, sin nuevo proveedor ni dependencia. IANA Buenos Aires/UTC
conforme al proyecto. Detalles, límites y operación: [MIS-TRABAJOS-UX-001](../REQUISITOS/MIS_TRABAJOS_UX_001.md).

## Alternativas y consecuencias

Reutilizar ContractRequest para trabajos externos requeriría contrapartes/estados ficticios:
se descarta. Sesión/localStorage no ofrecen persistencia ni atomicidad: se descartan.
Tres tablas requieren migración y operación del ejecutor; serializar por profesional reduce
paralelismo entre sus registros, a cambio de un orden de locks simple y comprobable.
Downgrade pierde registros/seguimientos/programación nuevos; notificaciones ya emitidas
permanecen. No amplía reputación, pagos ni permisos. No habilita producción automáticamente.
