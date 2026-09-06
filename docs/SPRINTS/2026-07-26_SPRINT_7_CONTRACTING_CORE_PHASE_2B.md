# Sprint 7 - Contracting Core Fase 2B

## Objetivo

Incorporar una negociación formal opcional, limitada a contratación directa, sin reemplazar el contacto simple ni los flujos históricos de presupuesto y propuesta.

## Resultado canónico

- `ContractNegotiation` representa el agregado precontractual.
- Cada cambio crea un snapshot inmutable `ContractNegotiationVersion` con hash canónico.
- Cliente y profesional aceptan expresamente la misma versión vigente.
- Sólo el cliente materializa el contrato cuando ambas aceptaciones son coherentes.
- La materialización crea un `ContractRequest` en `CREADA` y pasa la negociación a `CONTRACTED` en una única transacción.
- Actor, ownership, versión e idempotencia se validan dentro del servicio antes del replay.
- Las aceptaciones se protegen con identidad real de las partes, FK compuesta y triggers PostgreSQL.

## Estados

`OPEN`, `AGREED`, `CANCELLED`, `REJECTED`, `CONTRACTED`.

## Alcance y exclusiones

La fase conserva `contracting_mode = EXTERNAL` y `hiring_mode = SINGLE`. No incluye negociación desde presupuesto o propuesta, retiro de aceptaciones, expiración automática, chat libre, pagos, garantías ni disputas.

## Migraciones y validación

- `20260726_04`: negociación directa MVP.
- `20260726_05`: inmutabilidad de snapshots y coherencia de aceptaciones.
- PostgreSQL 16.14: gate final 8/8 con dos conexiones independientes, propuestas concurrentes, aceptaciones, finalización, rollback y downgrade seguro.

## Deuda no bloqueante

- Sustituir APIs SQLAlchemy legacy y timestamps deprecated.
- Diseñar cualquier ampliación precontractual como una fase futura independiente.
