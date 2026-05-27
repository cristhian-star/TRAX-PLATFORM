# Alembic en TRAX

## Que es Alembic

Alembic es el sistema oficial de migraciones para el schema SQLAlchemy de TRAX. Permite versionar cambios de estructura, aplicarlos de forma ordenada y preparar una futura transicion desde SQLite DEV hacia PostgreSQL.

La aplicacion selecciona la base mediante configuracion:

- desarrollo local sin `DATABASE_URL`: SQLite en `instance/trax.db`;
- Docker Compose DEV: PostgreSQL mediante `DATABASE_URL`.

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

Docker Compose DEV configura `trax-web` para usar PostgreSQL. En una base PostgreSQL nueva, aplicar el schema con Alembic:

```powershell
docker compose exec trax-web alembic upgrade head
docker compose exec trax-web alembic current
docker compose exec trax-web alembic history
```

La SQLite previa y el volumen `trax_instance` se conservan; esta fase no migra sus datos a PostgreSQL.

## Limites de esta fase

Esta configuracion habilita PostgreSQL DEV, pero no migra datos SQLite ni reemplaza automaticamente bases SQLite legacy. La baseline registra el modelo actual sin borrar datos. Los backfills de ownership y la limpieza de referencias historicas deben tratarse explicitamente antes de endurecer constraints o mover datos a produccion.
