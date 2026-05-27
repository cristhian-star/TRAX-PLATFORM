# Alembic en TRAX

## Que es Alembic

Alembic es el sistema oficial de migraciones para el schema SQLAlchemy de TRAX. Permite versionar cambios de estructura, aplicarlos de forma ordenada y preparar una futura transicion desde SQLite DEV hacia PostgreSQL.

La aplicacion sigue usando SQLite por ahora:

- desarrollo local: `instance/trax.db`
- Docker: `/app/instance/trax.db`

Alembic obtiene la URI desde `create_app().config["SQLALCHEMY_DATABASE_URI"]`; no se configura una ruta de base hardcodeada en `migrations/env.py`.

## Baseline inicial

La revision `initial_schema_baseline` representa el schema ORM actual. Como la base DEV existente ya contiene tablas y datos, se registra con `stamp` en lugar de volver a crear tablas:

```powershell
alembic stamp head
```

`stamp` solamente marca la version aplicada en `alembic_version`; no borra ni transforma datos existentes. Para una base nueva vacia, usar `alembic upgrade head`.

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

El volumen Docker mantiene una SQLite distinta de la copia local del host. Ejecutar los comandos dentro del contenedor para afectar `/app/instance/trax.db`:

```powershell
docker compose exec trax-web alembic current
docker compose exec trax-web alembic stamp head
docker compose exec trax-web alembic upgrade head
```

Antes de estampar un volumen existente, auditar su schema y conservar una copia de respaldo DEV.

## Limites de esta fase

Esta configuracion no migra a PostgreSQL ni reemplaza automaticamente bases SQLite legacy. La baseline registra el modelo actual sin borrar datos. Los backfills de ownership y la limpieza de referencias historicas deben tratarse expl?citamente antes de endurecer constraints o mover datos a produccion.
