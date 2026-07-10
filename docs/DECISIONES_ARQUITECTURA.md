# DECISIONES DE ARQUITECTURA TRAX

## 2026-07-09

Se decidio incorporar una documentacion permanente y viva dentro del repositorio como parte obligatoria del proceso oficial de desarrollo.

Motivo:

El proyecto TRAX necesita conservar el contexto tecnico, funcional y de UX sin depender de la memoria del equipo ni del historial de Git.

Alcance:

- Registrar cambios implementados y aceptados en `docs/CHANGELOG.md`.
- Mantener el estado general del producto en `docs/ROADMAP.md`.
- Documentar decisiones relevantes en `docs/DECISIONES_ARQUITECTURA.md`.
- Mantener pendientes, mejoras y deuda tecnica en `docs/BACKLOG.md`.
- Mantener las reglas permanentes de desarrollo en `docs/ESTANDARES_DESARROLLO.md`.
- Crear un documento independiente por sprint en `docs/SPRINTS/` con nombre `AAAA-MM-DD_Nombre_del_Sprint.md`.

Criterio:

Solo se documentaran funcionalidades implementadas, probadas y validadas. No se registraran experimentos descartados, codigo temporal ni ideas sin validar.

Condicion de cierre:

Un sprint solo se considerara cerrado cuando este implementado, probado, documentado, versionado y mergeado en `develop`.

## 2026-07-09

Se decidio crear `docs/ESTANDARES_DESARROLLO.md` como manual permanente de desarrollo de TRAX.

Motivo:

El crecimiento del proyecto requiere reglas explicitas y estables para ramas, commits, flujo Git, estructura, UX/UI, seguridad, Docker, Alembic y aceptacion de Pull Requests.

Criterio:

El documento se actualizara solo ante cambios de reglas permanentes del proyecto, no para registrar tareas diarias ni implementaciones puntuales.

## 2026-07-10

Se decidio consolidar el sistema visual de TRAX en una capa semantica de variables CSS v2.

Motivo:

El cambio de tema Light/Dark debe depender de variables globales y no de duplicacion de estilos por pantalla.

Alcance:

- Crear `app/static/css/design-system-v2.css`.
- Mantener compatibilidad con tokens existentes del Design System v1.
- Adaptar pantallas y componentes existentes sin redisenar la arquitectura visual.
- No modificar navbar, rutas, modelos, migraciones, Docker ni logica de negocio.

Criterio:

Las nuevas pantallas deberan consumir variables semanticas del Design System v2 para heredar automaticamente Light/Dark.
