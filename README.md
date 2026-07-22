# TRAX Platform

TRAX es una plataforma Flask para conectar clientes con profesionales, gestionar solicitudes operativas y sostener flujos de presupuestos, emergencias, propuestas, contrataciones, cobertura y contacto controlado por WhatsApp.

## Tecnologias principales

- Python
- Flask
- PostgreSQL
- Docker Compose
- Alembic

## Flujo principal de ejecucion

El entorno principal del proyecto es Docker. No se debe depender de `python run.py` para validar la aplicacion local completa.

Desde la raiz del repositorio:

```bash
docker compose down
docker compose up --build -d
docker compose ps
docker compose logs trax-web --tail=100
```

Aplicacion local:

```text
http://localhost:5000/
```

## Base de datos

Alembic es la autoridad del esquema fuera de tests. Las migraciones se ejecutan dentro del flujo Docker/PostgreSQL.

`db.create_all()` queda reservado para tests o desarrollo local explicitamente controlado.

## Validaciones recomendadas

```bash
python -m unittest discover tests
python -m compileall app scripts tests
git diff --check
```
