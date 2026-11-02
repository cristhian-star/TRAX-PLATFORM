# PROF-UX-001 — Espacio profesional

Timestamp: 2026-10-14T12:15:05-03:00. Origen: laptop. Responsable: implementador local.
Estado: READY_TO_RESUME — implementado; revisión visual de Producto y testing independiente pendientes.
Rama: `feature/professional-workspace-ux`.
HEAD base conservado: `2e552f2fdc57c152c97f0486050574696f6b250e`.
Encargo aprobado: 2026-10-14T11:05:37-03:00, Cristian Sánchez.

## Comportamiento construido

Layout profesional compartido, logos oficiales sin subtítulo, selector existente
`theme-switch-v1.js`, notificaciones y menú de cuenta. Navegación lateral en
escritorio y cuatro accesos superiores en móvil. Inicio respeta la composición de
los cuatro bocetos: saludo, atención, trabajos, oportunidades, perfil y actividad.
Los datos de ejemplo de los bocetos no se incorporan a producción.

| Ruta | Comportamiento |
| --- | --- |
| `/` | Profesional activo va a su inicio; CLIENTE conserva home público autenticado; SUPER_ADMIN conserva entrada anterior. Rol comprobado en persistencia. |
| `/profesional/dashboard` | Hasta tres contratos no terminales, una solicitud y una propuesta recientes, perfil y hasta tres notificaciones. |
| `/profesional/oportunidades` | Hasta tres publicaciones de cada fuente, enlaces a filtros canónicos, presupuestos enviados, postulaciones propias paginadas de a 20 y últimos cinco contactos WhatsApp. |
| `/profesional/trabajos` | Contratos propios de todos los orígenes y estados, paginados de a 20, enlace al detalle canónico. |
| `/profesional/perfil/completar` | Formulario existente dentro del layout; encabezado compacto, media, cobertura, credenciales y configuración preservados. |
| `/cliente/dashboard` | Conservado como Mis operaciones; retiro futuro fuera de este incremento. |

Las cuatro vistas requieren el rol PROFESIONAL persistido y cuenta activa por
`role_required`. Contratos: `ContractRequest.professional_id` referencia
`Professional.id`; `professional_user_id` referencia `User.id`. El listado exige
ambas relaciones de propiedad coherentes. No equipara una postulación/contacto/
presupuesto con un contrato. COMPLETADA significa espera de confirmación del cliente.
No modifica transiciones ni contratos históricos incoherentes.

Servicio de presentación: `app/services/professional_workspace_service.py`.
Reutiliza `has_pro_access`, verificación aprobada, rating/reseñas, cobertura,
media publicada y `calculate_private_profile_completion`. Inicio y perfil usan
los mismos valores. Presentación del perfil no equivale a verificación,
habilitación para ofertar ni disponibilidad. Etiquetas FREE/PRO.
No hay rating ficticio para ausencia de reseñas.

La entrada de clientes ofrece iniciales y Mis operaciones en el menú existente;
no se añadió un modelo de foto de cliente. Login, registro, consentimiento y
validación de `next` siguen en AUTH sin cambios.

## Diferencias deliberadas frente al boceto

- Oportunidades recientes, no «en tu zona»: no se afirma matching territorial.
- Trabajos pendientes y en curso representa también aceptación y confirmación.
- Atención deriva del porcentaje real; no afirma que falte una foto sin comprobarla.
- Verificación y plan son reales; no se incorpora el 67 % ilustrativo ni contadores de ejemplo.
- Los filtros completos y acciones transaccionales permanecen en sus pantallas
  canónicas, enlazadas desde el espacio. No se rediseñan sus detalles en este incremento.
- Los contactos WhatsApp se consultan en Oportunidades, separados de contratos.
- CSS encapsulado consume tipografía, bordes, texto y acentos DS v2; superficies
  oscuras locales #101820/#1b2832 y acento suave #402b21 siguen los bocetos.
- Perfil conserva sus nueve paneles y todos los formularios, con menor encabezado.

## Accesibilidad y resiliencia

Navegación con enlaces nativos, estado `aria-current`, foco visible, controles de
cabecera de 44 CSS px y POST de logout con CSRF. Progreso etiquetado.
Sin JavaScript se ocultan el selector de tema y controles que requieren scripts;
los nueve paneles del perfil quedan visibles y los formularios conservan sus POST.
`prefers-reduced-motion` desactiva animaciones y transiciones dentro del workspace.
No se agregó controlador de tema, dependencia, migración, seed ni modelo.

## Evidencia local de esta sesión

SQLite en memoria con datos sintéticos. Suite final: **89/89 pruebas Python**.
Incluye 13 nuevas pruebas focales, AUTH, media/portfolio, marca, contratación,
presupuesto a contrato, propuesta a contrato, elegibilidad, portal y seguridad.
No se suman repeticiones como cobertura nueva.

Comando final:

```powershell
$env:DATABASE_URL='sqlite:///:memory:'
$env:PYTHONDONTWRITEBYTECODE='1'
.venv/Scripts/python.exe -m unittest tests.test_professional_workspace_ux tests.test_auth_ux_redesign_v1 tests.test_professional_identity_portfolio_v1 tests.test_platform_brand tests.test_sprint7_contracting_core tests.test_sprint7_budget_to_contract tests.test_sprint7_proposal_to_contract tests.test_proposal_eligibility tests.test_proposal_portal_p1 tests.test_security_controls -q
node --test tests/js/auth_ux.test.js
```

Node: 1 archivo de test aprobado, sin fallos. `compileall` de app y test nuevo,
UTF-8 sin BOM/NUL/U+FFFD y `git diff --check`: correctos. Pycache fuera del repo.
La primera prueba de media falló por permisos del temporal de sandbox; se repitió
con TEMP/TMP en el directorio autorizado de evidencia y pasó sin cambiar producto.
El log ERROR del test de errores seguros es intencional; la suite final termina OK.

Regresión adicional DS/footer: 15 tests, cuatro fallos de assertions (dos son
subtests de footer) y un error. Se reproducen con `base.html` original obtenido
con `git show HEAD:app/templates/base.html` y cargado en memoria, sin checkout:

- `test_auth_css_delegates_core_controls_to_design_system`: espera ausencia de regla AUTH actual.
- `test_auth_templates_use_canonical_components_and_keep_accessibility`: espera radios de registro retirados por AUTH.
- `test_global_footer_and_responsive_focus_contrast`: espera footer en login y registro.
- `test_logged_layout_does_not_link_to_visitor_only_anchors`: intenta extraer footer inexistente de login.

AUTH_UX_001 documenta layout sin navbar/footer. No se modificaron esos tests ni
AUTH para satisfacer expectativas anteriores. Se actualizó el test de marca para
cubrir logos oficiales tanto en AUTH independiente como en el workspace nuevo.
No se declara la suite completa del repositorio aprobada.

QA navegador Chrome, preview propio en 54931, SQLite memoria; Docker 5050 intacto:

- Inicio: comprobación DOM de ancho en 1440/1280/768/390/320, claro y oscuro, sin overflow.
- Perfil: cinco anchos en claro sin overflow; activación de Fotos y Portfolio por Enter.
- Foco de panel confirmado visible, outline sólido tras ajuste encapsulado.
- Oportunidades inspeccionada en 390; trabajos en 320, ambos navegables.
- Fallback del perfil comprobado con respuesta de preview sin scripts de aplicación:
  nueve paneles visibles, selector oculto, sin overflow a 320. No equivale a una
  sesión completa con JavaScript desactivado mediante configuración del navegador.
- Capturas válidas: escritorio claro, escritorio oscuro 1440 y móvil oscuro 390.
- Pares de contraste focales: #b9380a/blanco 5.78:1; #ff8a4c/#1b2832 6.44:1;
  #111827/blanco 17.74:1; #cbd5e1/#1b2832 10.13:1. No es auditoría AA integral.
- Consola inspeccionada: errores de una extensión Chrome; no error de aplicación observado.
- La extensión perdió conexión durante matrices adicionales y captura móvil clara;
  no se atribuye cobertura a llamadas que terminaron por timeout.

Pendientes: matriz completa de las otras vistas en ambos temas, captura móvil
clara definitiva, emulación real de movimiento reducido, QA completo sin JS,
axe/lector de pantalla y retest independiente. Movimiento reducido solo estático.
No se ejecutaron gates PostgreSQL, migraciones ni pruebas sobre datos compartidos.

## Inventario del incremento

Modificados:

- `app/routes/main_routes.py`
- `app/services/budget_service.py`
- `app/templates/base.html`
- `app/templates/completar_perfil_profesional.html`
- `app/templates/profesional_dashboard.html`
- `tests/test_platform_brand.py`
- `docs/HANDOFFS/ACTIVE_HANDOFF.md`

Nuevos:

- `app/services/professional_workspace_service.py`
- `app/static/css/professional-workspace.css`
- `app/static/css/professional-workspace-nojs.css`
- `app/templates/professional_workspace_base.html`
- `app/templates/components/_workspace_cards.html`
- `app/templates/professional_jobs.html`
- `app/templates/professional_opportunities.html`
- `tests/test_professional_workspace_ux.py`
- `docs/REQUISITOS/PROF_UX_001.md`

`docs/INDEX.md` es trabajo previo excluido del incremento; SHA-256 conservado:
`46400cbd6de53ddabc3f535fec46cc1d901f17a1ed2001c6c5e1916041acd7a0`.

## Revisión en Docker compartido — solo Cristian

Desde la raíz del repo, con el entorno QA previamente configurado:

```powershell
docker compose --env-file .env.example -f docker-compose.stabilization.yml -p mandobra_stabilization build web
docker compose --env-file .env.example -f docker-compose.stabilization.yml -p mandobra_stabilization up -d --no-deps web
```

No ejecutar down, recrear postgres, migrar ni sembrar para este incremento.
Luego revisar 5050 con el usuario profesional de QA existente y repetir testing.
Staging vacío; sin commit/push/PR/merge ni cambios de rama; integración no autorizada.

## Corrección focal — panel de notificaciones

Timestamp: 2026-10-14T13:22:50-03:00. Rama `feature/professional-workspace-ux`.
HEAD conservado: `2e552f2fdc57c152c97f0486050574696f6b250e`.

La campanita es un botón con aria-expanded/aria-controls. Abre y cierra un panel
anclado sin navegación ni requests. Escape devuelve foco al botón; clic fuera,
salida de foco por Tab, scroll de página y pagehide cierran sin encerrar el foco.
Ancho máximo 380 px, margen de 12 px sobre clientWidth (excluye scrollbar), alto
máximo 520 px o espacio disponible, listado con scroll propio. Temas existentes.

Datos renderizados por servidor mediante obtener_notificaciones_usuario para el
usuario autenticado. Incluye todo su historial, sin polling ni truncado del listado;
las descripciones se resumen a 180 caracteres. Fecha según el formato existente.
Leída/no leída tienen texto explícito y las no leídas borde/superficie diferenciada.
Contador real del contexto existente; abrir no marca lecturas. POST canónico con
CSRF y ownership para marcar individualmente; vuelve a la vista profesional y
actualiza el contador. Destinos internos canónicos preservados; no se cambian
rutas ni templates de las operaciones. No hay Ver todas ni navegación al centro
público desde este ajuste; se retiró también el enlace de Última actividad.
Estado vacío: No tenés notificaciones. Carga síncrona: no aplica spinner ni error
asíncrono; se mantiene el manejo general de errores del servidor. El disclosure
requiere JavaScript y su botón no se revela sin él. No se altera el fallback de
los formularios del perfil. Historial muy voluminoso: una futura paginación del
panel reduciría el HTML inicial; no se añade un endpoint en este ajuste.

Archivos de la corrección: professional_workspace_service.py,
professional_workspace_base.html, completar_perfil_profesional.html (super del
bloque scripts), profesional_dashboard.html, professional-workspace.css,
professional-notifications.js (nuevo), test_professional_workspace_ux.py,
js/professional_notifications.test.js (nuevo), este requisito y ACTIVE_HANDOFF.
No se modifican modelos, dependencias, permisos, operaciones de lectura ni INDEX.

Validación focal actual: 40 pruebas Python aprobadas (workspace, AUTH y marca),
2 tests Node del controlador real y node --check aprobado. Dos nuevas pruebas
Python comprueban ownership, escape, lecturas, contador, estado vacío, integración
en las cuatro vistas y rechazo CSRF. Pruebas Node: disclosure, Escape, foco,
clic fuera, Tab, geometría móvil y cierre por pagehide. No se suman ejecuciones
históricas de 89 tests a este resultado. Comandos:

```powershell
$env:DATABASE_URL='sqlite:///:memory:'
$env:PYTHONDONTWRITEBYTECODE='1'
.venv/Scripts/python.exe -m unittest tests.test_professional_workspace_ux tests.test_auth_ux_redesign_v1 tests.test_platform_brand -q
node --test tests/js/professional_notifications.test.js
node --check app/static/js/professional-notifications.js
```

QA Chrome con SQLite en memoria y usuarios sintéticos: escritorio 1440 y móvil
320, claro/oscuro, panel abierto sin cambio URL, Escape con foco, Enter, clic fuera,
lectura explícita 3→2 y scroll de listado. Capturas actuales externas al repo:
notificaciones-desktop-claro.png, notificaciones-desktop-oscuro.png,
notificaciones-mobile-claro.png y notificaciones-mobile-oscuro.png.
La barra de scroll móvil inicialmente recortaba el borde: corregido con clientWidth.
No se declara auditoría AA integral ni testing independiente. Sin Docker ni DB
compartida. Preview propio detenido al cierre. Staging vacío; INDEX conserva SHA
46400cbd6de53ddabc3f535fec46cc1d901f17a1ed2001c6c5e1916041acd7a0.
Estado: implementado localmente, pendiente de retest independiente.

