# Alembic en MANDOBRA

## Head vigente y diagnóstico Docker

El head vigente es `20260917_03`, descendiente de `20260917_02`.
Para una base nueva de diagnóstico usar el servicio `migrate` del
[Compose descartable](RUNBOOKS/DOCKER_STABILIZATION.md); web espera su éxito.
No ejecutar estas validaciones sobre `trax_db` ni adoptar esquemas históricos
marcando revisiones sin comprobar qué cambios están realmente aplicados.

## Identidad PSP contextual (historia)

Al 2026-09-11, `20260911_02` era el head único y desciende de
`20260911_01`. Agrega contexto PSP nullable a `payment_attempts`; no realiza
backfill y su downgrade conserva la bandeja creada por su revisión padre.

## Que es Alembic

Alembic es el sistema oficial de migraciones para el schema SQLAlchemy de MANDOBRA. Permite versionar cambios de estructura, aplicarlos de forma ordenada y preparar una futura transicion desde SQLite DEV hacia PostgreSQL.

La aplicacion selecciona la base mediante configuracion:

- desarrollo local sin `DATABASE_URL`: SQLite en `instance/trax.db`;
- Docker Compose DEV: PostgreSQL mediante `DATABASE_URL`.

Alembic obtiene la URI desde `create_app().config["SQLALCHEMY_DATABASE_URI"]`; no se configura una ruta de base hardcodeada en `migrations/env.py`.

## Baseline inicial

La revisión `20260527_01` es la baseline inicial, no el esquema ORM actual.
Una base nueva vacía se crea mediante `alembic upgrade head`. La adopción de
una base histórica exige auditoría previa del esquema y de las revisiones ya
aplicadas: marcar el head sin ejecutar migraciones ocultaría cambios pendientes.

## Comandos habituales

Ver la version aplicada:

```powershell
alembic current
```

Ver el historial:

```powershell
alembic history
```

Aplicar migraciones pendientes:

```powershell
alembic upgrade head
```

Generar una nueva migracion a partir de cambios de modelos:

```powershell
alembic revision --autogenerate -m "add payments"
```

Revisar siempre el archivo generado antes de aplicar `upgrade`, especialmente en SQLite.

## Uso en Docker

Docker Compose DEV configura `trax-web` para usar PostgreSQL. En una base PostgreSQL nueva, aplicar el schema con Alembic:

```powershell
docker compose exec trax-web alembic upgrade head
docker compose exec trax-web alembic current
docker compose exec trax-web alembic history
```

La SQLite previa y el volumen `trax_instance` se conservan; esta fase no migra sus datos a PostgreSQL.

## Limites de esta fase

Esta configuracion habilita PostgreSQL DEV, pero no migra datos SQLite ni reemplaza automaticamente bases SQLite legacy. La baseline registra el modelo actual sin borrar datos. Los backfills de ownership y la limpieza de referencias historicas deben tratarse explicitamente antes de endurecer constraints o mover datos a produccion.
# Downgrade de `20260904_01`

Timestamp: 2026-09-04T10:29:16-03:00

El downgrade desde `20260904_01` es reversible en estructura, pero elimina la
columna `source_type` y pierde los valores `TRANSACTIONAL`/`SUBSCRIPTION`. Un
re-upgrade recrea la columna nullable y esas filas vuelven con
`source_type=NULL`. No ejecutar el downgrade cuando deba conservarse esa
clasificacion sin respaldo y autorizacion explicita.

# Persistencia neutral de pagos `20260910_01`

Timestamp: 2026-09-11T14:00:30-03:00

La revision `20260910_01`, descendiente de `20260904_01`, crea
`payment_obligations` y luego `payment_attempts`. El downgrade elimina primero
los intentos y despues las obligaciones. No contiene backfills ni altera otras
tablas. `alembic upgrade head` debe resolver un unico head dinamico; no aplicar
esta migracion ni ejecutar su downgrade sobre `trax_db` durante la etapa de
revision local.
