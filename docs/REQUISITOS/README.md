# Requisitos

Esta carpeta contiene requisitos funcionales y no funcionales aprobados de
MANDOBRA. Cada requisito debe definir alcance, exclusiones, reglas de negocio y
criterios de aceptacion verificables.

La linea base vigente esta en [MANDOBRA Master Spec](MASTER_SPEC.md).

## Requisitos aprobados

- [REQ-001 - Activacion y vigencia de MANDOBRA PRO](REQ-001-activacion-y-vigencia-pro.md)
  - Estado: `APROBADO`.
  - Implementacion: `IMPLEMENTACION_PARCIAL`; Foundation integrada, PSP,
    creditos, cobros y suscripciones comerciales pendientes.
- [REQ-002 - Facturacion MANDOBRA PRO MVP](REQ-002-facturacion-pro-mvp.md)
  - Estado: `APROBADO`.
  - Implementacion: `PENDIENTE`.
- [REQ-003 - Creacion de ordenes de cobro Checkout Pro](REQ-003-creacion-de-ordenes-de-cobro-checkout-pro.md)
  - Estado: `APROBADO`.
  - Implementacion productiva completa: `PENDIENTE`.
  - Avance técnico parcial implementado y probado: contrato puro y adaptador
    determinista en memoria.

## Actualización posterior de REQ-003 - incremento 4A

Timestamp: 2026-09-16T22:40:04-03:00
Agente: 01 - Documentation Engineer
Motivo: registrar avance técnico interno aprobado localmente en `4373b64`.
REQ-003 mantiene `APROBADO` e implementación productiva `PENDIENTE`.
Se agregó persistencia durable independiente `PaymentOrder`, ciclo local,
auditoría y garantías PostgreSQL; migración/head único `20260916_01`.
El próximo paso es 4B: aplicación y ownership contractual sin Mercado Pago real.
PSP real, experiencia de usuario, correlación de pagos, efectos financieros,
publicación, PR, merge y producción continúan pendientes.
Detalle: [REQ-003](REQ-003-creacion-de-ordenes-de-cobro-checkout-pro.md#actualización-posterior---incremento-técnico-4a).

## Borradores activos

- [Planes, reputacion, guardias y contratacion](BORRADOR_PLANES_REPUTACION_GUARDIAS_CONTRATACION.md)

Los borradores pueden vivir aqui si estan marcados expresamente como
`BORRADOR`. Una idea del segundo cerebro no se considera requisito hasta quedar
formalizada y aprobada en esta carpeta.

Usar la plantilla [Requisito](../PLANTILLAS/REQUISITO.md).
