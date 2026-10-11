# AUTH-UX-001 — Acceso y registro

Timestamp: 2026-10-09T22:26:04-03:00. Origen: laptop. Responsable: implementador local.
Estado: IMPLEMENTADO SEGÚN INFORME LOCAL; pendiente de revisión y testing independiente.
Rama: feature/auth-onboarding-foundation.
HEAD: b20f41adef46b51bf423b03b4d971072d251b9c7.

## Comportamiento

Layout exclusivo de autenticación, sin navbar ni footer, con logos oficiales
claro/oscuro centrados y tarjeta responsive basada en tokens DS v2.
Login: email editable, Continuar valida formato en el navegador sin petición de
existencia; despliega contraseña, enfoca el campo y cambia a Ingresar. El POST
real conserva backend, CSRF, rate limiting, bloqueo de cuentas y next seguro.
Sin JavaScript, ambos campos y el botón Ingresar están presentes en HTML.
Después de un error servidor, contraseña queda desplegada. Pageshow restablece
el botón para evitar bloqueo al volver mediante historial/BFCache.
El controlador de tema existente se carga como recurso local; no se debilita CSP.

Cliente/Profesional son enlaces a registro con rol preseleccionado mediante GET.
Solo PROFESIONAL se reconoce expresamente; valores GET desconocidos muestran
CLIENTE. Esto es presentación, no permiso: el POST conserva su whitelist vigente.
La cuenta y TermsAcceptance mantienen su transacción y versión legal existentes.

## Diferencias necesarias respecto de los bocetos

- Solo email: auth_service.py authenticate_user consulta User.email; no username.
- Nombre completo único: User.nombre, máximo 120 caracteres. No se añade apellido
  ni se inventa una separación de identidad que el modelo no representa.
- Se conserva password_confirm obligatorio y el indicador orientativo de fortaleza.
- No se muestra Google ni enlaces legales inexistentes. El consentimiento sigue
  siendo obligatorio; su contenido/versionado no se altera.
- Paleta y fuentes adaptadas al DS v2; controles textuales Mostrar/Ocultar.

## Validación

SQLite en memoria, datos sintéticos, sin bases compartidas ni Docker.
Primera ejecución: 29/29 OK (auth_ux_redesign_v1, security_controls,
security_compliance_phase3). Tras agregar cobertura: autenticación 13/13 OK.
No son 42 pruebas únicas: la segunda ejecución repite las focales iniciales.
Node tests/js/auth_ux.test.js OK: paso local, formato inválido, foco,
envío, error desplegado y pageshow; entorno sin API de red.
Sintaxis JavaScript y git diff --check: OK.
Advertencias legacy datetime.utcnow/Query.get existentes; el log de error seguro
pertenece a pruebas de fallos deliberados. No se ejecutó suite completa.

Navegador real sobre preview exclusivo SQLite memoria en puerto 54902:
login inicial/desplegado y registro de ambos roles, capturados en claro/oscuro.
Email sintético; no se crearon cuentas reales. Foco en login-password al continuar
con Enter; Mostrar cambia el tipo del campo. Sin errores registrados en consola.
Mediciones a 1280/768/390/320 px en oscuro y 320 px en claro: sin overflow;
contraseña a 320 px conserva 130.34 px de ancho; botones medidos >=48 px de alto;
label clicable del consentimiento >=44 px. Contraste medido en claro:
título 18.72:1, texto/ayudas 10.35:1, botón/enlace principal 4.56:1.
Capturas fuera del repositorio: auth-login[-expanded]-light/dark.jpg,
auth-register-client/professional-light/dark.jpg y registros móviles.

Limitaciones: no se emuló JavaScript deshabilitado ni reduced motion en navegador;
fallback cubierto por HTML y backend, CSS elimina animaciones/transiciones bajo
reduced motion. No se ejecutó auditoría AA completa ni medición exhaustiva de
contraste oscuro. Testing independiente debe completarlas y revisar BFCache real.

## Pendientes funcionales fuera de alcance

Google: especificar OIDC, proveedor/librería compatible, client ID y secreto
administrado fuera del repositorio, callbacks por entorno/HTTPS, state/nonce/PKCE
según cliente, validación de tokens, vinculación segura de cuentas existentes,
email verificado, consentimiento, rol inicial, bloqueo de cuentas y manejo de errores.
No equiparar identidad Google con verificación profesional.
Username: decidir necesidad, unicidad, normalización, colisiones y recuperación;
requiere evaluar dominio/persistencia y migración, no solo cambiar una etiqueta.
Recuperación de contraseña, correo verificado y documentos legales siguen pendientes.

## Archivos

Modificados: app/routes/auth_routes.py (solo selección GET del rol),
app/templates/login.html, app/templates/register.html,
app/static/css/auth-ux-v1.css, app/static/js/auth-ux-v1.js,
tests/test_auth_ux_redesign_v1.py, docs/HANDOFFS/ACTIVE_HANDOFF.md.
Nuevos: app/templates/auth_base.html, tests/js/auth_ux.test.js y esta especificación.
Sin modelos, migraciones, dependencias ni assets nuevos.


## 2026-10-09T23:23:38-03:00 - Selector de tema en acceso y registro

Se reutiliza theme-switch-v1 en auth_base.html, con carga diferida para vincular
el control después del DOM. Selector arriba a la derecha, en flujo normal, separado
del logo y formulario; tamaño mínimo 108 x 44 px y ancho compacto también a 320 px.
Sin JavaScript el control permanece oculto. La preferencia se conserva mediante
el controlador existente. No se modifica autenticación ni estilos globales.
Validación: sintaxis JS y prueba Node auth_ux OK; navegador real en claro/oscuro,
cambio con clic y Espacio, persistencia entre login y registro, escritorio 1280 px
y móvil 320 px sin overflow ni superposición. No se repitió la suite Python
para este ajuste de presentación; sus resultados anteriores no son un nuevo retest.
Archivos de este ajuste: app/templates/auth_base.html, app/static/css/auth-ux-v1.css,
app/static/js/auth-ux-v1.js, esta especificación y ACTIVE_HANDOFF.md.


## 2026-10-09T23:48:48-03:00 - AUTH-UX-001-FIX-01

Estado: CORREGIDO SEGÚN INFORME LOCAL; PENDIENTE DE RETEST INDEPENDIENTE.
Base del dictamen: P2 contraste y P3 cobertura comunicados en el pedido del
2026-10-09T23:38:19-03:00; no se recibió otro archivo de dictamen.
Preflight: rama feature/auth-onboarding-foundation, HEAD
b20f41adef46b51bf423b03b4d971072d251b9c7, origin esperado confirmado, staging
vacío y exactamente los diez paths AUTH pendientes, coherentes con el handoff.

Corrección P2: únicamente CSS encapsulado en AUTH, sin cambiar theme-switch-v1.
La pista clara usa el token gray-600, el borde text-muted y el texto text-secondary;
hover usa text-secondary/text. El foco mantiene secondary. La pista oscura conserva
orange-600. Tamaño/posición y controlador permanecen. Se hace explícito display:none
para el selector [hidden], pues display:inline-flex podía anular la ocultación nativa.
Indicadores necesarios: círculo y pista (posición/estado), perímetro (identificación
del control), texto y foco. La sombra es decorativa y no acredita contraste.

Colores computados en navegador real; ratios de luminancia sRGB:

| Par | Colores | Ratio |
| --- | --- | --- |
| Antes claro: círculo/pista y pista/superficie | #FFFFFF / #E5E7EB | 1.24:1 |
| Después claro: círculo/pista y pista/superficie | #FFFFFF / #4B5563 | 7.56:1 |
| Claro borde/superficie | #64748B / #FFFFFF | 4.76:1 |
| Claro borde/página | #64748B / #F7F9FC | 4.51:1 |
| Claro texto/superficie | #334155 / #FFFFFF | 10.35:1 |
| Claro foco/página | #0B8799 / #F7F9FC | 4.03:1 |
| Oscuro círculo/pista | #FFFFFF / #D3440E | 4.56:1 |
| Oscuro pista/superficie | #D3440E / #101827 | 3.89:1 |
| Oscuro borde/superficie | #94A3B8 / #101827 | 6.93:1 |
| Oscuro borde/página | #94A3B8 / #070B10 | 7.69:1 |
| Oscuro texto/superficie | #CBD5E1 / #101827 | 11.97:1 |
| Oscuro foco/página | #67E8F9 / #070B10 | 13.61:1 |
| Claro hover texto/superficie | #111827 / #FFFFFF | 17.74:1 |
| Claro hover borde/superficie | #334155 / #FFFFFF | 10.35:1 |
| Oscuro hover texto/superficie | #F8FAFC / #101827 | 16.98:1 |
| Oscuro hover borde/superficie | #CBD5E1 / #101827 | 11.97:1 |

P3: HTMLParser comprueba login y ambos roles de registro con un único button de
tipo button, hidden y fuera del formulario. Fixture Node deja de devolver null
para el selector; ejecuta auth-ux-v1.js y theme-switch-v1.js reales en el mismo
contexto. Verifica revelado, clases, aria-pressed, aria-label, texto, trax-theme,
restauración de preferencia, datos y panel desplegado sin bloquear submit. El test
HTML verifica la ausencia de mecanismo de submit accidental; navegador confirma
que el clic/Espacio no navega ni envía el formulario. No hay un mecanismo de tema nuevo.

Validación ejecutada en SQLite en memoria (TestingConfig), sin Docker ni bases compartidas:
- `.venv/Scripts/python.exe -B -m unittest tests.test_auth_ux_redesign_v1 -q`: 14/14 OK.
- `node tests/js/auth_ux.test.js`: OK, incluyendo controlador real.
- `node --check app/static/js/auth-ux-v1.js`: OK.
- Navegador con preview aislado: claro/oscuro, hover real, foco con Espacio,
  campos conservados y panel abierto. A 320 px: 108 x 44 px; sin overflow.
  Capturas nuevas de claro a 320 y oscuro a 390, guardadas fuera del repositorio.
- Consola: cero errores observados.
- `git diff --check`: OK (advertencia de normalización LF/CRLF del handoff).

Limitaciones: no se emularon JavaScript deshabilitado ni prefers-reduced-motion
en el navegador disponible. Se inspeccionaron el fallback HTML, hidden explícito
y media query que elimina transiciones; no equivalen a QA de navegador de esos modos.
No se ejecutó suite completa ni auditoría AA integral. Warning preexistente de
datetime.utcnow en SQLAlchemy; no se alteró dentro de este alcance.

Archivos afectados por FIX-01: app/static/css/auth-ux-v1.css, tests/js/auth_ux.test.js,
tests/test_auth_ux_redesign_v1.py, esta especificación y ACTIVE_HANDOFF.md.
No se cambió autenticación, roles, consentimiento, datos, modelos o dependencias.


## Cierre aprobado de AUTH-UX-001

Timestamp: 2026-10-10T21:35:01-03:00. Dispositivo: laptop. Responsable: implementador local.
Esta entrada actualiza el estado del incremento; los registros anteriores quedan
como antecedentes fechados, sin atribuirles las verificaciones posteriores.

Implementado: login progresivo con fallback sin JavaScript, registros diferenciados
Cliente/Profesional, layout AUTH independiente con logos oficiales y ambos temas,
selector de tema accesible y persistente. Se conservan email como único identificador,
nombre completo, confirmación de contraseña, consentimiento y reglas del servidor.
Google y acceso por nombre de usuario permanecen fuera del incremento.

Retest independiente final: 2026-10-10T20:36:20-03:00, agente
"03 - Testing - Test Executor", chat 01a06392-4542-7532-875d-7120e33afc38.
Dictamen: VERIFICADO EN EL ALCANCE EVALUADO. P2 y P3 cerrados; sin hallazgos pendientes.
Última ejecución Python: 15/15 aprobadas, cero fallos, errores u omisiones:
14 focales AUTH y el contrato de tema de PlatformBrandTest.
Node aprobado; sintaxis de auth-ux-v1.js y theme-switch-v1.js correcta;
git diff --check correcto. Estos resultados pertenecen a Testing; no se reejecutaron
en este cierre documental. Las tandas históricas 29/29, 13/13 y 14/14 no se suman
como cobertura adicional.

QA sin JavaScript satisfactorio mediante harness aislado que retiró scripts:
selector oculto, login y ambos registros operativos con redirecciones 302.
Movimiento reducido comprobado estáticamente en el retest final; sin emulación
disponible, por lo que no se acredita emulación real. No se declara suite completa.
Aprobación visual de Cristian Sánchez en Docker: 2026-10-10T21:11:03-03:00,
comunicada por el responsable en la solicitud de cierre. No se ejecutó Docker en
esta tarea ni se amplía esa aprobación a validaciones no informadas.

Base e integridad: feature/auth-onboarding-foundation,
HEAD b20f41adef46b51bf423b03b4d971072d251b9c7.
Origin https://github.com/cristhian-star/TRAX-PLATFORM.git.
Diez paths pendientes: siete modificados y tres nuevos sin seguimiento; staging vacío.
Los diez SHA-256 coincidieron al iniciar con la salida final del retest citado.
Sólo esta especificación y ACTIVE_HANDOFF.md cambian en este cierre; código y
pruebas mantienen los siguientes hashes del retest:

| Archivo | SHA-256 |
| --- | --- |
| app/routes/auth_routes.py | `b196919cf30d72db53788cd9a8c5e78aacb384fc6ce8158ddaf617cbd5cb27cf` |
| app/static/css/auth-ux-v1.css | `c724202bd75ca2c71c8aaef9d1503b2bde31db657de28c602956c2485c90726b` |
| app/static/js/auth-ux-v1.js | `20dd3c612d9b077cd6e982241efa2926387188b0bac08c5370b05e2852d15429` |
| app/templates/login.html | `f079f96b2d86b523456e1bbc60a85a8c457188c5a501145a91d2de3f797c0453` |
| app/templates/register.html | `f3efcff5e6c302b00e4c63a2ea48f0e1322ed71f00b2e1a4fc17ecf0a00b3e6e` |
| tests/test_auth_ux_redesign_v1.py | `8bf5f359d1bddeb31c5cfe1980fb2a7afbcf7227ff1a0d67b872affeafdc42fc` |
| app/templates/auth_base.html | `880c7c5895ce7bf11de263256b675dd22bf1ca33579cff24690454d0e5fef5b5` |
| tests/js/auth_ux.test.js | `2c5804fecea8baf8cf5149e50b3dd3227402db6f4c8e321ac254b8b50b4c5727` |

Commit propuesto: `feat(auth): refine login and registration UX`.
Descripción:
- Incorporar layout AUTH independiente con logos oficiales y ambos temas.
- Desplegar contraseña progresivamente, conservando el acceso sin JavaScript.
- Diferenciar registro Cliente/Profesional y preservar reglas existentes.
- Integrar selector de tema accesible y persistente.
- Añadir cobertura focal y documentación del incremento.

Commit, push, PR y merge todavía no ejecutados. Sin autorización de integración.
Estado: CIERRE DOCUMENTAL COMPLETADO; COMMIT PREPARADO, PENDIENTE DE AUTORIZACIÓN.
