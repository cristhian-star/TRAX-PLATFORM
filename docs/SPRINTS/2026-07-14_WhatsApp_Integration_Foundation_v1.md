# WhatsApp Integration Foundation v1

## Objetivo

Crear la infraestructura base para iniciar contactos por WhatsApp desde TRAX mediante un flujo centralizado, auditable y seguro.

## Resumen

Se reemplazaron enlaces directos `wa.me` por una ruta `POST /whatsapp/iniciar` con consentimiento obligatorio, validacion de operacion y registro de sesion. No se implemento WhatsApp Business API, IA, webhooks ni lectura de conversaciones.

## Cambios implementados

- Modelo `WhatsAppContactSession` para registrar sesiones de contacto.
- Servicio central `whatsapp_contact_service.py`.
- Ruta unica `POST /whatsapp/iniciar`.
- Modal de consentimiento previo a la salida hacia WhatsApp.
- Reemplazo de enlaces directos en perfiles, tarjetas, emergencias, presupuestos adjudicados y propuestas aceptadas.
- Notificaciones internas para cliente y profesional.
- Resumenes operativos en Dashboard Cliente y Dashboard Profesional.

## Archivos creados

- `app/models/whatsapp_contact_session.py`
- `app/routes/whatsapp_routes.py`
- `app/services/whatsapp_contact_service.py`
- `app/static/js/whatsapp-consent-v1.js`
- `app/templates/components/_whatsapp_consent_modal.html`
- `migrations/versions/20260714_01_whatsapp_contact_sessions.py`
- `docs/SPRINTS/2026-07-14_WhatsApp_Integration_Foundation_v1.md`

## Archivos modificados

- `app/__init__.py`
- `app/routes/main_routes.py`
- `app/routes/operation_routes.py`
- `app/static/css/styles.css`
- `app/static/css/client-dashboard-v1.css`
- `app/static/css/professional-dashboard-v1.css`
- `app/templates/base.html`
- `app/templates/perfil_profesional.html`
- `app/templates/components/_professional_card.html`
- `app/templates/components/_emergency_professional_card.html`
- `app/templates/detalle_presupuesto.html`
- `app/templates/detalle_propuesta.html`
- `app/templates/directorio_emergencias.html`
- `app/templates/resultados.html`
- `app/templates/cliente_dashboard.html`
- `app/templates/profesional_dashboard.html`
- `docs/CHANGELOG.md`
- `docs/ROADMAP.md`
- `docs/DECISIONES_ARQUITECTURA.md`
- `docs/BACKLOG.md`

## Rutas agregadas

- `POST /whatsapp/iniciar`

## Migraciones realizadas

- `20260714_01_whatsapp_contact_sessions`

## Validaciones ejecutadas

- `python -m compileall app scripts`
- `git diff --check`
- `docker compose down`
- `docker compose up --build -d`
- `docker compose ps`
- `docker compose logs trax-web --tail=100`
- `docker compose exec -T trax-web alembic upgrade head`
- `docker compose exec -T trax-web alembic current`
- Prueba funcional con Flask client en Docker: visitante, consentimiento, emergencia, presupuesto adjudicado, propuesta aceptada, ownership, sesiones y notificaciones.
- Validacion visual en navegador: perfil publico, modal de consentimiento, Dashboard Cliente, Dashboard Profesional, desktop, mobile, tema claro y tema oscuro.

## Capturas

- `C:/Users/Usuario/.codex/visualizations/2026/07/10/019f495b-0a05-7271-aaf8-b0014c25503a/whatsapp-foundation-v1/perfil_modal_whatsapp_dark.png`
- `C:/Users/Usuario/.codex/visualizations/2026/07/10/019f495b-0a05-7271-aaf8-b0014c25503a/whatsapp-foundation-v1/cliente_dashboard_whatsapp_light.png`
- `C:/Users/Usuario/.codex/visualizations/2026/07/10/019f495b-0a05-7271-aaf8-b0014c25503a/whatsapp-foundation-v1/profesional_dashboard_whatsapp_mobile_light.png`

## Riesgos pendientes

- Definir criterio futuro para WhatsApp Business API y webhooks.
- No existe trazabilidad posterior al click porque la conversacion ocurre fuera de TRAX.

## Problemas encontrados

- Existian enlaces directos de WhatsApp distribuidos en templates de perfiles, emergencias, presupuestos y propuestas.

## Decisiones tomadas

- Las URLs de WhatsApp solo se generan desde el servicio central.
- El consentimiento es obligatorio antes de redirigir fuera de TRAX.
- No se almacenan mensajes, archivos ni conversaciones.

## Resultado final

TRAX queda con una base centralizada para iniciar contactos por WhatsApp, registrar sesiones y mostrar actividad operativa sin incorporar APIs externas.

## Proximo Sprint recomendado

Validar el uso real del flujo en operaciones cerradas y definir, si corresponde, una fase posterior para WhatsApp Business API.
