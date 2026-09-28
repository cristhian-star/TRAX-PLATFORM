# Requisitos

## Cierre de revisión documental UX-07A — 2026-09-28

Registro: `2026-09-28T19:42:16-03:00`. Dictamen: `2026-09-28T19:31:39-03:00`.
Responsable de Producto: Cristian Sánchez. Revisor: agente documental local.
Estado: APROBADO COMO ESPECIFICACIÓN. Hallazgos: P0: 0; P1: 0; P2: 0; P3: 0.
Implementación: PENDIENTE. Pruebas técnicas y funcionales: PENDIENTES.
ADR-002: PROPUESTO / PENDIENTE DE DECISIÓN ARQUITECTÓNICA; no aceptado ni implementado.
UX-07A.1 permanece pendiente de aprobación arquitectónica y autorización de implementación.
UX-07A.2 depende de UX-07A.1 implementado y verificado antes de afirmar disponibilidad.
Próximo paso: decidir ADR-002 y preparar el paquete UX-07A.1. Ninguna implementación iniciada.
Este cierre aprueba la especificación documental; no acredita implementación ni pruebas
funcionales, ni acepta las soluciones técnicas propuestas. Los 27 criterios se conservan.
Los registros fechados anteriores mantienen su estado histórico; este cierre expresa el vigente.

- [REQ-004](REQ-004-emergencias-guardia-vigente.md): APROBADO COMO ESPECIFICACIÓN; implementación PENDIENTE.
- [ADR-002](../ADR/ADR-002-emergencias-guardia-vigente.md): PROPUESTO / PENDIENTE DE DECISIÓN ARQUITECTÓNICA.

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

## Requisito en especificación — UX-07A

Registro: `2026-09-27T23:14:25-03:00`. Responsable de Producto: Cristian Sánchez; redacción: Codex, laptop MANDOBRA.
Rama: `feature/ux-ui-foundation`. HEAD: `4489c5c208245368a2a9bfd1672a261cf3004c93`.
Motivo: formalizar el preflight UX-07A aprobado y la decisión de Producto de
`2026-09-27T23:03:15-03:00`, `APROBADO PARA ESPECIFICACIÓN`.
Estado: especificación para revisión; implementación PENDIENTE. El preflight es el
antecedente de inspección del chat, no evidencia de guardias implementadas.
Orden neutral: PRO no habilita ni prioriza Emergencias; verificación es filtro obligatorio,
no privilegio adicional de orden. Próximo paso: revisar REQ-004/ADR-002 y autorizar
UX-07A.1; UX-07A.2 depende de su verificación.


- [REQ-004 — Emergencias y guardia vigente](REQ-004-emergencias-guardia-vigente.md).
  Estado documental BORRADOR PARA REVISIÓN. Producto APROBADO PARA ESPECIFICACIÓN;
  implementación PENDIENTE. Dos paquetes: .1 guardia/matching/seguridad y .2 experiencia
  visual dependiente. Los detalles técnicos propuestos no se listan como aprobados.
- [ADR-002 propuesto](../ADR/ADR-002-emergencias-guardia-vigente.md).
