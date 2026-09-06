# Sprint 7 - Cierre Contracting Core aprobado

> Estado: auditoría independiente de integración aprobada. Sprint 7 está
> técnicamente cerrado y aprobado para PR hacia `develop`. Este cierre no
> autoriza publicación ni despliegue productivo.

## Alcance cerrado

Sprint 7 consolida contratación directa y derivada desde presupuestos/propuestas, fundamentos de idempotencia y concurrencia, negociación directa opcional y reviews contractuales con reputación neutral.

## Contratos canónicos

El flujo exitoso es:

`CREADA -> ACEPTADA -> EN_PROGRESO -> COMPLETADA -> CONFIRMADA`

`CONFIRMADA` es el único terminal exitoso para contratos nuevos. `CERRADA` es exclusivamente histórica y se interpreta o migra como `CONFIRMADA`. No existe transición automática posterior.

La única modalidad habilitada es `hiring_mode = SINGLE`. `contracting_mode = EXTERNAL` no incorpora comportamiento financiero.

## Reviews y reputación

Las reviews nuevas requieren un contrato `CONFIRMADA`, actor cliente explícito y ownership. Una review por contrato se protege en servicio y base. La reputación pública se reconstruye desde hechos neutrales y no usa un score nuevo. Los registros legacy se preservan sin vinculación heurística cuando son ambiguos. Los lectores admiten exclusivamente orígenes `CONTRACTUAL` y `LEGACY` verificada.

`20260726_06` conserva su semántica mediante un snapshot migratorio versionado
y autocontenido. No es una API productiva: no existen callers productivos y
ese contrato se verifica mediante pruebas de dependencias, sin presentarlo
como una frontera contra imports arbitrarios dentro de Python. El adaptador
vigente exige ambos IDs de ownership y falla ante payloads incompletos.
`20260726_07` usa exclusivamente esa API fail-closed y es el único estado
operativo soportado. Un downgrade a `_06`
reinstala defensas históricas más débiles y no equivale a `_07` para operación
normal.

## Validación final

Entorno PostgreSQL 16.14 descartable, Alembic `20260726_07`:

- Auditoría independiente de integración: aprobada.
- Hallazgos abiertos P0/P1/P2: ninguno.
- P3 no bloqueante: contraseña demo predecible pendiente de endurecimiento futuro.

- Contratación y concurrencia: 8/8.
- Negociación 2B: 8/8.
- Reviews, concurrencia, convergencia y ataques aislados: 10/10.
- Rutas, privacidad y moderación: 8/8.
- Migración parcial de comandos: 21/21.
- PostgreSQL legacy: 4/4.
- Total PostgreSQL: 59/59, sin omisiones.
- Suite Sprint 7 con PostgreSQL habilitado: 165 ejecutadas, 164 aprobadas, 1 omitida.
- Suite completa con PostgreSQL habilitado: 266 ejecutadas, 265 aprobadas, 1 omitida, cero fallos.

La única omisión es el placeholder SQLite que documenta que ese motor no ofrece locks de fila ni sesiones independientes equivalentes. Esos comportamientos quedaron cubiertos por 59 pruebas PostgreSQL ejecutadas sin omisiones. SQLite no se usa como evidencia de locks ni triggers PostgreSQL.

## Fuera de alcance

Quedan fuera del Sprint 7: `MULTIPLE`, badges plata/oro, ranking propietario, pagos, facturación, custodia, garantías, disputas financieras, mediación, producción y despliegue.

## Deuda no bloqueante

- Migrar `Query.get()` a `db.session.get()`.
- Reemplazar `datetime.utcnow()` por timestamps timezone-aware.
- Evaluar auditoría de lectura administrativa individual del comentario original.
- Reconciliar en una fase futura la elegibilidad PRO que aún consulta puntos históricos.

## Veredicto

La auditoría independiente de integración aprobó el cierre con cero P0/P1/P2.
Sprint 7 queda técnicamente cerrado y aprobado para preparar PR hacia
`develop`. `20260726_07` es el único estado operativo soportado; un downgrade
a `_06` restaura defensas históricas más débiles.

La aprobación técnica y la aptitud para PR no autorizan merge automático,
publicación ni despliegue productivo. Permanece como P3 no bloqueante el
endurecimiento futuro de la contraseña demo predecible.
