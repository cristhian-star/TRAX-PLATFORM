# Sprint 7 - Contractual Trust Fases 2E-2F

## Objetivo

Vincular reviews nuevas a trabajos confirmados y derivar reputación pública neutral, auditable y reconstruible sin asignar puntos propietarios.

## Modelo y operación canónica

- `Review.contract_id` identifica el contrato reseñado y es único para reviews nuevas.
- Cliente y profesional se derivan exclusivamente de `ContractRequest`.
- Sólo el cliente propietario activo puede crear una review sobre un contrato exactamente `CONFIRMADA`.
- `create_contract_review()` exige idempotency key estable, bloquea el contrato y autoriza antes del replay.
- Misma key y payload devuelve la misma review; payload distinto produce conflicto; otra key sobre contrato reseñado produce conflicto de dominio.
- Review, `ReputationEvent`, `AuditLog`, `ActivityNotification` y `OperationCommand` son atómicos.
- No se crea `ContractEvent`.

## Privacidad y moderación

- `comentario` preserva el original auditable e inmutable.
- `comment_public` es el único contenido expuesto en perfiles.
- Reportar pasa el comentario a `PENDING_MODERATION` sin excluir el rating.
- Sólo `SUPER_ADMIN` activo puede mostrar, ocultar, redactar o excluir el rating mediante operaciones cerradas.
- Toda decisión de moderación genera `AuditLog`; no borra la review ni modifica el original.
- El lector administrativo de originales exige `SUPER_ADMIN` también en el servicio.

## Reputación neutral

Las métricas públicas son promedio elegible, distribución por estrellas, cantidad de reviews verificadas, contratos confirmados y cobertura de reviews. Contractuales y legacy verificadas se distinguen. `UNVERIFIED` y ratings `EXCLUDED` quedan fuera.

No existe score propietario nuevo. Plata/oro, rankings y fórmulas reputacionales quedan para una decisión futura.

## Legacy

- La ruta anterior de creación responde `410`.
- `add_reputation_event()` fue retirado y no tiene callers productivos.
- Los eventos y reviews históricos no se eliminan.
- PostgreSQL y SQLite bloquean nuevas filas reputacionales con puntos.

## Validación PostgreSQL

PostgreSQL 16.14, Alembic `20260726_06`, base exclusiva descartable:

- Reviews/concurrencia: 8/8.
- Rutas, CSRF, privacidad y moderación: 8/8.
- Se demostraron replay, conflictos, conteos exactos, rollback, sesión reutilizable, inmutabilidad del original, redacción pública, exclusión separada, cero puntos y cero `ContractEvent`.

## Deuda no bloqueante

- La lectura administrativa del original está restringida, pero no genera todavía un evento separado por cada visualización.
- Persisten warnings de SQLAlchemy por `Query.get()` y deprecaciones de `datetime.utcnow()`.
