# Registros de decisiones de arquitectura

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

- [REQ-004](../REQUISITOS/REQ-004-emergencias-guardia-vigente.md): APROBADO COMO ESPECIFICACIÓN; implementación PENDIENTE.
- [ADR-002](ADR-002-emergencias-guardia-vigente.md): PROPUESTO / PENDIENTE DE DECISIÓN ARQUITECTÓNICA.

Los ADR conservan decisiones tecnicas de alto impacto y el razonamiento que las
sostiene. No reemplazan el registro historico existente en
[`DECISIONES_ARQUITECTURA.md`](../DECISIONES_ARQUITECTURA.md); lo complementan
cuando una decision necesita analisis independiente y trazabilidad detallada.

Usar la plantilla [Decision de arquitectura](../PLANTILLAS/DECISION_ARQUITECTURA.md).

## Decisiones vigentes

- [ADR-001 - Nucleo calculado de entitlement PRO](ADR-001-pro-entitlement-foundation.md)

## Decisión propuesta — UX-07A

Registro: `2026-09-27T23:14:25-03:00`. Responsable de Producto: Cristian Sánchez; redacción: Codex, laptop MANDOBRA.
Rama: `feature/ux-ui-foundation`. HEAD: `4489c5c208245368a2a9bfd1672a261cf3004c93`.
Motivo: formalizar el preflight UX-07A aprobado y la decisión de Producto de
`2026-09-27T23:03:15-03:00`, `APROBADO PARA ESPECIFICACIÓN`.
Estado: especificación para revisión; implementación PENDIENTE. El preflight es el
antecedente de inspección del chat, no evidencia de guardias implementadas.
Orden neutral: PRO no habilita ni prioriza Emergencias; verificación es filtro obligatorio,
no privilegio adicional de orden. Próximo paso: revisar REQ-004/ADR-002 y autorizar
UX-07A.1; UX-07A.2 depende de su verificación.


- [ADR-002 — Emergencias y guardia vigente](ADR-002-emergencias-guardia-vigente.md): PROPUESTO, implementación pendiente.
- Contrato: [REQ-004](../REQUISITOS/REQ-004-emergencias-guardia-vigente.md), pendiente de revisión documental.

La aprobación de Producto para especificación no significa aceptación de todas las
soluciones técnicas propuestas ni autorización para migrar o implementar.
