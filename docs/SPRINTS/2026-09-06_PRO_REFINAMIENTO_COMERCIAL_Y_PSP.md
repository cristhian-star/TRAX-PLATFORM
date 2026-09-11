# PRO - Refinamiento comercial, PSP y plan de tres sprints

Timestamp de actualizacion: 2026-09-07T21:31:53-03:00
Timestamp de cierre documental: 2026-09-07T21:54:36-03:00
Estado: CERRADO_DOCUMENTALMENTE_INTEGRACION_GIT_PENDIENTE
Responsable de producto: Cristian Sánchez  
Agente: 01 - Documentation Engineer  
Rama observada: `develop`
Commit observado: `1d22f87adc358eae20121ea727142b0276cf337e`

## Correccion focal P2 de persistencia

Timestamp: 2026-09-11T14:41:40-03:00
Estado: PAYMENT_PERSISTENCE_FOUNDATION_CORREGIDA_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Rama: `feature/payment-persistence-foundation`
Commit base: `c78c5176cf3c43cdbab673454fc6a625b1b3c0fa`

La revision independiente `REQUIERE_CORRECCIONES` detecto que una violacion FK
durante `register_or_get_attempt()` podia reinterpretarse como replay y terminar
en `NoResultFound`. La correccion limita la recuperacion a la unicidad
idempotente comprobada mediante SQLSTATE `23505` y nombre estructurado de la
constraint. FK, checks y errores no identificables conservan su
`IntegrityError` original.

La regresion PostgreSQL confirma SQLSTATE `23503`, constraint
`fk_payment_attempts_obligation`, cero escrituras parciales y recuperacion de
la sesion tras rollback. Focal: 55/55; gate PostgreSQL: 7/7; suite completa:
359 ejecutadas, 354 aprobadas, 5 omisiones historicas, 0 fallos y 0 errores;
`compileall` y head unico `20260910_01`: aprobados. La base descartable
`trax_payment_persistence_test_p2_20260911` fue limpiada y eliminada.

No cambia el esquema ni acredita Mercado Pago, webhooks, produccion o el diseño
general 2.0. El paquete permanece pendiente de retest independiente.

## Incremento local - persistencia neutral minima de pagos

Timestamp: 2026-09-11T14:00:30-03:00
Estado: PAYMENT_PERSISTENCE_FOUNDATION_IMPLEMENTADA_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Rama: `feature/payment-persistence-foundation`
Commit base: `c78c5176cf3c43cdbab673454fc6a625b1b3c0fa`
Migracion: `20260910_01`, descendiente de `20260904_01`

Se agrego una base minima de dos tablas para persistir obligaciones monetarias
e intentos/resultados ya obtenidos por el orquestador. El servicio no llama al
PSP y deja `commit()`/rollback bajo control del llamador. Unicidad, FK, importe
positivo, estados y coherencia se protegen en el esquema; la conciliacion usa
lock de fila solamente para serializar cambios concurrentes del mismo intento.

Focal portable y regresiones PSP/orquestador: 55/55. Gate PostgreSQL real: 6/6
en `trax_payment_persistence_test_20260911a`, con carreras idempotentes y
conflictivas, visibilidad transaccional, rollback, recuperacion y ciclo
upgrade/downgrade/upgrade. La base quedo sin tablas y fue eliminada. Suite
completa: 359 ejecutadas, 354 aprobadas, 5 omisiones historicas, 0 fallos y 0
errores. `compileall` y head unico `20260910_01`: aprobados.

PR #9 fue integrado mediante
`c78c5176cf3c43cdbab673454fc6a625b1b3c0fa`. No se toco `trax_db` y no se
implementaron persistencia de coordinacion externa, Mercado Pago, checkout,
webhooks, creditos, comisiones, PRO, ARCA ni Enterprise. El diseño general 2.0
continua `PROPUESTO_NO_APROBADO`.

## Alcance y continuidad historica

Esta secuencia no reinicia la numeracion historica ni modifica el cierre de
Sprint 7. “Sprint 1”, “Sprint 2” y “Sprint 3” son etiquetas del ciclo PRO
comercial iniciado el 2026-09-06.

La PRO Entitlement Foundation esta integrada mediante PR #5 y merge `1548935`.
El resultado post-merge informado es `APROBADO_POST_MERGE`: 294 tests, 289
aprobados, 0 fallos y 5 omisiones justificadas; Alembic `20260904_01`, sin
P0/P1 y con `trax_db` preservada. Esta evidencia no acredita PSP, creditos,
pagos, suscripciones recurrentes ni facturacion.

## Sprint 1 - Especificacion y viabilidad

Objetivo: consolidar cobros, creditos, PRO y facturacion; preparar los
expedientes juridico/contable y PSP; delimitar evaluacion fiscal.

Entregables documentales:

- REQ-001 conciliado con creditos, periodos y transiciones aprobadas.
- REQ-002 separado de cobro y actualizado para todos los periodos PRO.
- Master Spec, Roadmap, Backlog, Changelog, indices y handoff consistentes.
- [Consultas Mercado Pago](../CONSULTAS/MERCADO_PAGO_v0_1.md), todas pendientes
  y no enviadas.
- [Base de revision juridica](../LEGAL/BASE_REVISION_JURIDICA_v0_2.md), sin
  valor de dictamen.
- Evaluacion fiscal delimitada; implementacion fiscal en incremento separado.

Cierre documental: diff revisado, enlaces validos y pendientes con responsable.
La viabilidad externa puede continuar pendiente y bloquear solo incrementos
dependientes. Este documento no autoriza implementacion.

### Integracion y revisiones recuperadas

- Git local confirma que PR #7 integro en `develop` el commit documental
  `817fb4f3888a44984b951badc655eceeec2b9df8` mediante el merge
  `1d22f87adc358eae20121ea727142b0276cf337e`, fechado
  `2026-09-06T20:11:47-03:00`.
- Antes del commit se informo en la conversacion de revision focalizada el
  resultado `APROBADO_PARA_COMMIT` sobre los cuatro P1 y dos P2 corregidos.
  Es evidencia conversacional; no equivale a una review nativa de GitHub.
- El informe del Agente 02, emitido el `2026-09-07T20:59:03-03:00`, registro
  cero reviews nativas en PR #7 y dictamino
  `EVALUACION_TECNICA_COMPLETADA_CON_CIERRE_DOCUMENTAL_PENDIENTE`.
- Ninguna regla vigente exige una review nativa para reconocer el merge. La
  revision del presente diff sigue pendiente y el Sprint 1 no se marca cerrado.

### Pendientes y responsables propuestos

Las siguientes son propuestas de responsabilidad, no asignaciones aceptadas:

| Capacidad | Pendiente | Bloqueo especifico | Responsable propuesto |
|---|---|---|---|
| Onboarding y checkout PSP | Resolver MP-08 a MP-10, MP-12, MP-13 y MP-16 | Bloquea integracion real, enlaces/QR y confirmacion autoritativa; no bloquea el contrato conceptual | Responsable tecnico MANDOBRA para consulta; Mercado Pago para respuesta |
| Reservas y pagos mixtos | Definir plazo, vencimiento durante reserva, aprobaciones tardias, reintentos y reversas; resolver MP-04 a MP-06, MP-09, MP-10 y MP-15 | Bloquea implementacion financiera y pruebas transaccionales reales | Producto + arquitectura; revision juridica/contable |
| Suscripcion y renovacion | Resolver MP-01 a MP-07, MP-10, MP-11 y MP-14 a MP-16; definir consentimiento y cobros en curso | Bloquea recurrencia real y sincronizacion del switch | Producto + responsable tecnico; revision juridica |
| Creditos y comision | Definir precio, porcentaje/base, conversion, moneda, redondeo, impuestos y reversas | Bloquea ledger definitivo, cobro y acreditacion | Cristian Sánchez/producto + contabilidad |
| Facturacion opcional | Comparar ARCA directo/proveedor y completar revision fiscal, juridica, contable y de seguridad | Bloquea solo el incremento fiscal; no debe acoplarse al cobro o contratacion | Producto + responsable fiscal/contable por designar |

No se contacto a Mercado Pago ni se obtuvo dictamen juridico o contable. Las
preguntas MP-01 a MP-16 y la base de revision continuan abiertas.

### Correcciones propuestas al diseño 2.0

Estado: `PROPUESTO_NO_APROBADO`. Este bloque corrige la propuesta del Agente 02;
no modifica las reglas comerciales aprobadas, no decide modelos ni autoriza
implementacion.

1. **Pago mixto con diferencia monetaria.** Cuando los creditos cubren solo una
   parte, la reserva no se consume hasta confirmar autoritativamente el pago
   completo de la diferencia. Incertidumbre, rechazo no definitivo o evento
   tardio mantienen el flujo sujeto a conciliacion conforme REQ-001.
2. **Cobertura total con creditos.** Si la diferencia monetaria es cero, no hay
   cobro PSP que pueda confirmar el pago. El diseño debe definir una
   confirmacion interna atomica que cierre una unica obligacion, consuma los
   importes reservados y aplique el efecto PRO una sola vez. Validar una tarjeta
   vinculada es un requisito comercial separado y no confirma un cobro.
3. **Unicidad e importes.** La proteccion contra doble financiacion debe operar
   por obligacion/periodo y por importe aplicado. Un lote puede consumirse
   parcialmente en operaciones distintas; cada operacion preserva la traza del
   importe y el saldo remanente conserva el vencimiento original. No se propone
   unicidad global del lote.
4. **Estimacion 25-43 horas.** El rango informado no debe tratarse como trabajo
   restante ni total hasta que el Agente 02 aclare su base. Ya estan cubiertos
   documentalmente REQ-001/REQ-002, expedientes PSP y juridico, trazabilidad,
   mapa de brechas y propuesta conceptual; no se les imputan horas retroactivas.
   Deben identificarse los entregables incluidos, los ya cubiertos y los
   restantes sin crear una estimacion nueva.

Estas correcciones requieren revision de arquitectura posterior. No se aprueba
la arquitectura 2.0, un ADR, un SDK, un esquema de datos ni una migracion.

### Matriz de cierre de Sprint 1

| Criterio | Evidencia actual | Estado para cierre |
|---|---|---|
| Paquete documental integrado | PR #7; commits `817fb4f` y `1d22f87` | CUMPLIDO |
| Correcciones P1/P2 revisadas | `APROBADO_PARA_COMMIT` informado en conversacion previa; sin review nativa | CUMPLIDO_CON_EVIDENCIA_CONVERSACIONAL |
| REQ, Master Spec, planificacion y expedientes coherentes | 15 Markdown integrados por PR #7 | CUMPLIDO; sujeto al control del diff actual |
| Informe del Agente 02 recuperado | `REVISION_FOCAL_COMPLETADA / DISEÑO_2_0_PROPUESTO` | CUMPLIDO; propuesta no aprobada |
| Pendientes identificados | Matriz anterior y MP-01 a MP-16 | CUMPLIDO; responsables solo propuestos |
| Viabilidad Mercado Pago | Expediente no enviado y sin respuestas | PENDIENTE; bloquea capacidades PSP dependientes |
| Revision juridica/contable | Base preparada, sin dictamen | PENDIENTE; bloqueo selectivo segun capacidad |
| Estimacion 25-43 h trazable | Falta definir total/restante y entregables incluidos | PENDIENTE_DE_ACLARACION |
| Revision del diff de cierre | Agente 02, `2026-09-07T21:41:54-03:00`; sin hallazgos y `APROBADO_PARA_COMMIT` | CUMPLIDO |

Resultado provisional: `LISTO_PARA_REVISION_DE_DIFF`. El Sprint 1 permanece
abierto hasta esa revision; no queda automaticamente `APROBADO` ni `CERRADO`.

### Cierre documental

La revision independiente del Agente 02 del
`2026-09-07T21:41:54-03:00` concluyo sin hallazgos, declaro el diff
`APROBADO_PARA_COMMIT` y considero satisfechos los criterios documentales de
cierre. Con esa evidencia, Sprint 1 queda `CERRADO_DOCUMENTALMENTE`, con la
integracion Git de este registro todavia pendiente.

La conclusion no resuelve ni elimina los pendientes selectivos de Mercado Pago,
revision juridica/contable y aclaracion del rango de 25-43 horas. El diseño 2.0
permanece `PROPUESTO_NO_APROBADO` y su implementacion no esta autorizada. La
ausencia de reviews nativas de GitHub continua atribuida al informe disponible,
no a una verificacion propia de esta sesion.

### Incremento local posterior: simulador PSP en memoria

Timestamp: 2026-09-07T22:40:12-03:00
Estado: SIMULADOR_PSP_EN_MEMORIA_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: 02 - Implementacion - Builder
Rama y commit base: `develop` en
`1e85c6e592f970b2640a1e71d5b9a7019f8b3383`

Se implemento exclusivamente un simulador PSP generico y determinista para
pruebas y desarrollo futuro. Mantiene almacenamiento por instancia, importes
exactos `Decimal`, idempotencia, resultados configurables y separacion entre
incertidumbre de llamada y estado consultable. No se integra con la aplicacion
operativa ni aprueba el diseño general 2.0.

Las 21 pruebas focales pasaron. La suite completa no pudo validarse con el
runtime de Codex Desktop: de 54 casos descubiertos, 21 pasaron y 33 terminaron
en error de importacion por dependencias del proyecto ausentes. No se instalaron
dependencias ni se uso Docker. `compileall`, enlaces relativos y
`git diff --check` pasaron.

La evidencia no acredita persistencia, atomicidad o concurrencia PostgreSQL,
autenticidad, entrega u orden de webhooks, ni viabilidad tecnica, contractual o
comercial de Mercado Pago. No selecciona proveedor ni arquitectura productiva.
El diseño 2.0 permanece `PROPUESTO_NO_APROBADO`.

Revalidacion del `2026-09-08T21:46:39-03:00`: el trabajo previo se inspecciono
y conservo sin cambios funcionales. Las 21 pruebas focales volvieron a pasar y
`compileall` aprobo. La suite completa repitio 54 pruebas descubiertas, 21
aprobadas, 0 fallos de asercion, 33 errores de importacion y 0 omitidas por las
dependencias ausentes del runtime. El estado maximo permanece
`SIMULADOR_PSP_EN_MEMORIA_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION`.

Revision independiente del `2026-09-08T22:28:13-03:00`, registrada el
`2026-09-08T22:37:42-03:00` por Codex sobre `develop` en la base
`1e85c6e592f970b2640a1e71d5b9a7019f8b3383`: `APROBADO_PARA_COMMIT`, sin
hallazgos P0-P3. La focal aprobo 21/21 y la suite completa en Docker aprobo
310/315, con 5 omisiones historicas, 0 fallos y 0 errores. `compileall`, enlaces
relativos y `git diff --check` aprobaron. El nuevo estado previo a integracion
es `SIMULADOR_PSP_EN_MEMORIA_APROBADO_PARA_COMMIT`.

Esta aprobacion no acredita persistencia, concurrencia o atomicidad PostgreSQL,
autenticidad de webhooks ni viabilidad de Mercado Pago, y no implementa o
valida ARCA. El simulador no esta conectado a flujos productivos; el diseño
general 2.0 continua `PROPUESTO_NO_APROBADO`, con Mercado Pago y revision
juridica/contable pendientes. Integracion Git: pendiente en este registro.

Integracion confirmada el `2026-09-08T22:40:33-03:00` por Codex: el commit
`50babd206369d47d68765e0dbf0fd3f2f42c21d0`,
`feat: add deterministic in-memory PSP simulator`, fue publicado mediante push
normal a `origin/develop`; el hash remoto observado coincide. Estado:
`SIMULADOR_PSP_EN_MEMORIA_INTEGRADO`.

Integrado refiere unicamente al simulador aislado y sus pruebas. No esta
conectado a flujos productivos y no acredita persistencia, concurrencia o
atomicidad PostgreSQL, autenticidad de webhooks ni viabilidad PSP. Mercado
Pago, ARCA y revision juridica/contable continuan pendientes; el diseño general
2.0 permanece `PROPUESTO_NO_APROBADO`.

### Incremento 2.0-B: contrato neutral PSP

#### Interfaz interna de desarrollo para simulacion visual

Timestamp: 2026-09-10T21:46:04-03:00
Estado: `PAYMENT_ORCHESTRATION_AND_SIMULATOR_UI_APROBADOS_PARA_COMMIT_Y_PR`
Agente: Codex - implementador tecnico y frontend local
Dispositivo: laptop / Codex Desktop local
Rama y commit base: `feature/payment-orchestration-in-memory` sobre
`a4951a27f0f0bef5fa834ad25159abfc875ec59e`
Revision independiente: `APROBADO_PARA_SEGUNDO_COMMIT_Y_PR` del
`2026-09-10T22:02:38-03:00`, sin hallazgos P0-P3.

Se implemento `/dev/qa/payments/simulator` como pantalla server-rendered del
blueprint interno. Solo se registra en development/testing, requiere
`ENABLE_DEV_QA_PANEL` y responde 404 cuando no esta habilitada o cuando la
aplicacion usa configuracion de produccion.

Cada envio compone una instancia nueva del controlador de escenarios,
simulador y orquestador. La interfaz permite observar aprobacion, rechazo,
pendiente financiero e incertidumbre como conciliacion requerida, conserva
valores ante validacion fallida y no usa `float`, historial, estado global,
polling o retries. Usa el Design System v2 y no agrega JavaScript.

La focal de interfaz y orquestacion aprobo 29/29 y la del contrato/simulador
24/24. La suite completa ejecuto 347 pruebas: 342 aprobadas, 5 omisiones
historicas, 0 fallos y 0 errores. `compileall`, HTML, enlaces y
`git diff --check` aprobaron. QA visual aprobada en claro/oscuro,
movil/desktop y teclado. PostgreSQL no aplica.

Esta herramienta no es checkout, no mueve dinero y no acredita integracion o
viabilidad PSP. No agrega persistencia, modelos, migraciones, HTTP, SDK, OAuth,
webhooks, creditos, reservas, comisiones, suscripciones, PRO, Mercado Pago o
ARCA. El diseño general 2.0 permanece `PROPUESTO_NO_APROBADO`; Mercado Pago y
la revision juridica/contable continuan pendientes.

#### Incremento local posterior: orquestacion neutral de pagos en memoria

Timestamp: 2026-09-10T21:23:10-03:00
Estado: `PAYMENT_ORCHESTRATION_IN_MEMORY_IMPLEMENTADA_LOCALMENTE_PENDIENTE_DE_REVISION`
Agente: Codex - implementador tecnico local
Dispositivo: laptop / Codex Desktop local
Rama y commit base: `feature/payment-orchestration-in-memory` sobre
`e7ec86f217ebbbd836f7434092041e6abefbbe4a`

Se implemento una orquestacion aislada y en memoria que recibe una obligacion
monetaria inmutable, depende unicamente de `PSPAdapter` y diferencia pago
aprobado, rechazado, pendiente financiero e incertidumbre que requiere
conciliacion. El resultado conserva referencia, importe exacto, moneda, clave
idempotente, ID opcional, estado financiero conocido e indicador de
conciliacion.

La conciliacion es siempre explicita: con ID consulta `get_attempt`; sin ID
repite una unica vez la creacion con los mismos datos y clave. Una nueva
incertidumbre conserva `RECONCILIATION_REQUIRED`. No existe almacenamiento
propio, retries automaticos, esperas, temporizadores, aleatoriedad o IDs
inventados. Los importes usan `Decimal`, deben ser positivos y finitos y no se
cuantizan ni redondean.

La focal nueva aprobo 19/19 y la focal del contrato/simulador 24/24. La suite
completa Docker ejecuto 337 pruebas: 332 aprobadas, 5 omitidas, 0 fallos y 0
errores. `compileall` aprobo. PostgreSQL no se ejecuto porque no aplica.

No se incorporaron persistencia, SQLAlchemy, modelos, migraciones, HTTP, SDK,
OAuth, webhooks, rutas, UI, creditos, reservas, comisiones, suscripciones, PRO,
Mercado Pago o ARCA. La evidencia no acredita persistencia, concurrencia o
atomicidad PostgreSQL, autenticidad u orden de webhooks ni viabilidad PSP. El
diseño general 2.0 permanece `PROPUESTO_NO_APROBADO`; Mercado Pago y la
revision juridica/contable continuan pendientes.

Validacion local post-merge registrada el `2026-09-10T13:42:55-03:00` por
Codex - implementador tecnico local, sobre `develop`. Estado:
`PSP_ADAPTER_CONTRACT_INTEGRADO_POST_MERGE_VALIDADO_LOCALMENTE_PENDIENTE_DE_REVISION_DOCUMENTAL`.

Se confirmo la integracion de PR #8 en el merge
`f9c0e394af413cfcb0c1aa8142a85af16ad3729b`, con base previa
`2e7de49dfde6c20bc798089139ea235534ea0a75` y segundo padre correctivo
`8f709e64149d7dfbdeb9c2e1a319f7134ae6f0f4`. `develop` y
`origin/develop` coincidieron sin divergencia.

El alcance integrado comprende el contrato PSP neutral, intento inmutable,
estados y errores neutrales diferenciados, ID opcional ante incertidumbre,
simulador determinista en memoria, controlador FIFO, replay idempotente y
recuperacion mediante consulta. La focal aprobo 24/24. La suite completa en
Docker ejecuto 318 pruebas: 313 aprobadas, 5 omitidas, 0 fallos y 0 errores.
`compileall`, enlaces relativos y `git diff --check` aprobaron.

PostgreSQL no se ejecuto porque no aplica. Esta evidencia no acredita
persistencia, concurrencia o atomicidad PostgreSQL, autenticidad u orden de
webhooks ni viabilidad tecnica, contractual o comercial de un PSP. No se
integraron Mercado Pago, ARCA, SDK, HTTP o flujos productivos. El diseño 2.0
permanece `PROPUESTO_NO_APROBADO`; Mercado Pago y la revision
juridica/contable continuan pendientes.

Correccion P2 preparada el `2026-09-09T20:42:09-03:00` por Codex en
`feature/psp-adapter-contract`, PR #8, sobre el commit observado
`64eed3fdbf16ff55f7994b246a87b514a41a31bb`. Estado:
`PSP_ADAPTER_CONTRACT_P2_CORREGIDO_PR_ACTUALIZADO_PENDIENTE_DE_RETEST`.

El hallazgo consistia en que una cola vacia fallaba despues de invocar la
fabrica de IDs y el reloj, rompiendo el determinismo de dependencias con estado.
La correccion inspecciona el proximo escenario sin consumirlo, valida ID y reloj
y confirma su consumo inmediatamente antes de almacenar. ID duplicado, reloj
invalido, validacion, replay, conflicto y consulta no consumen escenarios; una
creacion valida consume exactamente uno. La focal aprobo 24/24 y la suite
completa Docker ejecuto 318/318: 313 aprobadas, 5 omisiones historicas,
0 fallos y 0 errores. `compileall`, enlaces relativos y `git diff --check`
fueron aprobados.

PostgreSQL no aplica. No se incorporan persistencia, concurrencia, locks,
migraciones ni integracion productiva. PR #8 permanece abierto, no aprobado
para merge y pendiente de retest independiente.

Timestamp: 2026-09-08T23:01:15-03:00
Estado: PSP_ADAPTER_CONTRACT_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: 02 - Implementacion - Builder
Rama: `feature/psp-adapter-contract`
Commit base: `2e7de49dfde6c20bc798089139ea235534ea0a75`

Se separo el contrato que MANDOBRA usaria con un PSP de la configuracion de
escenarios exclusiva del simulador. El contrato neutral permite crear y
consultar intentos sin aceptar `outcome`, `scenario` u otras instrucciones
artificiales. Un controlador FIFO local al simulador programa estados e
incertidumbre de forma determinista sin introducir aleatoriedad o esperas.

La focal aprobo 17/17. La suite completa en Docker aprobo 306/311, con 5
omisiones historicas, 0 fallos y 0 errores. `compileall`, enlaces relativos y
`git diff --check` aprobaron. Los gates PostgreSQL no se ejecutaron porque este
incremento permanece exclusivamente en memoria.

No se implementaron persistencia, modelos financieros, HTTP, SDK, webhooks,
Mercado Pago, ARCA ni integracion productiva. La evidencia no acredita
concurrencia o atomicidad PostgreSQL, autenticidad de webhooks ni viabilidad
PSP. El diseño general 2.0 permanece `PROPUESTO_NO_APROBADO` y la revision
juridica/contable continua pendiente.

Correccion posterior a revision independiente:

Timestamp: 2026-09-09T20:01:57-03:00
Estado: PSP_ADAPTER_CONTRACT_CORREGIDO_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: 02 - Implementacion - Builder
Rama y base: `feature/psp-adapter-contract` en
`2e7de49dfde6c20bc798089139ea235534ea0a75`
Revision: `REQUIERE_CORRECCIONES` del `2026-09-09T19:53:36-03:00`

El P1 contractual quedo corregido: una respuesta incierta puede omitir el ID
externo y representarlo con `None`, o conservar exactamente una cadena no vacia
cuando el adaptador la conoce. El simulador adjunta el identificador porque crea
internamente el intento; un proveedor real puede no entregarlo y la
conciliacion debe poder continuar con la clave idempotente conocida.

El P3 quedo cubierto mediante inspeccion AST de imports en ambos modulos,
identidad de reexportaciones, comportamiento atomico y aislado de `enqueue`, y
diferenciacion observable de errores neutrales. Focal: 22/22. Suite completa
Docker: 311/316, con 5 omisiones historicas, 0 fallos y 0 errores. `compileall`,
enlaces relativos y `git diff --check`: aprobados.

No se incorporaron persistencia, PostgreSQL, HTTP, SDK, webhooks, Mercado Pago,
ARCA ni integracion productiva. El diseño 2.0 continua
`PROPUESTO_NO_APROBADO`; el diff requiere retest independiente.

Retest independiente registrado el `2026-09-09T20:23:34-03:00` por Codex sobre
`feature/psp-adapter-contract` en la base
`2e7de49dfde6c20bc798089139ea235534ea0a75`: el resultado emitido el
`2026-09-09T20:14:06-03:00` fue `APROBADO_PARA_COMMIT`. P1 y P3 quedaron
`RESUELTO` y no existen hallazgos actuales P0-P3. Estado:
`PSP_ADAPTER_CONTRACT_APROBADO_PARA_COMMIT`.

La evidencia comprende focal 22/22 y suite completa 311/316, con 5 omisiones
historicas, 0 fallos y 0 errores; `compileall`, enlaces relativos y
`git diff --check` aprobados. PostgreSQL no fue ejecutado ni acreditado porque
no aplica al incremento en memoria. Persistencia, webhooks, Mercado Pago, ARCA
e integracion productiva siguen fuera de alcance y el diseño 2.0 permanece
`PROPUESTO_NO_APROBADO`. Commit, push y PR continuan pendientes en este
registro.

## Sprint 2 - Cobros transaccionales y creditos

Estado: PENDIENTE_DE_REFINAMIENTO_Y_AUTORIZACION.

Objetivo propuesto: un cobro trazable vinculado al nucleo contractual o enlace
independiente admitido; checkout/QR; comision efectiva; lotes de creditos;
reserva, consumo, vencimiento y renovacion transaccional sin duplicados.

Dependencias principales: decisiones economicas y juridicas, MP-08 a MP-10 y
MP-12 a MP-16, ADR de integracion/eventos/ledger y autorizacion de desarrollo.
El origen `EXTERNAL` del Contracting Core se conserva; pagos integrados son una
capacidad futura, sin renombrar enums ni crear migraciones en Sprint 1.

## Sprint 3 - Suscripcion y transicion de modalidades

Estado: PENDIENTE_DE_REFINAMIENTO_Y_AUTORIZACION.

Objetivo propuesto: suscripcion de 30 dias, creditos como pago total/parcial,
inicio diferido, renovacion manual/automatica, exencion, gracia y retorno
transaccional, con consentimiento e idempotencia.

Dependencias principales: MP-01 a MP-11 y MP-14 a MP-16, politicas de baja,
reversas y reintentos, pruebas juridicas del consentimiento y ADR aprobados.

## Facturacion

Sprint 1 evalua alcance, riesgos, integracion directa/proveedor y evidencia
fiscal. No se agrega ARCA ni IA a Sprint 3. La implementacion de Facturacion
PRO MVP debe estimarse como incremento propio despues de la evaluacion de
REQ-002, seguridad, legal, fiscal y contabilidad.

## Handoff previsto a Agente 02

El Agente 02 debe producir una propuesta revisable, no codigo:

1. mapa de capacidades y brechas;
2. evaluacion separada de marketplace y suscripcion contra MP-01 a MP-16;
3. comparacion con evidencia oficial de ARCA directo y proveedores;
4. slicing de sprints 2 y 3, criterios, dependencias y riesgos;
5. estrategia de pruebas para idempotencia, concurrencia, fechas, reservas y
   reversas, con PostgreSQL donde corresponda;
6. estimaciones de trabajo separadas de esperas externas;
7. recomendacion y decisiones que requieren aprobacion antes de codigo.

No debe contactar proveedores o abogados ni implementar integraciones sin una
autorizacion posterior y expresa.
