# Identidad y Portfolio Profesional

## Objetivo

Validar y cerrar la primera base funcional para foto de perfil profesional, portada, galeria de trabajos, metadata, privacidad, moderacion y storage configurable.

## Resumen

Se incorporo `ProfessionalMedia` como modelo central para identidad visual profesional. La solucion procesa imagenes en backend, genera miniaturas, elimina EXIF/GPS, valida ownership y expone publicamente solo media publicada. El almacenamiento local quedo validado y Cloudinary quedo preparado por variables de entorno para staging.

## Cambios implementados

- Modelo `ProfessionalMedia` con tipos `AVATAR`, `COVER` y `GALLERY`.
- Estados de moderacion: `BORRADOR`, `PENDIENTE_MODERACION`, `PUBLICADO`, `RECHAZADO`, `OCULTO` y `ELIMINADO`.
- Migracion Alembic `20260723_01_professional_media_v1`.
- Servicio de procesamiento seguro de imagenes con Pillow.
- Servicio de storage local y Cloudinary configurable.
- Servicio de dominio para upload, reemplazo, metadata, orden, principal, borrado logico y moderacion.
- Rutas privadas para gestion de avatar, portada y galeria.
- Acciones administrativas para publicar, rechazar, ocultar y restaurar imagenes.
- Integracion minima en perfil privado, perfil publico, galeria publica, cards y moderacion admin.
- Compatibilidad con campos legacy como fallback.

## Archivos creados

- `app/models/professional_media.py`
- `app/services/media_image_service.py`
- `app/services/media_storage_service.py`
- `app/services/professional_media_service.py`
- `migrations/versions/20260723_01_professional_media_v1.py`
- `tests/test_professional_identity_portfolio_v1.py`
- `docs/SPRINTS/2026-07-23_Identidad_Portfolio_Profesional.md`

## Archivos modificados

- `.env.example`
- `.gitignore`
- `README.md`
- `app/__init__.py`
- `app/config/config.py`
- `app/models/professional.py`
- `app/routes/main_routes.py`
- `app/static/css/professional-cards-v1.css`
- `app/static/css/professional-profile-v2.css`
- `app/templates/admin_moderacion.html`
- `app/templates/completar_perfil_profesional.html`
- `app/templates/components/_professional_card.html`
- `app/templates/components/_professional_gallery.html`
- `app/templates/perfil_profesional.html`
- `docker-compose.yml`
- `requirements.txt`
- `docs/CHANGELOG.md`
- `docs/ROADMAP.md`
- `docs/BACKLOG.md`
- `docs/DECISIONES_ARQUITECTURA.md`

## Rutas agregadas

- `POST /profesional/media/avatar`
- `POST /profesional/media/portada`
- `POST /profesional/media/galeria`
- `POST /profesional/media/<id>/editar`
- `POST /profesional/media/reordenar`
- `POST /profesional/media/<id>/principal`
- `POST /profesional/media/<id>/eliminar`
- `POST /admin/media/<id>/publicar`
- `POST /admin/media/<id>/rechazar`
- `POST /admin/media/<id>/ocultar`
- `POST /admin/media/<id>/restaurar`

## Migraciones realizadas

- `20260723_01_professional_media_v1`: crea `professional_media`, indices, constraints y unicidad parcial para avatar/portada activos.

## Validaciones ejecutadas

- `python -m unittest discover tests`: 80 tests OK.
- `python -m compileall app scripts tests`.
- `git diff --check`.
- `alembic upgrade head`.
- `alembic current`: `20260723_01 (head)`.
- `docker compose up --build -d`.
- `docker compose ps`.
- Tests dentro del contenedor: 80 tests OK.
- Smoke tests HTTP de `/`, `/buscar`, `/profesional/1`, perfil privado sin sesion y administracion sin sesion.
- Validacion visual liviana en perfil publico y busqueda, desktop y mobile, sin overflow ni errores de consola.

## Validaciones funcionales

- Avatar: subida, reemplazo y publicacion automatica en entorno local.
- Portada: ruta y procesamiento disponibles.
- Galeria: subida, limite maximo, metadata, orden, principal y borrado logico cubiertos por servicio/rutas.
- Metadata: titulo, descripcion, categoria y alt text con limites.
- Moderacion: publicar, rechazar con motivo, ocultar y restaurar.
- Ownership: usuarios ajenos no pueden editar, borrar ni reordenar media de otro profesional.
- CSRF: formularios protegidos y rechazo validado.
- Seguridad de archivos: rechazo de MIME falso, extension falsa, archivo corrupto, tamano excesivo y dimensiones invalidas.
- Privacidad: EXIF/GPS retirado por re-encode, `storage_key` no expuesto publicamente y media rechazada/oculta/eliminada no aparece en perfil publico.
- Auditoria: acciones principales registran `AuditLog`.

## Storage

- Local: validado en tests y Docker con `MEDIA_STORAGE_PROVIDER=local`.
- Cloudinary: implementado y configurable, pero no validado contra proveedor real porque no habia credenciales de staging disponibles en el entorno.

Checklist Cloudinary pendiente:

- Configurar credenciales reales solo por entorno.
- Validar subida, thumbnail, URL segura, reemplazo y eliminacion.
- Probar rollback DB/storage ante error.
- Confirmar ausencia de secretos en HTML, logs y errores.
- Revisar cuotas, carpeta, politicas de borrado y CDN.

## Riesgos pendientes

- Validar Cloudinary en staging con credenciales reales.
- Incorporar antivirus o escaneo externo de imagenes.
- Implementar limpieza asincronica de archivos huerfanos.
- Evaluar `PortfolioItem` futuro si el portfolio requiere trabajos agrupados.
- Evaluar videos solo con alcance, costos y moderacion definidos.
- Evaluar moderacion automatica cuando exista politica aprobada.
- Reemplazar usos legacy de `Query.get()`.
- Reemplazar `datetime.utcnow()` por timestamps timezone-aware.

## Problemas encontrados

- No habia credenciales Cloudinary de staging disponibles, por lo que la validacion real del proveedor queda pendiente.
- El entorno local Docker usa storage local, que es correcto para desarrollo pero no representa CDN productivo.

## Decisiones tomadas

- Usar `ProfessionalMedia` como tabla separada para evitar sobrecargar `Professional`.
- Mantener avatar, portada y galeria dentro del mismo modelo para el MVP.
- Mantener campos legacy como fallback hasta una migracion funcional posterior.
- No crear `PortfolioItem`, videos ni moderacion automatica en este sprint.
- No almacenar binarios ni base64 en PostgreSQL.

## Resultado final

La rama queda lista para revision tecnica y merge, con almacenamiento local validado, Cloudinary preparado por configuracion y deuda de staging claramente documentada.

## Proximo Sprint recomendado

Media Storage Staging v1: validar Cloudinary real, politicas de carpetas, rollback, limpieza de huerfanos, monitoreo de errores y checklist productivo de archivos.
