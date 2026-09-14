# PRO - Refinamiento comercial, PSP y plan de tres sprints

Timestamp de actualizacion: 2026-09-07T21:31:53-03:00
Timestamp de cierre documental: 2026-09-07T21:54:36-03:00
Estado: CERRADO_DOCUMENTALMENTE_INTEGRACION_GIT_PENDIENTE
Responsable de producto: Cristian Sánchez  
Agente: 01 - Documentation Engineer  
Rama observada: `develop`
Commit observado: `1d22f87adc358eae20121ea727142b0276cf337e`

## Correcciones P2 del adaptador PSP de consulta Mercado Pago

Timestamp: 2026-09-13T23:27:35-03:00
Estado: MERCADOPAGO_PAYMENT_QUERY_PSP_ADAPTER_CORREGIDO_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Rama y base: `feature/mercadopago-payment-query-adapter` en
`c2cdc1aaa920b74b4ba4fb3581a935fdea72cd5e`

Los hallazgos P2 quedan conservados como evidencia histórica. El contexto del
adaptador y la configuración del cliente quedaron congelados estructuralmente:
proveedor, modo, cliente, token, transporte y timeout no admiten reasignación.
El proveedor sigue siendo exclusivamente `mercadopago` y las propiedades de
contexto expuestas son de solo lectura.

El transporte cierra una única vez todo `HTTPError` sin leer cuerpo ni retener
headers. Incluso si el cierre falla, la excepción queda aislada y se conserva
la clasificación neutral por código sin filtraciones del proveedor.

Focal completa 49/49, regresiones PSP/pagos 131/131, PostgreSQL 15/15 y suite
completa 476 ejecutadas, 471 aprobadas y 5 omitidas, sin fallos ni errores. La
base descartable fue eliminada y `trax_db` permaneció intacta. No se agregó
migración ni se amplió el alcance; queda pendiente el retest independiente.

## Adaptador PSP de consulta de pagos Mercado Pago

Timestamp: 2026-09-13T22:54:24-03:00
Estado: MERCADOPAGO_PAYMENT_QUERY_PSP_ADAPTER_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Rama y base: `feature/mercadopago-payment-query-adapter` en
`c2cdc1aaa920b74b4ba4fb3581a935fdea72cd5e`

La decisión aprobada segrega creación y consulta sin modificar `PSPAdapter`.
La nueva capacidad `PSPPaymentQueryAdapter` devuelve un DTO mínimo inmutable con
identidad externa y estado neutral. Así, el adaptador Mercado Pago no fabrica
referencia, importe, moneda, idempotencia o fecha y no accede a persistencia.

El proveedor queda fijo en `mercadopago` y el modo es explícito. El procesador
valida ambos contra el evento antes de consultar, realiza como máximo una
llamada y conserva la separación entre transacción de lectura, red y segunda
transacción de persistencia. Incertidumbres y estados no representables no se
convierten en rechazo; errores contractuales/configuración quedan explícitos y
sin escritura.

El transporte estándar usa TLS verificado, host fijo, timeout y ningún redirect
o retry; los tests inyectan transporte simulado. Focal 45/45, regresiones
PSP/pagos 161/161, PostgreSQL 15/15 y suite completa 472 ejecutadas, 467
aprobadas y 5 omitidas, sin fallos ni errores. La base descartable fue eliminada
y `trax_db` permaneció presente.

No hay procesamiento automático desde webhook, creación de cobros, SDK,
worker, nueva migración ni credencial real. El incremento queda pendiente de
revisión independiente.

## Bloqueo contractual del adaptador de consulta Mercado Pago

Timestamp: 2026-09-13T22:43:20-03:00
Estado: MERCADOPAGO_PAYMENT_QUERY_PSP_ADAPTER_BLOQUEADO_POR_CONTRATO_NEUTRAL
Agente: Codex - implementador tecnico local
Rama y base: `feature/mercadopago-payment-query-adapter` en
`c2cdc1aaa920b74b4ba4fb3581a935fdea72cd5e`

La inspección previa detectó que el contrato neutral actual no permite conectar
la consulta sin fabricar información. `get_attempt()` promete un
`PaymentAttempt` completo, pero la respuesta aprobada aporta únicamente ID,
estado, modo y detalle; referencia interna, importe, moneda, idempotencia y fecha
no están disponibles. El mismo protocolo exige además `create_attempt()`, fuera
del alcance autorizado.

No se simuló compatibilidad mediante valores ficticios, un tipo de retorno
distinto o un método de creación inutilizable. Se requiere decidir entre
segregar las capacidades neutrales de creación/consulta o hacer que el
procesador dependa de un resultado mínimo explícito. El desarrollo y sus gates
quedan suspendidos hasta esa definición; los dos commits previos permanecen
intactos.

## Corrección P2 del Bearer del cliente HTTP de pagos

Timestamp: 2026-09-13T22:16:45-03:00
Estado: MERCADOPAGO_PAYMENT_QUERY_HTTP_CLIENT_CORREGIDO_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Rama y base: `feature/mercadopago-payment-query-adapter` en
`2547f483329b6c17c5cbc86e25ab73e4f9d2463c`

El hallazgo P2 queda preservado históricamente y corregido mediante una
allowlist ASCII compatible con `b64token`. La parte principal debe ser no vacía
y contener solo letras, números o `-._~+/`; `=` queda limitado al padding final.
Se fija un máximo de 2048 caracteres y no se transforma el valor recibido.

Se bloquean whitespace, controles C0/C1, `DEL`, caracteres invisibles,
bidireccionales o Unicode visualmente similares y padding intermedio antes de
construir headers o invocar el transporte. La excepción permanece neutral y no
expone el token. El resto del contrato HTTP no cambia y la corrección queda
pendiente de retest independiente.

Validación: focal cliente/contrato 26/26, regresiones PSP/pagos 151/151 y suite
completa 462 ejecutadas, 457 aprobadas y 5 omitidas, sin fallos ni errores.

## Cliente HTTP de consulta de pagos Mercado Pago

Timestamp: 2026-09-13T12:38:36-03:00
Estado: MERCADOPAGO_PAYMENT_QUERY_HTTP_CLIENT_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Rama y base: `feature/mercadopago-payment-query-adapter` en
`2547f483329b6c17c5cbc86e25ab73e4f9d2463c`

El segundo incremento agrega un cliente autenticado con transporte inyectable
para la consulta puntual de pagos al host productivo fijo. La solicitud es un
único `GET`, sin body, query, redirects ni retries, con timeout acotado y los
headers mínimos de Bearer y aceptación JSON. El token no se expone ni se lee
desde configuración global.

Las respuestas se clasifican sin confiar en cuerpos de error. El éxito requiere
JSON UTF-8 acotado, objeto inequívoco, claves únicas y `Content-Type` válido;
el contenido se transforma después mediante el contrato neutral aprobado. Los
errores externos recuperables permanecen separados de autenticación, ausencia
del pago y rechazo de solicitud.

No se realiza red real en pruebas, no se integra aún `PSPAdapter`, no hay
persistencia o modificación financiera y no se incorporan SDK, dependencia o
migración. El diseño general 2.0 y la conexión productiva siguen pendientes.

Validación: focal cliente/contrato 25/25, regresiones PSP/pagos 150/150 y suite
completa 461 ejecutadas, 456 aprobadas y 5 omitidas, sin fallos ni errores.
PostgreSQL no aplica al incremento HTTP aislado y sin persistencia.

## Corrección P2 del contrato de consulta de pagos Mercado Pago

Timestamp: 2026-09-13T12:13:00-03:00
Estado: MERCADOPAGO_PAYMENT_QUERY_CONTRACT_CORREGIDO_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Rama y base: `feature/mercadopago-payment-query-adapter` en
`1cb89cdb647cd358d66b4a013f9f671d1cfb8388`

El hallazgo P2 queda preservado históricamente y corregido: `status_detail` es
un token técnico opcional, de hasta 128 caracteres, iniciado por letra ASCII
minúscula y compuesto solo por letras ASCII minúsculas, números y guion bajo.
Se rechazan valores numéricos y secuencias de 13 a 19 dígitos consecutivos aun
cuando posean prefijo o sufijo, además de espacios, mayúsculas, guiones y
Unicode. El error neutral no conserva ni expone el valor rechazado.

Los tokens `accredited`, `pending_contingency` y
`cc_rejected_bad_filled_card_number` permanecen válidos. Identidad, entorno y
mapeos de estados continúan sin cambios. La corrección queda pendiente de
retest independiente y no amplía el alcance a HTTP, persistencia o integración
productiva con Mercado Pago.

Validación: focal 14/14, regresiones PSP/pagos 139/139 y suite completa 450
ejecutadas, 445 aprobadas y 5 omitidas, sin fallos ni errores.

## Contrato de consulta de pagos Mercado Pago

Timestamp: 2026-09-13T11:52:01-03:00
Estado: MERCADOPAGO_PAYMENT_QUERY_CONTRACT_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Rama: `feature/mercadopago-payment-query-adapter`
Base: `1cb89cdb647cd358d66b4a013f9f671d1cfb8388`

Se implementó una frontera pura e inmutable para validar una respuesta ya
decodificada de `GET /v1/payments/{id}`. La identidad solicitada se restringe a
un segmento numérico ASCII seguro; la respuesta exige objeto inequívoco, `id`
entero estricto coincidente y `live_mode` booleano coincidente con el entorno.

El contrato mapea únicamente estados representables al enum neutral existente:
`approved`; `pending`/`in_process`/`authorized`; y
`rejected`/`cancelled`. Reembolsos, contracargos y estados desconocidos exigen
conciliación explícita mediante una excepción neutral. No se conserva payload
crudo y `status_detail` solo se expone como token seguro acotado.

Validación: focal 13/13, regresiones PSP/pagos 138/138 y suite completa 449
ejecutadas, 444 aprobadas y 5 omitidas, sin fallos ni errores. PostgreSQL no
aplica. Fuente oficial: [Obtener pago - Mercado Pago Developers](https://www.mercadopago.com.ar/developers/es/reference/online-payments/subscriptions/get-payment/get).

Este incremento no realiza HTTP, no lee credenciales, no persiste ni modifica
estados financieros y no agrega SDK, dependencias o migraciones. La integración
real con Mercado Pago y la aprobación integral del diseño 2.0 siguen pendientes.

## Integración post-merge del Webhook de Mercado Pago

Timestamp: 2026-09-13T00:00:12-03:00
Estado: POST_MERGE_MERCADOPAGO_WEBHOOK_INGRESS_REGISTRADO_PENDIENTE_DE_REVISION_DOCUMENTAL
Agente: Codex - implementador documental local
Rama destino: `develop`
Rama integrada: `feature/mercadopago-webhook-ingress`
PR: `#13`
Base previa: `08471f76900cde263a7a4590ff77f60751ffd704`
Merge: `c8dc017be48a2a3526947de50c9121986047e2d4`

El PR #13 integró los commits `73b3fd9`, `199be11` y `540d953`: 12 archivos,
1851 inserciones y 0 eliminaciones. El head Alembic permaneció en
`20260911_02`. `develop` local y remoto coinciden, y el árbol de `c8dc017`
coincide exactamente con el del commit de característica `540d953`.

La evidencia previa continúa siendo la del SHA probado: focal 44/44,
regresiones PSP 63/63, pagos 65/65, PostgreSQL 2/2 y suite completa 436
ejecutadas, 431 aprobadas y 5 omitidas, sin fallos ni errores. No se repitieron
pruebas post-merge; la continuidad de la evidencia se basa en la identidad Git
verificada.

Se registra una desviación procesal: el merge se realizó con aprobación local
para commit y apertura de PR, pero antes de un gate remoto independiente
`APROBADO_PARA_MERGE`. No se clasifica como defecto o regresión funcional y no
se presenta como aprobación remota retroactiva.

Continúan ausentes credenciales productivas, consulta al PSP, conciliación
automática, OAuth, SDK, workers, retries y deploy. El diseño general 2.0 no se
declara completo por esta integración.

## Correcciones P2 del ingreso HTTP de Webhooks de Mercado Pago

Timestamp: 2026-09-12T23:27:36-03:00
Estado: MERCADOPAGO_WEBHOOK_HTTP_INGRESS_CORREGIDO_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Rama: `feature/mercadopago-webhook-ingress`
Base: `199be11cb6b85cd5a9b963e93097aebca31d3638`

Se conservan los hallazgos históricos. El endpoint ahora rechaza un
`X-Request-Id` plegado con coma, múltiple, vacío o con whitespace ambiguo antes
de verificar la firma o iniciar actividad de base de datos. Un valor válido no
se normaliza ni se modifica para el manifiesto.

El JSON se decodifica desde el cuerpo original mediante una frontera estricta:
UTF-8, `json.loads()`, pares de objetos para detectar cualquier clave repetida
y rechazo explícito de `NaN`/`Infinity`. Un sentinel evita propagar o encadenar
errores del decoder, y no se exponen payload, claves, valores ni detalles
internos en respuestas, excepciones o logs.

Focal HTTP, firma, contrato y configuración 44/44; regresiones PSP 63/63;
regresiones de pagos 65/65; PostgreSQL 2/2 y suite completa 436 ejecutadas,
431 aprobadas y 5 omitidas, sin fallos ni errores. `compileall` y el head único
`20260911_02` fueron aprobados. La base descartable
`trax_mp_webhook_test_ingress_p2_20260912` fue eliminada y confirmada ausente;
`trax_db` permaneció intacta.

No se agregó migración, dependencia, conciliación automática ni conexión nueva
con el PSP. La corrección queda pendiente de retest independiente.

## Ingreso HTTP de Webhooks de Mercado Pago

Timestamp: 2026-09-12T19:34:39-03:00
Estado: MERCADOPAGO_WEBHOOK_HTTP_INGRESS_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Rama: `feature/mercadopago-webhook-ingress`
Base: `199be11cb6b85cd5a9b963e93097aebca31d3638`

El tercer incremento conecta el verificador, el contrato de notificación y el
inbox mediante `POST /api/webhooks/mercadopago`. El endpoint es público, sin
autenticación de usuario, y exige la firma HMAC con el secreto obtenido de
configuración. Conserva la multiplicidad de query y headers, valida la firma
antes del JSON y crea el tiempo de recepción en UTC.

La transacción pertenece a la ruta: el evento se registra con el servicio
existente, se confirma antes del `200` y se revierte ante conflicto o fallo.
Nuevo y replay comparten una respuesta mínima idéntica; los errores utilizan
estados `400`, `401`, `409`, `500` o `503` y mensajes genéricos sin datos
sensibles ni detalles internos.

Focal HTTP, firma, contrato y configuración 39/39; regresiones PSP 58/58;
regresiones de pagos 65/65; PostgreSQL 2/2 y suite completa 431 ejecutadas,
426 aprobadas y 5 omitidas, sin fallos ni errores. `compileall` y el head único
`20260911_02` fueron aprobados. La base descartable
`trax_mp_webhook_test_ingress_20260912` fue eliminada y confirmada ausente;
`trax_db` permaneció intacta.

No hay migración nueva, SDK, OAuth, consulta al PSP, conciliación automática,
worker, retry, QR, checkout, créditos, PRO ni ARCA. El incremento queda
pendiente de revisión independiente y no declara completa la arquitectura 2.0.

## Corrección P2 del contrato de notificación Webhook de Mercado Pago

Timestamp: 2026-09-12T19:03:04-03:00
Estado: MERCADOPAGO_WEBHOOK_NOTIFICATION_CONTRACT_CORREGIDO_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Rama: `feature/mercadopago-webhook-ingress`
Base: `73b3fd951315d6f2876b7745347dea04c63b3a64`

Se conserva el hallazgo histórico y se registra su corrección. El parseo ISO
8601 quedó encapsulado en un helper que transforma `ValueError` o `TypeError`
en un sentinel interno; la excepción neutral se produce fuera del bloque de
captura y no conserva causa ni contexto del parser.

Una regresión con marcador sensible confirma que el dato no aparece en
`str`, `repr` ni el traceback de la excepción y que `__cause__` y `__context__`
son nulos. La revisión de otros parseos del contrato no encontró otra
conversión equivalente. No cambiaron firma, normalización, hash ni DTO.

Focal 21/21, regresiones PSP 47/47, regresiones de pagos 65/65 y suite completa
420 ejecutadas, 415 aprobadas y 5 omitidas, sin fallos ni errores. `compileall`
y el head único `20260911_02` fueron aprobados. PostgreSQL no aplica.

La corrección queda pendiente de retest independiente y no agrega endpoint,
HTTP, persistencia, SDK, credenciales ni integración real con Mercado Pago.

## Contrato de notificacion Webhook de Mercado Pago

Timestamp: 2026-09-12T18:42:12-03:00
Estado: MERCADOPAGO_WEBHOOK_NOTIFICATION_CONTRACT_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Rama: `feature/mercadopago-webhook-ingress`
Base: `73b3fd951315d6f2876b7745347dea04c63b3a64`

Se implementó el segundo incremento como frontera pura entre la notificación
específica de Mercado Pago y el DTO neutral del inbox. La firma se verifica
antes de producir el evento; query, headers y cuerpo se validan sin ambigüedad,
y el identificador firmado debe coincidir con el recurso informado. El valor
original se conserva y la minúscula se limita al manifiesto criptográfico.

El DTO usa proveedor `mercadopago`, modo derivado de `live_mode`, timestamps
con zona y un SHA-256 canónico del contenido validado estable. No guarda payload
crudo ni atribuye significado financiero a `action`; tampoco consulta al PSP
ni invoca conciliación.

Focal de firma y contrato 20/20, regresiones PSP 46/46, regresiones de pagos
65/65 y suite completa 419 ejecutadas, 414 aprobadas y 5 omitidas, sin fallos
ni errores. `compileall`, whitespace y Alembic head único `20260911_02`
aprobados. PostgreSQL no aplica y `trax_db` permaneció fuera de uso.

El incremento queda pendiente de revisión independiente. No agrega ruta Flask,
endpoint público, HTTP, SDK, OAuth, credenciales, migración, persistencia,
webhook productivo, procesador, Mercado Pago real, créditos, PRO, ARCA ni
deploy, y no declara completa la arquitectura 2.0.

## Corrección P2 del verificador de firma Webhook de Mercado Pago

Timestamp: 2026-09-12T18:20:35-03:00
Estado: MERCADOPAGO_WEBHOOK_SIGNATURE_VALIDATOR_CORREGIDO_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Rama: `feature/mercadopago-webhook-ingress`
Base: `08471f76900cde263a7a4590ff77f60751ffd704`

Se conserva el `REQUIERE_CORRECCIONES` histórico y se registra su corrección:
las claves de `x-signature` se canonicalizan mediante trim y minúsculas antes
de almacenarlas o compararlas. Por ello, variantes de casing de `ts` o `v1`
son el mismo componente y cualquier duplicado se rechaza sin sobrescritura,
aun cuando repita el mismo valor. Los valores de esos componentes no se
normalizan y permanecen sujetos a las validaciones previas.

Focal 10/10, regresiones PSP 36/36, regresiones de pagos 65/65 y suite completa
409 ejecutadas, 404 aprobadas y 5 omitidas, sin fallos ni errores. `compileall`
y el head único `20260911_02` fueron aprobados. PostgreSQL no aplica.

La corrección queda pendiente de retest independiente. No agrega ruta Flask,
endpoint público, respuesta HTTP, SDK, credenciales, persistencia ni conexión
real con Mercado Pago, y no amplía el alcance funcional del diseño 2.0.

## Verificador de firma Webhook de Mercado Pago

Timestamp: 2026-09-12T16:17:29-03:00
Estado: MERCADOPAGO_WEBHOOK_SIGNATURE_VALIDATOR_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Rama: `feature/mercadopago-webhook-ingress`
Base: `08471f76900cde263a7a4590ff77f60751ffd704`
Fuente oficial: [Notificaciones de pago de Mercado Pago](https://www.mercadopago.com.ar/developers/es/docs/checkout-pro-preferences/payment-notifications)

Se implementó un componente puro, sin Flask, base de datos ni SDK, que valida
el manifiesto oficial mediante HMAC-SHA256 y comparación en tiempo constante.
`data.id` se convierte a minúsculas exclusivamente dentro del manifiesto y su
valor original se conserva; no se normalizan los demás componentes firmados.

La documentación oficial admite omitir determinados pares ausentes. La
política local de MANDOBRA es deliberadamente más estricta: para aceptar una
notificación exige todos los componentes y el secreto. No se implementó una
ventana para `ts` porque la fuente no define una tolerancia obligatoria.

Focal 9/9, regresiones PSP 35/35, regresiones de pagos 65/65 y suite completa
408 ejecutadas, 403 aprobadas y 5 omitidas, sin fallos ni errores. `compileall`
y el head único `20260911_02` fueron aprobados. PostgreSQL no aplica.

Continúan pendientes la revisión independiente, la ruta Flask, el endpoint
público, la traducción de firma inválida a HTTP 401, configuración segura del
secreto, registro en inbox y consulta del pago. No existe integración real con
Mercado Pago ni procesamiento financiero.

## Integración post-merge del procesamiento de eventos PSP

Timestamp: 2026-09-12T14:03:46-03:00
Estado: POST_MERGE_PSP_EVENT_PROCESSING_REGISTRADO_PENDIENTE_DE_REVISION_DOCUMENTAL
Agente: Codex - implementador tecnico local
Rama destino: `develop`
PR: `#12`
Merge: `a96a55311283d331c70e49aad3550ec6f7b1a566`

La rama `feature/psp-event-processing` fue integrada limpiamente y sin
conflictos con sus tres commits: `f45f32c`, `9951d25` y `3c243b5`. El merge
incorporó 23 archivos, 1996 inserciones y 9 eliminaciones, incluidas las
migraciones `20260911_01` y `20260911_02`; el head final registrado es
`20260911_02`. La revisión remota final fue `APROBADO_PARA_MERGE`.

`develop` local y `origin/develop` coinciden en el merge SHA y en el árbol
exactamente probado. Por esa identidad continúa siendo válida la evidencia
histórica: procesador 9/9; procesador, inbox e identidad 26/26; persistencia,
orquestación y workflow 65/65; PostgreSQL 14/14; suite completa 399 ejecutadas,
394 aprobadas y 5 omitidas; `compileall`, enlaces y `git diff --check`
aprobados. No se repitieron estas validaciones después del merge.

El incremento integrado es infraestructura neutral. No acredita webhook
público, firmas, HTTP, SDK, OAuth, credenciales, integración real con Mercado
Pago, workers, retries, QR, checkout, créditos, PRO, ARCA ni producción. Este
registro queda pendiente de revisión documental independiente.

## Corrección P1 de tópicos del procesador PSP

Timestamp: 2026-09-12T13:32:58-03:00
Estado: PSP_EVENT_RECONCILIATION_PROCESSOR_CORREGIDO_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Rama: `feature/psp-event-processing`
Base: `9951d2503d9b70353ddcd674d6c750cbb2436997`

El procesador neutral ahora requiere una colección explícita y no vacía de
tópicos de pago, normalizada con trim y minúsculas y conservada como conjunto
inmutable. Cada adaptador futuro definirá sus tópicos; el servicio no contiene
valores de Mercado Pago ni un comodín implícito.

Un tópico no configurado produce `UNSUPPORTED_TOPIC` antes de correlacionar o
consultar al PSP. La reproducción con `merchant_order`, ID coincidente y acción
`payment.approved` dejó el intento en `PENDING`, sin búsquedas ni llamadas, aun
al reprocesarse. El tópico sólo clasifica la procesabilidad del recurso.

Focal 9/9, regresiones 26/26 y 65/65, PostgreSQL 14/14 y suite completa 399
ejecutadas, 394 aprobadas y 5 omitidas, sin fallos ni errores. `compileall` y
head único `20260911_02` aprobados; no se agregó migración. Se conserva el
`REQUIERE_CORRECCIONES` histórico y falta retest independiente. No existe
integración real con Mercado Pago ni endpoint webhook productivo.

## Procesador neutral de conciliación por eventos PSP

Timestamp: 2026-09-12T13:10:46-03:00
Estado: PSP_EVENT_RECONCILIATION_PROCESSOR_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Rama: `feature/psp-event-processing`
Base: `9951d2503d9b70353ddcd674d6c750cbb2436997`

El tercer incremento implementa un coordinador neutral que toma un evento ya
registrado únicamente como aviso. Correlaciona mediante proveedor, modo e ID
externo, libera la sesión antes de consultar `PSPAdapter` y persiste después el
estado autoritativo con las transiciones existentes. No deriva estado desde el
tópico, acción o contenido del evento.

Focal 7/7, regresiones 24/24 y 65/65, PostgreSQL real 14/14 y suite completa
397 ejecutadas, 392 aprobadas y 5 omitidas, sin fallos ni errores. `compileall`
y el head único `20260911_02` fueron aprobados; no existe migración nueva.

Permanece pendiente la revisión independiente antes del tercer commit. No hay
integración real con Mercado Pago, endpoint webhook productivo, HTTP, firmas,
SDK, workers, retries, checkout, créditos, PRO, ARCA ni interfaz.

## Corrección P2/P3 de identidad PSP

Timestamp: 2026-09-11T22:54:46-03:00
Estado: PAYMENT_ATTEMPT_PSP_IDENTITY_CORREGIDA_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Rama: `feature/psp-event-processing`
Base: `f45f32ce3c032b6a4b7404886b9c2558cdb5e62a`

La recuperación por carrera de referencia quedó limitada a la violación única
real de `uq_payment_obligations_reference`, identificada por SQLSTATE `23505`
y diagnóstico estructurado. Una constraint distinta, un `23514` o diagnóstico
incompleto conserva el `IntegrityError` original y el llamador puede ejecutar
rollback y reutilizar la sesión. Se corrigió además el whitespace señalado.

Focal 14/14, regresiones 82/82, PostgreSQL real 13/13 y suite completa 390
ejecutadas, 385 aprobadas y 5 omitidas, sin fallos ni errores. `compileall` y el
head Alembic único `20260911_02` fueron aprobados. El estado histórico
`REQUIERE_CORRECCIONES` se conserva; el paquete corregido requiere retest
independiente. No se implementó el procesador ni integración real con PSP.

## Identidad PSP contextual adoptada

Timestamp: 2026-09-11T22:26:39-03:00
Estado: PAYMENT_ATTEMPT_PSP_IDENTITY_IMPLEMENTADA_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Rama: `feature/psp-event-processing`
Base: `f45f32ce3c032b6a4b7404886b9c2558cdb5e62a`

La decisión aprobada incorpora proveedor, modo e ID externo como identidad
contextual de un intento. `20260911_02` agrega el contexto sin backfill y con
unicidad sólo para identidades completas; los intentos legacy no pueden
correlacionarse automáticamente. El proveedor usa la misma canonicalización
que el inbox.

Focal 23/23, regresiones 81/81, PostgreSQL 12/12 y suite completa 389
ejecutadas, 384 aprobadas y 5 omitidas, sin fallos ni errores. El bloqueo previo
se conserva como antecedente. El procesador de eventos y toda integración real
con Mercado Pago continúan fuera de alcance y pendientes de otro incremento.

## Procesador de conciliación de eventos PSP - bloqueo de correlación

Timestamp: 2026-09-11T22:16:16-03:00
Estado: PSP_EVENT_RECONCILIATION_PROCESSOR_BLOQUEADO_POR_DEFINICION_DE_CORRELACION
Agente: Codex - implementador tecnico local
Rama: `feature/psp-event-processing`
HEAD: `f45f32ce3c032b6a4b7404886b9c2558cdb5e62a`

La inspección del esquema confirmó que el evento identifica proveedor y modo,
pero el intento de pago no conserva esas dimensiones y su identificador PSP no
es único. No puede demostrarse una correlación inequívoca sin una definición
adicional. Se evitó una consulta global insegura y no se agregó una migración.

Debe aprobarse una de estas bases contractuales: identidad PSP completa y
única en `payment_attempts`, con reglas para registros existentes, o relación
explícita evento-intento con un mecanismo confiable de asociación. El segundo
incremento permanece bloqueado; Mercado Pago, HTTP, workers y procesamiento
productivo continúan fuera de alcance.

## Corrección P1/P2 de bandeja de eventos PSP

Timestamp: 2026-09-11T20:57:36-03:00
Estado: PSP_EVENT_INBOX_FOUNDATION_CORREGIDA_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Rama: `feature/psp-event-processing`
Base: `3b6bc44d0bddfa108b4b18e6d04e23f5c0b34fee`

Sin eliminar el dictamen histórico `REQUIERE_CORRECCIONES`, se corrigieron sus
dos hallazgos. Una entrega repetida puede tener otro `received_at` sin cambiar
el contenido material: devuelve la fila original y preserva su primera fecha.
El hash SHA-256 se canonicaliza a minúsculas en la frontera del DTO; diferencias
de casing son replay y diferencias reales continúan bloqueadas como conflicto.

Resultados locales: focal 11/11; regresiones 75/75; PostgreSQL 3/3; suite
completa 383 ejecutadas, 378 aprobadas y 5 omitidas, sin fallos ni errores.
La migración `20260911_01` permanece vigente. El incremento sigue pendiente de
retest independiente y no está autorizado para su primer commit.

## Bandeja persistente de eventos PSP - primer incremento

Timestamp: 2026-09-11T20:09:34-03:00
Estado: PSP_EVENT_INBOX_FOUNDATION_IMPLEMENTADA_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Rama: `feature/psp-event-processing`
Base: merge `3b6bc44` del PR #11; feature previa `f10616c`

Se implemento exclusivamente el contrato neutral normalizado y su bandeja
persistente idempotente. La notificacion conserva identidad, tópico, acción,
recurso, modo, tiempos y hash, pero no es evidencia financiera ni acredita
autenticidad. La migracion `20260911_01` desciende de `20260910_01`.

Resultados: focal 9/9; regresiones 73/73; PostgreSQL 3/3; suite completa 381
ejecutadas, 376 aprobadas y 5 omitidas, sin fallos ni errores. Este es el primer
incremento de la rama agrupada; el PR se abrira solamente despues del segundo
commit. Endpoint, HMAC, respuesta HTTP, consulta a Mercado Pago, procesamiento,
workers, creditos, PRO, ARCA e interfaz permanecen fuera de alcance.

## Workflow persistente de pagos - contrato de incertidumbre resuelto

Timestamp: 2026-09-11T19:22:09-03:00
Estado: PERSISTENT_PAYMENT_WORKFLOW_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Rama: `feature/persistent-payment-workflow`
Commit base: `dfbb7e3f53e61638eb52113286870eca1b59d031`

La definicion inicial del incremento que vinculaba incertidumbre de transporte
con `PENDING` fue reemplazada tras contrastarla con el esquema integrado y la
semantica financiera. La representacion aprobada conserva estado financiero
`NULL`, resultado `RECONCILIATION_REQUIRED`, conciliacion requerida e
identificador PSP opcional. `PENDING` queda reservado para una respuesta
autoritativa del PSP.

Las pruebas cubren incertidumbre con y sin identificador, conciliacion desde
estado desconocido hacia `PENDING`, `APPROVED` y `REJECTED`, no inferencia de
rechazo o aprobacion, replay, conflictos y dos transacciones breves sin llamada
al adaptador dentro de ellas. Workflow: 13/13; focal mas regresiones: 68/68;
PostgreSQL real: 10/10; suite completa: 372 ejecutadas, 367 aprobadas y 5
omisiones historicas, sin fallos ni errores. `compileall`, head Alembic unico
`20260910_01`, enlaces relativos y `git diff --check`: aprobados. La base
descartable `trax_payment_persistence_test_workflow_contract_20260911` fue
vaciada por el gate, eliminada y verificada ausente. No existe migracion nueva.

Mercado Pago, HTTP, webhooks, checkout, creditos, PRO, ARCA, interfaz,
dependencias, procesamiento automatico y la arquitectura 2.0 completa
permanecen fuera de alcance. El incremento queda pendiente de revision
independiente y sin integracion Git.

## Workflow persistente de pagos - avance local bloqueado

Timestamp: 2026-09-11T19:09:43-03:00
Estado: PERSISTENT_PAYMENT_WORKFLOW_BLOQUEADO_POR_DEFINICION_DE_ESTADO_INCIERTO
Agente: Codex - implementador tecnico local
Rama: `feature/persistent-payment-workflow`
Commit base: `dfbb7e3f53e61638eb52113286870eca1b59d031`

Se implemento la coordinacion entre el orquestador neutral y la persistencia
existente usando dos transacciones breves separadas por la llamada al adaptador.
El flujo admite replay, fallos antes y despues de la llamada, reanudacion
idempotente y conciliacion explicita con y sin identificador externo. No llama
controles internos del simulador desde el servicio ni agrega retries.

Focal y regresiones: 67/67. Gate PostgreSQL: 10/10 sobre
`trax_payment_persistence_test_workflow_20260911`, limpiada y eliminada. Suite
completa: 371 ejecutadas, 366 aprobadas, 5 omisiones historicas, sin fallos ni
errores. `compileall` y head unico `20260910_01`: aprobados.

El estado objetivo no se declara alcanzado porque existe una contradiccion:
el nuevo paquete exige `PENDING` como estado financiero de una respuesta
incierta, pero `20260910_01` exige `NULL` para un resultado
`RECONCILIATION_REQUIRED`. No se modifico Alembic sin autorizacion. Debe
definirse cual representacion es canónica antes de cerrar el incremento.

Mercado Pago, pagos productivos, webhooks, checkout, creditos, PRO, ARCA y la
arquitectura 2.0 completa permanecen fuera de alcance.

## Integracion verificada de payment-persistence-foundation

Timestamp: 2026-09-11T15:46:40-03:00
Estado: PAYMENT_PERSISTENCE_FOUNDATION_INTEGRADA_Y_VERIFICADA_POST_MERGE
Agente: Codex - implementador tecnico local
Rama: `develop`
PR: `#10`
Commit de caracteristica: `fae81e62f1526a0daa229f03efbc19c918dc8ff0`
Merge commit: `8dd773692004453d663742be02048f79cae0aa0c`

Quedaron integrados los 14 archivos del incremento con Alembic head
`20260910_01`. `develop` local y remoto coinciden en el merge commit y el arbol
previo a este registro estaba limpio.

El merge ocurrio antes de completar el gate final solicitado y Testing no pudo
emitir una autorizacion preventiva. La verificacion post-merge confirmo que el
contenido remoto es exactamente el commit previamente probado y aprobado, sin
diferencias de alcance ni defectos funcionales detectados. Se conserva la
integracion sin iniciar una reversion; la desviacion es de proceso y no una
regresion del codigo.

No se repitieron pruebas despues del merge. Evidencia historica conservada:
focal portable y regresiones 55/55; PostgreSQL real 7/7; suite completa 359
ejecutadas, 354 aprobadas y 5 omisiones historicas, sin fallos ni errores;
`compileall`, enlaces y `git diff --check` aprobados; base PostgreSQL
descartable eliminada y `trax_db` intacta.

No quedan acreditados Mercado Pago, pagos productivos, webhooks, checkout,
creditos, PRO, ARCA, deploy ni la arquitectura 2.0 completa.

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
