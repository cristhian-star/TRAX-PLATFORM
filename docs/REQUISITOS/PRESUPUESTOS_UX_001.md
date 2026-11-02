# PRESUPUESTOS-UX-001 — Completar el recorrido existente

Registro: 2026-10-19T21:11:34-03:00. Responsable: Codex local; laptop.
Estado: IMPLEMENTADO LOCALMENTE, pendiente de revisión visual y testing independiente.
Prioridad autorizada: 2026-10-19T20:21:08-03:00. Exclusivamente Presupuestos;
pagos y cobros postergados. Rama `feature/professional-workspace-ux`, HEAD base
`2e552f2fdc57c152c97f0486050574696f6b250e`; origin TRAX-PLATFORM esperado confirmado.

## Comportamiento y fuentes reales

- `/profesional/presupuestos` presenta el listado canónico con filtros GET categoría/zona,
  paginación visible y acceso a enviados. `/presupuestos` sigue operativo; ambas entradas
  reutilizan el mismo handler y permisos. Se muestran solicitudes disponibles, no una
  bandeja de asignaciones personales inexistente.
- Detalle `/presupuestos/<id>` y `/presupuestos/mis-enviados` conservan shell profesional,
  menú seleccionado, tema y notificaciones. El CLIENTE usa el layout público autenticado.
- Se reutilizan `budget_service`, `operation_view_service`, `BudgetRequest`, `BudgetOffer`
  y `ContractRequest`. No se modifica la máquina de estados ni se crean modelos/migraciones.
- Oferta POST `/<id>/ofertar`: perfil completo, límites existentes, rango/visita/plazo/condiciones,
  una oferta por profesional/solicitud y validaciones vigentes. El perfil incompleto recibe
  un enlace concreto para completarlo. La confirmación de envío requiere una oferta real.
- Cliente propietario: compara ofertas, despliega confirmación antes de adjudicar o cancelar
  mediante details/summary y POST con CSRF. No depende de JavaScript.
- Adjudicación `/<id>/adjudicar/<offer_id>` reutiliza `award_budget_offer` y la derivación
  idempotente existente: solicitud ADJUDICADA, oferta ADJUDICADO y contrato CREADA.
  Esto no equivale a trabajo finalizado; CONFIRMADA mantiene su significado canónico.
- Ambos participantes encuentran el contrato derivado. Su detalle usa shell privado sólo
  para el profesional en un contrato BUDGET; los restantes contratos mantienen su layout.
- Seguimiento distingue adjudicación propia, adjudicación ajena, cancelación/cierre y espera.
  El propietario conserva `/presupuestos/mis-solicitudes` y sus filtros/operaciones reales.
- DSv2 encapsulado en `.budget-page`, foco visible, controles y confirmaciones accesibles,
  una columna móvil, estados vacíos y errores de validación del servidor conservados.

## Auditoría focal y límites

Operativo: creación CLIENTE, recuperación del formulario, listado profesional, ofertas,
comparación privada del propietario, cancelación, adjudicación, contratos y notificaciones.
Se completó su conexión visual y navegación, sin ampliar roles, ownership ni CSRF.
La selección de datos personales sigue vinculada al usuario autenticado.

Discrepancia documentada: decisiones UX-06A describen al profesional como solicitante,
pero las rutas actuales y `test_budget_request_ux06a` restringen creación y gestión a CLIENTE.
Se preserva la regla ejecutable; ampliar solicitantes requiere una decisión posterior.
No hay nueva asignación automática, nuevos canales de contacto, pagos, impuestos ni facturación.
Las estimaciones siguen siendo preliminares, no importes finales garantizados.
El listado conserva la consulta existente en memoria; optimización SQL/paginación de grandes
volúmenes queda pendiente y no se presenta como realizada.

## Archivos de este incremento

- `app/routes/main_routes.py`: entrada profesional delegada al listado canónico.
- `app/routes/operation_routes.py`: contexto de layout y paginación; contrato BUDGET.
- `app/services/operation_view_service.py`: layout, estado de seguimiento y contrato del adjudicado.
- `app/templates/budget_layout.html` (nuevo): layout por rol persistido.
- `app/templates/components/_professional_navigation.html`: selección Presupuestos.
- `app/templates/listado_presupuestos.html`: filtros/listado/paginación privada.
- `app/templates/detalle_presupuesto.html`: oferta, confirmación y seguimiento.
- `app/templates/mis_presupuestos_enviados.html`: estados reales y shell.
- `app/templates/mis_solicitudes_presupuesto.html`: cancelación confirmable sin JS y vacío.
- `app/templates/contract_detail.html`: shell condicional para derivación BUDGET.
- `app/static/css/budget-workflow.css` (nuevo): estilos locales, temas y responsive.
- `tests/test_budget_workflow_ux.py` (nuevo): siete pruebas focales del recorrido.
- `tests/test_budget_request_ux06a.py`: expectativa de Inicio acorde a su redirección privada.
- Este requisito (nuevo), `docs/HANDOFFS/ACTIVE_HANDOFF.md` y `docs/CHANGELOG.md`.

## Validación ejecutada

SQLite en memoria, datos sintéticos, sin Docker ni PostgreSQL compartido:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:DATABASE_URL='sqlite:///:memory:'
.venv/Scripts/python.exe -m unittest tests.test_budget_workflow_ux tests.test_sprint7_budget_to_contract tests.test_budget_request_ux06a tests.test_professional_workspace_ux tests.test_professional_workspace_ux_002 -q
.venv/Scripts/python.exe -m unittest tests.test_sprint7_contracting_core tests.test_sprint7_contract_review_routes_ui_moderation tests.test_budget_creation_recovery -q
```

Resultados finales: **55/55 + 34/34 = 89 pruebas aprobadas**, siete nuevas incluidas.
Cobertura: envío duplicado, adjudicación repetida con un solo contrato, ownership entre clientes,
permisos anónimo/profesional, CSRF, XSS escapado, filtros/vacío, lectura sin commit,
perfil incompleto, cancelación y seguimiento, regresiones contractuales/reviews/recuperación.
No se cuentan repeticiones como cobertura adicional. Primer intento: error de limpieza de
TemporaryDirectory del sandbox y regresión por import ContractRequest omitido (corregido).
También se corrigió una expectativa de Inicio anterior al shell privado y una aserción que
confundía el título de una notificación de cancelación con una tarjeta del listado.

Chrome real: **30 combinaciones**, cinco pantallas × 320/390/1440 px × claro/oscuro;
200 y sin overflow horizontal. Verificados envío, adjudicación sin JavaScript, acceso al
contrato desde ambos actores, vacío, foco y emulación real de movimiento reducido.
Ajuste CSS final del resumen/avatar: seis comprobaciones adicionales sobre el detalle cliente
con foco y sin overflow; no son seis pantallas nuevas. Capturas escritorio/móvil de ambos temas.
Sin pageerror ni recursos HTTP fallidos. La consola registra 37 bloqueos del mismo script inline
por CSP; no se declara consola limpia. No se modifica esa política global.

Controles de entrega: sintaxis Python mediante AST, UTF-8 sin BOM/NUL/U+FFFD en archivos
intervenidos y `git diff --check`. Sin nuevas dependencias, migraciones ni JavaScript productivo.
No se ejecutó Node, suite completa, PostgreSQL ni auditoría AA integral.

## Evidencias y revisión

[Resultados de navegador](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PRESUPUESTOS-UX-001/browser-results.json),
[ajuste final CSS](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PRESUPUESTOS-UX-001/final-css-check.json),
[pruebas focales](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PRESUPUESTOS-UX-001/tests-final.log),
[regresiones](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PRESUPUESTOS-UX-001/regressions.log).
Capturas en la misma carpeta durable fuera del repositorio; prefijos `pro-` y `cliente-`.
Preview aislada `preview.py`, datos sintéticos únicamente, puerto 54955; se detiene al terminar.
Rutas de revisión en una aplicación local iniciada por el responsable:
`/profesional/presupuestos`, `/presupuestos/mis-enviados`, `/presupuestos/<id>`,
`/presupuestos/mis-solicitudes` y `/contratacion/<id>` para el adjudicado.

No hubo commit, push, PR ni merge. No se verificó sincronización remota por red.
INDEX y archivos ajenos conservados por comparación SHA-256 con baseline externo.
Próximo paso: revisión visual humana y testing independiente antes del cierre.

Inventario final: 16 archivos intervenidos; 55 paths pendientes iniciales y 67 finales.
Rama y HEAD conservados, staging vacío; archivos ajenos e INDEX sin variación de hashes.


## Corrección focal de dos P2 — 2026-10-19T22:02:37-03:00

Responsable: Codex local, laptop. Solicitud 2026-10-19T21:40:29-03:00.
Estado: **P2 CORREGIDOS LOCALMENTE; PENDIENTES DE RETEST INDEPENDIENTE.**
No sustituye el dictamen independiente ni cierra el incremento.

Identidad inicial/final: origin TRAX-PLATFORM esperado, rama `feature/professional-workspace-ux`,
HEAD `2e552f2fdc57c152c97f0486050574696f6b250e`, staging vacío, 67 paths pendientes.
Baseline SHA-256 externo tomado antes de editar; INDEX y todo archivo ajeno conservados.

### Evidencia antes y causa

La reproducción usó `/presupuestos/2/ofertar` con una solicitud sintética válida (el identificador
faltaba en la URL abreviada del encargo). NaN en monto_desde devolvió **500**. El rango 200–100
produjo **302** y luego detalle **200** sin conservar monto 200, plazo ni condiciones.
[Reproducción JSON](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PRESUPUESTOS-UX-001-P2/reproduction.json) y [regresiones antes del cambio](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PRESUPUESTOS-UX-001-P2/before.log).
Los dos métodos ejecutados antes fallaron, con 19 fallos de aserción/subcasos; no son 19 tests nuevos.
Causas: Decimal admite valores no finitos que fallan al compararse; el manejo de error redirigía
sin mantener los valores POST y el template no repoblaba sus controles.

### Corrección mínima

- `app/services/budget_service.py`: `is_finite()` antes de comparaciones, con el mismo ValueError
  de validación. Conserva conversión Decimal, obligatoriedad, precisión y no negatividad/rango.
  Aplica a monto_desde/monto_hasta y precio_visita cuando está presente, usando el parser existente.
- `app/routes/operation_routes.py`: errores recuperables renderizan detalle con **400**, contexto
  autorizado y sólo seis campos permitidos del POST. No guarda textos en URL ni sesión, no captura
  excepciones generales. Solicitud inexistente 404 y propia del profesional 403; decoradores de
  autenticación, rol y perfil completo siguen presentes. El envío válido conserva la redirección
  exitosa y la prevención de duplicados.
- `app/templates/detalle_presupuesto.html`: repuebla importes, plazo, condiciones y selección de
  visita con escape automático Jinja. CSRF vuelve a generarse mediante el mecanismo vigente.
- `tests/test_budget_workflow_ux.py`: tres métodos nuevos. Matriz de NaN/sNaN/Infinity/-Infinity/
  conversión inválida en ambos importes y visita (15 subcasos); ausencia de ofertas, contratos,
  cambio de estado y llamada de éxito; conservación de campos con rango inválido, plazo vacío y
  visita requerida vacía; XSS escapado, CSRF real, corregir/reintentar sin duplicados; campos
  obligatorios/negativos y valores cero/centavos preservados.
- Documentos: este requisito, ACTIVE_HANDOFF y CHANGELOG, con antecedentes íntegros.

Total: **7 archivos intervenidos**, ningún nuevo path. No se cambian modelos, migraciones,
CSS, JavaScript, roles, contratos ni la decisión pendiente de Producto sobre solicitantes.

### Validación posterior

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:DATABASE_URL='sqlite:///:memory:'
.venv/Scripts/python.exe -m unittest tests.test_budget_workflow_ux tests.test_sprint7_budget_to_contract tests.test_budget_request_ux06a -q
```

**36/36 aprobadas**: tres métodos nuevos y 33 existentes, sobre SQLite en memoria.
[Log final](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PRESUPUESTOS-UX-001-P2/after.log). Incluye permisos, CSRF, oferta y adjudicación idempotente.
Las 89 pruebas y la matriz anterior se mantienen como antecedentes; no se cuentan como ejecución nueva.
AST Python, UTF-8 sin BOM/NUL/U+FFFD y `git diff --check` verificados. No PostgreSQL, suite completa ni Node.

Chrome real: **8 recorridos** (390/1440 × claro/oscuro × JS/sin JS), error 400, seis campos
conservados, corrección/reenvío exitoso y sin overflow. [Resultados](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PRESUPUESTOS-UX-001-P2/browser-results.json).
Capturas `error-<ancho>-<tema>-js/nojs.png` en la misma carpeta durable externa.
Con JavaScript se utilizó clic; sin JavaScript, envío nativo por Enter. El primer intento de clic
automatizado en móvil sin JS no produjo POST y agotó la espera; no se atribuye una causa de producto
sin evidencia. La comprobación posterior por teclado fue satisfactoria; clic móvil sin JS queda
para el retest independiente. Para observar ambos estilos sin JS, el controlador de prueba aplica
la clase CSS de tema: no se afirma persistencia ni cambio de tema operativo sin scripts.
Sin errores pageerror en la matriz final; no se declara auditoría AA ni consola global limpia.
CSP heredada permanece fuera de alcance.

Preview descartable detenida al terminar; sin Docker, bases compartidas ni Git mutable.
Sin commit/push/PR/merge: revisión independiente y autorización aún pendientes.
Próximo paso: retest de ambos P2, incluyendo las limitaciones de navegador declaradas.


## Cierre técnico independiente — 2026-10-20T19:35:42-03:00

**P2 CERRADOS — PRESUPUESTOS-UX-001 VERIFICADO EN EL ALCANCE EVALUADO.**
Dictamen independiente: 2026-10-20T14:09:02-03:00. Registro: Codex local, laptop.
Evidencia atribuida al retest: 36/36 pruebas, 10 combinaciones adversariales, ocho
combinaciones de navegador y tap móvil adicional sin JavaScript aprobados.
[Carpeta durable](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/presupuestos-ux-001-p2-independent-retest), con focused-regressions.log, adversarial-results.json,
browser-independent-results.json y mobile-nojs-touch.json leídos en esta sesión.
La ruta recibida omitía la barra anterior a .codex; se referencia la ubicación comprobada.
El tap adicional resuelve la comprobación pendiente del clic móvil sin JavaScript.
No se repitieron pruebas para este cierre documental ni se suman resultados históricos
como ejecuciones nuevas. Se conservan hallazgos y correcciones anteriores.
Pendientes: profesionales como solicitantes (Producto), PostgreSQL, certificación AA
y dispositivo móvil físico. No implica integración, despliegue ni preparación productiva.
Rama feature/professional-workspace-ux, HEAD 2e552f2fdc57c152c97f0486050574696f6b250e;
67 paths iniciales, staging vacío. Sin Git mutable ni Docker.


## Diseño A — Lista compacta de Presupuestos

Registro: 2026-10-23T21:20:50-03:00. Responsable: Codex local, laptop.
Decisión de Producto: boceto A aprobado por Cristian. Estado: IMPLEMENTADO LOCALMENTE;
PENDIENTE DE REVISIÓN VISUAL Y TESTING INDEPENDIENTE.
Rama `feature/professional-workspace-ux`; HEAD `2e552f2fdc57c152c97f0486050574696f6b250e`.
Origin esperado confirmado, staging vacío; 74 paths pendientes al inicio, 75 al cierre.
Este registro cambia la presentación del listado; conserva íntegro el cierre independiente
P2 del 2026-10-20 y sus pendientes. No reabre ni reemplaza ese dictamen.

### Implementación y correspondencia con A

- `/profesional/presupuestos` comienza con enlaces de navegación reales: Solicitudes disponibles
  y Presupuestos enviados. Ambos listados tienen h1 accesible oculto visualmente y aria-current.
- Sin encabezado Marketplace profesional, hero/título visible, cupo superior, filtros visibles
  ni encabezados redundantes. Las URLs GET existentes con categoría/zona siguen funcionando;
  cuando están presentes se ofrece un enlace para ver todas. No cambia la lógica de filtros.
- Solicitudes en una columna: categoría y zona declarada, título, descripción truncada escapada,
  antigüedad real, cantidad real de ofertas y máximo proveniente de MAX_OFFERS_PER_REQUEST.
  Acento lateral naranja fino, superficie DSv2, CTA Ver solicitud a la derecha; apilado móvil.
- Antigüedad calculada sobre fecha_creacion UTC existente: minutos, horas y días completos,
  o Recién publicada. No utiliza la fecha estimada del trabajo ni cifras del boceto.
- La pestaña de enviados conserva estados, importes estimados y seguimiento existentes;
  comparte navegación superior y listado de una columna. No se eliminan reglas de cupo.
- El aviso preliminar se retira de estos listados después de comprobar su presencia en
  detalle_presupuesto.html, tanto en el formulario de oferta como en la información de oferta.
- CSS bajo `.budget-compact`; no se modifica navegación global, modelos, migraciones,
  dependencias, validadores, permisos, CSRF, estados ni adjudicación/idempotencia.

### Inventario atribuible (11 archivos)

1. `app/templates/listado_presupuestos.html`: composición A, datos reales y paginación.
2. `app/templates/mis_presupuestos_enviados.html`: pestañas iniciales y eliminación de hero/banner redundantes.
3. `app/templates/components/_budget_tabs.html`: nuevo parcial compartido, navegación nativa.
4. `app/static/css/budget-workflow.css`: estilos encapsulados, temas, móvil y foco heredado.
5. `app/services/operation_view_service.py`: helper de antigüedad de publicación.
6. `app/routes/operation_routes.py`: mapa de antigüedad y constante canónica de máximo en contexto.
7. `tests/test_budget_workflow_ux.py`: tres pruebas nuevas; expectativas del estado vacío actualizado.
8. `tests/test_budget_request_ux06a.py`: destino de navegación acorde a entrada profesional.
9. `docs/REQUISITOS/PRESUPUESTOS_UX_001.md`: esta entrada, sin borrar antecedentes.
10. `docs/HANDOFFS/ACTIVE_HANDOFF.md`: continuidad de esta sesión.
11. `docs/CHANGELOG.md`: registro del incremento visual.

### Pruebas y evidencias nuevas

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:DATABASE_URL='sqlite:///:memory:'
.venv/Scripts/python.exe -m unittest tests.test_budget_workflow_ux tests.test_sprint7_budget_to_contract tests.test_budget_request_ux06a tests.test_professional_workspace_ux tests.test_professional_workspace_ux_002 -q
```

61/61 aprobadas en 12.834 s. Incluye los dos P2 (importes inválidos controlados y campos
repoblados), CSRF, ownership, adjudicación sin duplicados, shell, vacíos y lectura sin escritura.
Tres métodos nuevos comprueban contenido/escape, fuente del máximo, pestañas/vacíos y antigüedad.
La primera ejecución tuvo cuatro fallos: expectativas de textos/enlace sustituidos y una
recodificación accidental del template. Se corrigieron antes de la ejecución final; no se
atribuyeron a fallos preexistentes. El log de una excepción SQL privada es parte del caso
controlado de error del workspace; la suite final termina OK.

Chrome real, SQLite en memoria y datos sintéticos: 20 combinaciones (ambas pestañas ×
320/390/768/1024/1440 px × claro/oscuro), sin overflow horizontal detectado. Incluye solicitud
con título, zona y descripción largos. Navegación entre pestañas y acceso al detalle por
Enter con JavaScript deshabilitado; dos estados vacíos adicionales comprobados. Capturas
con tema establecido por clase del driver; no se declara retest de persistencia del switch.
Sin JavaScript productivo nuevo ni dependencias. No se contactaron servicios externos.

[Evidencia durable](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PRESUPUESTOS-DISENO-A/):
`baseline.json`, `integrity-final.json`, `tests.log`, `tests-final.log`, `browser-results.json`,
preview y script QA; capturas `available-*`, `sent-*` y `empty-*`.
Capturas comparables con A: `available-1440-dark.png`, `available-1440-light.png`;
móvil: `available-320-light.png`, `available-390-dark.png`.

Sintaxis AST Python, UTF-8 sin BOM/NUL/U+FFFD/mojibake y git diff --check comprobados.
INDEX y archivos ajenos conservados por hash. No pruebas PostgreSQL, AA integral ni móvil
físico. El aviso CSP inline global documentado anteriormente queda fuera de este cambio;
no se declara consola limpia ni suite completa. No hay Docker, bases compartidas ni operaciones
Git mutables. Preview descartable detenido al finalizar. Revisión: `/profesional/presupuestos`
y `/presupuestos/mis-enviados` en el entorno que administre Cristian.

IMPLEMENTADO LOCALMENTE; PENDIENTE DE REVISIÓN VISUAL Y TESTING INDEPENDIENTE.


## Cierre técnico independiente del diseño A

Registro documental: 2026-10-23T22:36:39-03:00. Responsable: Codex local, laptop.
Dictamen independiente: **2026-10-23T21:31:20-03:00**.
**VERIFICADO EN EL ALCANCE EVALUADO.** Sin hallazgos P0–P3.

Resultados del QA independiente: **61/61 pruebas aprobadas** y **20 combinaciones de
navegador**. Ambos P2 anteriores se conservan como corregidos: importes inválidos con
respuesta controlada y formulario repoblado ante errores. Estos resultados pertenecen
al retest independiente; no son una ejecución nueva de esta sesión documental ni se
suman a las pruebas del implementador como cobertura adicional.

[Evidencias del QA independiente](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/presupuestos-diseno-a-independent-qa/): `focused-regressions.log`,
`browser-results.json`, `adversarial-retest.json` y capturas `available-*`, `sent-*` y
`empty-*`. La ubicación comprobada está bajo `.codex` en el perfil del usuario; se corrigió
la omisión del separador entre el perfil y `.codex` en la referencia recibida.

La selección del **boceto A** por Producto está vigente. La **aprobación visual final de
la implementación por Cristian todavía está pendiente**; este dictamen técnico no la
sustituye. Se conservan los antecedentes, la CSP heredada y los pendientes de profesionales
como solicitantes, PostgreSQL, certificación AA y dispositivo móvil físico. No se declara
certificación AA, integración, despliegue ni preparación productiva.

Integridad inicial/final: rama `feature/professional-workspace-ux`, HEAD
`2e552f2fdc57c152c97f0486050574696f6b250e`, origin TRAX-PLATFORM esperado, 75 paths pendientes
y staging vacío. Sólo se actualizaron este requisito, ACTIVE_HANDOFF y CHANGELOG; todos
los demás archivos versionados y no ignorados, incluido INDEX, conservados por SHA-256.
Se verificaron UTF-8 y git diff --check; sin nuevas pruebas funcionales, código, Docker,
bases compartidas ni operaciones Git mutables. Urgencias espera la revisión visual
solicitada por Cristian, sin nuevas actuaciones en ese módulo.


## Ver solicitud — Rediseño del detalle aprobado el 2026-10-25

Registro: 2026-10-25T13:36:39-03:00. Responsable: Codex local, laptop. Estado: IMPLEMENTADO LOCALMENTE;
PENDIENTE DE REVISIÓN VISUAL Y TESTING INDEPENDIENTE.
Rama `feature/professional-workspace-ux`, HEAD `2e552f2fdc57c152c97f0486050574696f6b250e`.
Origin esperado confirmado; 75 paths pendientes y staging vacío, antes/después.

### Aprobaciones y continuidad

Cristian aprobó visualmente el **listado A el 2026-10-25**, según este encargo. Esta aprobación
actualiza su pendiente visual anterior sin borrar el dictamen técnico independiente del
2026-10-23T21:31:20-03:00 ni los cierres de ambos P2. El código del listado A se conserva.
También aprobó el **boceto del detalle** el 2026-10-25: su implementación entregada ahora
requiere revisión visual final y testing independiente; no se confunden esas aprobaciones.
Urgencias continúa esperando la revisión visual solicitada por Cristian.

### Composición implementada y alcance

- Navegación superior separada: propietario vuelve a sus solicitudes; profesional vuelve al
  listado privado y dispone de enlace a presupuestos enviados. Destinos canónicos existentes.
- Título moderado; categoría, zona declarada, estado e identificador una vez en el encabezado.
  Contador compacto usa offer_count/max_offers reales, sin copiar cifras del boceto.
- Profesional: dos columnas desde 1024 px, descripción/datos a la izquierda y oferta a la derecha.
  Hasta 768 px, descripción antes del formulario. Fecha estimada y urgencia conservadas.
- Se retiran títulos decorativos y el panel lateral de reglas para el profesional; la regla
  de una oferta sigue junto al botón. Formulario en una sola superficie, sin panel anidado.
- Todos los campos, nombres, valores, POST, CSRF y validaciones se mantienen; plazo ancho completo.
  Aviso preliminar discreto y cupo real conservados. Campos recuperados siguen escapados.
- Se conservan oferta enviada, perfil incompleto, cupo agotado y solicitud no receptiva.
  Comparador CLIENTE, confirmación/adjudicación y contacto adjudicado permanecen en su rama del
  template compartido. No se cambian servicios, rutas, estados, idempotencia ni reglas comerciales.
- CSS bajo `.budget-detail-redesign`, con variante profesional y tokens DSv2. Se conserva foco
  visible y espacio inferior móvil. No hay JS productivo nuevo, modelos, migraciones o dependencias.

### Inventario de seis archivos

- `app/templates/detalle_presupuesto.html`: composición y semántica, condiciones operativas preservadas.
- `app/static/css/budget-workflow.css`: estilos exclusivos del detalle, sin modificar reglas del listado A.
- `tests/test_budget_workflow_ux.py`: un método nuevo para propietario y estados sin formulario activo.
- `docs/REQUISITOS/PRESUPUESTOS_UX_001.md`: esta entrada y aprobación visual del listado A.
- `docs/HANDOFFS/ACTIVE_HANDOFF.md`: continuidad.
- `docs/CHANGELOG.md`: registro del incremento.

### Validación nueva

SQLite descartable en memoria y datos sintéticos, PYTHONDONTWRITEBYTECODE=1 y
DATABASE_URL=sqlite:///:memory:. Sin Docker ni bases compartidas.

```text
.venv/Scripts/python.exe -m unittest tests.test_budget_workflow_ux tests.test_sprint7_budget_to_contract tests.test_budget_request_ux06a tests.test_professional_workspace_ux tests.test_professional_workspace_ux_002 -q
.venv/Scripts/python.exe -m unittest tests.test_budget_workflow_ux -q
```

Primera selección: **61/61** en 11.614 s. Después de añadir el caso focal de estados alternativos:
**14/14** en 3.223 s, de los cuales trece ya estaban en la selección anterior. **62 casos únicos
aprobados**, sin sumar repeticiones como cobertura adicional. Incluye P2, permisos, CSRF,
conservación de campos y adjudicación idempotente. La excepción SQL del log corresponde al caso
controlado de error del workspace; resultado final OK. No suite completa ni PostgreSQL validado.

Chrome real: **20 combinaciones**, 320/390/768/1024/1440 × claro/oscuro × JS activo/deshabilitado.
Cada combinación recorrió detalle inicial, rango inválido (400 con campos conservados) y envío
corregido (302 seguido de confirmación 200). Capturas de los tres estados: 60 imágenes finales.
Se comprobó orden de columnas/apilado, texto largo, overflow inicial, foco visible y que el centro
del botón de envío fuese alcanzable sin superposición móvil. Enter envió el formulario incluso
con JavaScript realmente deshabilitado. Los temas se establecieron con clase CSS desde el driver:
no equivale a retest del switch global. Sesiones sintéticas firmadas para profesionales distintos
por caso evitaron agotar cupos; no se alteraron las reglas para permitir los envíos.

Primer chequeo de alcance del botón midió antes de terminar el desplazamiento suave; se corrigió
el driver con scroll instantáneo, no la navegación del producto. Tras inspección visual se quitó
el fondo/padding del formulario anidado y se repitió la matriz completa, reemplazando las capturas.
No se cuenta esa repetición como cobertura adicional. Comparador y adjudicación del CLIENTE se
verificaron mediante regresiones; no se declara una matriz visual nueva específica del cliente.

[Evidencia durable](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PRESUPUESTOS-DETALLE-UX/):
`baseline.json`, `integrity-final.json`, `tests.log`, `states-tests.log`, `browser-results.json`,
preview y controlador QA, `detail-*`, `error-*`, `sent-*`. Todo dato de capturas es sintético.
Se conservaron hashes de INDEX, listado A, servicios, rutas y demás archivos ajenos.
UTF-8 sin BOM/NUL/U+FFFD y git diff --check correctos. Preview descartable detenido al cierre.

Pendientes heredados: CSP inline global, profesionales como solicitantes, PostgreSQL,
certificación AA y móvil físico. No se declara consola limpia, integración, despliegue ni
preparación productiva. Sin operaciones Git mutables. Revisión: abrir Ver solicitud desde
`/profesional/presupuestos`, destino `/presupuestos/<id>` con un registro existente autorizado.

IMPLEMENTADO LOCALMENTE; PENDIENTE DE REVISIÓN VISUAL Y TESTING INDEPENDIENTE.


## Cierre técnico independiente de Ver solicitud

Registro documental: 2026-10-25T14:00:38-03:00. Responsable: Codex local, laptop.
Dictamen independiente: **2026-10-25T13:50:29-03:00**.
**VERIFICADO EN EL ALCANCE EVALUADO.** Sin hallazgos P0–P3.

- Pruebas: **62/62 aprobadas**.
- Navegador: **20/20 combinaciones aprobadas**, con estados inicial, error repoblado y envío corregido.
- Ambos P2 anteriores permanecen corregidos: importes inválidos con respuesta controlada y conservación de campos ante errores.

Estos resultados corresponden al dictamen independiente recibido; no son nuevas ejecuciones de
esta sesión ni se suman a las pruebas históricas como cobertura adicional.
[Evidencia independiente existente](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/presupuestos-detalle-independent-qa/) (`browser-results.json` y capturas del recorrido).
Se comprobó la existencia de la carpeta bajo el directorio `.codex` del usuario; la referencia
recibida omitía el separador anterior a `.codex`. No se movieron ni modificaron las evidencias.

Se conserva la aprobación visual del listado A por Cristian del **2026-10-25** y sus cierres
anteriores. El boceto de Ver solicitud fue aprobado por Cristian el **2026-10-25**; la aprobación
visual de la implementación del detalle **continúa pendiente**. Este dictamen cierra el QA técnico
en el alcance evaluado, sin sustituir esa revisión visual.

Limitaciones vigentes: PostgreSQL no validado, sin certificación AA integral ni validación en
móvil físico; decisión de Producto pendiente sobre profesionales como solicitantes. CSP heredada
conservada como limitación. No se declara integración, despliegue ni preparación productiva.

Identidad inicial/final: rama `feature/professional-workspace-ux`, HEAD
`2e552f2fdc57c152c97f0486050574696f6b250e`, 75 paths pendientes y staging vacío.
Cambios de esta sesión exclusivamente en esta especificación, `docs/HANDOFFS/ACTIVE_HANDOFF.md`
y `docs/CHANGELOG.md`. Los demás archivos, incluido `docs/INDEX.md`, conservados por SHA-256.
UTF-8 y `git diff --check` verificados en este cierre. Sin nuevas pruebas funcionales, Docker,
bases compartidas ni operaciones Git mutables. Urgencias espera la revisión visual de Cristian.

## PRESUPUESTOS — corrección focal P3 de prueba de actor contratante — 2026-11-01T22:04:08-03:00

Estado: READY_TO_RESUME. **P3 CORREGIDO LOCALMENTE; PENDIENTE DE RETEST INDEPENDIENTE.**
Rama `feature/professional-workspace-ux`; HEAD `2e552f2fdc57c152c97f0486050574696f6b250e`;
staging vacío; 160 paths pendientes preexistentes. Responsable: Codex local, laptop.

Se reprodujo antes de editar el fallo de `test_professional_never_has_client_contract_capabilities`
(1 caso, AssertionError: PermissionError not raised). La aserción universal estaba desactualizada:
la autoridad CLIENT de un contrato PROPOSAL admite al profesional publicador propietario.
No se identificó un defecto productivo que requiriera ampliar el alcance.

Se conserva el caso como `test_professional_client_capabilities_are_scoped_to_own_proposal`:
permite exclusivamente al propietario profesional de PROPOSAL; rechaza al profesional ajeno,
al propietario como prestador y al prestador como contratante. DIRECT y BUDGET siguen rechazando
al profesional contratante. No se eliminan casos ni se agregan omisiones. La cobertura positiva
real existente en `tests/test_professional_proposals.py` y los módulos sprint7 comprueba aceptación,
propiedad persistida, contrato canónico, SINGLE, transiciones e idempotencia, sin duplicarla.

Resultados nuevos, separados:
- Caso corregido: 1/1, repetido dentro de la selección siguiente; no suma cobertura adicional.
- Misma selección proporcional que históricamente dio 122/123: **123/123**, 54.798 s.
  Se conciliaron los identificadores completos con el log anterior, salvo el nombre corregido.
- Regresiones adicionales de permisos y contratación: **25/25**, 5.970 s.
- Total de esta ejecución satisfactoria: **148 casos únicos**; no es la suite completa del proyecto.

Comandos reproducibles (PowerShell, entorno virtual existente):
```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:DATABASE_URL='sqlite:///:memory:'
.\.venv\Scripts\python.exe -B -m unittest -v tests.test_budget_request_ux06a.BudgetRequestUX06ATest.test_professional_client_capabilities_are_scoped_to_own_proposal
.\.venv\Scripts\python.exe -B -m unittest -v tests.test_billing_preparation tests.test_billing_access_policy tests.test_billing_preparation_service tests.test_professional_billing_ux tests.test_work_records tests.test_budget_request_ux06a tests.test_payment_order_application tests.test_payment_effect_credits
.\.venv\Scripts\python.exe -B -m unittest -v tests.test_professional_proposals tests.test_sprint7_proposal_to_contract tests.test_sprint7_budget_to_contract tests.test_sprint7_contracting_core
```

Evidencia fuera del repositorio: `budget-p3-20261101`, bajo la carpeta de evidencias de esta sesión
(`.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/`).
Contiene `before.log`, `after.log`, `proportional.log`, `contract-regression.log`,
`selection-before.json`, `selection-final.json` y manifiestos de integridad.

Inventario focal: `tests/test_budget_request_ux06a.py`, `docs/REQUISITOS/PRESUPUESTOS_UX_001.md`,
`docs/HANDOFFS/ACTIVE_HANDOFF.md`, `docs/CHANGELOG.md`. Sin cambios productivos.
El registro se añade después del cierre documental fiscal de 2026-11-01T21:57:16-03:00,
comprobado en modo lectura; conserva ese cierre, su 122/123 histórico y el trabajo de IA.
Sintaxis Python, UTF-8 y git diff --check comprobados. Los demás archivos se cotejan por SHA-256.
No se ejecutaron PostgreSQL, navegador ni Node: no cambiaron producción, interfaces o controladores.
No se valida concurrencia nueva, AA, aprobación visual ni habilitación productiva.
Sin Docker, bases compartidas, migraciones, commit, push, PR, merge o despliegue; sin sincronización
remota nueva. No hubo merge porque no está autorizado. Próximo paso: retest independiente del P3
sobre estos comandos, preservando el árbol mixto y sin ampliar permisos ni modificar producción.
