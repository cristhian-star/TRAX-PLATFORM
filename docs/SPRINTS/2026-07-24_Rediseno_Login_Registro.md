# Rediseño de Login y Registro

## Objetivo

Rediseñar login y registro de TRAX con mejor UX/UI, validacion, accesibilidad y seguridad, manteniendo URLs actuales y sin migraciones.

## Resumen

Se implemento una experiencia dedicada de autenticacion. El registro ahora crea una cuenta basica, registra aceptacion versionada de terminos/privacidad y redirige segun rol. Login y registro mantienen CSRF, rate limiting y `next` sanitizado.

## Cambios implementados

- Rediseño de `login.html` con labels, errores inline, copy de confianza y toggle de contraseña.
- Rediseño de `register.html` con cuenta basica, selector cliente/profesional y aceptacion obligatoria.
- CSS dedicado `auth-ux-v1.css` compatible con Design System v2.
- JS dedicado `auth-ux-v1.js` para toggle de contraseña, fortaleza simple, copy por rol y prevencion de doble submit.
- Validacion centralizada en `auth_service.py`.
- `TermsAcceptance` conectado al registro con version centralizada.
- Inicio de sesion inmediato despues del registro.
- Redirect cliente a `next` seguro o inicio.
- Redirect profesional a `/profesional/perfil/completar`.
- Rechazo de usuarios suspendidos o inactivos en login.
- Mensaje neutral ante email duplicado para reducir enumeracion.

## Archivos creados

- `app/static/css/auth-ux-v1.css`
- `app/static/js/auth-ux-v1.js`
- `tests/test_auth_ux_redesign_v1.py`
- `docs/SPRINTS/2026-07-24_Rediseno_Login_Registro.md`

## Archivos modificados

- `README.md`
- `app/routes/auth_routes.py`
- `app/services/auth_service.py`
- `app/templates/login.html`
- `app/templates/register.html`
- `docs/CHANGELOG.md`
- `docs/ROADMAP.md`
- `docs/BACKLOG.md`
- `docs/DECISIONES_ARQUITECTURA.md`

## Rutas agregadas

- No se agregaron rutas.

## Migraciones realizadas

- No se realizaron migraciones.

## Validaciones ejecutadas

- `python -m unittest discover tests`: 91 tests OK.
- `python -m compileall app scripts tests`.
- `git diff --check`.
- `docker compose up --build -d`.
- `docker compose ps`.
- Tests dentro del contenedor: 91 tests OK.
- Smoke tests HTTP de `/login` y `/register`.
- Validacion manual en navegador integrado.

## Validaciones manuales

- Login valido con usuario activo.
- Login invalido con mensaje seguro.
- Usuario suspendido rechazado.
- `next` interno permitido.
- `next` externo bloqueado.
- Toggle mostrar/ocultar contraseña.
- Registro cliente valido con redirect a `next`.
- Registro profesional valido con redirect a completar perfil.
- Email duplicado con mensaje neutral.
- Contraseña corta, confirmacion distinta y terminos no aceptados con errores inline.
- `TermsAcceptance` creado para cliente y profesional.
- Desktop y mobile sin overflow horizontal.
- Assets CSS/JS cargados y sin errores de consola.

## Riesgos pendientes

- Implementar recuperacion de contraseña real con tokens seguros y expiracion.
- Implementar verificacion de email.
- Revisar textos legales definitivos con profesional.
- Evaluar rol o flujo empresa cuando exista definicion funcional.
- Reemplazar usos legacy de `Query.get()`.
- Reemplazar `datetime.utcnow()` por timestamps timezone-aware.

## Problemas encontrados

- No existe backend de recuperacion de contraseña; por eso no se agrego enlace activo.
- No existe rol `EMPRESA`; se mantiene fuera del alcance.

## Decisiones tomadas

- Mantener cuenta basica primero y perfil progresivo despues.
- No crear `Professional` automaticamente durante el registro.
- Usar mensaje neutral para email duplicado.
- Registrar consentimiento en la misma transaccion que el usuario.
- No simular login social ni recuperacion de contraseña.

## Resultado final

Sprint cerrado a nivel de implementacion, validacion, Docker y documentacion. La rama queda lista para revision y merge.

## Proximo Sprint recomendado

Auth Recovery & Email Verification v1: recuperacion de contraseña, verificacion de email, plantillas de email, tokens seguros y pruebas de expiracion.
