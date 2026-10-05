# Centro documental de MANDOBRA

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

- [REQ-004](REQUISITOS/REQ-004-emergencias-guardia-vigente.md): APROBADO COMO ESPECIFICACIÓN; implementación PENDIENTE.
- [ADR-002](ADR/ADR-002-emergencias-guardia-vigente.md): PROPUESTO / PENDIENTE DE DECISIÓN ARQUITECTÓNICA.

Esta carpeta es la fuente documental canonica del proyecto MANDOBRA y puede
abrirse directamente como una boveda de Obsidian.

## Como interpretar la informacion

La prioridad de las fuentes es:

1. Codigo, migraciones y pruebas ejecutables.
2. Requisitos aprobados y decisiones vigentes.
3. Documentacion operativa y tecnica validada.
4. Documentos de sprint e historial.
5. Ideas, borradores e investigacion aun no aprobada.

Si un documento contradice al codigo o a una migracion aplicada, no debe
corregirse silenciosamente: se registra la inconsistencia y se determina cual
de las dos partes debe cambiar.

## Navegacion principal

### Producto y alcance

- [Master Spec](REQUISITOS/MASTER_SPEC.md)
- [Roadmap](ROADMAP.md)
- [Backlog](BACKLOG.md)
- [Taxonomia del producto](trax-taxonomy-v1.md)
- [Requisitos](REQUISITOS/README.md)
- [REQ-001 - Activacion y vigencia de MANDOBRA PRO](REQUISITOS/REQ-001-activacion-y-vigencia-pro.md)
- [REQ-002 - Facturacion MANDOBRA PRO MVP](REQUISITOS/REQ-002-facturacion-pro-mvp.md)
- [REQ-003 - Creacion de ordenes de cobro Checkout Pro](REQUISITOS/REQ-003-creacion-de-ordenes-de-cobro-checkout-pro.md)

### Refinamiento comercial y consultas externas

- [Plan documental y tres sprints PRO](SPRINTS/2026-09-06_PRO_REFINAMIENTO_COMERCIAL_Y_PSP.md)
- [Consultas tecnicas y comerciales a Mercado Pago](CONSULTAS/MERCADO_PAGO_v0_1.md)
- [Base comercial para revision juridica y contable](LEGAL/BASE_REVISION_JURIDICA_v0_2.md)

### Estado documental

- [Auditoria documental del 2026-08-31](AUDITORIA_DOCUMENTAL_2026-08-31.md)
- [Auditoria tecnica del 2026-09-02](AUDITORIA_TECNICA_2026-09-02.md)

### Arquitectura y datos

- [Decisiones de arquitectura](DECISIONES_ARQUITECTURA.md)
- [ADR individuales](ADR/README.md)
- [ADR-001 - Nucleo calculado de entitlement PRO](ADR/ADR-001-pro-entitlement-foundation.md)
- [Alembic](alembic.md)
- [PostgreSQL de desarrollo](postgres_dev.md)

### Desarrollo y calidad

- [Estandares de desarrollo](ESTANDARES_DESARROLLO.md)
- [QA local](QA_LOCAL.md)
- [Handoffs tecnicos](HANDOFFS/README.md)
- [Troubleshooting](TROUBLESHOOTING/README.md)
- [Runbooks](RUNBOOKS/README.md)

### Experiencia visual

- [Design System v2](DESIGN_SYSTEM_V2.md)
- [Design System v1](design-system-v1.md)

### Historia del proyecto

- [Changelog](CHANGELOG.md)
- [Documentacion de sprints](SPRINTS/)
- [Incremento PRO entitlement foundation](SPRINTS/2026-09-04_PRO_ENTITLEMENT_FOUNDATION.md)
- [Refinamiento comercial, PSP y tres sprints](SPRINTS/2026-09-06_PRO_REFINAMIENTO_COMERCIAL_Y_PSP.md)

### Reglas y plantillas

- [Guia de documentacion](GUIA_DOCUMENTACION.md)
- [Plantillas](PLANTILLAS/README.md)

## Separacion respecto del segundo cerebro

`docs/` contiene conocimiento especifico, vigente y verificable de MANDOBRA.
El segundo cerebro personal puede conservar ideas, aprendizaje e investigacion
transversal. Cuando una idea sea aprobada para MANDOBRA, debe formalizarse aqui
como requisito, decision, riesgo o tarea.

## Seguridad

No se almacenan contrasenas, tokens, claves privadas, archivos `.env`, datos
personales reales ni volcados de bases de datos en esta boveda.

## UX-07A — Especificación pendiente de revisión

Registro: `2026-09-27T23:14:25-03:00`. Responsable de Producto: Cristian Sánchez; redacción: Codex, laptop MANDOBRA.
Rama: `feature/ux-ui-foundation`. HEAD: `4489c5c208245368a2a9bfd1672a261cf3004c93`.
Motivo: formalizar el preflight UX-07A aprobado y la decisión de Producto de
`2026-09-27T23:03:15-03:00`, `APROBADO PARA ESPECIFICACIÓN`.
Estado: especificación para revisión; implementación PENDIENTE. El preflight es el
antecedente de inspección del chat, no evidencia de guardias implementadas.
Orden neutral: PRO no habilita ni prioriza Emergencias; verificación es filtro obligatorio,
no privilegio adicional de orden. Próximo paso: revisar REQ-004/ADR-002 y autorizar
UX-07A.1; UX-07A.2 depende de su verificación.


- [REQ-004 — Emergencias y guardia vigente](REQUISITOS/REQ-004-emergencias-guardia-vigente.md): BORRADOR, Producto aprobado para especificación; implementación pendiente.
- [ADR-002 — Emergencias y guardia vigente](ADR/ADR-002-emergencias-guardia-vigente.md): PROPUESTO.
- [Handoff](HANDOFFS/ACTIVE_HANDOFF.md): continuidad documental y próximos gates .1/.2.
