# PostgreSQL DEV con Docker

## Alcance

Este entorno incorpora PostgreSQL para desarrollo en Docker. No migra los datos existentes de SQLite y no elimina ninguna base ni volumen previo. El backup local previo se conserva en `instance/trax_backup_before_postgres.db`.

## Base usada segun entorno

- Fuera de Docker, si `DATABASE_URL` no esta definida, TRAX mantiene SQLite en `instance/trax.db`.
- Dentro de Docker Compose, `trax-web` recibe `DATABASE_URL=postgresql+psycopg2://trax_user:trax_password@postgres:5432/trax_db` y utiliza PostgreSQL.
- El volumen SQLite existente `trax_instance` se conserva, pero no recibe nuevos datos mientras la web use PostgreSQL.
- PostgreSQL persiste datos DEV en el volumen `trax_postgres_data`.

## Levantar PostgreSQL y la aplicacion

Definir `SECRET_KEY` en `.env` y ejecutar:

```powershell
docker compose up --build -d
```

El servicio `postgres` expone `localhost:5432` con estas credenciales DEV:

```text
DB: trax_db
User: trax_user
Password: trax_password
```

Estas credenciales son solo para desarrollo local.

## Crear el schema con Alembic

El contenedor web no crea tablas automaticamente al arrancar. En una base PostgreSQL nueva, aplicar la baseline y migraciones con:

```powershell
docker compose exec trax-web alembic upgrade head
docker compose exec trax-web alembic current
```

Para ver el historial:

```powershell
docker compose exec trax-web alembic history
```

`upgrade head` crea schema vacio en PostgreSQL; no importa filas desde SQLite.

## Volver a SQLite local

Para ejecutar TRAX localmente con SQLite, no definir `DATABASE_URL` y usar el entorno Python local:

```powershell
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
python run.py
```

La aplicacion volvera a leer `instance/trax.db`. En caso de necesitar restaurar manualmente datos DEV, el backup existente es `instance/trax_backup_before_postgres.db`; no se reemplaza automaticamente.

## Advertencias

- No borrar `instance/trax.db`, `instance/trax_backup_before_postgres.db` ni el volumen `trax_instance`.
- No ejecutar importaciones de datos SQLite a PostgreSQL durante esta fase.
- Este compose usa credenciales fijas de desarrollo y no representa una configuracion productiva.
