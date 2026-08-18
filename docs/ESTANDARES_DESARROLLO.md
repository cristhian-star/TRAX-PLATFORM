# ESTANDARES DE DESARROLLO MANDOBRA

## Objetivo

Definir las reglas permanentes de trabajo para mantener MANDOBRA ordenado, seguro y mantenible a largo plazo.

Este documento funciona como manual de desarrollo del proyecto. Debe cambiar solo cuando exista una decision tecnica, funcional o de proceso relevante.

## Convencion de ramas

Usar nombres claros, breves y descriptivos.

- `feature/nombre-corto`: nuevas funcionalidades.
- `fix/nombre-corto`: correcciones de errores.
- `hotfix/nombre-corto`: correcciones urgentes sobre produccion.
- `refactor/nombre-corto`: reorganizacion interna sin cambio funcional esperado.
- `docs/nombre-corto`: cambios exclusivos de documentacion.

## Convencion de commits

Usar prefijos consistentes:

- `feat:` nueva funcionalidad.
- `fix:` correccion de error.
- `refactor:` cambio interno sin cambio funcional esperado.
- `docs:` documentacion.
- `style:` ajustes visuales o de formato sin cambio funcional.
- `test:` pruebas o validaciones.
- `chore:` tareas operativas o mantenimiento.

Los commits deben describir el cambio real, no el intento de implementacion.

## Flujo Git

El flujo oficial es:

`feature/fix/hotfix -> develop -> main`

Reglas:

- Todo cambio funcional debe salir desde una rama especifica.
- `develop` concentra trabajo validado antes de produccion.
- `main` representa estado estable.
- No mergear a `main` sin validacion previa en `develop`.
- El cierre tecnico puede quedar validado y documentado en la rama de feature antes de su aprobacion independiente.
- El cierre integrado y publicable requiere commit, merge a `develop` y validacion posterior; un cierre tecnico no implica despliegue.

## Estructura de carpetas

Estructura principal:

- `app/`: aplicacion principal.
- `app/config/`: configuracion.
- `app/database/`: conexion y configuracion de base de datos.
- `app/models/`: modelos de dominio y persistencia.
- `app/routes/`: rutas y controladores.
- `app/services/`: logica de negocio reutilizable.
- `app/static/`: assets estaticos.
- `app/templates/`: vistas HTML.
- `app/utils/`: utilidades internas.
- `docs/`: documentacion permanente.
- `docs/SPRINTS/`: cierre documentado de cada sprint validado.
- `migrations/`: migraciones Alembic.
- `scripts/`: scripts operativos o de mantenimiento.

## Reglas UX/UI

- Respetar el Design System MANDOBRA definido en `docs/design-system-v1.md`.
- Mantener consistencia visual entre pantallas publicas, privadas y dashboards.
- Priorizar claridad, jerarquia visual y acciones evidentes.
- No introducir patrones visuales aislados si no responden a una necesidad real.
- Separar la operatoria interna de la imagen publica cuando representen objetivos distintos.
- Validar que los textos sean breves, claros y orientados a la accion.

## Seguridad

- Mantener proteccion CSRF en formularios y acciones sensibles.
- Validar permisos y roles en rutas protegidas.
- No confiar en controles de UI como unica barrera de seguridad.
- No exponer secretos, tokens ni credenciales en el repositorio.
- Validar entradas del usuario antes de persistir o ejecutar acciones.
- Evitar cambios que amplien permisos sin decision explicita.
- Exigir actor explicito y activo también dentro de servicios sensibles; la ruta no reemplaza RBAC ni ownership de dominio.
- Autorizar antes de resolver replays idempotentes.
- No exponer modelos ORM con campos privados a templates o respuestas públicas; usar DTOs públicos mínimos.
- Separar contenido original auditable, contenido público y elegibilidad de métricas.

## Integridad transaccional

- Las operaciones sensibles deben concentrar comando, entidad, auditoría, notificación y hechos derivados en una sola transacción.
- Ningún helper interno puede ejecutar `commit()` si participa de una operación atómica superior.
- PostgreSQL real es obligatorio para validar locks, carreras, triggers y recuperación de sesiones; SQLite no sustituye ese gate.
- Los gates destructivos sólo pueden usar bases exclusivas y descartables con autorización explícita de reset.

## Docker

- Mantener `Dockerfile` y `docker-compose.yml` alineados con las dependencias reales del proyecto.
- Probar Docker antes de cerrar sprints cuando el cambio afecte runtime, dependencias, base de datos o configuracion.
- No incorporar configuraciones locales no reproducibles.
- Documentar cambios relevantes de entorno en `docs/` cuando correspondan.

## Alembic

- Usar migraciones Alembic para cambios de esquema.
- No modificar manualmente el estado de base de datos como reemplazo de una migracion.
- Revisar que cada migracion tenga upgrade y downgrade coherentes cuando aplique.
- Documentar migraciones realizadas en el documento del sprint.

## Pull Requests

Checklist minimo para aceptar un Pull Request:

- [ ] La rama sigue la convencion definida.
- [ ] Los commits usan prefijos validos.
- [ ] El cambio esta acotado al objetivo del PR.
- [ ] No incluye codigo temporal ni pruebas descartadas.
- [ ] Las rutas protegidas validan permisos y roles.
- [ ] Los formularios o acciones sensibles mantienen CSRF.
- [ ] La UI respeta el Design System MANDOBRA.
- [ ] `python -m compileall app scripts` ejecutado correctamente.
- [ ] `git diff --check` ejecutado correctamente.
- [ ] Docker probado si el cambio afecta runtime, dependencias, base de datos o configuracion.
- [ ] Documentacion actualizada cuando corresponde.
- [ ] CHANGELOG actualizado para cambios implementados y validados.
- [ ] ROADMAP, BACKLOG o DECISIONES_ARQUITECTURA actualizados si corresponde.
- [ ] Documento de sprint creado al cierre del sprint.

## Criterio de mantenimiento

Este documento no debe usarse para registrar cambios diarios. Para eso existen `CHANGELOG.md`, `ROADMAP.md`, `BACKLOG.md`, `DECISIONES_ARQUITECTURA.md` y los documentos de `docs/SPRINTS/`.

Actualizar este documento solo cuando cambien las reglas permanentes del proyecto.
