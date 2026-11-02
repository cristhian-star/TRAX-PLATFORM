# PROF-UX-004 — Conexión interna de cobros simulados

Registro: 2026-10-18T15:28:27-03:00. Responsable: Codex implementador local; laptop confirmada.
Estado: IMPLEMENTADO LOCALMENTE; pendiente de revisión visual y testing independiente.
Motivo: encargo preparado 2026-10-18T14:54:56-03:00, posterior a auditoría de Cobros.
Identificador libre verificado; PROF-UX-003 y sus antecedentes no se sobrescriben.
Rama inicial/final: `feature/professional-workspace-ux`.
HEAD inicial/final: `2e552f2fdc57c152c97f0486050574696f6b250e`.
Origin: `https://github.com/cristhian-star/TRAX-PLATFORM.git`.

## Antecedente y plan ejecutado

Leído íntegramente el informe y su matriz, fechado 2026-10-18T14:25:11-03:00,
APTO PARA PLANIFICAR LA CONEXIÓN INTERNA EN EL ALCANCE EVALUADO. Ubicación externa:
`auditorias/cobros-20261018/INFORME_AUDITORIA_COBROS.md` en el directorio de evidencia
01a0afe3-1eed-7981-8e70-6afbac0e721e del 2026/09/17. Se contrastaron los 41 hashes de
`repository-final.json`: todos coincidían antes de editar. Sus 246 pruebas son
antecedentes recibidos, NO ejecuciones de este incremento. La auditoría no autoriza
reglas nuevas, migraciones ni activación productiva.

Plan aplicado: reutilizar POST/GET/QR 4D y aplicación 4B, agregar proyección mínima de
selector/revisión/historial, composición temporal explícita, controlador de copia y
pruebas aisladas. Sin modificar locks, sesiones dedicadas, constraints o esquema.

## Recorrido y alcance real

Sólo en el lanzador aislado: Crear cobro simulado → contratos propios CONFIRMADA con
importe válido → revisión ARS del total → confirmación firmada y CSRF → POST canónico
creación/replay → resultado con enlace/QR/copia/descarga → historial propio de órdenes.
El banner «SIMULACIÓN — no procesa dinero» está presente en todas las páginas de esta app.
Datos sintéticos, sin cuenta Mercado Pago conectada ni pagos reales. No se equipara orden
creada, enlace copiado o QR descargado con pago, finalización ni autorización fiscal.

La app habitual conserva PROF-UX-003: disponibilidad futura y páginas preparadas.
No hay flag de URL/formulario ni fallback a un proveedor falso por falta de OAuth.
Factura y marca permanecen preparadas. No hay formulario fiscal o importe editable.
La fase actual admite el total de trabajos MANDOBRA confirmados; no define para siempre
el alcance comercial de Cobros. Ampliación separada en el anexo propuesto.

## Composición y aislamiento

`isolated_app(enable_simulation=True)` crea exclusivamente un TemporaryDirectory nuevo,
con prefijo `mandobra-collections-`, bajo el temporal del sistema y `preview.sqlite` nuevo.
No acepta app, motor, ruta de base ni URL aportados por el caller. Valida destino antes de
`create_all` y fixtures. Sobrescribe DATABASE_URL heredado; TESTING/ENV_NAME y motor/path
se verifican, incluida la identidad del motor y ausencia de symlink en el directorio.
Por defecto sin opt-in la factory rechaza la operación. La app normal no llama esta factory.

Reutiliza `InMemoryPSPPaymentOrderCreationAdapter`, `PaymentOrderApplicationService` y
`PaymentOrderDeliveryService` con sessionmaker dedicado. Extensión explícita sólo en esta
app. Flags de webhook, conciliación, efectos, comisión y demo E2E compartida forzados a false.
No se relajan los gates de `simulated_mercadopago_demo` ni se modifica Compose/configuración
habitual. No se construye un ejecutor 4E/4F ni se conecta un adaptador remoto.

URL de prueba estricta: `https://checkout.example.test/payment-orders/` + 64 hexadecimales;
provider fake y live_mode false. La política existente del adaptador real permanece intacta.
No es una URL navegable de checkout: la interfaz lo informa y no ofrece abrirla.
El QR codifica exactamente la URL mostrada/copiada. Descarga/copia son acciones explícitas.
No hay envíos externos, WhatsApp, compartir automático ni peticiones al host reservado.

## Rutas, autorización y consistencia

| Ruta | Comportamiento |
| --- | --- |
| GET `/profesional/facturacion/cobro` | Selector simulado, o preparado normal sin composición. |
| GET `/profesional/facturacion/cobro/<contract_id>` | Revisión propia y token de confirmación, o regreso a preparado. |
| POST `/contratacion/<id>/orden-de-cobro` | POST canónico 4D con CSRF; en simulación exige revisión firmada; 303 a su GET. |
| GET `/contratacion/<id>/orden-de-cobro` | Entrega existente; shell privado sólo en simulación. |
| GET `/contratacion/<id>/orden-de-cobro/qr.png` | QR existente; mismas garantías de vigencia y ownership. |
| GET `/profesional/facturacion/ordenes` | Historial propio; preparado si no hay composición. |

Permisos persistidos: profesional activo, ContractRequest.professional_user_id y
Professional.user_id coherentes, CONFIRMADA. El servicio 4B reautoriza al ejecutar;
la selección no concede permisos. Se mantiene ARS/Decimal y precio acordado canónico.
Identificación mínima del cliente: número interno, no domicilio, teléfono o email.

La revisión firma actor, contrato, importe y versión durante 30 minutos. Un cambio antes
del POST exige revisar de nuevo. El adaptador simulado usa el hook existente
`prepare_payment_order`, ejecutado por 4B antes del claim durable bajo su transacción:
compara el importe canónico bloqueado contra el importe revisado del contexto de request.
No se cambia 4B ni se añade un lock/transacción. El test cambia el precio después de la
comprobación HTTP y verifica rechazo antes de crear reserva. Esto no acredita concurrencia
PostgreSQL: ese gate sigue pendiente y no se sustituye con SQLite.

Reserva/idempotencia existentes preservadas; doble POST reproduce la misma orden.
UNCERTAIN/CALL_IN_PROGRESS mantienen bloqueo y clave; no hay recuperación ni retry nuevo.
Revisión bloqueada no ofrece confirmar. Estados vencidos/cancelados/incoherentes no
entregan QR/enlace. GET no crea ni llama al proveedor. Headers privados de 4D preservados;
se extienden no-store/private/no-referrer a las vistas de Facturación.

## Historial y estados

Proyección mínima de PaymentOrder → PaymentObligation → ContractRequest → Professional,
filtrando ambos owners y profesional de la orden. Orden descendente por fecha/id,
20 órdenes por página y límites seguros de page. Incluye importe, fechas UTC y estado
persistido ACTIVE/EXPIRED/CANCELLED. El plazo vencido se informa por separado, sin mutar GET.
No se infiere pago acreditado ni se consulta proveedor. Entrega canónica revalida cada acceso.
Además se muestran hasta 20 generaciones propias bloqueadas, separadas de órdenes emitidas,
por actor/profesional/contrato coherentes; sin inventar una orden que no se persistió.

Estados distintos: capacidad no disponible en app normal; historial sin órdenes en preview;
generación bloqueada; error de lectura con reintento GET seguro. No se transforma error en
cero registros ni se inventan cobros, saldos, comisiones o créditos.

## Inventario del incremento

[Baseline](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-004/baseline.json) y [estado previo](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-004/status-before.txt).
41 paths previos preservados salvo cambios autorizados siguientes:

- `app/routes/main_routes.py`: conexión de selector/revisión/historial, sin alterar otros flujos.
- `app/templates/base.html`: banner condicional sólo de la app aislada; script/CSP existentes intactos.
- `app/templates/components/_professional_navigation.html`: selección de Facturación en resultado canónico simulado.
- `app/templates/professional_billing.html`: acceso e historial condicionales de simulación.
- `app/static/css/professional-billing.css`: composición mínima del recorrido/copia/QR.
- `docs/HANDOFFS/ACTIVE_HANDOFF.md`, `docs/CHANGELOG.md`: registro nuevo con antecedentes preservados.

Archivos antes limpios intervenidos:
- `app/__init__.py`: headers privados para páginas de Facturación; no composición normal.
- `app/routes/payment_order_delivery_routes.py`: revisión, render privado simulado y gate cerrado; conserva POST/GET canónicos.

Archivos nuevos:
- `app/services/professional_collection_service.py`: DTOs mínimos de lectura, revisión firmada y gate de disponibilidad.
- `app/services/isolated_collection_preview.py`: factory temporal explícita; no importada por create_app.
- `app/templates/professional_collection.html`.
- `app/static/js/collection-copy.js`.
- `scripts/preview_professional_collections.py`.
- `tests/test_professional_collection_ux.py`.
- `tests/js/collection_copy.test.js`.
- `docs/REQUISITOS/PROF_UX_004.md`.
- `docs/REQUISITOS/PROF_UX_004_AMPLIACION_PROPUESTA.md`.

Total previsto conciliado: 18 archivos intervenidos; 52 paths pendientes totales.
INDEX exacto: SHA-256 `46400cbd6de53ddabc3f535fec46cc1d901f17a1ed2001c6c5e1916041acd7a0`.
PROF_UX_002.md y PROF_UX_003.md sin cambios; sin migraciones/modelos/dependencias/ADR/Master Spec.

## Validación actual

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:DATABASE_URL='sqlite:///:memory:'
.venv/Scripts/python.exe -m unittest tests.test_professional_collection_ux tests.test_payment_order_delivery tests.test_payment_order_application tests.test_professional_billing_ux tests.test_professional_workspace_ux_002 -q
node --test tests/js/collection_copy.test.js tests/js/professional_navigation.test.js tests/js/professional_notifications.test.js
```

**68/68 Python**: 13 nuevas, 26 entrega, 16 aplicación, 6 billing y 7 workspace002.
**6/6 Node**: 2 nuevas del controlador real de copia, 4 regresiones navegación/campana.
No se suman repeticiones; no se reejecutaron 246 de auditoría ni suite completa.
[Log focal](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-004/focal-tests.log). APIs legacy/deprecadas y errores SQL inducidos por tests
aparecen en el log, sin fallos finales. Primer intento restringido no pudo abrir SQLite
bajo temporal sandbox; se repitió con permiso local usando sólo temporales exclusivas.
No se clasificó como fallo preexistente de producto.

Cobertura: ownership y roles, cuenta inactiva, parámetros, token/CSRF, precio alterado
antes/después de revisión HTTP, replay/refresh, URL/QR exactos, GET sin proveedor, no efectos,
historial propio/vacío/error/no disponible/bloqueado, cancelación/vencimiento y factory
cerrada/ignora DATABASE_URL externo. Nuevos tests bloquean conexiones socket externas.
Tests 4D conservan falsificaciones, incoherencias y expiración del recorrido existente.
Sin PostgreSQL ni afirmaciones nuevas de locks/carreras/recuperación real.

Chrome headless real contra app aislada, URL y pestaña identificadas:
- 40 combinaciones: selector/revisión/resultado/historial × 320/390/768/1024/1440 CSS px × claro/oscuro.
- innerWidth exacto, sin overflow. Teclado de campana/menú y restauración de foco comprobados.
- Copia real al portapapeles de la URL sintética idéntica al campo; fallback probado con controlador real en Node.
- JS realmente deshabilitado: selector → revisión → POST replay → resultado; entrada readonly copiable manualmente, botón JS oculto, sin overflow a 320.
- Reduced motion realmente emulado: media query true y cero animaciones activas.
- Cero excepciones JS y cero solicitudes externas en la matriz. Se observaron 45 mensajes
  CSP repetidos del script inline heredado. Se conserva esta observación separada; no se
  cambia CSP ni se declara consola completamente limpia. No auditoría AA integral.

[Resultados de navegador](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-004/browser-results.json). Capturas sintéticas duraderas:
[selector 390 claro](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-004/selector-390-light.png), [selector 390 oscuro](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-004/selector-390-dark.png),
[selector 1440 claro](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-004/selector-1440-light.png), [selector 1440 oscuro](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-004/selector-1440-dark.png),
[resultado 390 claro](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-004/result-390-light.png), [resultado 390 oscuro](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-004/result-390-dark.png),
[resultado 1440 claro](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-004/result-1440-light.png), [resultado 1440 oscuro](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-004/result-1440-dark.png).
No son cobros reales. Sintaxis Python/JS, UTF-8 y git diff --check comprobados al cierre.

## Reproducir y detener exclusivamente el preview

Desde la raíz del repositorio, sin Docker:
```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe .\scripts\preview_professional_collections.py
```

Puerto fijo propio **54954**, bind **127.0.0.1**, sin debug/reloader. No terminar otro
proceso si el puerto está ocupado. Cada arranque genera una base nueva en
`%TEMP%/mandobra-collections-<aleatorio>/preview.sqlite`, cuya ruta imprime el lanzador.
Ingreso sintético en `http://127.0.0.1:54954/login`:
`profesional@example.test` / `Simulacion-local-2026!` (credencial pública sólo de fixture).
Después `http://127.0.0.1:54954/profesional/facturacion/cobro`.
El campo de orden generado usa un host reservado no navegable; no abrirlo como checkout.

Detener con **Ctrl+C en esa misma consola**; el context manager dispone sesiones/motor y
elimina únicamente el temporal creado. Si una herramienta mata abruptamente el proceso,
verificar su terminación y retirar sólo el directorio exacto impreso por ese arranque,
validando primero que está bajo TEMP. Nunca borrar temporales ajenos por comodín.
Los previews propios de esta sesión se detuvieron y sus bases específicas se retiraron;
se conservan capturas/logs fuera del repositorio.

## Pendientes y cierre

Revisión visual y testing independiente. Anticipos, parciales y trabajos externos requieren
las decisiones/migraciones del anexo BORRADOR. OAuth real, política remota, worker de
conciliación, retornos, recuperación de incertidumbre y activación productiva conservan sus
dependencias; no quedan habilitados por esta conexión. ARCA y efectos PRO fuera de alcance.
No hubo Git mutable, Docker compartido, deploy, commit, push, PR ni merge. Staging vacío,
HEAD y rama preservados. Sin merge por falta de autorización. No se verificó sincronización
GitHub. Esta entrega no es Cobros completo ni preparación productiva.


## Corrección focal P2 — 2026-10-18T18:52:15-03:00

Responsable: Codex implementador local; laptop. Encargo: 2026-10-18T18:42:34-03:00.
Hallazgo independiente original: 2026-10-18T17:06:18-03:00; P2 en los fallbacks de
revisión e historial sin composición simulada. Se conserva ese dictamen: este registro
es una corrección local, no una aprobación ni un reemplazo del retest independiente.

Identidad inicial/final: `feature/professional-workspace-ux`, HEAD
`2e552f2fdc57c152c97f0486050574696f6b250e`, origin
`https://github.com/cristhian-star/TRAX-PLATFORM.git`. Raíz esperada confirmada, staging
vacío y 52 paths pendientes antes/después. Inventario y hashes iniciales registrados.

Causa: ambas ramas invocaban `url_for` sin importarlo desde Flask, devolviendo 500
al intentar la redirección al estado preparado. Corrección productiva única: incorporar
`url_for` al import existente de `app/routes/main_routes.py`. Sin modificar rutas,
CSRF, ownership, composición, CSP ni reglas de negocio.

Pruebas añadidas en `tests/test_professional_billing_ux.py`: cuatro métodos para GET
`/profesional/facturacion/cobro/1`, su variante `?enable_simulation=1`,
`/profesional/facturacion/ordenes` y su variante `?simulation=true`; un quinto método
comprueba anónimo y CLIENTE persistido, incluso con rol de sesión manipulado.
Aplicación normal vía create_app, sin extensión de simulador ni servicio de entrega,
fixtures sintéticos en SQLite descartable en memoria. Se comprueban 302 a
`/profesional/facturacion/cobro`, 200 preparado al seguirlo, ausencia de activación por
query, órdenes/obligaciones/reservas en cero, ausencia de DML/commit y de llamadas al
servicio/adaptador/red. No se usa la base compartida.

Evidencia antes del import: 5 pruebas ejecutadas, 4 fallos `500 != 302` y una aprobada
(restricciones). No se revirtieron archivos. Después: **50/50 pruebas aprobadas** en
24.274 segundos, cinco nuevas y 45 focales existentes. Los cinco casos repetidos en
la segunda ejecución no se cuentan como cobertura adicional.

Comandos ejecutados con PYTHONDONTWRITEBYTECODE=1 y DATABASE_URL=sqlite:///:memory::
```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_professional_billing_ux.CollectionPreparedFallbackTest -v
.\.venv\Scripts\python.exe -m unittest tests.test_professional_billing_ux tests.test_professional_collection_ux tests.test_payment_order_delivery -v
```
El segundo comando comprueba también el recorrido aislado real mediante cliente Flask:
selector, revisión, POST/replay, resultado y QR exacto, historial y bloqueos. No se realizó
una nueva revisión visual en navegador. Los 40 casos de navegador y las seis pruebas
Node anteriores permanecen como evidencia histórica, no como ejecuciones de esta corrección.
Sin PostgreSQL ni suite completa. Sintaxis AST Python, UTF-8 sin BOM/NUL/U+FFFD y
`git diff --check` comprobados; avisos de finales de línea de Git sin normalización.

Archivos afectados: import de main_routes, pruebas de billing, este requisito,
ACTIVE_HANDOFF y CHANGELOG. Los otros archivos y docs/INDEX.md conservan sus hashes.
Sin archivos nuevos en el repositorio. Evidencia permanente fuera del repositorio:
[PROF-UX-004-P2](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-004-P2/)
(baseline, before.log, after.log, inventario y estado final).
Sin Git mutable, Docker, bases/perfiles compartidos ni servicios de preview persistentes.
Estado: **P2 CORREGIDO LOCALMENTE; PENDIENTE DE RETEST INDEPENDIENTE.**


## Cierre documental de QA — 2026-10-18T19:18:45-03:00

Responsable del registro: Codex local; laptop. Estado: cierre documental completado.
Se incorpora el dictamen independiente del **2026-10-18T19:03:49-03:00**:

**P2 CERRADO — PROF-UX-004 VERIFICADO EN EL ALCANCE EVALUADO.**

Fuente durable leída: [INFORME_RETEST_P2_PROF_UX_004.md](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/prof-ux-004-p2-retest/INFORME_RETEST_P2_PROF_UX_004.md).
Se conservan el hallazgo original del 2026-10-18T17:06:18-03:00, su corrección local
y todas las ejecuciones anteriores; este cierre no los reescribe ni suma repeticiones
como cobertura adicional. La corrección productiva se limitó al import Flask de `url_for`.

Resultados atribuidos exclusivamente al retest independiente:

- Cinco regresiones nuevas: **5/5 aprobadas**; focales seleccionadas: **8/8 aprobadas**.
- Las cuatro solicitudes normales de revisión/historial, incluidas las variantes
  `?enable_simulation=1` y `?simulation=true`, respondieron **302** al destino canónico
  `/profesional/facturacion/cobro`; al seguirlas, **200** con estado preparado.
- Parámetros HTTP sin activación simulada. Anónimo: 302 a login; CLIENTE persistido,
  aun con rol de sesión falsificado: 403. Comprobados en las cuatro solicitudes.
- Sin escrituras financieras: órdenes/obligaciones/reservas 0/0/0; cero DML en GET
  y cero llamadas al servicio de creación, adaptador o red en la aplicación normal.
- Recorrido simulado idempotente: dos POST 303, resultado/historial/QR 200,
  una llamada al adaptador, una orden y una reserva.
- Evidencia visual y Node anterior vigente por continuidad de hashes; no se cuenta
  como ejecución nueva. Sin hallazgos nuevos P0–P3.

El retest no ejecutó suite completa, Node, navegador ni PostgreSQL. Su primer intento
auxiliar se detuvo por sys.path del harness externo, luego corregido fuera del repositorio;
no fue un fallo del producto. Las 50 pruebas de la corrección local quedan como antecedente
distinto de las 5 + 8 pruebas del retest. En esta sesión documental no se ejecutaron pruebas.

Limitaciones conservadas: PostgreSQL no validado, CSP heredada, proveedor simulado y
activación productiva pendiente. No se declara certificación AA, integración, despliegue
ni preparación productiva. Las dependencias comerciales y técnicas anteriores siguen vigentes.

Identidad inicial/final: rama `feature/professional-workspace-ux`, HEAD
`2e552f2fdc57c152c97f0486050574696f6b250e`, origin esperado confirmado;
52 paths pendientes y staging vacío. Sólo se actualizan este requisito, ACTIVE_HANDOFF
y CHANGELOG. Código, pruebas, templates, CSS, JavaScript e INDEX preservados por hashes.
Sin Docker, bases compartidas ni operaciones Git mutables. git diff --check ejecutado
como control documental, sin nuevas pruebas. Próximo paso: decisión humana de continuidad
sobre el alcance verificado; no existe autorización de integración en este cierre.
