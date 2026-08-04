# Sprint 7 - Cierre Contracting Core

## Alcance cerrado

Sprint 7 consolida contratación directa y derivada desde presupuestos/propuestas, fundamentos de idempotencia y concurrencia, negociación directa opcional y reviews contractuales con reputación neutral.

## Contratos canónicos

El flujo exitoso es:

`CREADA -> ACEPTADA -> EN_PROGRESO -> COMPLETADA -> CONFIRMADA`

`CONFIRMADA` es el único terminal exitoso para contratos nuevos. `CERRADA` es exclusivamente histórica y se interpreta o migra como `CONFIRMADA`. No existe transición automática posterior.

La única modalidad habilitada es `hiring_mode = SINGLE`. `contracting_mode = EXTERNAL` no incorpora comportamiento financiero.

## Reviews y reputación

Las reviews nuevas requieren un contrato `CONFIRMADA`, actor cliente explícito y ownership. Una review por contrato se protege en servicio y base. La reputación pública se reconstruye desde hechos neutrales y no usa un score nuevo. Los registros legacy se preservan sin vinculación heurística cuando son ambiguos.

## Validación final

Entorno PostgreSQL 16.14 descartable, Alembic `20260726_06`:

- Contratación y concurrencia: 8/8.
- Negociación 2B: 8/8.
- Reviews y concurrencia: 8/8.
- Rutas, privacidad y moderación: 8/8.
- Migración parcial de comandos: 21/21.
- PostgreSQL legacy: 4/4.
- Total PostgreSQL: 57/57, sin omisiones.
- Suite Sprint 7 SQLite: 145 ejecutadas, 140 aprobadas, 5 omitidas.
- Suite completa: 246 ejecutadas, 241 aprobadas, 5 omitidas, cero fallos.

Las cinco omisiones del runner SQLite corresponden a cuatro pruebas legacy que exigen `TRAX_POSTGRES_TEST_URL` y una prueba marcada porque SQLite no ofrece locks de fila ni sesiones independientes equivalentes. Esos comportamientos quedaron cubiertos por los 57 gates PostgreSQL ejecutados sin omisiones. SQLite no se usa como evidencia de locks ni triggers PostgreSQL.

## Fuera de alcance

Quedan fuera del Sprint 7: `MULTIPLE`, badges plata/oro, ranking propietario, pagos, facturación, custodia, garantías, disputas financieras, mediación, producción y despliegue.

## Deuda no bloqueante

- Migrar `Query.get()` a `db.session.get()`.
- Reemplazar `datetime.utcnow()` por timestamps timezone-aware.
- Evaluar auditoría de lectura administrativa individual del comentario original.
- Reconciliar en una fase futura la elegibilidad PRO que aún consulta puntos históricos.

## Veredicto

El cierre formal requiere cero P0/P1, todos los gates verdes, suite completa aprobada, documentación reconciliada y limpieza del entorno descartable. El informe de auditoría del Bloque 5 registra la evidencia final.

Este documento representa cierre técnico en la rama de feature. No representa merge a `develop`, publicación ni despliegue.
