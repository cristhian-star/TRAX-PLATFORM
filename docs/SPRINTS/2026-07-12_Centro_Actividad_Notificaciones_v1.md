# Centro de Actividad + Notificaciones v1

## Objetivo

Crear un sistema interno y centralizado de actividad y notificaciones para TRAX, preparado para canales futuros.

## Resumen

Se implemento `ActivityNotification` como registro unico de actividad historica y notificacion interna. La primera version integra eventos reales de presupuestos, propuestas y emergencias, muestra campana en navbar y agrega el centro `/notificaciones`.

## Cambios implementados

- Modelo central `ActivityNotification`.
- Servicio `notification_service.py` con creacion, consulta y marcado de lectura.
- Campana global para usuarios autenticados con contador y ultimas 5 notificaciones.
- Centro de notificaciones con filtros por todas, no leidas, accion requerida, informacion y recordatorios.
- Resumen de actividad reciente en Dashboard Cliente y Dashboard Profesional.
- Integracion de eventos reales en presupuestos, propuestas y emergencias.

## Archivos creados

- `app/models/activity_notification.py`
- `app/services/notification_service.py`
- `app/routes/notification_routes.py`
- `app/templates/notificaciones.html`
- `app/static/css/notification-navbar-v1.css`
- `app/static/css/notifications-v1.css`
- `migrations/versions/20260712_01_activity_notifications_v1.py`
- `docs/SPRINTS/2026-07-12_Centro_Actividad_Notificaciones_v1.md`

## Archivos modificados

- `app/__init__.py`
- `app/routes/main_routes.py`
- `app/routes/operation_routes.py`
- `app/templates/base.html`
- `app/templates/cliente_dashboard.html`
- `app/templates/profesional_dashboard.html`
- `app/static/css/client-dashboard-v1.css`
- `app/static/css/professional-dashboard-v1.css`
- `docs/CHANGELOG.md`
- `docs/ROADMAP.md`
- `docs/DECISIONES_ARQUITECTURA.md`
- `docs/BACKLOG.md`

## Rutas agregadas

- `GET /notificaciones`
- `POST /notificaciones/<id>/leer`
- `POST /notificaciones/marcar-todas-leidas`

## Migraciones realizadas

- `20260712_01_activity_notifications_v1.py`
- Tabla: `activity_notifications`
- Revision aplicada: `20260712_01`

## Eventos conectados

- Cliente publica solicitud de presupuesto.
- Profesional envia presupuesto preliminar.
- Cliente recibe nueva oferta.
- Cliente adjudica una oferta.
- Profesional es adjudicado.
- Solicitud de presupuesto cancelada.
- Usuario publica propuesta.
- Profesional se postula.
- Publicador recibe nueva postulacion.
- Postulacion aceptada.
- Postulacion descartada.
- Propuesta cancelada.
- Usuario autenticado publica emergencia.

## Seguridad

- Todas las rutas de notificaciones requieren login.
- Las operaciones de lectura filtran por `user_id`.
- Un usuario no puede marcar como leida una notificacion ajena.
- Todos los POST mantienen CSRF.
- No se exponen datos privados de otros usuarios fuera de los mensajes operativos ya visibles en flujos existentes.

## Validaciones ejecutadas

- `python -m compileall app scripts` ejecutado correctamente.
- `git diff --check` ejecutado correctamente.
- `docker compose up --build -d` ejecutado correctamente.
- `alembic upgrade head` ejecutado correctamente.
- `alembic current` devuelve `20260712_01 (head)`.
- Prueba funcional integral ejecutada con cliente y profesionales demo.
- Validacion visual desktop claro, desktop oscuro y mobile con dropdown de campana.

## Riesgos pendientes

- No hay canal Email, WhatsApp, Push ni navegador en esta version.
- No hay tiempo real; las novedades se ven al recargar.
- Los eventos de cuenta `Perfil verificado` y `Cambio de plan` quedan pendientes para integrar en puntos especificos del flujo.
- Los mensajes actuales son internos y breves; puede requerirse una capa de copy transaccional por canal futuro.

## Problemas encontrados

- La app usa `db.create_all()` en desarrollo, por lo que la migracion se hizo tolerante a tabla ya existente.

## Decisiones tomadas

- Usar strings controlados por constantes en el servicio en lugar de enums rigidos.
- Centralizar actividad y notificaciones en el mismo modelo.
- No implementar WebSockets, polling, Email, WhatsApp, Push, Celery ni Redis en esta fase.

## Resultado final

TRAX cuenta con un sistema interno de actividad y notificaciones v1, integrado en navbar, dashboards y flujos operativos principales.

## Proximo Sprint recomendado

Implementar eventos de cuenta y preparar plantillas transaccionales para canal Email.
