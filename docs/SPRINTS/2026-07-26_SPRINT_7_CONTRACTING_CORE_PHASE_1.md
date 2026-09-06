# SPRINT 7 - Contracting Core Phase 1

## Objetivo

Convertir `ContractRequest` en el nucleo canonico comun de contratacion para TRAX, conectando presupuestos adjudicados y postulaciones aceptadas sin fusionar los dominios de Presupuestos y Propuestas.

## Decisiones

- Refactorizar `ContractRequest`; no crear un segundo modelo `Contract`.
- Crear contratos derivados en estado `CREADA`.
- Mantener aceptacion/rechazo posterior por parte del profesional.
- Hacer idempotente la creacion desde `BudgetOffer` y `ProposalApplication`.
- Evitar efectos duplicados en reintentos: no se regeneran eventos, auditorias ni notificaciones si el contrato ya existe.
- Aplicar `hiring_mode = SINGLE` en Propuestas: una postulacion aceptada cierra la propuesta y descarta otras postulaciones activas.
- Mantener fuera de alcance pagos, ARCA, facturacion, hitos, evidencias, disputas, negociacion avanzada, MCP e IA.

## Modelos

- `ContractRequest`: agrega `source_type`, `source_id`, `budget_offer_id`, `proposal_application_id` y `created_from_event`.
- `ContractEvent`: historial transaccional del contrato.
- `BudgetRequest`: corrige estados canonicos e incorpora `CANCELADA`.
- `ProposalRequest`: agrega `hiring_mode` con valor inicial `SINGLE`.
- `AuditLog`: agrega campos de correlacion con contrato, evento e idempotencia.

## Migracion

- `20260726_01_sprint7_contracting_core`.
- Agrega campos de origen a `contract_requests`.
- Crea tabla `contract_events`.
- Asigna `DIRECT` a contratos legacy.
- Agrega indices y restricciones unicas para origen presupuesto/propuesta.
- Agrega checks de consistencia para `source_type`, `source_id`, `budget_offer_id` y `proposal_application_id`.
- Normaliza presupuestos legacy `CERRADO` a `CERRADA`.
- Bloquea downgrade si existen eventos de contrato o contratos derivados que puedan perder trazabilidad.

## Servicios

- `contracting_core_service.py` centraliza creacion desde presupuesto y propuesta.
- `contract_service.py` mantiene contratacion directa y registra eventos de transicion.
- `budget_service.py` crea contrato al adjudicar oferta.
- `proposal_service.py` crea contrato al aceptar postulacion.

## Flujo Presupuesto A Contrato

1. Cliente adjudica `BudgetOffer`.
2. Se marca oferta como `ADJUDICADO`.
3. Se marca solicitud como `ADJUDICADA`.
4. Se crea `ContractRequest` con `source_type = BUDGET`.
5. Se registran `ContractEvent`, `AuditLog` y notificaciones.
6. Un reintento sobre la misma oferta devuelve el contrato existente sin duplicar efectos.

## Flujo Propuesta A Contrato

1. Publicador acepta `ProposalApplication`.
2. Se marca postulacion como `ACEPTADA`.
3. Se crea `ContractRequest` con `source_type = PROPOSAL`.
4. Se registran `ContractEvent`, `AuditLog` y notificaciones.
5. En modo `SINGLE`, se cierra la propuesta y se descartan otras postulaciones activas.
6. Un reintento sobre la misma postulacion devuelve el contrato existente sin duplicar efectos.

## Eventos

- `CONTRACT_CREATED`.
- `CREATED_FROM_BUDGET`.
- `CREATED_FROM_PROPOSAL`.
- `CONTRACT_ACCEPTED`.
- `CONTRACT_REJECTED`.
- `CONTRACT_STARTED`.
- `CONTRACT_COMPLETED`.
- `CONTRACT_CONFIRMED`.
- `CONTRACT_CANCELLED`.

## Pruebas

Se agregaron:

- `tests/test_sprint7_contracting_core.py`.
- `tests/test_sprint7_budget_to_contract.py`.
- `tests/test_sprint7_proposal_to_contract.py`.

Cobertura:

- Idempotencia por origen.
- Referencias a `BudgetOffer` y `ProposalApplication`.
- Ownership.
- Contratacion directa legacy.
- Eventos, auditoria y notificaciones.
- Ausencia de eventos, auditorias y notificaciones duplicadas en reintentos.
- Rollback si falla la creacion del contrato derivado.
- Politica `SINGLE` de Propuestas.
- Metadatos cerrados sin payload arbitrario.
- Aceptacion posterior del contrato.
- Transiciones invalidas.

## Deuda Pendiente

- Vincular reviews y reputacion a contrato.
- Definir negociacion y contraofertas.
- Definir si se habilitara `hiring_mode = MULTIPLE` y bajo que reglas.
- Definir cancelaciones con motivo y actor.
- Modelar hitos, evidencias, disputas y modificaciones.
- Preparar facturacion TRAX Pro sin integrar ARCA.
- Reemplazar `Query.get()` y `datetime.utcnow()`.

## Resultado Final

TRAX cuenta con una primera version del nucleo canonico de contratacion. Presupuestos y Propuestas siguen separados, pero ambos pueden producir una contratacion comun y auditable.

## Proximo Sprint Recomendado

Sprint 7 Fase 2: negociacion basica, politica de cierre/multiples contrataciones y trazabilidad de reviews/reputacion por contrato.
