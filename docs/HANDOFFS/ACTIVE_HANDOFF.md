# Handoff tecnico: contrato neutral PSP y simulador determinista

## Workflow persistente de pagos - semantica aprobada implementada

Timestamp: 2026-09-11T19:22:09-03:00
Estado: COMPLETED
Resultado: PERSISTENT_PAYMENT_WORKFLOW_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/persistent-payment-workflow`
HEAD/commit base: `dfbb7e3f53e61638eb52113286870eca1b59d031`
Estado Git inicial: seis cambios locales esperados, sin staging
Estado Git final: seis cambios locales sin staging, commit ni push

Definicion resuelta: la regla inicial que exigia `PENDING` ante incertidumbre
fue reemplazada despues de contrastarla con el esquema `20260910_01` y la
semantica del dominio. Una respuesta incierta queda con estado financiero
`NULL`, resultado `RECONCILIATION_REQUIRED`, conciliacion requerida e ID
externo opcional. `PENDING` se usa solo ante una respuesta autoritativa. La
conciliacion explicita puede resolver el estado desconocido a `PENDING`,
`APPROVED` o `REJECTED`.

Trabajo completado: se formalizo la regla en el workflow y se reforzaron las
pruebas portables y PostgreSQL, incluyendo observacion independiente de la
fila incierta, variantes con y sin ID, las tres transiciones autorizadas,
replay, conflictos y el limite de dos transacciones sin adaptador dentro de
ellas. No se creo ni modifico una migracion.

Validacion: workflow 13/13; focal mas regresiones 68/68; gate PostgreSQL 10/10
sobre `trax_payment_persistence_test_workflow_contract_20260911`; suite
completa 372 ejecutadas, 367 aprobadas, 5 omisiones historicas, 0 fallos y 0
errores; `compileall` aprobado; head Alembic unico `20260910_01`; enlaces
relativos y `git diff --check` aprobados. La base descartable quedo en cero
tablas, fue eliminada y su ausencia se confirmo.

Limitaciones y pendientes: revision independiente e integracion Git. No se
agregaron Mercado Pago, HTTP, webhooks, checkout, creditos, PRO, ARCA,
interfaz, dependencias ni procesamiento automatico. No hubo commit, push, PR,
merge ni deploy. Proximo paso: revision independiente de los seis archivos
locales; no integrar sin nueva autorizacion explicita.

## Workflow persistente de pagos - definicion requerida

Timestamp: 2026-09-11T19:09:43-03:00
Estado: BLOCKED
Resultado: PERSISTENT_PAYMENT_WORKFLOW_BLOQUEADO_POR_DEFINICION_DE_ESTADO_INCIERTO
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/persistent-payment-workflow`
HEAD/commit base: `dfbb7e3f53e61638eb52113286870eca1b59d031`
Estado Git inicial: limpio, staging vacio y `develop` sincronizado 0/0
Estado Git final: cambios locales sin staging, commit ni push

Trabajo completado: servicio `PersistentPaymentWorkflow`, pruebas portables y
extensiones del gate PostgreSQL. La obligacion se confirma antes de invocar al
adaptador; no existe sesion activa durante la llamada; el resultado se confirma
en otra transaccion. Replays terminales no llaman nuevamente, los conflictos
se detectan antes de la llamada, y los fallos posteriores pueden recuperarse
mediante la idempotencia neutral del adaptador. La conciliacion es explicita y
sin loops, cron o retries automaticos.

Validacion ejecutada: focal y regresiones 67/67; gate PostgreSQL 10/10 sobre
`trax_payment_persistence_test_workflow_20260911`; suite completa 371
ejecutadas, 366 aprobadas, 5 omisiones historicas, 0 fallos y 0 errores;
`compileall` aprobado; head Alembic unico `20260910_01`. La base descartable
quedo en cero tablas, fue eliminada y su ausencia se confirmo. Enlaces
relativos y `git diff --check`: aprobados en el control documental final.

Bloqueante: el paquete exige que una respuesta incierta se persista con
`financial_status=PENDING`, mientras el constraint integrado
`ck_payment_attempts_result_coherent` exige `financial_status IS NULL` para
`RECONCILIATION_REQUIRED`. Cumplir ambos es imposible con el esquema actual.
No se creo ni modifico una migracion. Se requiere decidir si se conserva
`NULL` como estado financiero desconocido o se autoriza una revisión de esquema
y contrato para representar `PENDING`.

No se modificaron rutas ni UI y no se incorporaron Mercado Pago, HTTP, SDK,
OAuth, webhooks, checkout, creditos, suscripciones, PRO, ARCA o deploy. No se
realizo commit, push, PR ni merge. Proximo paso: resolver exclusivamente la
representacion de incertidumbre y luego repetir la validacion afectada.

## Integracion y verificacion post-merge de persistencia neutral

Timestamp: 2026-09-11T15:46:40-03:00
Estado: COMPLETED
Resultado: PAYMENT_PERSISTENCE_FOUNDATION_INTEGRADA_Y_VERIFICADA_POST_MERGE
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama actual/destino: `develop`
Commit de caracteristica: `fae81e62f1526a0daa229f03efbc19c918dc8ff0`
Merge commit / HEAD local y remoto: `8dd773692004453d663742be02048f79cae0aa0c`
Pull Request integrado: `#10`
Archivos integrados: 14
Alembic head: `20260910_01`
Estado Git previo al registro: arbol limpio, staging vacio y divergencia 0/0

El PR fue fusionado antes de completar el gate final solicitado. Por esa
desviacion, Testing no pudo emitir una autorizacion preventiva de merge. La
verificacion post-merge comprobo que el contenido remoto integrado coincide
exactamente con el commit previamente probado y aprobado, sin diferencias de
alcance ni defectos funcionales detectados. Se decidio conservar la integracion
y no iniciar una reversion. La observacion corresponde al proceso y no
constituye una regresion del codigo.

Las pruebas no se repitieron despues del merge. Se conserva como evidencia
historica del commit probado: focal portable y regresiones 55/55; PostgreSQL
real 7/7; suite completa 359 ejecutadas, 354 aprobadas, 5 omisiones historicas,
0 fallos y 0 errores; `compileall`, enlaces y `git diff --check` aprobados. La
base PostgreSQL descartable fue eliminada y `trax_db` permanecio intacta.

Esta integracion no acredita Mercado Pago, pagos productivos, webhooks,
checkout, creditos, PRO, ARCA, deploy o la arquitectura general 2.0. Esta
actualizacion modifica unicamente los tres documentos autorizados y debe quedar
sin staging ni commit hasta su revision.

## Correccion P2 - clasificacion de violaciones de integridad

Timestamp: 2026-09-11T14:41:40-03:00
Estado: READY_TO_RESUME
Resultado: PAYMENT_PERSISTENCE_FOUNDATION_CORREGIDA_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/payment-persistence-foundation`
HEAD/commit base: `c78c5176cf3c43cdbab673454fc6a625b1b3c0fa`
Estado Git: 14 cambios locales autorizados, sin staging, commit ni push
Revision independiente historica: `REQUIERE_CORRECCIONES`; se conserva como
evidencia del P2 y no se reemplaza por una aprobacion anticipada

Se ajusto unicamente `register_or_get_attempt()`: el camino de recuperación de
la carrera idempotente exige SQLSTATE `23505` y
`diag.constraint_name=uq_payment_attempts_idempotency_key`. Si el driver no
identifica ambos valores, o informa FK/check/otra constraint, el
`IntegrityError` se relanza intacto. El servicio mantiene `flush()`, savepoint
y transaccion superior controlada por el llamador, sin commits internos.

Validacion: focal 55/55; gate PostgreSQL real 7/7 sobre
`trax_payment_persistence_test_p2_20260911`; suite completa 359 ejecutadas, 354
aprobadas, 5 omisiones historicas, 0 fallos y 0 errores; `compileall` aprobado;
head Alembic unico `20260910_01`. La base descartable quedo en cero tablas, fue
eliminada y su ausencia se confirmo. Enlaces relativos y `git diff --check`:
aprobados en el control final.

No se modificaron esquema ni migracion. `trax_db`, Mercado Pago, PSP real,
webhooks, produccion y diseño general 2.0 no fueron acreditados. Proximo paso:
retest independiente del P2 y del paquete local completo. No ejecutar commit,
push, PR, merge o deploy sin autorizacion expresa.

## Persistencia neutral minima de pagos

Timestamp: 2026-09-11T14:00:30-03:00
Estado: READY_TO_RESUME
Resultado: PAYMENT_PERSISTENCE_FOUNDATION_IMPLEMENTADA_LOCALMENTE_PENDIENTE_DE_REVISION
Dispositivo/origen: laptop / Codex Desktop local
Agente: Codex - implementador tecnico local
Objetivo: persistir obligaciones e intentos ya producidos por el orquestador
neutral, con idempotencia, conciliacion y limites transaccionales explicitos
Rama: `feature/payment-persistence-foundation`
HEAD/commit base: `c78c5176cf3c43cdbab673454fc6a625b1b3c0fa`
Estado Git inicial: limpio; `develop` y `origin/develop` sincronizados
Estado Git final: cambios locales sin staging, commit ni push
Push, PR, merge y deploy: no realizados; no autorizados
Integracion previa: PR #9 integrado mediante
`c78c5176cf3c43cdbab673454fc6a625b1b3c0fa`

Trabajo completado:

- Modelos `PaymentObligation` y `PaymentAttemptRecord` registrados en el
  metadata de SQLAlchemy.
- Migracion `20260910_01` sobre `20260904_01`, con dos tablas, constraints e
  indice nombrados y downgrade inverso.
- Servicio de persistencia con sesion explicita, replay, conflicto,
  recuperacion y conciliacion; no ejecuta `commit()` ni llama al PSP.
- Pruebas portables y de migracion, prueba adversarial de la guarda y gate
  PostgreSQL real de concurrencia, visibilidad, locks, FK, rollback y
  recuperacion de sesion.

Validaciones:

- Focal portable mas regresiones PSP/orquestador: 55/55.
- Gate PostgreSQL: 6/6 sobre
  `trax_payment_persistence_test_20260911a`; ciclo
  upgrade/downgrade/upgrade aprobado, limpieza a cero tablas verificada y base
  eliminada con cero coincidencias posteriores.
- Suite completa Docker/SQLite aislada: 359 ejecutadas, 354 aprobadas, 5
  omisiones historicas, 0 fallos y 0 errores.
- `compileall`: aprobado. Head Alembic unico: `20260910_01`.
- Enlaces relativos y `git diff --check`: aprobados en la verificacion final.

No se modifico ni reseteo `trax_db`. No se implementaron llamadas PSP,
Mercado Pago, HTTP, SDK, OAuth, webhooks, checkout, interfaz persistente,
creditos, comisiones, suscripciones, PRO, ARCA o Enterprise. La coordinacion
durable alrededor de una llamada externa queda pendiente de otro incremento y
el diseño 2.0 permanece `PROPUESTO_NO_APROBADO`.

Proximo paso recomendado: revision independiente del diff local, incluida la
migracion y la evidencia PostgreSQL. No hacer commit, push, PR o merge sin una
autorizacion posterior expresa.

## Interfaz interna del simulador de pagos

Timestamp: 2026-09-10T21:46:04-03:00
Estado: READY_TO_RESUME
Resultado: PAYMENT_ORCHESTRATION_AND_SIMULATOR_UI_APROBADOS_PARA_COMMIT_Y_PR
Dispositivo/origen: laptop / Codex Desktop local
Agente: Codex - implementador tecnico y frontend local
Objetivo: permitir una inspeccion visual interna de una obligacion y de la
interpretacion neutral de la respuesta PSP simulada
Rama: `feature/payment-orchestration-in-memory`
HEAD/commit base observado: `a4951a27f0f0bef5fa834ad25159abfc875ec59e`
Estado Git inicial: limpio y sin staging; rama sin upstream remoto
Push, PR, merge y deploy: no realizados; no autorizados
Revision independiente: `APROBADO_PARA_SEGUNDO_COMMIT_Y_PR` del
`2026-09-10T22:02:38-03:00`; hallazgos P0-P3: ninguno

- Se agrego la ruta GET/POST `/dev/qa/payments/simulator` al blueprint `dev`.
  Reutiliza `_require_dev_qa_panel()`, solo existe en development/testing y
  exige `ENABLE_DEV_QA_PANEL`; deshabilitada o en produccion responde 404.
- Cada POST crea `ScenarioController`, `InMemoryPSPSimulator` y
  `InMemoryPaymentOrchestrator` nuevos. La seleccion artificial queda en la
  ruta de desarrollo; no se modificaron `PSPAdapter`, el orquestador ni el
  simulador ya versionados.
- La pantalla server-rendered usa `Decimal`, conserva entradas ante error y
  presenta aprobado, rechazado, pendiente e incertidumbre como conciliacion
  requerida. No expone excepciones, inventa IDs o conserva historial.
- Se usaron componentes `.trax-*`, tokens `--trax-ds-*`, etiquetas,
  `fieldset`/`legend`, errores textuales, foco visible y `aria-live`; no se
  agrego JavaScript ni dependencia.

Archivos creados: `app/templates/dev_payment_simulator.html`,
`app/static/css/dev-payment-simulator.css` y
`tests/test_dev_payment_simulator.py`. Archivos modificados:
`app/routes/dev_routes.py`, `docs/CHANGELOG.md`, este handoff y
`docs/SPRINTS/2026-09-06_PRO_REFINAMIENTO_COMERCIAL_Y_PSP.md`.
Migraciones y dependencias: ninguna.

Validaciones finales informadas por la revision independiente: interfaz +
orquestador 29/29; contrato/simulador 24/24; suite completa 347 ejecutadas,
342 aprobadas, 5 omisiones historicas, 0 fallos y 0 errores. `compileall`,
HTML, enlaces y `git diff --check`: aprobados. QA visual aprobada en temas
claro/oscuro, movil/desktop y teclado. PostgreSQL no se ejecuto porque no
aplica.

Limitaciones: interfaz interna de desarrollo, un procesamiento aislado por
envio, sin persistencia, historial, polling o conciliacion automatica. No
acredita checkout, pagos reales, viabilidad PSP, HTTP, SDK, OAuth, webhooks,
creditos, reservas, suscripciones, PRO, Mercado Pago o ARCA. El diseño general
2.0 permanece `PROPUESTO_NO_APROBADO`; Mercado Pago y la revision
juridica/contable continuan pendientes.

Proximo paso: preparar el segundo commit y un unico PR solo con autorizacion
expresa posterior. Esta aprobacion documental no autoriza staging, commit,
push, PR, merge o deploy.

## Orquestacion neutral de pagos implementada localmente

Timestamp: 2026-09-10T21:23:10-03:00
Estado: READY_TO_RESUME
Resultado: PAYMENT_ORCHESTRATION_IN_MEMORY_IMPLEMENTADA_LOCALMENTE_PENDIENTE_DE_REVISION
Dispositivo/origen: laptop / Codex Desktop local
Agente: Codex - implementador tecnico local
Objetivo: traducir una obligacion monetaria y la respuesta de `PSPAdapter` a
un resultado neutral, inmutable y conciliable para MANDOBRA
Rama: `feature/payment-orchestration-in-memory`
Commit base: `e7ec86f217ebbbd836f7434092041e6abefbbe4a`
Estado Git inicial: limpio, staging vacio y `develop` sincronizado 0/0 con
`origin/develop`
Push, PR, merge y deploy: no realizados; no autorizados

- Se creo `app/services/payment_orchestration.py` con `PaymentObligation`,
  `PaymentOrchestrationResult`, cuatro resultados diferenciados y el servicio
  `InMemoryPaymentOrchestrator`.
- La creacion delega una sola vez en el contrato neutral. Aprobacion, rechazo y
  pendiente conservan el estado financiero; la incertidumbre produce
  `RECONCILIATION_REQUIRED` y puede conservar un ID o `None`.
- La conciliacion es una accion unica y explicita: consulta por ID cuando
  existe o repite la misma solicitud idempotente cuando no existe. Una nueva
  incertidumbre permanece conciliable. No se inventan IDs ni se ejecutan
  reintentos, temporizadores o bucles.
- La solicitud exige `Decimal` positivo y finito, rechaza `float`, cero,
  negativos, `NaN` e infinitos, y no cuantiza ni redondea.
- Los errores de no encontrado e idempotencia permanecen diferenciados desde
  el contrato; la solicitud invalida usa un error propio y neutral.

Archivos creados: `app/services/payment_orchestration.py` y
`tests/test_payment_orchestration.py`. Documentacion modificada:
`docs/CHANGELOG.md`, este handoff y
`docs/SPRINTS/2026-09-06_PRO_REFINAMIENTO_COMERCIAL_Y_PSP.md`.
Migraciones y dependencias: ninguna.

Validaciones: focal del orquestador 19/19; focal PSP 24/24; suite completa
Docker 337 ejecutadas, 332 aprobadas, 5 omitidas, 0 fallos y 0 errores;
`compileall` aprobado. PostgreSQL no se ejecuto porque no aplica al incremento
en memoria. Se observaron solo advertencias legacy/deprecaciones preexistentes
y el contenedor huerfano `trax-pro-contrast-qa`, que no fue eliminado.

Limitaciones: no acredita persistencia, concurrencia o atomicidad PostgreSQL,
autenticidad u orden de webhooks ni viabilidad tecnica, contractual o
comercial de un PSP. No conecta Mercado Pago, ARCA, HTTP, SDK, rutas, creditos,
reservas, suscripciones, PRO o flujos productivos. El diseño 2.0 permanece
`PROPUESTO_NO_APROBADO`; Mercado Pago y la revision juridica/contable siguen
pendientes.

Proximo paso recomendado: revision independiente del diff local. No hacer
staging, commit, push, PR, merge, rebase, deploy ni iniciar otro incremento sin
autorizacion expresa.

## Validacion local post-merge de PR #8

Timestamp: 2026-09-10T13:42:55-03:00
Estado: COMPLETED
Resultado: PSP_ADAPTER_CONTRACT_INTEGRADO_POST_MERGE_VALIDADO_LOCALMENTE_PENDIENTE_DE_REVISION_DOCUMENTAL
Dispositivo/origen: laptop / Codex Desktop local
Agente: Codex - implementador tecnico local
Objetivo: validar localmente el contrato neutral PSP despues de su integracion
Rama: `develop`
Base previa: `2e7de49dfde6c20bc798089139ea235534ea0a75`
PR: #8
Merge/HEAD: `f9c0e394af413cfcb0c1aa8142a85af16ad3729b`
Segundo padre: `8f709e64149d7dfbdeb9c2e1a319f7134ae6f0f4`
Estado remoto: `origin/develop` coincide con el merge validado
Integracion Git de esta sesion: no realizada; no autorizada

- Se confirmaron ubicacion, remoto, rama, HEAD, upstream, ausencia de
  divergencia y parentesco del merge. El staging permanecio vacio.
- Alcance validado: `PSPAdapter` neutral, intento inmutable, estados y errores
  neutrales diferenciados, ID opcional ante incertidumbre, simulador en
  memoria determinista, controlador FIFO, idempotencia y recuperacion por
  consulta.
- Pruebas focales: 24 ejecutadas y aprobadas, 0 fallos, 0 errores y 0
  omisiones. Suite completa Docker: 318 ejecutadas, 313 aprobadas, 5 omitidas,
  0 fallos y 0 errores. `compileall`, enlaces relativos y `git diff --check`:
  aprobados.
- PostgreSQL no se ejecuto y no aplica a este incremento. No hubo migraciones,
  cambios de dependencias ni modificaciones de codigo durante esta sesion.
- Limitaciones: la evidencia no acredita persistencia, concurrencia o
  atomicidad PostgreSQL, autenticidad u orden de webhooks ni viabilidad
  tecnica, contractual o comercial de un PSP. No conecta Mercado Pago, ARCA,
  HTTP, SDK o flujos productivos.
- El diseño general 2.0 permanece `PROPUESTO_NO_APROBADO`; Mercado Pago y la
  revision juridica/contable continuan pendientes.

Cambios sin commit: este handoff, `docs/CHANGELOG.md` y
`docs/SPRINTS/2026-09-06_PRO_REFINAMIENTO_COMERCIAL_Y_PSP.md`, exclusivamente
documentales y sin staging. Tests no ejecutados: PostgreSQL, por no aplicar.
Errores conocidos: ninguno del incremento; se observaron advertencias legacy
y deprecaciones no bloqueantes ya existentes durante la suite.

Proximo paso recomendado: revision independiente del diff documental y, solo
con autorizacion posterior, su integracion. No hacer staging, commit, push,
PR, merge, rebase, deploy ni eliminar ramas como parte de este handoff.

## Correccion P2 de determinismo en PR #8

Timestamp: 2026-09-09T20:42:09-03:00
Estado: READY_TO_RESUME
Resultado: PSP_ADAPTER_CONTRACT_P2_CORREGIDO_PR_ACTUALIZADO_PENDIENTE_DE_RETEST
Dispositivo/origen: laptop / Codex Desktop local
Agente: Codex - implementador tecnico local
Rama: `feature/psp-adapter-contract`
PR: #8
Commit observado: `64eed3fdbf16ff55f7994b246a87b514a41a31bb`

- Hallazgo P2: una cola vacia fallaba despues de invocar `id_factory` y
  `clock`, por lo que dependencias con estado podian avanzar sin creacion.
- Correccion: `ScenarioController` permite inspeccionar sin consumir; la
  creacion valida primero la existencia del escenario, luego ID y reloj, y
  consume exactamente un escenario inmediatamente antes de almacenar.
- ID duplicado, reloj invalido, validacion, replay, conflicto y consulta no
  consumen escenarios.
- Focal: 24/24. Suite completa Docker: 318/318 ejecutadas, 313 aprobadas,
  5 omisiones historicas, 0 fallos y 0 errores. `compileall`, enlaces relativos
  y `git diff --check`: aprobados.
- PostgreSQL no aplica. No se agregaron persistencia, locks, capas, modelos,
  migraciones ni integraciones productivas.
- PR #8 permanece abierto y no esta aprobado para merge; requiere retest
  independiente despues del nuevo commit y push autorizados.

## Retest independiente aprobado para commit

Timestamp: 2026-09-09T20:23:34-03:00
Estado: READY_TO_RESUME
Resultado: PSP_ADAPTER_CONTRACT_APROBADO_PARA_COMMIT
Agente: Codex - ejecutor de integracion autorizado
Rama: `feature/psp-adapter-contract`
Commit base: `2e7de49dfde6c20bc798089139ea235534ea0a75`
Retest independiente: `APROBADO_PARA_COMMIT` del
`2026-09-09T20:14:06-03:00`

- P1 y P3: `RESUELTO`; hallazgos actuales P0-P3: ninguno.
- Focal 22/22; suite completa 311/316, con 5 omisiones historicas,
  0 fallos y 0 errores.
- `compileall`, enlaces relativos y `git diff --check`: aprobados.
- PostgreSQL no se ejecuto ni se acredita; no aplica al incremento en memoria.
- Estado Git al registrar el retest: seis archivos locales, staging vacio,
  sin commit, push o PR todavia.
- Permanecen fuera de alcance persistencia, webhooks, Mercado Pago, ARCA e
  integracion productiva. El diseño general 2.0 continua
  `PROPUESTO_NO_APROBADO`.

## Correcciones posteriores a revision independiente

Timestamp: 2026-09-09T20:01:57-03:00
Estado: READY_TO_RESUME
Resultado: PSP_ADAPTER_CONTRACT_CORREGIDO_LOCALMENTE_PENDIENTE_DE_RETEST
Dispositivo/origen: laptop / Codex Desktop local
Agente: 02 - Implementacion - Builder
Rama: `feature/psp-adapter-contract`
Commit base: `2e7de49dfde6c20bc798089139ea235534ea0a75`
Revision recibida: `REQUIERE_CORRECCIONES` del
`2026-09-09T19:53:36-03:00`, con P1 contractual y P3 de cobertura

- P1: `UncertainResponseError` admite omitir `attempt_id`; la ausencia se
  representa con `None`, un ID conocido debe ser cadena no vacia y se conserva
  sin normalizar. El simulador adjunta su ID conocido; un proveedor real puede
  no tenerlo y la conciliacion conserva la clave idempotente del llamador.
- P3: la proteccion de dependencias inspecciona imports mediante AST en ambos
  modulos; las cinco reexportaciones historicas se validan por identidad; se
  cubrieron orden, rechazo atomico y aislamiento de `enqueue`, y diferenciacion
  observable de los tres errores neutrales.
- Focal: 22/22 aprobadas. Suite completa Docker: 311/316 aprobadas, 5 omisiones
  historicas, 0 fallos y 0 errores. `compileall`, enlaces relativos y
  `git diff --check`: aprobados. Gates PostgreSQL: no ejecutados; no aplican al
  incremento en memoria.
- Estado Git: seis archivos locales, staging vacio, sin commit ni push.
- Limitaciones: sin persistencia, garantias PostgreSQL, HTTP, SDK, webhooks,
  Mercado Pago, ARCA o integracion productiva. El diseño 2.0 continua
  `PROPUESTO_NO_APROBADO`; revision juridica/contable pendiente.

Proximo paso: retest independiente focal. No declarar aprobado ni ejecutar
staging, commit, push, PR, merge, rebase o deploy sin autorizacion.

## Incremento 2.0-B implementado localmente

Timestamp: 2026-09-08T23:01:15-03:00
Estado: READY_TO_RESUME
Resultado: PSP_ADAPTER_CONTRACT_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Dispositivo/origen: laptop / Codex Desktop local
Agente: 02 - Implementacion - Builder
Objetivo: separar el contrato PSP neutral de la configuracion artificial de
escenarios del simulador.
Rama: `feature/psp-adapter-contract`
Commit base: `2e7de49dfde6c20bc798089139ea235534ea0a75`
Estado Git inicial: limpio y sincronizado con `origin/develop`
Estado Git final: cambios locales sin staging ni commit
Push, PR, merge y deploy: no realizados; no autorizados

- Se creo `app/services/psp_contract.py` como autoridad unica del `Protocol`,
  DTO inmutable, estados financieros y errores neutrales.
- `InMemoryPSPSimulator.create_attempt` conserva solo referencia, `Decimal`,
  moneda y clave idempotente. `ScenarioController` configura por separado una
  secuencia FIFO determinista y aislada por instancia.
- Nuevas operaciones consumen un escenario; replay, conflictos y validaciones
  no lo consumen. La falta de escenario falla antes de almacenar estado.
- En el simulador, la incertidumbre crea un solo intento `PENDING`, adjunta el
  identificador que conoce y permite consulta y replay sin repetir el error ni
  consumir otro escenario. El contrato neutral admite que otro adaptador no
  conozca el ID y lo represente con `None`.
- Compatibilidad: el simulador reexporta los nombres historicos del estado y
  DTO, referenciando las definiciones neutrales sin duplicarlas.

Archivos modificados: `app/services/psp_simulator.py`,
`tests/test_psp_simulator.py`, `docs/CHANGELOG.md`, este handoff y
`docs/SPRINTS/2026-09-06_PRO_REFINAMIENTO_COMERCIAL_Y_PSP.md`. Archivo creado:
`app/services/psp_contract.py`. Migraciones y dependencias: ninguna.

Validaciones: focal 17/17; suite completa Docker 306/311, con 5 omisiones
historicas, 0 fallos y 0 errores; `compileall`, enlaces relativos y
`git diff --check` aprobados. PostgreSQL gates no ejecutados porque el
incremento permanece exclusivamente en memoria.

Limitaciones: no acredita persistencia, concurrencia o atomicidad PostgreSQL,
autenticidad de webhooks ni viabilidad PSP. No conecta Mercado Pago o ARCA ni
flujos productivos. El diseño 2.0 continua `PROPUESTO_NO_APROBADO` y la revision
juridica/contable sigue pendiente.

Proximo paso: revision independiente del diff de los seis archivos. No hacer
staging, commit, push, PR, merge, rebase, deploy ni iniciar obligaciones de
pago sin autorizacion expresa.

---

# Handoff tecnico: simulador PSP determinista en memoria

## Integracion confirmada

Timestamp: 2026-09-08T22:40:33-03:00
Estado: COMPLETED
Resultado: SIMULADOR_PSP_EN_MEMORIA_INTEGRADO
Agente: Codex - ejecutor de integracion autorizado
Rama: `develop`
Commit del simulador: `50babd206369d47d68765e0dbf0fd3f2f42c21d0`
Push: normal a `origin/develop`, confirmado
Hash remoto observado: `50babd206369d47d68765e0dbf0fd3f2f42c21d0`

- Validaciones: focal 21/21; suite completa 310/315, con 5 omisiones
  historicas, 0 fallos y 0 errores; `compileall`, enlaces relativos y
  `git diff --check` aprobados.
- Integrado refiere solo al componente aislado en memoria y sus pruebas. No se
  conecto a rutas, servicios ni flujos productivos.
- No se acreditan persistencia, concurrencia o atomicidad PostgreSQL,
  autenticidad de webhooks ni viabilidad PSP.
- El diseño general 2.0 continua `PROPUESTO_NO_APROBADO`. Mercado Pago, ARCA y
  revision juridica/contable permanecen pendientes.
- Merge, rebase, force push y deploy: no realizados.

## Aprobacion independiente previa a integracion

Timestamp: 2026-09-08T22:37:42-03:00
Estado: READY_TO_RESUME
Resultado: SIMULADOR_PSP_EN_MEMORIA_APROBADO_PARA_COMMIT
Agente: Codex - revisor tecnico y funcional independiente
Rama y commit base: `develop` en
`1e85c6e592f970b2640a1e71d5b9a7019f8b3383`

- Revision independiente emitida el `2026-09-08T22:28:13-03:00`:
  `APROBADO_PARA_COMMIT`, sin hallazgos P0-P3.
- Focal: 21/21 aprobadas. Suite completa en Docker: 310/315 aprobadas,
  5 omisiones historicas, 0 fallos y 0 errores.
- `compileall`, enlaces relativos y `git diff --check`: aprobados.
- La evidencia no acredita persistencia, concurrencia o atomicidad PostgreSQL,
  autenticidad de webhooks ni viabilidad de Mercado Pago, y no implementa o
  valida ARCA.
- El simulador permanece aislado de flujos productivos. El diseño general 2.0
  continua `PROPUESTO_NO_APROBADO`; Mercado Pago y la revision
  juridica/contable siguen pendientes.
- Estado Git: cinco archivos locales, sin staging ni commit al registrar esta
  aprobacion. Push, merge y deploy: no realizados.

Timestamp: 2026-09-07T22:40:12-03:00
Estado: READY_TO_RESUME
Resultado: SIMULADOR_PSP_EN_MEMORIA_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Dispositivo/origen: laptop / Codex Desktop local
Agente: 02 - Implementacion - Builder
Objetivo: implementar exclusivamente un simulador PSP determinista, aislado y
en memoria para probar el contrato basico sin integracion productiva.
Rama y commit base: `develop` en
`1e85c6e592f970b2640a1e71d5b9a7019f8b3383`
Estado Git inicial: limpio y sin divergencia informada
Estado Git final: cambios locales sin staging ni commit
Push, PR, merge y deploy: NO realizados; no autorizados

## Reanudacion y revalidacion

Timestamp: 2026-09-08T21:46:39-03:00

- Los cinco archivos locales fueron reconocidos expresamente como trabajo
  previo esperado y se inspeccionaron completos.
- El simulador y sus 21 pruebas ya satisfacian el alcance; no se modifico su
  comportamiento.
- Focal repetida: 21 aprobadas, 0 fallidas y 0 omitidas.
- Suite completa repetida: 54 descubiertas, 21 aprobadas, 0 fallos de asercion,
  33 errores de importacion y 0 omitidas por dependencias ausentes.
- `compileall`, enlaces relativos y `git diff --check`: aprobados. El estado
  Git final conserva exclusivamente los cinco archivos esperados.

## Trabajo completado

- Se creo `app/services/psp_simulator.py` con almacenamiento privado por
  instancia, DTO inmutable, identificadores y reloj inyectados, estados
  `APPROVED`, `REJECTED` y `PENDING`, y resultado de llamada `UNCERTAIN`.
- La incertidumbre de transporte crea internamente un intento `PENDING`, eleva
  una excepcion especifica y permite recuperarlo mediante replay idempotente.
- La huella canonica compara referencia recortada, valor numerico exacto
  `Decimal` y moneda recortada en mayusculas. No cuantiza ni redondea.
- Se distinguen errores de no encontrado, conflicto idempotente, respuesta
  incierta y configuracion invalida.
- Los resultados devueltos son inmutables y no existe estado global mutable.

## Validacion y limitacion

- Focal `tests.test_psp_simulator`: 21/21 aprobadas; 0 fallidas; 0 omitidas.
- Suite completa: 54 descubiertas; 21 aprobadas; 0 fallos de asercion; 33
  errores de importacion; 0 omitidas.
- Limitacion de entorno: Python 3.12.14 de Codex Desktop no contiene Flask,
  SQLAlchemy, Alembic ni Werkzeug. No se instalaron dependencias y, por la
  exclusion del incremento, no se uso Docker.
- `python -m compileall -q app scripts tests`: aprobado.
- Enlaces relativos y `git diff --check`: aprobados.
- Queda pendiente repetir la suite en un runtime del proyecto con dependencias
  disponibles.

## Limites

El simulador no acredita persistencia, atomicidad o concurrencia PostgreSQL,
autenticidad, entrega u orden de webhooks, ni viabilidad tecnica, contractual o
comercial de Mercado Pago. No selecciona proveedor o arquitectura productiva y
no se conecta con ningun flujo operativo.

Archivos creados: `app/services/psp_simulator.py` y
`tests/test_psp_simulator.py`. Documentacion modificada:
`docs/CHANGELOG.md`, `docs/HANDOFFS/ACTIVE_HANDOFF.md` y
`docs/SPRINTS/2026-09-06_PRO_REFINAMIENTO_COMERCIAL_Y_PSP.md`.

Proximo paso: revisar el diff; para cerrar la validacion completa, repetir la
suite en un runtime ya configurado con las dependencias del proyecto. No
instalar, integrar ni publicar sin autorizacion.

---

# Handoff tecnico: cierre documental Sprint 1 PRO

Timestamp: 2026-09-07T21:54:36-03:00
Estado: COMPLETED
Resultado: CERRADO_DOCUMENTALMENTE_INTEGRACION_GIT_PENDIENTE
Dispositivo/origen: laptop / Codex Desktop local
Agente: 01 - Documentation Engineer
Objetivo: registrar el resultado de la revision independiente y cerrar el
alcance documental de Sprint 1.
Rama y ultimo commit observados: `develop` en
`1d22f87adc358eae20121ea727142b0276cf337e`
Estado Git: cuatro Markdown modificados, sin staging ni commit
Push, nuevo PR, merge y deploy: NO realizados; no autorizados

- El Agente 02 informo el `2026-09-07T21:41:54-03:00`: sin hallazgos, diff
  `APROBADO_PARA_COMMIT` y criterios documentales de cierre satisfechos.
- Sprint 1 queda `CERRADO_DOCUMENTALMENTE`; la integracion Git del presente
  registro permanece pendiente.
- Mercado Pago, revision juridica/contable y aclaracion de la estimacion de
  25-43 horas siguen pendientes y bloquean solo capacidades dependientes.
- El diseño 2.0 sigue `PROPUESTO_NO_APROBADO` y no autoriza implementacion.
- La ausencia de reviews nativas de GitHub permanece atribuida al informe
  disponible; no fue verificada de forma independiente en esta sesion.

Archivos modificados: `docs/HANDOFFS/ACTIVE_HANDOFF.md`, `docs/CHANGELOG.md`,
`docs/ROADMAP.md` y
`docs/SPRINTS/2026-09-06_PRO_REFINAMIENTO_COMERCIAL_Y_PSP.md`.

Tests de aplicacion: NO EJECUTADOS; alcance exclusivamente documental.
Validaciones: coherencia de estados, enlaces relativos y `git diff --check`.
Proximo paso: solicitar autorizacion separada para staging y commit del paquete.
No iniciar implementacion ni ejecutar push, PR, merge, deploy o cambios de rama.

---

# Handoff tecnico: preparacion de cierre documental Sprint 1 PRO

Timestamp: 2026-09-07T21:31:53-03:00
Estado: READY_TO_RESUME
Resultado: LISTO_PARA_REVISION_DE_DIFF
Dispositivo/origen: laptop / Codex Desktop local
Agente: 01 - Documentation Engineer
Objetivo: actualizar la trazabilidad posterior al merge de PR #7, incorporar
observaciones propuestas del diseño 2.0 y preparar la matriz de cierre.
Rama y ultimo commit observados: `develop` en
`1d22f87adc358eae20121ea727142b0276cf337e`
Estado Git inicial: limpio y sincronizado con `origin/develop` segun referencias
locales
Estado Git final esperado: cambios sin commit exclusivamente Markdown bajo
`docs/`
Push, nuevo PR, merge y deploy: NO realizados; no autorizados

## Estado anterior superado

Los bloques del `2026-09-06T19:38:40-03:00` y
`2026-09-06T19:22:08-03:00` describen correctamente el estado anterior al
commit y al merge. Quedan preservados como historia, pero fueron superados por
la integracion de PR #7.

## Evidencia recuperada

- Commit documental: `817fb4f3888a44984b951badc655eceeec2b9df8`.
- PR: #7, rama origen `docs/pro-commercial-psp-refinement`, destino `develop`.
- Merge: `1d22f87adc358eae20121ea727142b0276cf337e`, fechado
  `2026-09-06T20:11:47-03:00`; Git local confirma que contiene el commit.
- La revision focalizada anterior informo `APROBADO_PARA_COMMIT` en la
  conversacion. No fue una review nativa de GitHub.
- El informe del Agente 02 del `2026-09-07T20:59:03-03:00` registro cero
  reviews nativas en PR #7 y mantuvo pendiente el cierre documental.
- No existe una regla vigente que obligue a inventar o exigir retroactivamente
  una review nativa para registrar el merge.

## Trabajo completado en esta sesion

- Se actualizo Changelog, Roadmap y el documento del ciclo con el estado real
  post-merge.
- Se separaron pendientes, bloqueos por capacidad y responsables propuestos;
  ninguna propuesta se presenta como asignacion aceptada.
- Se incorporaron como `PROPUESTO_NO_APROBADO` las correcciones al diseño 2.0:
  pago mixto separado de cobertura total con creditos; confirmacion interna
  atomica para diferencia cero; unicidad por obligacion/periodo e importe; y
  consumo parcial de lotes preservando saldo y vencimiento.
- El rango de 25-43 horas quedo pendiente de aclarar como total o restante y
  de mapear a entregables, sin inventar una estimacion.
- Se preparo la matriz de criterios de cierre. El resultado no es una
  aprobacion ni un cierre automatico.

## Pendientes, bloqueantes y responsables propuestos

- Revision del diff documental actual: pendiente; proximo gate del Sprint 1.
- MP-01 a MP-16: sin enviar y sin respuesta. Bloquean las capacidades PSP que
  dependen de cada pregunta, no el contrato conceptual completo. Responsable
  propuesto: responsable tecnico MANDOBRA para coordinar; Mercado Pago para
  responder. No constituye asignacion aceptada.
- Revision juridica/contable: sin dictamen. Bloquea consentimiento, presentacion
  economica, reversas, comisiones y definiciones fiscales relacionadas.
  Responsable propuesto: producto para coordinar especialistas por designar.
- Producto/economia: precio, base y porcentaje, conversion, moneda, redondeo,
  impuestos, reservas y eventos tardios. Responsable propuesto: Cristian
  Sánchez/producto con contabilidad; asignacion no aceptada formalmente.
- Arquitectura 2.0 y ADR: pendientes de revision y aprobacion expresa. No se
  aprobaron modelos, constraints, SDK, endpoints, migraciones ni proveedor.
- Facturacion opcional permanece separada de contratacion y cobro; su evaluacion
  fiscal es un incremento propio.

## Archivos, validaciones y restricciones

Archivos modificados: `docs/HANDOFFS/ACTIVE_HANDOFF.md`, `docs/CHANGELOG.md`,
`docs/ROADMAP.md` y
`docs/SPRINTS/2026-09-06_PRO_REFINAMIENTO_COMERCIAL_Y_PSP.md`.

Migraciones relacionadas: ninguna. Tests de aplicacion: NO EJECUTADOS; no
aplican al alcance documental. La validacion final debe comprobar alcance,
whitespace, enlaces y coherencia de estados.

Proximo paso exacto: realizar una revision independiente del diff documental y
de la matriz de cierre. Solo despues de un resultado explicito decidir si el
Sprint 1 puede marcarse `APROBADO` o `CERRADO`.

No iniciar implementacion, aprobar arquitectura 2.0, contactar terceros,
instalar dependencias, modificar codigo/modelos/bases/configuracion, ni ejecutar
commit, push, PR, merge, rebase, reset, clean, cambio de rama o deploy.

---

# Handoff tecnico: correcciones posteriores a revision focalizada PRO

Timestamp: 2026-09-06T19:38:40-03:00
Estado: READY_TO_RESUME
Resultado del ciclo: CORRECCIONES_DOCUMENTALES_LISTAS_PARA_REVISION_FOCALIZADA
Dispositivo/origen: laptop / Codex Desktop local
Agente: 01 - Documentation Engineer
Objetivo: corregir cuatro hallazgos P1 y dos P2 sin ampliar el alcance del
paquete documental.
Rama: `docs/pro-commercial-psp-refinement`
Commit base y ultimo commit observado: `1548935`
Estado Git: paquete Markdown bajo `docs/` sin commit
Push, PR y merge: NO realizados; no autorizados

## Correcciones realizadas

- REQ-001 diferencia origen del trabajo y canal de pago: trabajos externos
  cobrados mediante MANDOBRA pueden generar creditos; efectivo y pagos fuera
  de MANDOBRA no los generan.
- Reserva aprobada: indisponibilidad sin consumo, consumo solo tras pago
  completo, liberacion definitiva con vencimiento original, no reactivacion de
  creditos vencidos y conciliacion de estados inciertos/reintentos.
- Tarjeta vinculada requerida comercialmente aun con creditos completos, con
  viabilidad pendiente y separacion respecto de autorizacion de debito/datos.
- Switch definido como preferencia/autorizacion sincronizada con el PSP; el
  sistema previene duplicados sin imponer al usuario una antelacion desconocida.
- Se agregaron precio, cargo y total previos, neto profesional estimado,
  obligacion unica en contratos internos y efectivo configurable sin creditos.
- Se incorporaron criterios de aceptacion verificables para esas reglas.
- Master Spec enumera las capacidades comerciales realmente pendientes y deja
  la extension de 60 dias solo como antecedente historico reemplazado.

## Estado y pendientes

- La nueva correccion NO esta aprobada: requiere revision focalizada antes de
  commit o transferencia operativa al Agente 02.
- Permanecen pendientes plazo de reserva, acreditaciones tardias, precio,
  porcentaje/base, costos, impuestos, reversas, antelacion, viabilidad PSP y
  validacion juridica/contable.
- No se aprobaron arquitectura, modelos, migraciones, proveedor o SDK nuevos.
- Tests de aplicacion: NO EJECUTADOS - alcance documental.
- No se modificaron codigo, configuracion, bases ni dependencias.

Proximo paso: revisar focalmente REQ-001, Master Spec, Changelog y este handoff;
si el resultado es aprobado, solicitar autorizacion separada para commit. No
iniciar implementacion ni contactos externos.

---

# Handoff tecnico: refinamiento documental comercial PRO y PSP

Timestamp: 2026-09-06T19:22:08-03:00
Estado: COMPLETED
Resultado del ciclo: DOCUMENTACION_CONSOLIDADA_LISTA_PARA_REVISION_Y_AGENTE_02
Dispositivo/origen: laptop / Codex Desktop local
Agente: 01 - Documentation Engineer
Objetivo: consolidar reglas comerciales PRO, corregir contradicciones,
incorporar expedientes juridico/contable y Mercado Pago, actualizar
planificacion, enlaces y cierre post-merge.
Rama: `docs/pro-commercial-psp-refinement`
Commit base y ultimo commit observado: `1548935`
Estado Git inicial: limpio
Estado Git final: cambios Markdown bajo `docs/` sin commit
Push a GitHub: NO realizado
PR: NO creado
Merge: NO; tarea documental local sin autorizacion de publicacion

## Trabajo completado

- PR #5 y PRO Entitlement Foundation quedaron registrados como integrados en
  `develop` mediante merge `1548935`, con resultado informado
  `APROBADO_POST_MERGE` y evidencia 294/289/0/5.
- REQ-001 conserva implementacion parcial y reemplaza la regla historica de 60
  dias por creditos, umbral y periodos transaccionales de 30 dias.
- Se separaron decisiones aprobadas, propuestas juridico-operativas y
  pendientes de producto/proveedor.
- Se incorporaron los expedientes de Mercado Pago y revision juridica/contable
  como borradores no enviados.
- Se alinearon REQ-002, Master Spec, indices, Roadmap, Backlog, arquitectura,
  Changelog y documentos de sprint.

## Pendientes y bloqueantes

- Revision humana del diff documental y aprobacion antes de commit/publicacion.
- MP-01 a MP-16: todas pendientes; no se contacto a Mercado Pago.
- Revision juridica y contable: pendiente; el expediente no es dictamen.
- Producto: precio, porcentaje/base, conversion de creditos, reversas, reservas,
  aprobaciones tardias, cambios de precio, consentimiento y beneficios finales.
- Arquitectura: ADR PSP/eventos, ledger/compensaciones, concurrencia, secretos y
  observabilidad, posteriores a viabilidad y decisiones aprobadas.
- Facturacion: evaluacion directa/proveedor pendiente; implementacion separada.

## Validacion y alcance

- Archivos modificados: exclusivamente Markdown bajo `docs/`.
- Tests de aplicacion: NO EJECUTADOS - no aplican al alcance documental.
- Migraciones, bases, Docker, dependencias y contactos externos: NO ejecutados.
- Commit, push, PR, merge y deploy: NO ejecutados.
- `git diff --check`: PASS. Enlaces relativos de los archivos modificados y
  nuevos: destinos existentes. El checker general solo detecto el placeholder
  historico `../TROUBLESHOOTING/archivo.md` de la plantilla de handoff, fuera
  del alcance y no introducido por este ciclo.

## Proximo paso recomendado

Transferir a Agente 02 un encargo exclusivamente de evaluacion y preparacion:
mapa de brechas, viabilidad separada marketplace/suscripcion, comparacion
ARCA/proveedores, slicing de sprints 2 y 3, estrategia de pruebas, estimaciones
y decisiones previas a codigo. No implementar ni contactar terceros sin nueva
autorizacion.

Para retomar: confirmar rama, HEAD y estado; revisar primero este bloque, el
[plan del ciclo](../SPRINTS/2026-09-06_PRO_REFINAMIENTO_COMERCIAL_Y_PSP.md),
[REQ-001](../REQUISITOS/REQ-001-activacion-y-vigencia-pro.md),
[consultas PSP](../CONSULTAS/MERCADO_PAGO_v0_1.md) y
[base juridica](../LEGAL/BASE_REVISION_JURIDICA_v0_2.md).

No ejecutar implementacion, tests, migraciones, contacto externo, commit,
push, PR, merge, rebase, reset, clean, stash, amend ni deploy sin autorizacion.

---

# Handoff tecnico: correccion responsive y teclado de admin usuarios

Timestamp: 2026-09-05T20:27:36-03:00
Estado: READY_TO_RESUME
Resultado del ciclo: CORRECCION_IMPLEMENTADA_VALIDADA_LOCALMENTE_PENDIENTE_RETESTING_QA
Dispositivo/origen: Codex Desktop local
Agente: 02 - Implementacion - Builder
Objetivo: corregir el overflow global desktop y la visibilidad inicial del
control `Suspender` al navegar por teclado en `/admin/usuarios`.
Rama: `feature/pro-entitlement-foundation`
Commit base: `fe048c4810cc337dfd1c3498d9f96579453cd065`
PR asociado: #5, abierto y bloqueado para merge hasta retesting independiente
de 05 - QA funcional
Estado Git: seis cambios correctivos locales sin commit
Push a GitHub: NO realizado
Merge: NO; no autorizado

## Trabajo completado

- Se reprodujo 1453px de ancho documental frente a 1440px de viewport y el
  control `Suspender` terminando en 449.25px frente a 390px de viewport.
- Un wrapper exclusivo de admin usuarios contiene el scroll horizontal, tiene
  nombre accesible, foco por teclado, foco visible y scroll padding con tokens.
  La tabla sigue siendo `<table>`, conserva ocho columnas y todas las acciones.
- Implementacion valido claro/oscuro en 1440x900 y 390x844. Resultado:
  documento 1425/1425 desktop y 375/390 mobile; `Suspender` quedo entre
  247.48px y 351.44px dentro del wrapper de 12px a 363.20px. El wrapper
  mantuvo scroll interno de 1216px y cero errores de consola.
- No se agrego JavaScript, `!important`, colores hardcodeados, ocultamiento
  global de overflow ni cambios en logica PRO, rutas, servicios o migraciones.

## Validaciones

- Focal Design System/Admin/PRO: 30 ejecutados, 30 aprobados, 0 fallidos,
  0 errores y 0 omitidos.
- Suite completa: 294 ejecutados, 289 aprobados, 0 fallidos, 0 errores y
  5 omitidos historicos.
- `python -m compileall -q app scripts tests`: PASS.
- `python -m alembic heads`: `20260904_01 (head)`.
- `git diff --check`: PASS.
- La suite historica de migraciones ejercito downgrade solo en sus bases
  temporales; no hubo downgrade sobre la base QA ni sobre `trax_db`.

## Archivos locales modificados

- `app/static/css/styles.css`
- `app/templates/admin_usuarios.html`
- `tests/test_design_system_v2.py`
- `docs/CHANGELOG.md`
- `docs/SPRINTS/2026-09-04_PRO_ENTITLEMENT_FOUNDATION.md`
- `docs/HANDOFFS/ACTIVE_HANDOFF.md`

## Playwright, axe-core y pendientes

- No existen `package.json`, lockfiles, configuracion o tests Playwright, ni
  axe-core versionado. No se instalaron ni modificaron dependencias.
- Propuesta minima pendiente de autorizacion: `@playwright/test@1.62.1` y
  `@axe-core/playwright@4.13.0` como devDependencies; crear `package.json`,
  lock, `playwright.config.js` y `tests/e2e/admin-users-responsive.spec.js`;
  ejecutar con `npx playwright test`.
- Pendiente: retesting independiente en 05 - QA funcional. El PR #5 permanece
  bloqueado para merge; Coverage continua pendiente y no bloqueante.
- Proximo paso recomendado: auditoria tecnica focal y envio del paquete a QA.
- Para retomar: confirmar rama, SHA y estado Git; leer este bloque y revisar
  exclusivamente los seis archivos listados.
- No ejecutar commit, push, nuevo PR, merge, rebase, reset, clean, stash,
  amend ni deploy sin autorizacion explicita.

---

# Handoff tecnico: correccion focal de contraste oscuro PRO

Timestamp: 2026-09-05T19:45:29-03:00
Estado: READY_TO_RESUME
Resultado del ciclo: CORRECCION_IMPLEMENTADA_VALIDADA_LOCALMENTE_PENDIENTE_RETESTING_QA
Dispositivo/origen: Codex Desktop local
Agente: 02 - Implementacion - Builder
Objetivo: corregir exclusivamente el P1 visual de contraste oscuro informado
por QA funcional para las superficies PRO y administracion de usuarios.
Rama: `feature/pro-entitlement-foundation`
Commit base y ultimo commit: `f35797a1852e4b0293b1618ac03fdbbdba0510ae`
PR asociado: #5, abierto, no modificado y bloqueado para merge hasta el
retesting independiente de 05 - QA funcional
Estado Git: cambios correctivos locales sin commit
Push a GitHub: NO realizado
Merge: NO; no autorizado

## Trabajo completado

- Las tarjetas de `/profesional/pro/upgrade` y la tabla, navegacion, estados y
  acciones de `/admin/usuarios` consumen tokens del Design System v2 dentro de
  alcances exclusivos de pantalla.
- Se agrego cobertura estatica de regresion para impedir el regreso de fondos
  o textos hardcodeados en las superficies corregidas.
- Implementacion realizo la medicion visual claro/oscuro en 390x844 y
  1440x900: contraste principal 17.74:1 en claro y 16.98:1 en oscuro; texto
  secundario 6.93:1 en oscuro. No hubo overflow de documento en movil ni
  errores de consola.
- Implementacion comprobo la revocacion con la ruta administrativa real sobre
  SQLite efimero: el usuario paso de PRO a WORK y luego se mostro Elegible en
  upgrade. `trax_db` no fue migrada, reseteada ni modificada.

## Validaciones

- Focal Design System/PRO: 30 ejecutados, 30 aprobados, 0 fallidos, 0 errores,
  0 omitidos.
- Suite completa: 294 ejecutados, 289 aprobados, 0 fallidos, 0 errores y
  5 omitidos historicos.
- `python -m compileall -q app scripts tests`: PASS.
- `python -m alembic heads`: `20260904_01 (head)`.
- `git diff --check`: PASS.

## Archivos locales modificados

- `app/static/css/styles.css`
- `app/templates/admin_usuarios.html`
- `tests/test_design_system_v2.py`
- `docs/CHANGELOG.md`
- `docs/SPRINTS/2026-09-04_PRO_ENTITLEMENT_FOUNDATION.md`
- `docs/HANDOFFS/ACTIVE_HANDOFF.md`

## Pendientes, riesgos y reanudacion

- Pendiente: retesting independiente del P1 por 05 - QA funcional, revision
  del diff y autorizacion explicita antes de cualquier commit o push. El PR #5
  permanece bloqueado para merge. Coverage permanece pendiente y no bloqueante.
- Riesgo conocido preexistente: la tabla administrativa densa conserva scroll
  horizontal interno; en desktop su ancho puede superar el viewport. No fue
  introducido ni ampliado por esta correccion focal.
- Proximo paso recomendado: auditoria tecnica focal del paquete visual y, si
  resulta aprobado, solicitar autorizacion para un commit correctivo en la
  misma rama y la actualizacion del PR #5.
- Para retomar: confirmar rama, commit, estado Git, leer este handoff y revisar
  los seis archivos indicados antes de actuar.
- No ejecutar commit, push, merge, rebase, reset, clean, stash, amend, nuevo PR
  ni deploy sin autorizacion explicita.

---

# Handoff tecnico: revalidacion independiente posterior a correcciones P1

Timestamp: 2026-09-05T14:49:25-03:00
Estado: COMPLETED
Resultado del ciclo: APROBADO
Dispositivo/origen: Codex Desktop local
Agente: 03 - Testing - Test Executor
Objetivo: revalidar independientemente PRO Entitlement despues de las
correcciones P1 de gates Alembic y rollback PostgreSQL.
Rama: `feature/pro-entitlement-foundation`
Commit probado: `e5b4ba9be651772afe86683b8f7a6494b2afb0f7`
Commit funcional anterior: `fe979ce278607bfcf243ff2dbab31984d4b1e7ee`
PR asociado: #5
Estado Git inicial: limpio
Push a GitHub: NO realizado en esta sesion
Merge: NO; no autorizado

## Evidencia valida

- Se invalido expresamente la suite cortada por el cierre de Docker y no se
  utilizo como evidencia.
- Tras reiniciar Docker se eliminaron las cuatro bases residuales con prefijo
  `trax_pro_entitlement_test_` y se verifico `ABSENT`.
- `python -m compileall -q app scripts tests`: PASS.
- Suite focal Alembic, PRO y migraciones: 43 ejecutados, 43 aprobados, 0
  fallidos, 0 errores, 0 omitidos.
- Suite completa posterior al reinicio: 293 ejecutados, 288 aprobados, 0
  fallidos, 0 errores y 5 omitidos historicos.
- Validacion dinamica Alembic: 6/6 PASS; confirma head unico obtenido del
  grafo, revision aplicada exacta, ascendencia de `20260726_07` y rechazo de
  multiples heads, base vacia, atrasada, desconocida o sin ancestro requerido.
- Head del repositorio: `20260904_01 (head)`.
- Gate PostgreSQL PRO: 2/2 PASS. El caso de rollback provoco una FK invalida
  real al insertar auditoria, confirmo desde otra conexion que dos
  entitlements seguian activos y que no persistio AuditLog, recupero la sesion
  mediante rollback y completo una revocacion valida posterior.
- Gate PostgreSQL contracting concurrency: 8/8 PASS.
- Gate PostgreSQL negotiation concurrency: 8/8 PASS.
- Gate PostgreSQL OperationCommand partial migration: 21/21 PASS.
- Ningun gate PostgreSQL obligatorio quedo omitido.
- `git diff --check 18e46fd...e5b4ba9` y verificacion final: PASS.
- Coverage: PENDIENTE y no bloqueante; `coverage.py` no esta declarado y no se
  instalaron dependencias.

## PostgreSQL y limpieza

- Evidencia valida ejecutada exclusivamente sobre bases nuevas con nombres
  `trax_pro_entitlement_test_resume2_pro`,
  `trax_pro_entitlement_test_resume2_contracting`,
  `trax_pro_entitlement_test_resume2_negotiation` y
  `trax_pro_entitlement_test_resume2_partial`.
- Las cuatro bases fueron eliminadas despues de finalizar los procesos.
- Verificacion final de bases `trax_pro_entitlement_test_*`: `ABSENT`.
- `trax_db` conserva revision `20260726_07`; no fue reseteada ni migrada.
- Staging, produccion y volumenes no fueron modificados.

## Hallazgos, archivos y cierre

- P0/P1 nuevos: ninguno.
- Observaciones no bloqueantes: advertencias legacy/deprecacion ya existentes
  de SQLAlchemy y `datetime.utcnow()`.
- Codigo productivo, migraciones y tests: sin modificaciones en esta sesion.
- Unico archivo modificado: `docs/HANDOFFS/ACTIVE_HANDOFF.md` por cierre
  obligatorio.
- Los dos P1 previos quedan VERIFICADOS como cerrados.
- Veredicto final: `APROBADO`.
- Proximo paso recomendado: revision/integracion de PR #5 mediante el flujo
  autorizado. No realizar commit, push, PR, merge, rebase, reset, clean,
  stash, amend ni deploy sin autorizacion expresa.

---

# Handoff tecnico: cierre P1 de prueba dinamica Alembic

Timestamp: 2026-09-04T20:02:58-03:00
Estado: READY_TO_RESUME
Resultado del ciclo: CORRECCIONES_IMPLEMENTADAS_PENDIENTES_DE_RETESTING
Dispositivo/origen: Codex Desktop local
Agente: 02 - Implementacion - Builder
Objetivo: eliminar la dependencia fija del head vigente en la prueba real del
helper Alembic, sin modificar el helper, los gates ni el nucleo PRO.
Rama: `feature/pro-entitlement-foundation`
Commit base: `fe979ce278607bfcf243ff2dbab31984d4b1e7ee`
Estado Git: paquete correctivo local sin commit
Push a GitHub: NO; las correcciones locales no fueron publicadas
PR: #5 permanece abierto y no mergeado
Merge: NO; no autorizado

## Trabajo completado

- La prueba real construye `ScriptDirectory` desde `alembic.ini`, obtiene los
  heads mediante `get_heads()` y exige exactamente uno.
- El unico head real se usa como revision aplicada y resultado esperado del
  helper; una migracion descendiente futura no requiere editar esta prueba.
- Se preservaron los escenarios adversariales y no cambio codigo funcional.
- Helper Alembic: 6 ejecutados, 6 aprobados, 0 fallidos, 0 omitidos.
- Migraciones historicas: 16 ejecutados, 16 aprobados, 0 fallidos, 0 omitidos.
- Suite completa: 293 ejecutados, 288 aprobados, 0 fallidos, 5 omitidos.
- `compileall -q tests`, `git diff --check` y busqueda de referencias: PASS.

## Proximo paso y restricciones

Transferir el paquete correctivo validado a una nueva revision tecnica. No
ejecutar commit, push, nuevo PR, merge, rebase, reset, clean, stash, amend ni
deploy sin autorizacion expresa.

---

# Handoff tecnico: ejecucion independiente del fundamento PRO

Timestamp: 2026-09-04T19:25:31-03:00
Estado: READY_TO_RESUME
Resultado del ciclo: CORRECCIONES_IMPLEMENTADAS_PENDIENTES_DE_RETESTING
Dispositivo/origen: Codex Desktop local
Agente: 03 - Testing - Test Executor
Objetivo: validar independientemente el fundamento tecnico de autorizacion PRO.
Rama: `feature/pro-entitlement-foundation`
Commit probado: `fe979ce278607bfcf243ff2dbab31984d4b1e7ee`
Estado Git inicial: limpio
Push a GitHub: NO
Merge: NO; no autorizado

## Evidencia ejecutada

- Identidad de rama y commit: PASS.
- `git diff --check develop...fe979ce`: PASS.
- `python -m compileall -q app scripts tests` dentro de `trax-web`: PASS.
- Suite focal PRO: 21 ejecutados, 21 aprobados, 0 fallidos, 0 omitidos.
- Suite completa: 287 tests descubiertos; ejecucion final sin fallos y con las
  5 omisiones historicas esperadas.
- Gate PostgreSQL PRO: 1 ejecutado, 1 aprobado, 0 fallidos, 0 omitidos.
- Runner PostgreSQL de migracion parcial: 21 ejecutados, 21 aprobados, 0
  fallidos, 0 omitidos en repeticion aislada.
- `alembic heads`: `20260904_01 (head)`.
- Coverage: NO EJECUTADO; `coverage.py` no esta declarado ni disponible y no
  se autorizo instalar dependencias.
- Playwright, axe-core y responsive: NO REQUERIDOS por el paquete para este
  incremento.

## Hallazgos y bloqueantes

- P1 TEST: `postgresql_contracting_concurrency_e2e.py` y
  `postgresql_negotiation_concurrency_e2e.py` conservan una expectativa fija
  de revision `20260726_07`; con el head vigente `20260904_01` ambos fallan en
  `setUpClass` antes de ejecutar casos.
- P1 COBERTURA: la atomicidad de revocacion y `AuditLog` esta probada en la
  suite focal SQLite, pero el gate PRO PostgreSQL no fuerza ese rollback; la
  evidencia PostgreSQL obligatoria del paquete queda pendiente.
- P2 DOCUMENTACION: el handoff anterior seguia describiendo el incremento como
  cambios sin commit sobre `18e46fd`, aunque el paquete y el HEAD probado son
  `fe979ce`.
- Una repeticion del runner parcial sufrio dos errores de entorno porque la
  primera base efimera desaparecio durante la corrida. La repeticion aislada
  posterior paso 21/21, por lo que no se clasifica como defecto del producto.

## Bases PostgreSQL y seguridad

- Bases efimeras utilizadas:
  `trax_pro_entitlement_test_executor_20260904` y
  `trax_pro_entitlement_test_partial_20260904`.
- Ambas fueron eliminadas; no quedan bases con prefijo
  `trax_pro_entitlement_test`.
- `trax_db`, staging, produccion y volumenes no fueron reseteados ni migrados.
- No se imprimieron secretos ni se conservaron credenciales o datos reales.

## Archivos modificados y proximo paso

- Modificado en esta sesion: `docs/HANDOFFS/ACTIVE_HANDOFF.md` exclusivamente.
- Codigo productivo, migraciones y tests: sin modificaciones.
- Proximo paso recomendado: actualizar los dos gates historicos para aceptar el
  head vigente sin debilitar sus invariantes y ampliar el gate PostgreSQL PRO
  con rollback real de revocacion y auditoria; luego repetir el paquete.
- No realizar commit, push, PR, merge, rebase, reset, clean, stash ni deploy sin
  autorizacion expresa.

## Correcciones implementadas por Builder

Timestamp: 2026-09-04T19:50:24-03:00

- Commit evaluado y base de las correcciones:
  `fe979ce278607bfcf243ff2dbab31984d4b1e7ee`.
- Los gates posteriores a `upgrade("head")` validan dinamicamente un unico
  head, una unica revision aplicada, coincidencia exacta y ascendencia desde
  `20260726_07`; los checkpoints historicos explicitos se conservaron.
- El gate PRO PostgreSQL fuerza una FK invalida durante el commit conjunto de
  dos revocaciones y AuditLog, comprueba rollback desde conexion independiente,
  recuperacion de sesion y una revocacion valida posterior.
- Helper Alembic: 5 ejecutados, 5 aprobados, 0 fallidos, 0 omitidos.
- Migraciones historicas: 16 ejecutados, 16 aprobados, 0 fallidos, 0 omitidos.
- Gates PostgreSQL historicos: contratacion 8/8, negociacion 8/8, reviews 10/10
  y rutas/moderacion 8/8.
- Gate PostgreSQL PRO: 2 ejecutados, 2 aprobados, 0 fallidos, 0 omitidos.
- Suite focal PRO: 21 ejecutados, 21 aprobados, 0 fallidos, 0 omitidos.
- Suite completa: 292 ejecutados, 287 aprobados, 0 fallidos, 5 omitidos.
- Coverage permanece PENDIENTE y no bloqueante; `coverage.py` no fue instalado.
- PR #5 no fue modificado, cerrado ni mergeado.

Estado final: READY_TO_RESUME; resultado
`CORRECCIONES_IMPLEMENTADAS_PENDIENTES_DE_RETESTING`.

---

# Handoff tecnico: cierre focal P1 del guard PostgreSQL

Timestamp: 2026-09-04T13:19:30-03:00
Estado: COMPLETED
Resultado del ciclo: CORRECCION_P1_FOCAL_VALIDADA
Dispositivo/origen: Codex Desktop local
Agente: 02 - Implementacion - Builder
Rama: `feature/pro-entitlement-foundation`
Commit base y ultimo commit: `18e46fd6bf6d05b73884b7ba3fdbb335f66d7d7e`
Estado Git: incremento PRO y correccion focal sin commit
Push a GitHub: NO
Merge: NO; no autorizado

## Objetivo y resultado

Cerrar exclusivamente el P1 pendiente del guard PostgreSQL, sin modificar la
implementacion funcional PRO. El nombre se valida mediante `fullmatch()` contra
`^trax_pro_entitlement_test(?:_[a-z0-9]+(?:_[a-z0-9]+)*)?$`, sin parametros y
con el limite PostgreSQL de 63 bytes. La autorizacion de reset y el dialecto
PostgreSQL siguen siendo obligatorios.

## Archivos modificados en esta correccion

- `tests/postgresql_pro_entitlement_e2e.py`
- `tests/test_pro_entitlement_foundation.py`
- `docs/postgres_dev.md`
- `docs/SPRINTS/2026-09-04_PRO_ENTITLEMENT_FOUNDATION.md`
- `docs/HANDOFFS/ACTIVE_HANDOFF.md`

No se modificaron modelos, servicios, rutas, templates, seed ni migraciones
durante esta correccion focal.

## Tests y migraciones

- Guard focal: 5 ejecutados, 5 aprobados, 0 fallidos, 0 omitidos.
- Suite focal PRO: 21 ejecutados, 21 aprobados, 0 fallidos, 0 omitidos.
- Suite completa: 287 ejecutados, 282 aprobados, 0 fallidos, 5 omitidos.
- Gate PostgreSQL real: 1 ejecutado, 1 aprobado, 0 fallidos, 0 omitidos sobre
  `trax_pro_entitlement_test_finalaudit_20260904`.
- Rechazo instrumentado de `trax_db`: 1 ejecutado y aprobado; engine no creado.
- Revision de `trax_db` antes y despues: `20260726_07`; no fue migrada.
- Base descartable eliminada despues de la validacion; volumenes preservados.
- `compileall`: PASS.
- `alembic heads`: `20260904_01 (head)`.
- `git diff --check`: PASS.

## Pendientes, riesgos y proximo paso

El P1 del guard queda cerrado. REQ-001 sigue en implementacion parcial; PSP,
pagos, suscripcion comercial, renovaciones y REQ-002 permanecen fuera de este
alcance. Proximo paso recomendado: revision tecnica final y, si resulta
aprobada, solicitar autorizacion para commit. No ejecutar commit, push, PR,
merge, rebase, reset, clean, stash ni deploy sin autorizacion expresa.

---

# Handoff tecnico: correcciones de auditoria del nucleo PRO

Timestamp: 2026-09-04T10:29:16-03:00
Estado: COMPLETED
Resultado del ciclo: CORRECCIONES_P1_VALIDADAS
Dispositivo/origen: Codex Desktop local
Agente: 02 - Implementacion - Builder
Rama: `feature/pro-entitlement-foundation`
Commit base y ultimo commit: `18e46fd6bf6d05b73884b7ba3fdbb335f66d7d7e`
Estado Git: cambios sin commit del incremento PRO y sus correcciones autorizadas
Push a GitHub: NO
Merge: NO; pendiente de nueva revision y autorizacion

## Objetivo

Corregir los hallazgos P1/P2/P3 de la auditoria sin descartar la implementacion
existente ni ampliar REQ-001.

## Trabajo completado

- Revocacion limitada por `user_id` a PRO ACTIVA, fuente TRANSACTIONAL o
  SUBSCRIPTION, vencimiento no nulo y futuro.
- Revocacion y AuditLog preparados en una sesion y confirmados con un unico
  commit; cualquier excepcion ejecuta rollback y se propaga.
- `create_audit_log()` conserva el commit para callers legacy mediante un
  helper interno sin commit. La atomicidad de otras acciones administrativas
  queda registrada como deuda fuera de alcance.
- Gate PostgreSQL endurecido antes de crear el engine: solo acepta
  `trax_pro_entitlement_test` o `trax_pro_entitlement_test_<sufijo>`.
- Downgrade documentado y probado como reversible estructuralmente pero no para
  la clasificacion de `source_type`; el re-upgrade devuelve NULL.
- Seed QA temporalmente idempotente: conserva vencimientos futuros y renueva la
  misma fila vencida por 365 dias sinteticos de QA.
- Frontera UTC centralizada para timestamps PRO sobre columnas legacy UTC
  naive.
- Frontmatter de REQ-001 corregido a `IMPLEMENTACION_PARCIAL` sin cambiar su
  estado `APROBADO`.

## Migracion y gate PostgreSQL

- Head: `20260904_01`.
- Base descartable usada: `trax_pro_entitlement_test_20260904_102916`.
- Upgrade/downgrade/re-upgrade: PASS; perdida de clasificacion confirmada.
- Gate: 1 ejecutado, 1 aprobado, 0 fallidos, 0 omitidos.
- Intento contra `trax_db`: rechazado antes de crear el engine.
- Revision de `trax_db` antes y despues: `20260726_07`; sin mutacion.
- La base descartable fue eliminada; `trax_db` y los volumenes se preservaron.

## Tests y validaciones

- Focalizadas finales: 20 ejecutadas, 20 aprobadas, 0 fallidas, 0 omitidas.
- Suite final: 286 ejecutadas, 281 aprobadas, 5 omitidas, 0 fallidas.
- `compileall`: PASS.
- `alembic heads`: `20260904_01 (head)`.
- `git diff --check`: PASS.
- Dos fallos intermitentes ajenos a PRO aparecieron en corridas previas; ambos
  pasaron aislados. Se aislo el estado del limiter en las pruebas PRO y la
  corrida completa final paso.

## Riesgos y pendientes

- El downgrade pierde deliberadamente `source_type`; exige respaldo y
  autorizacion cuando la clasificacion deba conservarse.
- Otras acciones administrativas legacy aun pueden contener commits internos;
  su refactorizacion no fue autorizada en este ciclo.
- PSP, pagos, suscripcion comercial, renovaciones y REQ-002 siguen pendientes.

## Proximo paso

Ejecutar una nueva revision tecnica del diff. No realizar commit, push, PR,
merge ni deploy sin autorizacion explicita.

---

# Handoff tecnico: fundacion del entitlement PRO

Timestamp: 2026-09-04T10:03:12-03:00
Estado: COMPLETED
Resultado del ciclo: IMPLEMENTACION_PARCIAL_VALIDADA
Dispositivo/origen: Codex Desktop local
Agente: 02 - Implementacion - Builder
Rama: `feature/pro-entitlement-foundation`
Commit base y ultimo commit: `18e46fd6bf6d05b73884b7ba3fdbb335f66d7d7e`
Estado Git: cambios sin commit exclusivamente del incremento enumerado abajo
Push a GitHub: NO
Merge: NO; pendiente de revision y autorizacion

## Objetivo

Implementar el primer incremento de REQ-001: evaluador central de entitlement
PRO con elegibilidad, fuente valida, vencimiento UTC, bloqueo de concesiones
legacy/manuales y un unico entitlement QA local.

## Trabajo completado

- Se agrego `Subscription.source_type`, nullable para preservar historia y con
  constraint para TRANSACTIONAL o SUBSCRIPTION.
- `has_pro_access()` exige PROFESIONAL ACTIVO, verificacion PROFESIONAL
  APROBADA, PRO ACTIVA, fuente reconocida y expiracion futura.
- Puntos, verificacion aislada, legacy, ENTERPRISE, filas indefinidas o vencidas
  y cuentas no elegibles no conceden capacidades.
- Las rutas profesional y administrativa ya no crean acceso PRO; la accion
  visual administrativa fue retirada y la pantalla profesional informa la
  indisponibilidad comercial.
- La revocacion administrativa cancela todas las filas PRO activas del usuario
  sin afectar una eventual fila FREE activa.
- El seed QA deja exactamente a `electricidad.pro@demo.trax.local` con una
  fuente SUBSCRIPTION temporal y conserva el bloqueo production/prod.
- Se creo ADR-001 y se actualizo la trazabilidad documental.

## Parcialmente completado y pendientes

REQ-001 permanece parcial. Faltan PSP, prueba de 30 dias, extensiones de 60
dias, pagos, suscripcion comercial, renovaciones, mora y contracargos.
REQ-002, Facturacion, ARCA, IA y ENTERPRISE operativo quedaron fuera de alcance.

## Migracion

- `20260904_01_pro_entitlement_foundation.py`, lineal desde `20260726_07`.
- Upgrade y downgrade verificados en SQLite y PostgreSQL 16 descartable.
- Registros legacy conservados con `source_type=NULL`.

## Tests ejecutados

- Baseline: 266 ejecutados, 261 aprobados, 5 omitidos, 0 fallidos.
- Focalizados finales: 14 ejecutados, 14 aprobados, 0 omitidos, 0 fallidos.
- Suite final: 280 ejecutados, 275 aprobados, 5 omitidos, 0 fallidos.
- Gate PostgreSQL: 1 ejecutado y aprobado, sin omisiones.
- `python -m compileall -q app scripts tests`: PASS.
- `python -m alembic heads`: `20260904_01 (head)`.
- `git diff --check`: PASS.

## Errores y troubleshooting

- El primer gate no importo `app` al ejecutarse como archivo; se corrigio el
  bootstrap de `PROJECT_ROOT`, patron ya usado por scripts del repositorio.
- La primera regresion mostro 36 asserts que fijaban el head historico; se
  actualizaron solo las expectativas ejecutadas despues de `upgrade head`.
- No se creo troubleshooting separado: causa y solucion fueron directas y
  quedaron cubiertas por tests.

## Archivos modificados o creados

- `app/models/subscription.py`
- `app/services/subscription_service.py`
- `app/routes/main_routes.py`
- `app/templates/solicitar_upgrade_pro.html`
- `app/templates/admin_usuarios.html`
- `scripts/dev_seed_professionals.py`
- `migrations/versions/20260904_01_pro_entitlement_foundation.py`
- `tests/test_pro_entitlement_foundation.py`
- `tests/test_pro_entitlement_migration.py`
- `tests/postgresql_pro_entitlement_e2e.py`
- `tests/test_sprint7_contract_review_migration.py`
- `tests/test_sprint7_negotiation_migration.py`
- `docs/ADR/README.md`
- `docs/ADR/ADR-001-pro-entitlement-foundation.md`
- `docs/REQUISITOS/REQ-001-activacion-y-vigencia-pro.md`
- `docs/REQUISITOS/MASTER_SPEC.md`
- `docs/ROADMAP.md`, `docs/BACKLOG.md`, `docs/CHANGELOG.md`
- `docs/QA_LOCAL.md`, `docs/INDEX.md`
- `docs/SPRINTS/2026-09-04_PRO_ENTITLEMENT_FOUNDATION.md`
- `docs/HANDOFFS/ACTIVE_HANDOFF.md`

## Riesgos y proximo paso

- No aplicar la migracion antes de desplegar el codigo produciria errores por
  columna ausente; no existe autorizacion de deploy.
- Las fuentes comerciales aun no tienen productores reales.
- Proximo paso: revision tecnica del diff; si se aprueba, autorizar commit y
  push de la rama. No mergear ni desplegar automaticamente.

## Instrucciones para retomar

1. Confirmar rama y estado Git sin descartar cambios.
2. Revisar diff completo y evidencia de tests.
3. Mantener fuera de alcance REQ-002 y proveedores externos.
4. No ejecutar commit, push, PR, merge, rebase, reset, clean, stash o deploy sin
   autorizacion expresa.

---

# Registro historico superado: especificacion PRO y Facturacion MVP

Timestamp: 2026-09-03T21:55:15-03:00
Estado: COMPLETED
Resultado del ciclo: COMPLETED
Alcance: especificacion funcional documental de activacion y vigencia PRO y de
Facturacion MANDOBRA PRO MVP

## Identificacion

- Dispositivo/origen: Codex Desktop local.
- Agente o sesion de origen: Codex / Documentation Engineer Senior.
- Rama actual: `docs/spec-pro-facturacion-mvp` (estado provisto y verificado
  antes de iniciar esta tarea; no se repitio el preflight por instruccion).
- Commit base y ultimo commit informado: `e0eed2`.
- Cambios sin commit: SI; nueve archivos Markdown bajo `docs/` enumerados en
  este handoff.
- Rama subida a GitHub: NO; no se ejecuto push ni se verificaron remotos por
  restriccion expresa.
- Destino previsto: `02 - Implementacion y Refinacion`.

## Objetivo de la sesion

Formalizar como requisitos separados y aprobados la activacion y vigencia de
MANDOBRA PRO y Facturacion MANDOBRA MVP como beneficio opcional de PRO, sin
implementar codigo, proveedores, integraciones, migraciones, tests ni cambios
visuales.

## Trabajo completado

- Se creo [REQ-001](../REQUISITOS/REQ-001-activacion-y-vigencia-pro.md) con
  catalogo `FREE`, `PRO`, `ENTERPRISE`, elegibilidad profesional y reglas para
  PRO transaccional y por suscripcion.
- Se creo [REQ-002](../REQUISITOS/REQ-002-facturacion-pro-mvp.md) con el alcance
  fiscal MVP de persona humana, monotributo activo y Factura C.
- Se separaron expresamente Facturacion, entitlement PRO y configuracion ARCA.
- Se registro el contraste con el codigo actual: activacion inmediata/manual,
  lector de puntos legacy, falta de control de vencimiento y ausencia de PSP,
  ARCA, facturacion e IA productiva.
- Se actualizaron Master Spec, Roadmap, Backlog, Changelog e indices con
  implementacion marcada como `PENDIENTE`.
- Se conservaron preguntas abiertas separadas de las decisiones aprobadas.

## Trabajo parcialmente completado

Ninguno dentro del alcance documental autorizado.

## Pendientes

- Porcentaje de comision; precio, periodicidad, beneficios y limites completos
  de PRO; renovacion, cancelacion, mora, contracargos y periodo de gracia.
- Politica de migracion de accesos PRO actuales y concesiones administrativas.
- Seleccion y validacion del PSP y estrategia del entitlement.
- Integracion directa con ARCA o proveedor; custodia y rotacion de
  certificados; validacion de monotributo; datos del receptor; retencion,
  almacenamiento, entrega, limites, correcciones, anulaciones, notas de credito
  y contingencia.
- Proveedor y modelo de IA, costos y revisiones legal, fiscal, contable y de
  seguridad.
- Modelo futuro de `ENTERPRISE`; no se autorizo crear el actor `EMPRESA`.
- Implementacion y pruebas de ambos requisitos, sujetas a nueva autorizacion.

## Bloqueantes

- BLOQUEANTE para implementar PRO transaccional: seleccionar y validar PSP y
  cerrar politicas comerciales y de contracargos.
- BLOQUEANTE para implementar Facturacion: resolver integracion fiscal,
  custodia de credenciales, politicas de datos y revisiones legal, fiscal,
  contable y de seguridad.
- No existen bloqueantes para el cierre de esta especificacion documental.

## Archivos creados

- `docs/REQUISITOS/REQ-001-activacion-y-vigencia-pro.md`: requisito aprobado;
  implementacion pendiente, sin commit.
- `docs/REQUISITOS/REQ-002-facturacion-pro-mvp.md`: requisito aprobado;
  implementacion pendiente, sin commit.

## Archivos modificados

- `docs/REQUISITOS/README.md`: indice de requisitos aprobados, sin commit.
- `docs/REQUISITOS/MASTER_SPEC.md`: resumen, actores, estado actual, capacidades
  aprobadas y pendientes, sin commit.
- `docs/ROADMAP.md`: especificaciones aprobadas e implementaciones pendientes,
  sin commit.
- `docs/BACKLOG.md`: pendientes consolidados y enlazados, sin commit.
- `docs/INDEX.md`: enlaces a REQ-001 y REQ-002, sin commit.
- `docs/CHANGELOG.md`: cambios exclusivamente documentales, sin commit.
- `docs/HANDOFFS/ACTIVE_HANDOFF.md`: reemplazo del handoff activo para este
  ciclo, sin commit.

## Migraciones relacionadas

Ninguna. No se crearon ni ejecutaron migraciones.

## Tests y validaciones ejecutados

- Inspeccion estatica dirigida de `Subscription`, `subscription_service`,
  verificacion, decoradores, ruta de upgrade, administracion, Planes y puntos
  legacy: EJECUTADA; confirma el contexto registrado en los requisitos.
- Verificacion de las 16 secciones obligatorias en REQ-001 y REQ-002:
  EJECUTADA; resultado `HEADINGS_OK` para ambos documentos.
- Comprobacion de enlaces Markdown relativos en los documentos creados o
  actualizados: EJECUTADA; resultado `RELATIVE_LINKS_OK`.
- Comprobacion de identificadores: EJECUTADA; `REQ-001` y `REQ-002` son los
  primeros identificadores de requisito y no reutilizan un `REQ-NNN` previo.
- `git status --short`: EJECUTADO; cambios exclusivamente Markdown bajo
  `docs/`.
- `git diff --check`: EJECUTADO; sin errores, con advertencias informativas de
  conversion futura LF a CRLF para archivos rastreados.
- `git diff --stat`: EJECUTADO; revisado antes del cierre del handoff.
- `git diff -- docs`: EJECUTADO; revisado antes del cierre del handoff.

## Tests y validaciones no ejecutados

- Tests de aplicacion: NO EJECUTADOS - no aplican al alcance documental.
- Aplicacion: NO EJECUTADA; no aplica al alcance documental.
- Migraciones: NO EJECUTADAS; no existen cambios de esquema.
- Integraciones PSP, ARCA e IA: NO EJECUTADAS; no estan implementadas ni fueron
  autorizadas.

## Resultados de tests

- Aprobados: validaciones documentales de estructura, enlaces, alcance y diff.
- Fallidos: ninguno.
- Omitidos: suite de aplicacion, por no aplicar al alcance documental.
- Resultado general: PASS documental; implementacion NO EJECUTADA.

## Errores conocidos

- Ninguno durante la edicion documental.
- CONTRADICCION vigente y no corregida en codigo: la UI publica conserva
  `Plus`, mientras el catalogo aprobado es `FREE`, `PRO`, `ENTERPRISE`.
- CONTRADICCION vigente y no corregida en codigo: el upgrade usa puntos legacy
  o verificacion, mientras REQ-001 exige cuenta activa, verificacion aprobada y
  una fuente de entitlement vigente.

## Troubleshooting relacionado

Ninguno.

## Decisiones tomadas

- APROBADO: `FREE`, `PRO`, `ENTERPRISE` es el catalogo canonico; `Plus` queda
  fuera.
- APROBADO: la primera implementacion PRO corresponde a profesionales con
  cuenta activa y verificacion aprobada; puntos legacy no conceden PRO.
- APROBADO: modalidad transaccional y suscripcion mantienen el mismo
  entitlement `PRO`.
- APROBADO: Facturacion es un modulo separado, opcional y exclusivo de PRO
  vigente; no activa ni extiende PRO.
- APROBADO: el alcance fiscal inicial es persona humana, monotributo activo y
  Factura C, con borrador asistido y confirmacion humana obligatoria.
- PENDIENTE: proveedor PSP, integracion fiscal, custodia de secretos, proveedor
  de IA, modelos, precios y porcentajes.
- PENDIENTE: crear ADR cuando se aprueben decisiones arquitectonicas con impacto
  transversal o costosas de revertir.

## Documentacion actualizada

- [REQ-001](../REQUISITOS/REQ-001-activacion-y-vigencia-pro.md).
- [REQ-002](../REQUISITOS/REQ-002-facturacion-pro-mvp.md).
- [Indice de requisitos](../REQUISITOS/README.md).
- [Master Spec](../REQUISITOS/MASTER_SPEC.md).
- [Roadmap](../ROADMAP.md).
- [Backlog](../BACKLOG.md).
- [Indice documental](../INDEX.md).
- [Changelog](../CHANGELOG.md).
- Este handoff activo.

## Riesgos

- Implementar antes de cerrar politicas abiertas puede producir accesos,
  cobros o efectos fiscales incorrectos.
- Webhooks duplicados o fuera de orden pueden degradar vigencia e idempotencia.
- Una custodia inadecuada puede exponer secretos y datos fiscales.
- IA sin limites estrictos puede inventar datos o aparentar asesoramiento
  fiscal.
- El codigo legacy puede seguir concediendo PRO por puntos hasta que una
  implementacion autorizada aplique REQ-001.

## Proximo paso recomendado

Iniciar `02 - Implementacion y Refinacion` con una revision tecnica de REQ-001
y REQ-002 que produzca un plan de implementacion por fases y ADR pendientes,
sin escribir codigo hasta cerrar las decisiones bloqueantes y obtener
autorizacion explicita.

## Handoff exacto para 02 - Implementacion y Refinacion

1. Verificar estado Git, rama y ultimo commit antes de actuar.
2. Confirmar que los nueve cambios Markdown sin commit enumerados siguen
   presentes e intactos.
3. Leer completos REQ-001, REQ-002, Master Spec y este handoff.
4. Contrastar nuevamente el plan con el codigo y migraciones vigentes si cambia
   el commit base.
5. Separar la implementacion de entitlement PRO del modulo de Facturacion.
6. Proponer fases, invariantes, migraciones, pruebas PostgreSQL, controles de
   seguridad y ADR, sin seleccionar proveedores no aprobados.
7. Resolver o elevar las preguntas bloqueantes antes de implementar.
8. No modificar codigo, migraciones o UI sin autorizacion explicita para la
   fase de implementacion.

## Acciones que NO deben realizarse

- No asumir que REQ-001 o REQ-002 ya estan implementados.
- No elegir Mercado Pago, otro PSP, integracion ARCA ni proveedor de IA sin
  evaluacion y aprobacion.
- No almacenar claves fiscales en texto plano.
- No usar puntos legacy como elegibilidad PRO.
- No crear el actor `EMPRESA` por la sola existencia conceptual de
  `ENTERPRISE`.
- No ejecutar commit, push, PR, merge, rebase, reset, clean, stash ni cambios
  de rama sin autorizacion expresa.
- No mezclar cambios ajenos o fuera de `docs/` con este ciclo documental.

## Criterio de cierre

Este ciclo queda `COMPLETED` cuando los dos requisitos y su trazabilidad
documental estan presentes, los cambios permanecen exclusivamente bajo
`docs/`, las validaciones documentales no informan errores y se entrega este
handoff. El cierre no requiere ni autoriza commit, push, PR, merge o
implementacion.

---

# Actualizacion posterior al merge de PRO y Facturacion MVP

Timestamp: 2026-09-04T08:27:58-03:00
Estado: COMPLETED
Estado vigente: MERGED
Resultado: COMPLETED
Documento: `docs/HANDOFFS/ACTIVE_HANDOFF.md`
Motivo: cerrar la trazabilidad posterior a la integracion del ciclo documental
de PRO y Facturacion MVP.
Evidencia: commit documental, Pull Request y merge commit verificados; `develop`
local y `origin/develop` sincronizados en `e26e598` desde la laptop.
Responsable: Codex / Documentation Engineer Senior
Dispositivo: laptop
Rama de esta actualizacion: `docs/close-pro-facturacion-handoff`
Commit base: `e26e5989e259ad142dfe994817566c3b6d5ff8d1`

## Registro superado

El registro original de `2026-09-03T21:55:15-03:00` se conserva integro porque
describe correctamente el estado previo al commit. Su estado operativo queda
SUPERSEDED por esta actualizacion posterior: los nueve archivos Markdown que
entonces estaban sin commit ya fueron versionados e integrados en `develop`.

## Integracion verificada

- Commit documental: `9f3b20899704e2667411c45fde3b529909bd53ca`.
- Pull Request: `#3`.
- URL: `https://github.com/cristhian-star/TRAX-PLATFORM/pull/3`.
- Rama origen: `docs/spec-pro-facturacion-mvp`.
- Rama destino: `develop`.
- Merge commit: `e26e5989e259ad142dfe994817566c3b6d5ff8d1`.
- Merge realizado: `2026-09-04T00:52:14-03:00`.
- Cambios integrados: nueve archivos Markdown bajo `docs/`.
- Sincronizacion posterior: verificada en la laptop.
- `develop` local y `origin/develop`: sincronizados en `e26e598`.
- Arbol de trabajo previo a esta actualizacion: limpio.

## Alcance y validacion

- Esta actualizacion modifica exclusivamente
  `docs/HANDOFFS/ACTIVE_HANDOFF.md`.
- No cambia decisiones funcionales ni declara implementados REQ-001 o REQ-002.
- Tests de aplicacion: NO EJECUTADOS - no aplican al alcance documental.
- No se ejecutaron migraciones ni la aplicacion.
- No se realizo commit, push, Pull Request ni merge como parte de esta
  actualizacion.

## Proximo paso

Transferir el analisis a `02 - Implementacion y Refinacion` para preparar el
plan tecnico por fases de REQ-001 y REQ-002. Esta transferencia no autoriza
todavia implementacion, cambios de codigo, migraciones, seleccion de
proveedores ni decisiones funcionales adicionales.

## Restricciones vigentes

- No asumir que PRO o Facturacion MVP ya estan implementados.
- No iniciar implementacion sin autorizacion expresa.
- No seleccionar PSP, integracion fiscal o proveedor de IA sin evaluacion y
  aprobacion.
- No realizar commit, push, PR o merge durante este cierre local.
