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

## Seguridad y produccion

Antes de promover TRAX a staging o produccion validar:

- Secretos reales fuera de Git: `SECRET_KEY`, `DATABASE_URL`, claves externas y credenciales operativas.
- HTTPS activo y HSTS habilitado solo sobre conexiones seguras.
- Redis u otro backend compartido para Flask-Limiter.
- Servidor WSGI productivo; no usar el servidor Flask de desarrollo.
- Backups automáticos y prueba de restauracion.
- Monitoreo de disponibilidad, errores y consumo de recursos.
- Logs sin payloads sensibles, tokens, cookies, documentos, telefonos completos ni coordenadas exactas.
- Cloudflare/WAF o equivalente configurado antes de exposicion publica.
- Migraciones Alembic aplicadas y verificadas.
- Rate limits revisados segun trafico real.
- Politicas legales revisadas por profesional: terminos, privacidad, cookies y consentimientos.
- Escaneo de dependencias y secretos antes de cada release.
