# Sprint 7 - Contracting Core - Fase 2A

## Objetivo

Fase 2A consolida las fundaciones transversales del nucleo contractual sin implementar negociacion, contratacion multiple, cancelacion consensuada, reviews contractuales ni reputacion derivada.

## Estado contractual

Flujo exitoso:

`CREADA -> ACEPTADA -> EN_PROGRESO -> COMPLETADA -> CONFIRMADA`

Semantica:

- `COMPLETADA`: el profesional declara que termino el trabajo.
- `CONFIRMADA`: el cliente confirma expresamente la finalizacion.
- `CONFIRMADA`: estado terminal exitoso.
- `CERRADA`: valor contractual legacy migrado a `CONFIRMADA`.

Estados terminales:

- `CONFIRMADA`;
- `RECHAZADA`;
- `CANCELADA`.

La matriz tambien reserva `CORRECCION_SOLICITADA`, pero Fase 2A no expone una operacion para solicitar correcciones.

## Modalidades

`ContractRequest.contracting_mode` describe la modalidad legal. En esta fase:

- es obligatorio;
- solo admite `EXTERNAL`;
- no activa pagos, garantias ni comportamiento protegido.

`ProposalRequest.hiring_mode` conserva otro significado:

- cantidad de profesionales contratables;
- `SINGLE` permanece como unica modalidad implementada;
- un check de base de datos impide persistir cualquier otro valor;
- `MULTIPLE` se difiere a Fase 2C.

## Servicio canonico

Las operaciones habilitadas son:

- `accept_contract`;
- `reject_contract`;
- `start_contract`;
- `declare_work_completed`;
- `confirm_completion`.

`complete_contract` y `confirm_contract` se conservan como aliases explicitos de compatibilidad. No aceptan un estado destino.

La cancelacion simple heredada permanece encapsulada como `CANCEL_CONTRACT_LEGACY`; no constituye el futuro flujo consensuado.

El mutador generico `update_contract_status` fue retirado.

## Ownership y RBAC

- El profesional asignado y con rol `PROFESIONAL` puede aceptar, rechazar, iniciar y declarar completado.
- El cliente owner y con rol `CLIENTE` puede confirmar.
- El rol sin ownership no habilita la operacion.
- Administradores no ejecutan operaciones ordinarias por las partes.
- La autorizacion se valida nuevamente dentro del servicio.
- Las creaciones desde presupuesto y propuesta cargan al actor activo desde la
  base de datos y autorizan al owner antes de resolver cualquier replay.

## Idempotencia

`OperationCommand` registra:

- actor;
- operacion;
- idempotency key;
- hash del payload;
- estado;
- resultado;
- correlacion;
- timestamps y fallo.

La unicidad es actor + operacion + key.

- Misma key y payload devuelve el resultado confirmado.
- Misma key y payload diferente produce conflicto.
- Un comando en `PROCESSING` produce conflicto reintentable.
- Un fallo transaccional revierte tambien el comando.

## Correlacion y payloads

`OperationCommand`, `ContractEvent`, `AuditLog` y `ActivityNotification` comparten `correlation_id`.

`ContractEvent` tiene secuencia unica por contrato e idempotency key unica cuando existe. Los payloads se construyen con campos permitidos; no se copian diccionarios arbitrarios ni datos sensibles.

Las correlaciones historicas que no pueden demostrarse permanecen nulas.

## Transaccion y concurrencia

La unidad transaccional contiene:

1. comando;
2. lock del contrato;
3. validacion de estado, actor y version;
4. mutacion e incremento de version;
5. evento;
6. auditoria;
7. notificacion interna;
8. resultado idempotente;
9. commit unico.

Las operaciones usan `SELECT FOR UPDATE`. Una version desactualizada produce conflicto y no sobrescribe el agregado.

Las creaciones derivadas bloquean su entidad fuente, vuelven a consultar el
contrato luego del lock y usan un savepoint para recuperar una colision unica
sin invalidar la transaccion externa. No realizan commits internos.

## Notificaciones

El unico canal es `INTERNAL`. Cada notificacion contractual nueva referencia su evento causal y tiene unicidad por destinatario, evento, template y canal.

No se implemento envio externo. Los campos agregados permiten sumar una outbox futura sin usar la notificacion como fuente de verdad.

## Migracion

La revision `20260726_02`:

- agrega columnas en forma compatible;
- completa `EXTERNAL` y version 1;
- migra contratos `CERRADA` a `CONFIRMADA`;
- deriva secuencias historicas ordenando por contrato, fecha e ID;
- no inventa correlation IDs historicos;
- crea constraints e indices al final;
- inspecciona y repara por separado columnas, nulabilidad, foreign key, check,
  unique e indices de una `operation_commands` parcial;
- en PostgreSQL valida identity/default de `operation_commands.id`, existencia,
  ownership y permisos de la secuencia, y su valor respecto de `MAX(id)`;
- valida ademas incremento positivo y ascendente, `NO CYCLE`, limites
  compatibles con `INTEGER`, proximo valor efectivo y uso no compartido;
- crea o repara un generador propio determinista cuando es seguro, sin apropiarse
  de secuencias ajenas, y demuestra insercion sin ID despues de la reparacion;
- bloquea antes de otras mutaciones Fase 2A cuando el esquema o sus datos no
  pueden repararse en forma segura;
- bloquea downgrade ante datos Fase 2A no representables.

La revision `20260726_03`:

- rechaza la migracion si encuentra un `hiring_mode` no nulo distinto de
  `SINGLE`;
- completa valores nulos con `SINGLE`;
- agrega el check fisico que mantiene `MULTIPLE` bloqueado hasta Fase 2C.

## Validacion

La cobertura incluye:

- matriz y terminales;
- ownership y rol;
- idempotencia y replay;
- payload conflictivo;
- version desactualizada;
- rollback en cada punto interno;
- correlacion completa;
- secuencia de eventos;
- frontera cerrada de eventos: no existe un helper generico publico y las
  creaciones derivadas emiten evento, auditoria y notificacion en conjunto;
- checks y uniques sobre SQLite;
- compatibilidad con pruebas de Fase 1.

La validacion PostgreSQL descartable del 2026-07-26 uso PostgreSQL 16.14:

- 8/8 escenarios E2E de concurrencia mediante servicios reales;
- dos conexiones y sesiones independientes, con backend PID distintos;
- 4/4 pruebas PostgreSQL legacy;
- 21/21 escenarios compatibles de migracion parcial, incluidos generadores
  ausentes, descendentes, ciclicos, desfasados, agotados, compartidos,
  incompatibles y ciclos de downgrade/upgrade;
- upgrade desde vacio y ciclo downgrade a Fase 1 / upgrade a head;
- 58 pruebas Sprint 7 con PostgreSQL habilitado, con una unica omision
  correspondiente al caso deliberadamente no reproducible en SQLite.

La suite critica `tests/postgresql_contracting_concurrency_e2e.py` no forma
parte del discovery SQLite. CI debe ejecutarla obligatoriamente contra una base
PostgreSQL descartable, migrada por la propia suite. Una ejecucion de la suite
general no reemplaza este gate.

La matriz destructiva de esquemas parciales PostgreSQL tambien es un gate
obligatorio separado:

`.\.venv\Scripts\python.exe tests\postgresql_operation_command_migration_partial.py`

## Deuda diferida

- Fase 2B: negociacion.
- Fase 2C: `MULTIPLE`.
- Fase 2D: correcciones y cancelacion consensuada.
- Fase 2E: reviews contractuales.
- Fase 2F: reputacion derivada y outbox si se habilitan canales externos.
- Reemplazo general de `Query.get()` y timestamps naive legacy.
