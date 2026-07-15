# WhatsApp Contact Privacy v1

## Objetivo

Incorporar un esquema hibrido de contacto por WhatsApp para mejorar la privacidad de los profesionales sin romper el flujo actual.

## Resumen

Se agrego username de WhatsApp, preferencia de contacto y resolucion centralizada del identificador. TRAX prioriza username como dato de privacidad cuando existe, pero mantiene telefono como fallback tecnico porque WhatsApp no ofrece una URL publica estable para abrir chats por username.

## Cambios implementados

- Campos nuevos en `Professional`: `whatsapp_username`, `whatsapp_contact_preference`.
- Campos nuevos en `WhatsAppContactSession`: `contact_identifier_type`, `contact_identifier_masked`.
- Helpers de normalizacion, validacion, preferencia y resolucion hibrida.
- Perfil privado con username y preferencia de contacto.
- Perfil publico con aviso de contacto protegido sin exponer telefono ni username completo.
- Nuevas sesiones con identificador enmascarado.

## Archivos creados

- `migrations/versions/20260715_01_whatsapp_contact_privacy_v1.py`
- `tests/test_whatsapp_contact_privacy_service.py`
- `docs/SPRINTS/2026-07-15_WhatsApp_Contact_Privacy_v1.md`

## Archivos modificados

- `app/models/professional.py`
- `app/models/whatsapp_contact_session.py`
- `app/routes/main_routes.py`
- `app/services/professional_service.py`
- `app/services/whatsapp_contact_service.py`
- `app/templates/completar_perfil_profesional.html`
- `app/templates/perfil_profesional.html`
- `app/static/css/professional-profile-v2.css`
- `docs/CHANGELOG.md`
- `docs/ROADMAP.md`
- `docs/DECISIONES_ARQUITECTURA.md`
- `docs/BACKLOG.md`

## Rutas agregadas

- No se agregaron rutas. Se mantiene `POST /whatsapp/iniciar`.

## Migraciones realizadas

- `20260715_01_whatsapp_contact_privacy_v1`

## Validaciones ejecutadas

- `python -m compileall app scripts tests`
- `git diff --check`
- `docker compose up --build -d`
- `docker compose exec -T trax-web alembic upgrade head`
- `docker compose exec -T trax-web alembic current`
- `python -m unittest tests.test_whatsapp_contact_privacy_service` dentro de Docker.
- Prueba funcional Docker: AUTO con username, fallback tecnico a telefono, sesion con tipo `USERNAME`, mascara segura, perfil publico sin telefono ni username completo.
- Validacion visual: perfil publico, modal de consentimiento, perfil privado, desktop, mobile, claro/oscuro, consola sin errores.

## Capturas

- `C:/Users/Usuario/.codex/visualizations/2026/07/10/019f495b-0a05-7271-aaf8-b0014c25503a/whatsapp-contact-privacy-v1/perfil_publico_privacidad_desktop.png`
- `C:/Users/Usuario/.codex/visualizations/2026/07/10/019f495b-0a05-7271-aaf8-b0014c25503a/whatsapp-contact-privacy-v1/perfil_publico_privacidad_mobile.png`
- `C:/Users/Usuario/.codex/visualizations/2026/07/10/019f495b-0a05-7271-aaf8-b0014c25503a/whatsapp-contact-privacy-v1/perfil_privado_whatsapp_username.png`

## Riesgos pendientes

- WhatsApp todavia no expone una URL publica estable para abrir chat por username.
- La apertura directa por username queda preparada pero no activa.
- Los grupos automaticos quedan pendientes y solo deberian implementarse con API oficial y consentimiento explicito.

## Problemas encontrados

- No hubo bloqueos tecnicos. Se documento la limitacion real de WhatsApp usernames.

## Decisiones tomadas

- `AUTO`: prioriza username si existe y es valido; usa telefono como fallback tecnico.
- `USERNAME`: si no hay username valido, usa telefono como fallback seguro cuando existe.
- `PHONE`: usa telefono.
- No se inventan URLs de username.
- No se almacenan telefonos completos duplicados en sesiones nuevas.

## Resultado final

TRAX mejora la privacidad del contacto por WhatsApp sin romper el flujo centralizado ni depender de APIs no implementadas.

## Proximo Sprint recomendado

Auditar todos los puntos publicos de contacto para agregar mas señales de privacidad y preparar futura compatibilidad con APIs oficiales de WhatsApp.
