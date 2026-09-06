# MANDOBRA Platform

MANDOBRA es una plataforma Flask para conectar clientes con profesionales, gestionar solicitudes operativas y sostener flujos de presupuestos, emergencias, propuestas, contrataciones, cobertura y contacto controlado por WhatsApp.

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

Antes de promover MANDOBRA a staging o produccion validar:

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

## Autenticacion y registro

El flujo de auth mantiene las URLs publicas actuales:

- `GET/POST /login`
- `GET/POST /register`
- `POST /logout`

Reglas actuales:

- Login y registro usan CSRF y rate limiting.
- `next` se acepta solo si es una ruta interna segura.
- El registro crea una cuenta basica con nombre, email, contraseña, rol y aceptacion de terminos/privacidad.
- `TermsAcceptance` se registra en la misma transaccion que el usuario.
- Cliente registrado inicia sesion y va a `next` seguro o inicio.
- Profesional registrado inicia sesion y va a `/profesional/perfil/completar`.
- No se crea `Professional` automaticamente durante el alta inicial.
- Los usuarios suspendidos o inactivos no pueden iniciar sesion.
- No hay recuperacion de contraseña ni login social hasta que exista backend real.

## Design System v2

La capa visual canonica esta en `app/static/css/design-system-v2.css`.

Orden de carga:

1. `design-tokens.css`: tokens legacy v1.
2. `design-system-v2.css`: contrato canonico `--trax-ds-*` y componentes `.trax-*`.
3. `styles.css`: estilos globales historicos y compatibilidad.
4. CSS por modulo: composicion puntual de cada pantalla.

Reglas:

- Las pantallas nuevas deben consumir variables `--trax-ds-*`.
- Los componentes reutilizables deben usar namespace `.trax-*`.
- Las clases legacy pueden convivir con `.trax-*` durante la migracion.
- No migrar pantallas complejas sin validacion visual especifica.
- Navbar, tablas/admin, marketplace, emergencias y perfil profesional completo mantienen migracion pendiente.

## WhatsApp

Toda apertura de WhatsApp debe pasar por `POST /whatsapp/iniciar`.

Reglas:

- No generar enlaces `wa.me` desde templates.
- Exigir consentimiento antes de salir de MANDOBRA.
- Validar operacion, ownership, CSRF y rate limit en backend.
- Registrar `WhatsAppContactSession` y pasar a `CONTACTO_ABIERTO`.
- Responder JSON seguro para apertura autorizada desde el frontend.
- Mantener redirect HTML como fallback compatible.
- No almacenar mensajes, archivos ni conversaciones.
- No exponer telefonos completos en HTML, DOM ni logs.

## Google Maps

`GOOGLE_MAPS_API_KEY` es una clave publica de navegador y debe configurarse por entorno.

Reglas:

- No hardcodear claves en el repositorio.
- Rechazar placeholders como `tu_clave_real`.
- Restringir la key por dominio/referrer autorizado.
- Limitar APIs habilitadas inicialmente a Maps JavaScript API.
- Configurar cuotas y alertas en Google Cloud.
- Mantener fallback visual cuando la key falte, sea placeholder, invalida o falle la carga del script.
- Mostrar coordenadas publicas aproximadas; nunca exponer el punto exacto profesional.

## Identidad y portfolio profesional

La identidad visual profesional se gestiona mediante `ProfessionalMedia`.

Alcance actual:

- Avatar, portada y galeria de trabajos.
- Procesamiento con Pillow para validar imagen real, extension, MIME, tamano y dimensiones.
- Re-encode de imagen y thumbnail para retirar metadatos EXIF/GPS.
- Borrado logico y estados de moderacion.
- Campos legacy de `Professional` usados solo como fallback.

Storage:

- Desarrollo/testing: `MEDIA_STORAGE_PROVIDER=local`.
- Staging/produccion: `MEDIA_STORAGE_PROVIDER=cloudinary` con `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` y `CLOUDINARY_FOLDER`.
- No versionar credenciales ni almacenar binarios/base64 en PostgreSQL.

Validar en staging antes de produccion:

- Subida real a Cloudinary.
- URL segura y thumbnail.
- Reemplazo de avatar/portada.
- Eliminacion y rollback ante error.
- Ausencia de secretos en HTML, logs y errores.
