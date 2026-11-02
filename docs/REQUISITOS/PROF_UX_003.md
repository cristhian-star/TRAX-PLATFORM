# PROF-UX-003 — Facturación y cobros: pantalla principal

Registro: 2026-10-18T13:56:00-03:00. Responsable: implementador local Codex, laptop confirmada por Cristian.
Estado: IMPLEMENTADO LOCALMENTE; pendiente de revisión visual y testing independiente.
Motivo: encargo preparado el 2026-10-18T13:23:12-03:00 y boceto adjunto aprobado.
Identificador libre comprobado antes de crear este documento.
Rama inicial/final: `feature/professional-workspace-ux`.
HEAD inicial/final: `2e552f2fdc57c152c97f0486050574696f6b250e`.
Origin: `https://github.com/cristhian-star/TRAX-PLATFORM.git`.

## Alcance construido y correspondencia visual

Pantalla privada con título, explicación breve, dos tarjetas principales de factura y cobro,
marca comercial secundaria e historial sencillo. Se conserva el shell profesional, logos
oficiales, menú, cuenta, campana y mecanismo de tema. Las tarjetas se apilan en móvil.
Se usan componentes `.trax-card`/`.trax-button` y tokens `--trax-ds-*`, sin nueva paleta.

Las dos acciones muestran «Disponible próximamente» ANTES de abrirlas. Son enlaces a
páginas GET informativas, sin formularios fiscales, confirmaciones ni escrituras financieras.
Marca y cuentas también abre una página preparada con regreso. No hay cargador de logo.
El dibujo de borrador es decorativo y no es un comprobante: no contiene datos fiscales.
El dibujo de enlace sustituye al QR del boceto: no se muestra un QR simulado o funcional.
No se copian nombres, cifras, estados de pago ni el plan PRO ilustrativos.

Se reemplaza el historial ilustrativo por «Tu historial estará disponible próximamente».
No se confunde capacidad no disponible con lista vacía, cero, fallo o pago confirmado.
No hay «Ver historial» sin destino ni enlaces `#`. Los datos del encabezado pertenecen
al usuario autenticado; avatar y portada no se reutilizan como marca de facturación.

## Inspección y capacidades

| Fuente local | Evidencia / decisión |
| --- | --- |
| `app/routes/main_routes.py`, `profesional_facturacion` | URL existente conservada; antes tenía tres paneles informativos. |
| `app/utils/decorators.py`, `role_required` | Comprueba usuario persistido activo y rol PROFESIONAL; aplicado también a accesos directos preparados. |
| `app/models/payment_order.py` | Órdenes de servicios con obligación y profesional; ACTIVE/EXPIRED/CANCELLED no son estados de pago recibido. |
| `app/models/payment_obligation.py` | Obligación vinculada a ContractRequest, no a facturas fiscales o comprobantes de suscripción. |
| `app/services/payment_order_application_service.py` | Creación interna por contrato y actor; no se invoca desde estas páginas. |
| `app/services/payment_order_delivery_service.py` | Lectura de checkout y QR condicionada a autorización, reserva y vigencia; no es un historial consolidado de facturas/cobros. |
| `app/routes/payment_order_delivery_routes.py` | POST por contrato y GET de checkout/QR detrás de `CHECKOUT_PRO_DELIVERY_ENABLED`; no se enlazan ni activan aquí. |
| `app/services/professional_media_service.py` | Avatar, portada y galería existentes no equivalen a marca fiscal autorizada. |
| `app/templates/professional_workspace_base.html` | Shell, notificaciones con ownership, formularios POST/CSRF y tema reutilizados sin cambios. |

No se encontró un modelo de factura fiscal ni servicio de historial conjunto adecuado a la
semántica del boceto. Se mantiene la capacidad de historial pendiente; no se consulta una
fuente alternativa para aparentar pagos confirmados. Los estados con registros/sin registros/error
no se inventan: no son aplicables a este historial todavía no habilitado. No se agregan
consultas financieras; se conserva la lectura del contexto profesional existente.

La Master Spec histórica describe una plataforma sin procesamiento de pagos; REQ-003 y
el código contienen capacidad interna posterior. Se distingue esa base interna de la
activación productiva, que este incremento no autoriza. Los estándares aún referencian DS v1;
se aplica DS v2 por encargo explícito y contrato canónico vigente, sin editar Master Spec/ADR.

## Rutas y permisos

| GET | Propósito |
| --- | --- |
| `/profesional/facturacion` | Pantalla principal, misma URL y endpoint anteriores. |
| `/profesional/facturacion/factura` | Preparación de emisión futura. |
| `/profesional/facturacion/cobro` | Preparación del enlace de pago y su QR. |
| `/profesional/facturacion/configuracion` | Preparación de marca y cuentas. |

Las tres entradas nuevas comparten endpoint `main.profesional_facturacion_preparacion`
con defaults explícitos y URLs generadas con `url_for`. Retorno al endpoint canónico.
La selección `aria-current="page"` incluye únicamente estos subdestinos de Facturación.
POST no habilitado (405), destino desconocido 404. Anónimo redirigido, CLIENTE rechazado,
cuenta suspendida/baneada redirigida; no se aceptan identificadores financieros del navegador.
Sin cambios de roles, CSRF, elegibilidad, suscripciones, contratos o acceso a otras secciones.

## Inventario diferencial

Línea base externa: [baseline.json](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-003/baseline.json) y
[status-before.txt](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-003/status-before.txt). Había 35 paths pendientes y staging vacío.

Modificados dentro del trabajo previo:
- `app/routes/main_routes.py`: tres destinos GET privados mínimos.
- `app/templates/components/_professional_navigation.html`: selección de Facturación en sus subdestinos.
- `app/templates/professional_billing.html`: nueva composición y enlaces preparados.
- `tests/test_professional_workspace_ux_002.py`: expectativa del texto de preparación actualizado.
- `docs/HANDOFFS/ACTIVE_HANDOFF.md`: nueva entrada conservando antecedentes.

Archivos nuevos:
- `app/services/professional_billing_view_service.py`: contenido de presentación de destinos; sin consultas/comandos financieros.
- `app/static/css/professional-billing.css`: composición encapsulada y regla del menú nativo cerrado limitada a esta pantalla.
- `app/templates/professional_billing_prepared.html`: destino informativo reutilizable.
- `tests/test_professional_billing_ux.py`: seis pruebas focales permanentes.
- `docs/REQUISITOS/PROF_UX_003.md`: este requisito.

Archivo antes limpio actualizado: `docs/CHANGELOG.md`, según checklist de estándares.
Total: 11 archivos intervenidos; 41 paths pendientes totales. INDEX permanece byte a byte
igual: SHA-256 `46400cbd6de53ddabc3f535fec46cc1d901f17a1ed2001c6c5e1916041acd7a0`.
Sin dependencias, modelos, migraciones, instrumentación ni cambios globales de tema.

## Validación ejecutada

Entorno exclusivo: SQLite en memoria, TestingConfig y fixtures sintéticos de vistas.
No Docker, bases compartidas, PostgreSQL, migraciones ni seeds. No se afirman garantías
transaccionales nuevas ni se sustituye un gate PostgreSQL.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:DATABASE_URL='sqlite:///:memory:'
.venv/Scripts/python.exe -m unittest tests.test_professional_billing_ux tests.test_professional_workspace_ux_002 tests.test_professional_workspace_ux tests.test_professional_urgencies_ux -q
node tests/js/professional_navigation.test.js
node tests/js/professional_notifications.test.js
```

Resultado final: **35/35 Python** (6 nuevas y 29 regresiones), **4/4 Node** (2 navegación,
2 notificaciones). Node ejecutado con runtime local disponible; sin instalar paquetes.
[Log Python](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-003/python-tests.log). Repeticiones no se suman como cobertura adicional.
Las 75 pruebas históricas de PROF-UX-002 no se presentan como ejecutadas sobre este código.
El log incluye warnings de deprecación y el error inducido por el test de estadísticas;
resultado unittest OK. No se ejecutó suite completa ni un gate financiero.

Pruebas focales: permisos persistidos y cuenta activa en las cuatro URLs; enlaces/regreso;
selección del menú; ausencia de escrituras SQL/commit/creación financiera durante GET;
POST rechazado; sin datos ilustrativos, ajenos o QR; contenido renderizado en servidor.
No hay JavaScript nuevo. Control de sintaxis Python mediante AST, UTF-8 sin BOM/NUL/U+FFFD,
`git diff --check` y staging vacío. Advertencia Git de futura conversión LF/CRLF en INDEX:
no se modificó el archivo ni se normalizó.

### Navegador real y evidencias

Chrome headless local con Playwright ya disponible, contra app aislada en loopback con
SQLite en memoria. Pestaña y URL verificadas antes de operar. Preview identificado por
fixture sintético «Técnica Uno», sin transacciones financieras de ejemplo.

- Principal: **10 combinaciones**, 320/390/768/1024/1440 CSS px × claro/oscuro;
  `innerWidth` verificado, sin overflow. Capturas por combinación.
- Tres destinos preparados a 390 y 1440 px: seis verificaciones adicionales, sin overflow,
  selección correcta y regreso funcional.
- Teclado: campana abre con Enter, cierra con Escape y clic externo; foco restaurado.
  Menú móvil abre con Enter y devuelve foco al cerrar con Escape; outline visible.
- Selector real de tema y persistencia al pasar a un destino preparados: comprobados.
- Botones principales >=48 px de alto. Foco de Crear cobro desplazado al centro y por encima
  de la barra inferior; espacio final de página preservado.
- JavaScript realmente deshabilitado: enlaces de los tres destinos y regreso funcionales
  a 320 px; menú nativo capturado a 390. Sin overflow final tras carga completa de estilos.
- Sin JS, la preferencia localStorage no se aplica: fallback claro existente. Dos valores
  almacenados ensayados no equivalen a validar dos temas sin JS; tema oscuro sin JS pendiente
  de un futuro mecanismo de tema. No se altera ese mecanismo en este incremento.
- Reduced motion realmente emulado: media query true y cero animaciones activas en ambos temas.
- Sin errores JS ni respuestas HTTP >=400 observadas en la matriz de navegador.
- Contraste focal de texto de botón: #fff/#d3440e **4,56:1** claro;
  #0b1220/#ff8a4c **8,02:1** oscuro. Texto secundario sobre tarjeta: **10,35:1 / 11,97:1**.
  No es certificación AA ni auditoría integral de accesibilidad.

Se detectó contenido del menú cerrado fuera de pantalla sin JS. Se limita su display
cuando está cerrado únicamente bajo `professional-billing-page`. Las mediciones finales
esperan carga completa de estilos y fin del scroll; no confunden geometría transitoria
con la final. No se atribuye un fallo a la línea base sin comparación.

[Resultados matriz](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-003/browser-results.json), [accesibilidad](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-003/accessibility-results.json)
y [tema](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-003/theme-results.json). Capturas actuales:
[1440 claro](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-003/billing-1440-light.png), [1440 oscuro](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-003/billing-1440-dark.png),
[390 claro](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-003/billing-390-light-viewport.png), [390 oscuro](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-003/billing-390-dark-viewport.png).
El directorio externo incluye capturas completas y los scripts de QA. `nojs-diagnostic.png`
es diagnóstico y no evidencia de cierre. Ninguna captura acredita facturas o pagos reales.

## Dependencias y límites futuros

- ARCA: emisión y autorización fiscal, tratamiento definitivo del comprobante y su QR fiscal,
  configuración y revisión propias. No se solicitan credenciales ni certificados aquí.
- Marca profesional: carga y autorización específicas; no equivale a avatar/portada.
- Cobros: futura activación de Checkout de Mercado Pago y QR que codifique exactamente el
  mismo enlace. No QR de posnet; separado del QR fiscal. No se modifica backend 4B/4C/4D.
- Historial: definición y fuente de facturas/cobros reales, estados canónicos, ownership,
  paginación y errores de lectura. No equiparar orden/enlace/retorno a pago recibido.
- Suscripción MANDOBRA: comprobantes separados de servicios al cliente.
- Trabajos obtenidos fuera de MANDOBRA: definición pendiente; esta UI no impone un contrato
  como entrada obligatoria ni implementa trabajos externos.

Sin integración, deploy, certificación AA ni preparación productiva. Staging vacío,
HEAD conservado, sin commit/push/PR/merge. No se hizo merge por falta de autorización.
Cristian administra manualmente QA compartido y operaciones Git.

URLs del preview temporal (detenido al cerrar): `http://127.0.0.1:54953/profesional/facturacion`
y sus subrutas. Para revisar en el QA existente, con sesión profesional:
`http://127.0.0.1:5050/profesional/facturacion` (no iniciado ni reconstruido en esta sesión).
