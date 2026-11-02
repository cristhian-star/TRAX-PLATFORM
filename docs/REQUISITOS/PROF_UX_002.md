# PROF-UX-002 — Navegación directa, Inicio y Estadísticas

## Cierre documental de QA — 2026-10-17T05:22:46-03:00

Estado: COMPLETED, limitado al cierre documental de QA. Responsable: agente local; dispositivo: laptop.

Se incorpora el dictamen independiente del **2026-10-16T22:41:51-03:00**, comunicado por el responsable del proyecto: **VERIFICADO EN EL ALCANCE EVALUADO**.

- **75 pruebas anteriores vigentes por continuidad de hashes**; no constituyen nuevas ejecuciones ni se suman repeticiones como cobertura adicional.
- Matriz de navegador: **20 combinaciones verificadas**, Inicio y Estadísticas en 320, 390, 768, 1024 y 1440 px, en claro y oscuro.
- **JavaScript deshabilitado y movimiento reducido comprobados realmente** en el retest independiente, superando las limitaciones de la revisión local histórica.
- Inventario conciliado: **17 archivos intervenidos por PROF-UX-002 y 35 paths pendientes totales**; el total incluye trabajo anterior preservado.
- **Sin hallazgos P0–P3** en el alcance evaluado.

Esta entrada actualiza los pendientes de QA del registro anterior sin borrar sus antecedentes ni convertir sus comprobaciones estáticas o simuladas en ejecuciones reales. La vigencia de las 75 pruebas se atribuye al dictamen independiente; esta sesión no ejecuta pruebas. No se declara certificación AA, integración ni preparación productiva.

### Evidencias permanentes

Las evidencias se conservaron fuera del repositorio en [QA-20261016T224151-0300](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-002/QA-20261016T224151-0300/). Se copiaron los **12 archivos originales (10 capturas y 2 JSON; 416851 bytes)** desde la carpeta temporal, sin borrar ni modificar los originales. Se verificó igualdad SHA-256 de cada copia.

- [Índice de navegador portable](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-002/QA-20261016T224151-0300/browser-evidence-portable.json): referencias relativas a las capturas preservadas; incluye las comprobaciones sin JavaScript y con movimiento reducido.
- [Matriz de viewports exactos](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-002/QA-20261016T224151-0300/exact-viewports.json): completa la matriz de 20 combinaciones junto con el índice anterior.
- [Captura sin JavaScript](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-002/QA-20261016T224151-0300/inicio-390-nojs.png) y [captura con movimiento reducido](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-002/QA-20261016T224151-0300/estadisticas-390-reduced-motion.png).
- [Manifiesto de preservación](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/PROF-UX-002/QA-20261016T224151-0300/preservation-manifest.json): inventario, pesos y SHA-256.

El JSON original de navegador se conserva íntegro como antecedente, incluidas sus rutas temporales históricas. El índice portable derivado es la referencia vigente para abrir las capturas; no representa una nueva ejecución. La línea base de integridad de esta sesión se conserva en `repository-before.json`, en la misma ubicación externa.

### Integridad y continuidad

Rama inicial/final: `feature/professional-workspace-ux`. HEAD conservado: `2e552f2fdc57c152c97f0486050574696f6b250e`. Origin: `https://github.com/cristhian-star/TRAX-PLATFORM.git`. Staging vacío; 35 paths pendientes totales, con trabajo previo sin commit.

Únicamente se actualizan `docs/REQUISITOS/PROF_UX_002.md` y `docs/HANDOFFS/ACTIVE_HANDOFF.md`. Código, pruebas y modificación previa de `docs/INDEX.md` se preservan por comparación SHA-256 contra la línea base de esta sesión. Control documental: `git diff --check`, sin nuevas pruebas ni Docker. Sin migraciones ni acceso a bases.

No se ejecutaron commit, push, PR ni merge; la integración no está autorizada por este cierre y permanece pendiente de decisión del responsable. No se verificó sincronización remota. Las capacidades futuras de instrumentación, metodología de mercado y facturación conservan sus dependencias y restricciones originales.

Próximo paso: revisión del cierre documental y decisión separada sobre integración. Para retomar, verificar identidad Git, staging y los 35 paths pendientes; consultar este cierre y las evidencias permanentes. No descartar trabajo previo ni interpretar este dictamen como habilitación de capacidades futuras.

---

## Antecedente de implementación local — 2026-10-16

Timestamp: 2026-10-16T21:18:44-03:00. Responsable: implementador local. Dispositivo: laptop.
Estado: READY_TO_RESUME — implementado localmente; revisión visual y testing independiente pendientes.
Rama inicial/final: `feature/professional-workspace-ux`.
HEAD conservado: `2e552f2fdc57c152c97f0486050574696f6b250e`.
Origin: https://github.com/cristhian-star/TRAX-PLATFORM.git.

## Alcance y decisiones

Bocetos aprobados de Inicio y Estadísticas: se mantienen sidebar, jerarquía,
indicadores superiores, dos columnas, perfil y adelantos. No se reproducen cifras,
curvas, mapas o precios ilustrativos. Logos oficiales y tokens DS v2 reutilizados.
La referencia v1 en Estándares es histórica respecto del DS v2 solicitado; no se
cambia el documento global. PROF-UX-001 y PROF-URGENCIAS-UX-001 conservan historia.

Sidebar: Inicio; TRABAJO (Presupuestos, Urgencias, Propuestas, Mis trabajos);
MI NEGOCIO (Estadísticas, Facturación y cobros); Mi perfil separado y perfil público
al pie. Móvil: Inicio, Urgencias, Mis trabajos y Menú nativo con todos los destinos.
Enlaces activos aria-current, Escape devuelve foco al summary; no trampa de foco.
El menú puede abrirse y cerrarse sin scripts. Campanita y tema existentes intactos.

Inicio: resumen actual de contratos no terminales propios, hasta tres trabajos
sin duplicados, presentación calculada por calculate_private_profile_completion,
actividad previa y acceso concreto a información/fotos del perfil por fragmentos.
«Para resolver hoy» no promete vencimientos ni agenda: se aclara en la interfaz.
Los adelantos de rendimiento y demanda llevan a Estadísticas. No se aplica un
período ficticio al stock actual de trabajos de Inicio.

## Rutas y compatibilidad

| GET | Comportamiento |
| --- | --- |
| /profesional/dashboard | Inicio refinado. |
| /profesional/presupuestos | Entrada privada directa, publicaciones recientes y seguimiento canónico. |
| /profesional/propuestas | Entrada privada directa, postulaciones propias paginadas, elegibilidad y enlace a creación vigente. |
| /profesional/oportunidades/urgencias | Ruta canónica de Urgencias conservada; no se crea un alias innecesario. |
| /profesional/trabajos | Listado previo sin cambio de reglas. |
| /profesional/estadisticas | tab=resumen/perfil/actividad/demanda; periodo=7/30/90 (30 inicial). |
| /profesional/facturacion | Preparación sin operaciones financieras. |
| /profesional/perfil/completar#perfil-general | Datos del perfil; #perfil-media abre fotos/portfolio con JS. Sin JS todos los paneles siguen visibles. |
| /profesional/oportunidades | Compatibilidad explícita: permanece la vista combinada anterior, incluidos #presupuestos y #propuestas, contactos y paginación. Sale del menú, no se redirigen POST. |

Todas las nuevas entradas usan role_required(PROFESIONAL), cuenta activa y rol
persistido. No admiten un identificador de otro profesional para estadísticas.
Los detalles, filtros completos y acciones de los módulos siguen en sus rutas
canónicas anteriores; no se rediseñan ni se sustituye su layout en este incremento.
La ruta /propuestas/nueva usa login_required y create_proposal_request admite al
propietario autenticado: se enlaza la capacidad real, sin ampliar permisos.
Los clientes conservan su navegación pública autenticada.

## Definiciones y fuentes

Estadísticas usa intervalos móviles de N*24 horas [ahora-N días, ahora), con un
único ahora por consulta. Los modelos guardan instantes UTC naive: se comparan con
UTC, sin interpretar fechas naive como hora local. Esta duración es idéntica en
America/Argentina/Buenos_Aires; no se promete agrupación por días calendario ni
se hace una conversión IANA implícita. No se modifica la política de guardias.

| Indicador | Fuente y significado | Estado |
| --- | --- | --- |
| Trabajos pendientes y en curso (Inicio) | owned_contracts; estado fuera de TERMINAL_STATES; todos los períodos | Disponible; cero significa ausencia real |
| Presupuestos enviados | BudgetOffer.fecha_creacion en intervalo; todos sus estados actuales | Disponible |
| Postulaciones enviadas | ProposalApplication.created_at en intervalo; todos sus estados actuales | Disponible |
| Solicitudes de contratación recibidas | ContractRequest.fecha_creacion en intervalo; todos los estados actuales | Disponible |
| Finalización confirmada por cliente | ContractRequest CONFIRMADA con confirmed_at en intervalo | Disponible; no se deduce desde oferta aceptada |
| Evolución de solicitudes | La misma cohorte de contratos, tramos consecutivos de hasta 7*24h; tabla cronológica | Disponible; una agregación SQL, sin curva ilustrativa |
| Estados comerciales | ENVIADO/ADJUDICADO, POSTULADA/ACEPTADA/RECHAZADA/DESCARTADA y estados canónicos de contratos | Estado actual de la cohorte creada; no historial de transiciones |
| Presentación del perfil | Cálculo vigente, sin nueva fórmula | Disponible |
| Presupuestos por responder | Falta bandeja de asignaciones personales | No disponible, no cero |
| Visitas/apariciones/contactos efectivos | No hay instrumentación suficiente; apertura WhatsApp no acredita mensaje | No disponible |
| Presupuestos recibidos de publicaciones propias | Requiere análisis separado por rol de publicador | Pendiente, no se suma a enviados |
| Demanda por zona/mapas/precios | Falta metodología aprobada, comparabilidad y privacidad agregada | No disponible; muestra insuficiente sólo podrá determinarse con esa metodología |
| Cobros/facturas/comprobantes suscripción | Tres conceptos separados | Preparados; sin saldos o acciones monetarias |

Para BudgetOffer, ProposalApplication y ContractRequest se requieren ambos
identificadores coherentes: professional_user_id y Professional.user_id unido
por professional_id. No se exponen registros ni domicilios ajenos. Agregaciones
acotadas, sin N+1. Sin commit en lectura. Error SQL capturado: rollback de la
transacción de lectura, mensaje neutro y Reintentar, nunca cifras parciales.
Sin registros: cero con texto explícito; no disponible: texto sin valor numérico.
COMPLETADA espera confirmación del cliente. CONFIRMADA indica la confirmación de
finalización por el cliente, según contract_service.OPERATION_CONFIRM.

## Inventario de este incremento

Modificados sobre el trabajo previo (conservando el resto):
- app/routes/main_routes.py
- app/static/css/professional-workspace.css
- app/templates/completar_perfil_profesional.html
- app/templates/components/_professional_opportunity_nav.html
- app/templates/profesional_dashboard.html
- app/templates/professional_workspace_base.html
- docs/HANDOFFS/ACTIVE_HANDOFF.md

Archivo previamente limpio modificado:
- app/static/js/profile-private-ux-a.js

Nuevos:
- app/services/professional_statistics_service.py
- app/static/js/professional-navigation.js
- app/templates/components/_professional_navigation.html
- app/templates/professional_billing.html
- app/templates/professional_marketplace.html
- app/templates/professional_statistics.html
- tests/js/professional_navigation.test.js
- tests/test_professional_workspace_ux_002.py
- docs/REQUISITOS/PROF_UX_002.md

Línea base externa baseline.json: SHA-256 de los paths con diff y no versionados
antes de editar. INDEX sólo presenta estado Git previo sin diff de contenido;
se verificó aparte su SHA-256, intacto:
46400cbd6de53ddabc3f535fec46cc1d901f17a1ed2001c6c5e1916041acd7a0.
25 paths pendientes iniciales, staging vacío. No se atribuye su autoría a esta sesión.
No modelos, migraciones, dependencias ni operaciones de dominio nuevas.

## Verificación local

SQLite en memoria y usuarios sintéticos. Suite focal/regresión: 59 pruebas Python
aprobadas. Tras agregar la evolución se repitieron las 7 pruebas focales: aprobadas;
no sumarlas como cobertura adicional. Primera ejecución focal encontró un error
en la construcción del fixture MultiDict, corregido; no fue un fallo de producto.
Node: 5 tests aprobados, incluyendo controladores productivos de navegación,
fragmentos del perfil, notificaciones y AUTH/tema. AST Python, sintaxis JS,
UTF-8 sin BOM/NUL/U+FFFD y git diff --check verificados al cierre.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:DATABASE_URL='sqlite:///:memory:'
.venv/Scripts/python.exe -m unittest tests.test_professional_workspace_ux_002 tests.test_professional_workspace_ux tests.test_professional_urgencies_ux tests.test_sprint7_contracting_core tests.test_sprint7_budget_to_contract tests.test_sprint7_proposal_to_contract tests.test_proposal_eligibility tests.test_loading_error_states -q
node --test tests/js/professional_navigation.test.js tests/js/professional_notifications.test.js tests/js/auth_ux.test.js
```

QA navegador Chrome, preview propio 54933, memoria SQLite, sin Docker:
- Inicio y Estadísticas Resumen: mediciones DOM en 320/390/768/1024/1440 CSS px,
  ambos temas, sin overflow (responsive.json). No equivalen a capturas de cada tamaño.
- Filtro 7 días y pestaña comercial conservan URL; tablas a 320 sin overflow.
- Menú a 320 con ocho enlaces de 44px, Escape cierra/restaura foco, outline 3px.
- Facturación desde menú, notificaciones vacías sin navegación y tema persistente.
- Texto secundario/acento frente a tarjeta: claro #334155/#fff 10.35:1,
  #b9380a/#fff 5.78:1; oscuro #cbd5e1/#1b2832 10.13:1,
  #ff8a4c/#1b2832 6.44:1. Medición focal, no auditoría AA integral.
- Preview sin scripts de aplicación: selector oculto, menú nativo abre a 320,
  sin overflow. Simulación por stripping, NO navegador con JavaScript deshabilitado.
- Reduced motion inspeccionado estáticamente: regla scoped existente; no emulación.
- Logs: errores de conexión de una extensión de Chrome; no errores JS de aplicación
  observados. Servidor observó /meta.json y /favicon.ico 404, no se atribuye a producto sin investigar;
  no se declara una red integralmente limpia.

Capturas válidas revisadas en directorio externo de evidencia prof-ux-002:
`inicio-final-claro.png` y `estadisticas-final-oscuro.png` (viewport natural 1920 CSS).
La captura anterior estadisticas-oscuro.png tiene un estado intermedio de tema y
NO es evidencia final. Capturas con viewport emulado fallaron por timeout del
navegador: pendientes capturas móviles y matriz visual completa en ambos temas.
No se declara validación integral. Preview propio detenido al finalizar.

## Continuidad

Revisar con cuenta profesional en QA:
- http://127.0.0.1:5050/profesional/dashboard
- http://127.0.0.1:5050/profesional/estadisticas
- http://127.0.0.1:5050/profesional/facturacion

Sólo Cristian ejecuta, si corresponde, reconstrucción de web (no ejecutada aquí):
```powershell
docker compose --env-file .env.example -f docker-compose.stabilization.yml -p mandobra_stabilization build web
docker compose --env-file .env.example -f docker-compose.stabilization.yml -p mandobra_stabilization up -d --no-deps web
```

Pendientes: testing independiente, revisión visual completa/móvil y no-JS real,
emulación reduced motion, metodología de demanda/precios, alcance instrumentado y
futuro diseño financiero. Ninguno se presenta como habilitado. Sin staging,
commit, push, PR, merge ni despliegue. Sin merge porque no está autorizado;
Cristian administra integración luego de su revisión y testing independiente.
