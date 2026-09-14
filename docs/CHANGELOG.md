# CHANGELOG MANDOBRA

## 2026-09-14 - Especificación de orden Checkout Pro

Timestamp: 2026-09-14T10:21:05-03:00
Estado: ESPECIFICACION_CHECKOUT_PRO_PAYMENT_ORDER_CONTRACT_PREPARADA_PENDIENTE_DE_REVISION
Agente: Codex - implementador técnico documental
Rama: `feature/checkout-pro-payment-order-contract`
Commit base: `9199d548dd312f65d84414f30e6193ab386bdc53`

- Se creó [REQ-003](REQUISITOS/REQ-003-creacion-de-ordenes-de-cobro-checkout-pro.md)
  para una orden en ARS, importe Decimal y vencimiento exacto a 72 horas.
- Una única URL de Checkout Pro se reutiliza como enlace remoto o contenido de
  QR; el producto QR de sucursales/cajas queda fuera del MVP.
- Se definió una capacidad neutral de creación separada de intentos y consultas,
  con DTOs, validaciones, errores y fake determinista previstos.
- No existe implementación: HTTP, SDK, credenciales, ORM, migraciones, QR,
  frontend, conciliación, PRO y producción permanecen fuera de alcance.

## 2026-09-14 - Integración del adaptador de consulta Mercado Pago

Timestamp: 2026-09-14T09:06:21-03:00
Estado: POST_MERGE_MERCADOPAGO_PAYMENT_QUERY_ADAPTER_REGISTRADO_PENDIENTE_DE_REVISION_DOCUMENTAL
Agente: Codex - implementador técnico documental
Rama: `develop`
Merge: `b816c69026f329466619291c413e7b15c758e9df`

- El PR #14, `feat: agregar adaptador de consulta de pagos de Mercado Pago`,
  fusionó sin conflictos informados la rama
  `feature/mercadopago-payment-query-adapter` hacia `develop`.
- Se integraron `2547f483329b6c17c5cbc86e25ab73e4f9d2463c`,
  `c2cdc1aaa920b74b4ba4fb3581a935fdea72cd5e` y
  `47632ad4d008e7b414a3699793578343a8595bd4`: 13 archivos, 2044
  inserciones y 35 eliminaciones. El árbol del commit final y el del merge son
  idénticos; el veredicto remoto previo fue `APROBADO_PARA_MERGE`.
- La evidencia local histórica del contenido evaluado fue: focales 49/49,
  regresiones PSP/pagos 165/165, PostgreSQL 15/15 y suite completa 476
  ejecutadas, 471 aprobadas y 5 omitidas, sin fallos ni errores; `compileall`,
  enlaces, whitespace y `git diff --check` aprobados. No se repitieron pruebas
  ni PostgreSQL después del merge porque el árbol integrado coincide.
- Quedaron integrados el contrato, el cliente HTTP y el adaptador neutral de
  consulta, manteniendo separadas consulta y creación, las sesiones cerradas
  durante HTTP, una segunda transacción breve, configuración inmutable,
  protección del token y cierre seguro de `HTTPError`. El webhook no consulta
  ni concilia automáticamente.
- No se agregaron migraciones ni dependencias; Alembic conserva el head único
  `20260911_02`. No hubo checks ni GitHub Actions remotos, limitación de
  evidencia CI que no constituye un fallo funcional.
- No existen creación de cobros, QR, credenciales reales, SDK, retries,
  workers, frontend ni deploy. Esta integración no autoriza producción.

## 2026-09-13 - Correcciones P2 del adaptador PSP Mercado Pago

Timestamp: 2026-09-13T23:27:35-03:00
Estado: MERCADOPAGO_PAYMENT_QUERY_PSP_ADAPTER_CORREGIDO_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Rama: `feature/mercadopago-payment-query-adapter`
Commit base: `c2cdc1aaa920b74b4ba4fb3581a935fdea72cd5e`

- Se conservan como antecedente los dos hallazgos P2: el contexto del adaptador
  y del cliente dependía de atributos reasignables, y el transporte no cerraba
  explícitamente los `HTTPError` de `urllib`.
- Adaptador y cliente son ahora estructuras congeladas con slots. Proveedor,
  modo, referencia al cliente, token, transporte y timeout no pueden
  reasignarse después de validar la construcción; `provider` y `live_mode` se
  exponen como propiedades de solo lectura.
- Todo `HTTPError` se cierra exactamente una vez sin leer el cuerpo. Se descartan
  cuerpo y headers, y hasta una excepción del cierre queda contenida antes de
  aplicar la clasificación neutral por código.
- Focal completa 49/49, regresiones PSP/pagos 131/131, PostgreSQL real 15/15 y
  suite completa 476 ejecutadas, 471 aprobadas y 5 omitidas, sin fallos ni
  errores. La corrección queda pendiente de retest independiente.

## 2026-09-13 - Adaptador PSP de consulta de pagos Mercado Pago

Timestamp: 2026-09-13T22:54:24-03:00
Estado: MERCADOPAGO_PAYMENT_QUERY_PSP_ADAPTER_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Rama: `feature/mercadopago-payment-query-adapter`
Commit base: `c2cdc1aaa920b74b4ba4fb3581a935fdea72cd5e`

- La decisión arquitectónica aprobada segregó la consulta en
  `PSPPaymentQueryAdapter` y `PSPPaymentQueryResult`, preservando sin cambios la
  capacidad existente `PSPAdapter` y su `get_attempt()`.
- `MercadoPagoPSPAdapter` implementa solo consulta, expone proveedor
  `mercadopago` y modo inmutable, valida el ID y traduce estados autoritativos o
  incertidumbre sin fabricar datos de creación ni acceder a persistencia.
- El procesador depende de la capacidad mínima, exige que proveedor y modo del
  adaptador coincidan antes de consultar y mantiene la llamada HTTP entre sus
  dos transacciones.
- Se agregó transporte estándar con TLS verificado, host fijo, timeout
  obligatorio y sin redirects/retries. Las pruebas usan transporte simulado.
- Focal 45/45, regresiones PSP/pagos 161/161, PostgreSQL real 15/15 y suite
  completa 472 ejecutadas, 467 aprobadas y 5 omitidas, sin fallos ni errores.

## 2026-09-13 - Bloqueo contractual del adaptador de consulta Mercado Pago

Timestamp: 2026-09-13T22:43:20-03:00
Estado: MERCADOPAGO_PAYMENT_QUERY_PSP_ADAPTER_BLOQUEADO_POR_CONTRATO_NEUTRAL
Agente: Codex - implementador tecnico local
Rama: `feature/mercadopago-payment-query-adapter`
Commit base: `c2cdc1aaa920b74b4ba4fb3581a935fdea72cd5e`

- La inspección previa confirmó que `PSPAdapter.get_attempt()` exige un
  `PaymentAttempt` completo, con referencia interna, importe, moneda, clave
  idempotente y fecha. `GET /v1/payments/{id}` solo fue contratado para aportar
  identidad, estado, modo y detalle; los campos restantes no pueden inferirse.
- `PSPAdapter` también exige `create_attempt()`, operación fuera del alcance de
  esta rama de consulta. No se fabricaron datos, no se devolvió un DTO distinto
  bajo una anotación falsa y no se agregó un método nominal que siempre falle.
- Se requiere aprobar si el contrato neutral se separa en capacidades de
  creación/consulta o si el procesador debe depender de un resultado mínimo de
  consulta. No se modificó código ni se ejecutaron pruebas.

## 2026-09-13 - Corrección P2 del Bearer del cliente de pagos

Timestamp: 2026-09-13T22:16:45-03:00
Estado: MERCADOPAGO_PAYMENT_QUERY_HTTP_CLIENT_CORREGIDO_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Rama: `feature/mercadopago-payment-query-adapter`
Commit base: `2547f483329b6c17c5cbc86e25ab73e4f9d2463c`

- Se conserva el hallazgo P2 como antecedente y se reemplaza la validación del
  Bearer por una allowlist ASCII compatible con `b64token`: parte principal no
  vacía con letras, números, `-`, `.`, `_`, `~`, `+` y `/`, seguida únicamente
  por padding `=` opcional.
- El límite explícito es 2048 caracteres. Se rechazan whitespace, controles C0
  y C1, `DEL`, caracteres invisibles o bidireccionales, Unicode visualmente
  similar y padding intermedio, sin normalizar el token.
- Toda configuración inválida falla antes de construir headers o invocar el
  transporte. La excepción neutral no conserva ni expone el token.
- Focal cliente/contrato 26/26; regresiones PSP/pagos 151/151; suite completa
  462 ejecutadas, 457 aprobadas y 5 omitidas, sin fallos ni errores.

## 2026-09-13 - Cliente HTTP de consulta de pagos Mercado Pago

Timestamp: 2026-09-13T12:38:36-03:00
Estado: MERCADOPAGO_PAYMENT_QUERY_HTTP_CLIENT_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Rama: `feature/mercadopago-payment-query-adapter`
Commit base: `2547f483329b6c17c5cbc86e25ab73e4f9d2463c`

- Se agregó un cliente autenticado desacoplado por transporte inyectable para
  consultar exclusivamente `GET https://api.mercadopago.com/v1/payments/{id}`.
  Valida el ID antes de construir la URL, envía headers mínimos, timeout
  acotado y deshabilita redirects; no realiza retries.
- El Bearer es obligatorio y no se expone mediante DTO, representación del
  cliente, errores o tracebacks. El cliente no lee variables de entorno.
- Las respuestas `200` exigen `application/json` UTF-8, cuerpo de hasta 1 MiB,
  objeto inequívoco, claves únicas y JSON estándar antes de delegar al contrato
  neutral aprobado.
- Se clasifican autenticación, pago inexistente, rechazo de solicitud e
  incertidumbre recuperable sin leer ni exponer cuerpos de error. No se agregó
  persistencia, red real en pruebas, dependencia ni migración.
- Focal cliente/contrato 25/25; regresiones PSP/pagos 150/150; suite completa
  461 ejecutadas, 456 aprobadas y 5 omitidas, sin fallos ni errores.

## 2026-09-13 - Corrección P2 del detalle de estado de pagos

Timestamp: 2026-09-13T12:13:00-03:00
Estado: MERCADOPAGO_PAYMENT_QUERY_CONTRACT_CORREGIDO_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Rama: `feature/mercadopago-payment-query-adapter`
Commit base: `1cb89cdb647cd358d66b4a013f9f671d1cfb8388`

- Se conserva el hallazgo P2 como antecedente y se restringe `status_detail` a
  un token técnico de hasta 128 caracteres: comienza con letra ASCII minúscula
  y admite únicamente letras ASCII minúsculas, números y guion bajo.
- Se rechazan valores numéricos, casing o whitespace no canónico, guiones,
  Unicode y cualquier secuencia de 13 a 19 dígitos consecutivos, incluso con
  prefijo o sufijo. Los errores no incluyen el valor rechazado en mensaje,
  traceback, causa, contexto, argumentos ni atributos.
- Permanecen aceptados `accredited`, `pending_contingency` y
  `cc_rejected_bad_filled_card_number`. Los demás contratos y mapeos no se
  modificaron. La corrección queda pendiente de retest independiente.
- Focal 14/14, regresiones PSP/pagos 139/139 y suite completa 450 ejecutadas,
  445 aprobadas y 5 omitidas, sin fallos ni errores.

## 2026-09-13 - Contrato de consulta de pagos Mercado Pago

Timestamp: 2026-09-13T11:52:01-03:00
Estado: MERCADOPAGO_PAYMENT_QUERY_CONTRACT_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Rama: `feature/mercadopago-payment-query-adapter`
Commit base: `1cb89cdb647cd358d66b4a013f9f671d1cfb8388`

- Se agregó un contrato puro e inmutable que valida la respuesta ya decodificada
  de `GET /v1/payments/{id}` y transforma estados representables a
  `PaymentAttemptStatus`, sin realizar HTTP ni conservar el payload crudo.
- El identificador solicitado admite solamente dígitos ASCII en un segmento
  acotado; el `id` devuelto debe ser entero estricto, coincidir con la consulta
  y no puede ser booleano. `live_mode` también se valida estrictamente contra
  el entorno esperado.
- `approved`, los estados pendientes autoritativos y los rechazos/cancelaciones
  se mapean de forma explícita. Reembolsos, contracargos y estados desconocidos
  requieren conciliación explícita y nunca se interpretan silenciosamente.
- `status_detail` solo se conserva cuando es un token seguro y acotado. Las
  excepciones son neutrales y no incluyen contenido recibido.
- Focal 13/13; regresiones PSP/pagos 138/138; suite completa 449 ejecutadas,
  444 aprobadas y 5 omitidas, sin fallos ni errores. `compileall`, Alembic,
  enlaces, whitespace y `git diff --check` quedan registrados en el cierre de
  esta sesión. PostgreSQL no aplica a este contrato puro.
- Fuente oficial consultada: [Obtener pago - Mercado Pago Developers](https://www.mercadopago.com.ar/developers/es/reference/online-payments/subscriptions/get-payment/get).
  No se incorporaron HTTP, credenciales, SDK, persistencia, migraciones ni
  cambios financieros.

## 2026-09-13 - Integracion post-merge del Webhook de Mercado Pago

Timestamp: 2026-09-13T00:00:12-03:00
Estado: POST_MERGE_MERCADOPAGO_WEBHOOK_INGRESS_REGISTRADO_PENDIENTE_DE_REVISION_DOCUMENTAL
Agente: Codex - implementador documental local
Rama: `develop`
Pull Request: `#13`
Rama integrada: `feature/mercadopago-webhook-ingress`
Base previa: `08471f76900cde263a7a4590ff77f60751ffd704`
Merge commit: `c8dc017be48a2a3526947de50c9121986047e2d4`

- El PR #13 integró `73b3fd9` (validador de firma), `199be11` (contrato de
  notificación) y `540d953` (ingreso HTTP): 12 archivos, 1851 inserciones y
  0 eliminaciones. El head Alembic se conservó en `20260911_02`.
- `develop` local y `origin/develop` coinciden en `c8dc017`; el árbol del merge
  coincide exactamente con el árbol del commit integrado `540d953`.
- Se conserva como evidencia previa del commit integrado: focal 44/44,
  regresiones PSP 63/63, pagos 65/65, PostgreSQL 2/2 y suite completa 436
  ejecutadas, 431 aprobadas y 5 omitidas, sin fallos ni errores. Las pruebas no
  se repitieron después del merge porque la identidad del árbol fue confirmada.
- Desviación procesal: el merge ocurrió con aprobación local para commit y
  apertura del PR, pero antes de un gate remoto independiente
  `APROBADO_PARA_MERGE`. Se registra como observación de proceso, no como
  regresión funcional ni como evidencia adicional de calidad.
- Todavía no existen credenciales productivas, consulta al PSP, conciliación
  automática, OAuth, SDK, workers, retries ni deploy.

## 2026-09-12 - Correcciones P2 del ingreso HTTP de Webhooks

Timestamp: 2026-09-12T23:27:36-03:00
Estado: MERCADOPAGO_WEBHOOK_HTTP_INGRESS_CORREGIDO_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Rama: `feature/mercadopago-webhook-ingress`
Commit base: `199be11cb6b85cd5a9b963e93097aebca31d3638`

- Se conservan los hallazgos históricos y se corrigió `X-Request-Id`: se
  rechazan valores múltiples, vacíos, con whitespace exterior o con coma por
  posible plegado WSGI, antes de verificar la firma o acceder al inbox. El
  valor válido no se transforma para construir el manifiesto.
- `request.get_json()` dejó de ser la decodificación autoritativa. El cuerpo
  original se decodifica como UTF-8 y con `json.loads()` estricto, usando pares
  para rechazar claves duplicadas en cualquier nivel y bloqueando `NaN` e
  `Infinity`.
- Una frontera con sentinel absorbe `JSONDecodeError`, `UnicodeDecodeError` y
  errores internos controlados sin exponer payload, claves, valores, traceback,
  causa o contexto. Las respuestas y logs permanecen genéricos.
- Focal HTTP, firma, contrato y configuración 44/44; regresiones PSP 63/63;
  regresiones de pagos 65/65; PostgreSQL 2/2; suite completa 436 ejecutadas,
  431 aprobadas y 5 omitidas, sin fallos ni errores. `compileall` aprobado y
  Alembic conserva el head único `20260911_02`.
- La base `trax_mp_webhook_test_ingress_p2_20260912` fue eliminada y confirmada
  ausente; `trax_db` permaneció intacta. No se agregó migración ni dependencia.

## 2026-09-12 - Ingreso HTTP de Webhooks de Mercado Pago

Timestamp: 2026-09-12T19:34:39-03:00
Estado: MERCADOPAGO_WEBHOOK_HTTP_INGRESS_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Rama: `feature/mercadopago-webhook-ingress`
Commit base: `199be11cb6b85cd5a9b963e93097aebca31d3638`

- Se agregó `POST /api/webhooks/mercadopago`, público y exento de autenticación
  de usuario/CSRF, protegido por la firma HMAC y por un secreto leído desde
  `MERCADOPAGO_WEBHOOK_SECRET`.
- La ruta conserva query y headers como secuencias de pares, verifica la firma
  antes de interpretar JSON y entrega el contenido validado al contrato neutral.
  El tiempo de recepción se genera en UTC del servidor.
- El evento se registra con `psp_event_inbox` y el endpoint controla
  `commit()`/`rollback()`. Nuevo y replay responden el mismo `200` mínimo;
  firma inválida usa `401`, solicitud malformada `400`, conflicto `409`, secreto
  ausente `503` y fallo de persistencia `500`, todos con respuestas genéricas.
- Focal HTTP, firma, contrato y configuración 39/39; regresiones PSP 58/58;
  regresiones de pagos 65/65; PostgreSQL real 2/2; suite completa 431
  ejecutadas, 426 aprobadas y 5 omitidas, sin fallos ni errores. `compileall`
  aprobado y Alembic conserva el head único `20260911_02`.
- La base descartable `trax_mp_webhook_test_ingress_20260912` se eliminó y se
  confirmó ausente; `trax_db` permaneció presente e intacta. No se agregó
  migración, SDK, OAuth, worker, retry ni conciliación automática.

## 2026-09-12 - Correccion P2 del contrato de notificacion Webhook

Timestamp: 2026-09-12T19:03:04-03:00
Estado: MERCADOPAGO_WEBHOOK_NOTIFICATION_CONTRACT_CORREGIDO_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Rama: `feature/mercadopago-webhook-ingress`
Commit base: `73b3fd951315d6f2876b7745347dea04c63b3a64`

- Se conserva el hallazgo histórico y se corrigió la filtración del error
  interno de `datetime.fromisoformat()`: un helper captura `ValueError` y
  `TypeError`, devuelve un sentinel privado y la excepción neutral se crea
  después, fuera del bloque `except`.
- La regresión con un marcador sensible confirma ausencia del valor en
  `str`, `repr` y el traceback, además de `__cause__` y `__context__` nulos.
- Se revisaron los restantes parseos del contrato y no existe otra conversión
  de fecha equivalente. Las reglas de firma, normalización, hash y DTO no se
  modificaron.
- Focal 21/21; regresiones PSP 47/47; regresiones de pagos 65/65; suite completa
  420 ejecutadas, 415 aprobadas y 5 omitidas, sin fallos ni errores;
  `compileall` aprobado y Alembic conserva el head único `20260911_02`.
- PostgreSQL no aplica. La corrección queda pendiente de retest independiente.

## 2026-09-12 - Contrato de notificacion Webhook de Mercado Pago

Timestamp: 2026-09-12T18:42:12-03:00
Estado: MERCADOPAGO_WEBHOOK_NOTIFICATION_CONTRACT_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Rama: `feature/mercadopago-webhook-ingress`
Commit base: `73b3fd951315d6f2876b7745347dea04c63b3a64`

- Se agregó un normalizador puro que recibe parámetros de query, headers y
  cuerpo JSON ya decodificado, valida primero la firma y produce el `PSPEvent`
  neutral usado por el inbox.
- El contrato exige estructuras inequívocas, coherencia entre el `data.id`
  firmado y el recurso del cuerpo, `type`, `action`, `live_mode`, timestamps
  con zona y versión `v1`. Proveedor y modo se mapean a `mercadopago` y al
  inverso de `live_mode`, sin interpretar estados financieros.
- El identificador original se conserva; su minúscula se limita al manifiesto
  criptográfico. El hash SHA-256 canónico cubre el contenido validado estable,
  excluye `received_at` y no conserva payload crudo.
- Focal de firma y notificación 20/20; regresiones PSP 46/46; regresiones de
  pagos 65/65; suite completa 419 ejecutadas, 414 aprobadas y 5 omitidas, sin
  fallos ni errores; `compileall` aprobado y Alembic conserva el head único
  `20260911_02`.
- No se agregaron ruta Flask, persistencia, migración, consulta al proveedor,
  procesador, dependencia, credencial ni integración productiva. PostgreSQL no
  aplica a este contrato puro.

## 2026-09-12 - Correccion P2 del parser de x-signature

Timestamp: 2026-09-12T18:20:35-03:00
Estado: MERCADOPAGO_WEBHOOK_SIGNATURE_VALIDATOR_CORREGIDO_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Rama: `feature/mercadopago-webhook-ingress`
Commit base: `08471f76900cde263a7a4590ff77f60751ffd704`

- Se corrigió el hallazgo P2 conservando el `REQUIERE_CORRECCIONES`
  histórico: las claves de cada componente de `x-signature` se normalizan con
  trim y minúsculas antes de almacenarlas o compararlas.
- `ts`/`TS` y `v1`/`V1` representan el mismo componente semántico. Toda
  repetición posterior a esa normalización se rechaza, incluso cuando los
  valores coinciden; nunca se sobrescribe silenciosamente un valor previo.
- Los valores de `ts` y `v1` permanecen sin normalización de casing o contenido,
  fuera del trim estructural ya admitido por el contrato previo.
- Focal 10/10; regresiones PSP 36/36; regresiones de pagos 65/65; suite completa
  409 ejecutadas, 404 aprobadas y 5 omitidas, sin fallos ni errores;
  `compileall` aprobado y Alembic conserva el head único `20260911_02`.
- PostgreSQL no aplica a esta corrección criptográfica pura. Continúan
  pendientes el retest independiente y la futura capa HTTP.

## 2026-09-12 - Verificador de firma Webhook de Mercado Pago

Timestamp: 2026-09-12T16:17:29-03:00
Estado: MERCADOPAGO_WEBHOOK_SIGNATURE_VALIDATOR_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Rama: `feature/mercadopago-webhook-ingress`
Commit base: `08471f76900cde263a7a4590ff77f60751ffd704`
Fuente oficial: [Notificaciones de pago de Mercado Pago](https://www.mercadopago.com.ar/developers/es/docs/checkout-pro-preferences/payment-notifications)

- Se implementó un verificador puro del header `x-signature`: extrae `ts` y
  `v1`, construye el manifiesto oficial y valida HMAC-SHA256 hexadecimal con
  comparación en tiempo constante.
- Conforme a la fuente oficial vigente, `data.id` se convierte a minúsculas
  sólo para el manifiesto; el valor original se conserva fuera del cálculo.
  `x-request-id`, `ts`, secreto y demás componentes no se normalizan.
- Como política local más estricta de MANDOBRA, todos los campos del manifiesto
  y el secreto son obligatorios. Esta decisión fail-closed no se atribuye a
  Mercado Pago y no incorpora una ventana temporal no definida por la fuente.
- Focal 9/9; regresiones PSP 35/35; regresiones de pagos 65/65; suite completa
  408 ejecutadas, 403 aprobadas y 5 omitidas, sin fallos ni errores;
  `compileall` aprobado y Alembic permanece en `20260911_02`.
- No existe todavía ruta Flask, endpoint público, respuesta HTTP, lectura de
  secretos productivos, registro en inbox, SDK ni conexión real con Mercado Pago.

## 2026-09-12 - Integracion post-merge del procesamiento de eventos PSP

Timestamp: 2026-09-12T14:03:46-03:00
Estado: POST_MERGE_PSP_EVENT_PROCESSING_REGISTRADO_PENDIENTE_DE_REVISION_DOCUMENTAL
Agente: Codex - implementador tecnico local
Rama: `develop`
Pull Request: `#12`
Merge commit: `a96a55311283d331c70e49aad3550ec6f7b1a566`

- Se verificó la integración limpia y sin conflictos de la rama
  `feature/psp-event-processing`, compuesta por `f45f32c` (inbox), `9951d25`
  (identidad contextual) y `3c243b5` (procesador de conciliación).
- El merge incorporó 23 archivos, 1996 inserciones y 9 eliminaciones, incluidas
  las migraciones `20260911_01` y `20260911_02`; el head final registrado es
  `20260911_02`.
- La revisión remota final fue `APROBADO_PARA_MERGE`. HEAD, `origin/develop` y
  el árbol remoto coinciden exactamente con el contenido probado.
- Se conserva como evidencia histórica del SHA probado: procesador 9/9;
  procesador, inbox e identidad 26/26; persistencia, orquestación y workflow
  65/65; PostgreSQL 14/14; suite completa 399 ejecutadas, 394 aprobadas y 5
  omitidas; `compileall`, enlaces y `git diff --check` aprobados. Estas pruebas
  no fueron repetidas post-merge.
- La integración aporta infraestructura neutral. No acredita webhook público,
  firmas, HTTP, SDK, OAuth, credenciales, Mercado Pago real, workers, retries,
  QR, checkout, créditos, PRO, ARCA ni producción.

## 2026-09-12 - Correccion P1 de topicos del procesador PSP

Timestamp: 2026-09-12T13:32:58-03:00
Estado: PSP_EVENT_RECONCILIATION_PROCESSOR_CORREGIDO_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Rama: `feature/psp-event-processing`
Commit base: `9951d2503d9b70353ddcd674d6c750cbb2436997`

- El procesador exige una colección explícita, no vacía e inmutable de tópicos
  de pago. Los valores se normalizan con trim y minúsculas; entradas vacías,
  inválidas o una cadena usada como colección se rechazan al configurarlo.
- Un tópico no configurado devuelve `UNSUPPORTED_TOPIC` antes de buscar el
  intento o llamar al adaptador. El tópico sólo decide procesabilidad y nunca
  determina un estado financiero.
- Se reprodujo `merchant_order` con ID coincidente y acción engañosa
  `payment.approved`: cero búsquedas financieras, cero llamadas y pago intacto.
- Focal 9/9; regresiones 26/26 y 65/65; PostgreSQL 14/14; suite completa 399
  ejecutadas, 394 aprobadas y 5 omitidas, sin fallos ni errores.
- El `REQUIERE_CORRECCIONES` histórico se conserva. La corrección queda
  pendiente de retest independiente y no agrega integración PSP productiva.

## 2026-09-12 - Procesador neutral de conciliacion por eventos PSP

Timestamp: 2026-09-12T13:10:46-03:00
Estado: PSP_EVENT_RECONCILIATION_PROCESSOR_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Rama: `feature/psp-event-processing`
Commit base: `9951d2503d9b70353ddcd674d6c750cbb2436997`

- Se agregó un coordinador que usa el evento persistido sólo como señal,
  correlaciona por proveedor, modo e ID externo y consulta una vez al adaptador
  fuera de toda sesión o transacción.
- El estado financiero procede exclusivamente de `PSPAdapter`; eventos
  inexistentes, contextos incompatibles, intentos legacy/sin correlación y
  terminales producen resultados explícitos sin escrituras indebidas.
- La persistencia reutiliza `apply_reconciliation()`, con una segunda
  transacción y lock breve. No se creó migración: `20260911_02` sigue siendo el
  único head.
- Focal 7/7; regresiones 24/24 y 65/65; PostgreSQL 14/14; suite completa 397
  ejecutadas, 392 aprobadas y 5 omitidas, sin fallos ni errores.
- Todavía no existe integración real con Mercado Pago ni endpoint webhook
  productivo; tampoco HTTP, SDK, workers, retries o procesamiento automático.

## 2026-09-11 - Correccion P2/P3 de identidad PSP

Timestamp: 2026-09-11T22:54:46-03:00
Estado: PAYMENT_ATTEMPT_PSP_IDENTITY_CORREGIDA_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Rama: `feature/psp-event-processing`
Commit base: `f45f32ce3c032b6a4b7404886b9c2558cdb5e62a`

- La recuperación concurrente de obligaciones ahora sólo admite SQLSTATE
  `23505` y la constraint exacta `uq_payment_obligations_reference`, obtenidos
  desde atributos estructurados del driver. Cualquier otro diagnóstico vuelve
  a propagar el `IntegrityError` original.
- Se corrigió el whitespace final de la prueba de migración y se comprobaron
  explícitamente todos los archivos no rastreados.
- Focal 14/14; regresiones 82/82; PostgreSQL real 13/13; suite completa 390
  ejecutadas, 385 aprobadas y 5 omitidas, sin fallos ni errores; `compileall` y
  head Alembic único `20260911_02` aprobados.
- Se conserva el `REQUIERE_CORRECCIONES` histórico. La corrección queda
  pendiente de retest independiente; no se implementó el procesador PSP.

## 2026-09-11 - Identidad PSP contextual en intentos de pago

Timestamp: 2026-09-11T22:26:39-03:00
Estado: PAYMENT_ATTEMPT_PSP_IDENTITY_IMPLEMENTADA_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Rama: `feature/psp-event-processing`
Commit base: `f45f32ce3c032b6a4b7404886b9c2558cdb5e62a`

- Se adoptó la decisión `INCORPORAR_IDENTIDAD_PSP_CONTEXTUAL_EN_PAYMENT_ATTEMPTS`:
  proveedor canónico, modo y ID externo forman la identidad contextual.
- La migración `20260911_02`, descendiente de `20260911_01`, agrega contexto
  nullable, constraint de pareja completa e índice único parcial. No atribuye
  contexto a filas históricas ni impone unicidad global al ID externo.
- Los servicios permiten crear/asociar contexto, impiden reemplazarlo y buscan
  exclusivamente por identidad completa. Los intentos legacy quedan excluidos.
- Focal 23/23; regresiones 81/81; PostgreSQL 12/12; suite completa 389
  ejecutadas, 384 aprobadas y 5 omitidas, sin fallos ni errores.
- El bloqueo histórico de correlación se conserva. No se implementó todavía el
  procesador, Mercado Pago real, HTTP, firmas, workers ni lógica financiera.

## 2026-09-11 - Procesador de eventos PSP bloqueado por correlacion

Timestamp: 2026-09-11T22:16:16-03:00
Estado: PSP_EVENT_RECONCILIATION_PROCESSOR_BLOQUEADO_POR_DEFINICION_DE_CORRELACION
Agente: Codex - implementador tecnico local
Rama: `feature/psp-event-processing`
HEAD: `f45f32ce3c032b6a4b7404886b9c2558cdb5e62a`

- El inbox identifica eventos por proveedor, modo e ID externo, pero
  `payment_attempts` sólo conserva `external_attempt_id`: no registra proveedor
  ni modo y ese campo no posee unicidad.
- Una búsqueda global por ID de recurso sería ambigua ante colisiones entre
  proveedores o modos. No se implementó esa asociación insegura ni se creó una
  migración sin contrato aprobado.
- Se requiere definir una identidad PSP completa en el intento o una relación
  explícita evento-intento, incluyendo reglas de alta, unicidad y compatibilidad
  con datos existentes. No se ejecutaron pruebas porque no hubo cambio de código.

## 2026-09-11 - Correccion P1/P2 de la bandeja de eventos PSP

Timestamp: 2026-09-11T20:57:36-03:00
Estado: PSP_EVENT_INBOX_FOUNDATION_CORREGIDA_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Rama: `feature/psp-event-processing`
Commit base: `3b6bc44d0bddfa108b4b18e6d04e23f5c0b34fee`

- Se conserva la revision historica `REQUIERE_CORRECCIONES`. P1 queda corregido:
  una redelivery con distinto `received_at` es replay y conserva sin actualizar
  la fecha de la primera fila. El contenido material estable sigue detectando
  conflictos.
- P2 queda corregido: el DTO acepta SHA-256 hexadecimal y lo normaliza a
  minusculas antes de persistir o comparar; mayusculas/minusculas son el mismo
  digest y un digest diferente continúa siendo conflicto.
- Focal 11/11; regresiones de pagos 75/75; PostgreSQL 3/3; suite completa 383
  ejecutadas, 378 aprobadas y 5 omitidas, sin fallos ni errores. Pendiente de
  retest independiente antes del primer commit.

## 2026-09-11 - Contrato neutral y bandeja persistente de eventos PSP

Timestamp: 2026-09-11T20:09:34-03:00
Estado: PSP_EVENT_INBOX_FOUNDATION_IMPLEMENTADA_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Rama: `feature/psp-event-processing`
Commit base: `3b6bc44d0bddfa108b4b18e6d04e23f5c0b34fee`

- Primer incremento de una rama agrupada; el PR se abrira despues del segundo
  commit. Se registro como antecedente el PR #11, feature `f10616c` y merge
  `3b6bc44`.
- Se agregaron un DTO inmutable de evento PSP normalizado, almacenamiento
  idempotente y consultas por ID interno e identidad externa. No contiene
  estado financiero, firma, headers completos ni payload crudo.
- Migracion `20260911_01`, descendiente de `20260910_01`, con tabla
  `psp_event_inbox` e identidad proveedor/modo/ID externo.
- Focal: 9/9; regresiones de pagos: 73/73; PostgreSQL real: 3/3; suite completa:
  381 ejecutadas, 376 aprobadas y 5 omitidas, sin fallos ni errores.
- No se implementaron endpoint, firma, HTTP, Mercado Pago, procesamiento,
  workers, creditos, PRO, ARCA ni interfaz.

## 2026-09-11 - Workflow persistente de pagos con semantica de incertidumbre aprobada

Timestamp: 2026-09-11T19:22:09-03:00
Estado: PERSISTENT_PAYMENT_WORKFLOW_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Rama: `feature/persistent-payment-workflow`
Commit base: `dfbb7e3f53e61638eb52113286870eca1b59d031`

- La definicion inicial que exigia representar una respuesta incierta como
  `PENDING` fue reemplazada, tras contrastarla con el esquema vigente y la
  semantica del dominio. La incertidumbre de transporte persiste con
  `financial_status=NULL`, resultado `RECONCILIATION_REQUIRED`, conciliacion
  requerida e identificador externo opcional.
- `PENDING` queda reservado para una respuesta autoritativa del PSP. La
  conciliacion explicita desde estado financiero desconocido admite
  `PENDING`, `APPROVED` o `REJECTED` sin interpretar la incertidumbre como
  rechazo o aprobacion.
- Focal del workflow: 13/13. Focal mas regresiones de persistencia,
  orquestacion, contrato/simulador y guard: 68/68. Gate PostgreSQL: 10/10 en
  `trax_payment_persistence_test_workflow_contract_20260911`. Suite completa:
  372 ejecutadas, 367 aprobadas, 5 omisiones historicas, 0 fallos y 0 errores.
  `compileall`, head Alembic unico `20260910_01`, enlaces relativos y
  `git diff --check`: aprobados.
- La base PostgreSQL descartable quedo en cero tablas, fue eliminada y su
  ausencia se confirmo. No se creo ni modifico una migracion.
- Permanecen fuera de alcance Mercado Pago, HTTP, webhooks, checkout,
  creditos, PRO, ARCA, interfaz, dependencias y procesamiento automatico.

## 2026-09-11 - Workflow persistente de pagos, avance bloqueado por contrato de estado

Timestamp: 2026-09-11T19:09:43-03:00
Estado: PERSISTENT_PAYMENT_WORKFLOW_BLOQUEADO_POR_DEFINICION_DE_ESTADO_INCIERTO
Agente: Codex - implementador tecnico local
Rama: `feature/persistent-payment-workflow`
Commit base: `dfbb7e3f53e61638eb52113286870eca1b59d031`

- Se implemento un coordinador de aplicacion con una transaccion breve para
  confirmar la obligacion, llamada neutral fuera de sesion activa y una segunda
  transaccion atomica para persistir el resultado.
- Incluye replay sin nueva llamada, conflicto previo al adaptador, reanudacion
  tras fallos, conciliacion explicita por ID o replay y ausencia de retries.
- Focal y regresiones: 67/67. Gate PostgreSQL: 10/10 en una base descartable
  eliminada. Suite completa: 371 ejecutadas, 366 aprobadas, 5 omisiones
  historicas, 0 fallos y 0 errores. `compileall` y head Alembic
  `20260910_01`: aprobados.
- Bloqueo: el nuevo alcance pide persistir incertidumbre con estado financiero
  `PENDING`, pero el esquema vigente `20260910_01` exige
  `financial_status IS NULL` cuando el resultado es
  `RECONCILIATION_REQUIRED`. No se altero la migracion sin autorizacion; el
  flujo conserva temporalmente la representacion canónica integrada (`NULL`).
- No se conectaron Mercado Pago, HTTP, webhooks, checkout, creditos, PRO, ARCA
  ni componentes productivos.

## 2026-09-11 - Integracion de la persistencia neutral de pagos

Timestamp: 2026-09-11T15:46:40-03:00
Estado: PAYMENT_PERSISTENCE_FOUNDATION_INTEGRADA_Y_VERIFICADA_POST_MERGE
Agente: Codex - implementador tecnico local
Rama: `develop`
Commit de caracteristica: `fae81e62f1526a0daa229f03efbc19c918dc8ff0`
Merge commit / HEAD: `8dd773692004453d663742be02048f79cae0aa0c`
Pull Request: `#10`

- Se verifico la integracion de los 14 archivos del incremento y el head
  Alembic `20260910_01`. `develop` local y `origin/develop` coinciden en el
  merge commit y el arbol previo a este registro estaba limpio.
- Desviacion de proceso: el PR fue fusionado antes de completar el gate final
  solicitado, por lo que Testing no pudo emitir una autorizacion preventiva de
  merge. Se conservo la integracion y no se inicio una reversion porque la
  verificacion post-merge confirmo que el contenido remoto coincide exactamente
  con el commit previamente probado y aprobado, sin diferencias de alcance ni
  defectos funcionales detectados. Es una observacion de proceso, no una
  regresion del codigo.
- No se repitieron pruebas post-merge. La evidencia historica del commit
  identificado permanece: focal y regresiones 55/55; PostgreSQL real 7/7;
  suite completa 359 ejecutadas, 354 aprobadas y 5 omisiones historicas, sin
  fallos ni errores; `compileall`, enlaces y `git diff --check` aprobados; base
  descartable eliminada y `trax_db` intacta.
- La integracion no acredita Mercado Pago, pagos productivos, webhooks,
  checkout, creditos, PRO, ARCA, deploy ni la arquitectura 2.0 completa.

## 2026-09-11 - Correccion focal de integridad en intentos de pago

Timestamp: 2026-09-11T14:41:40-03:00
Estado: PAYMENT_PERSISTENCE_FOUNDATION_CORREGIDA_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Rama: `feature/payment-persistence-foundation`
Commit base: `c78c5176cf3c43cdbab673454fc6a625b1b3c0fa`

- Se corrigio el P2 de la revision independiente: el replay de intentos se
  recupera exclusivamente ante SQLSTATE `23505` y la constraint estructurada
  `uq_payment_attempts_idempotency_key`.
- Violaciones FK, checks u otras constraints conservan el `IntegrityError`
  original; no se transforman en `NoResultFound`.
- Regresion PostgreSQL: el FK inexistente expone `23503` y
  `fk_payment_attempts_obligation`, no deja escritura parcial y permite
  reutilizar la sesion tras el rollback del llamador.
- Focal: 55/55. Gate PostgreSQL: 7/7. Suite completa: 359 ejecutadas, 354
  aprobadas, 5 omisiones historicas, 0 fallos y 0 errores. `compileall` y head
  Alembic `20260910_01`: aprobados.
- La correccion no modifica esquema, migracion, contrato PSP, simulador,
  orquestacion o interfaz. No acredita Mercado Pago, webhooks, produccion ni el
  diseño general 2.0.

## 2026-09-11 - Base de persistencia neutral de pagos

Timestamp: 2026-09-11T14:00:30-03:00
Estado: PAYMENT_PERSISTENCE_FOUNDATION_IMPLEMENTADA_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Dispositivo: laptop / Codex Desktop local
Rama: `feature/payment-persistence-foundation`
Commit base: `c78c5176cf3c43cdbab673454fc6a625b1b3c0fa`

- Se registraron dos modelos neutrales: obligaciones monetarias e intentos de
  pago, con `NUMERIC` sin precision o escala impuesta, claves unicas, FK
  `RESTRICT` y constraints de dominio/coherencia.
- La migracion `20260910_01`, descendiente de `20260904_01`, crea y elimina las
  tablas en orden seguro sin backfills ni cambios sobre datos existentes.
- El servicio usa una sesion explicita, `flush()` y transacciones controladas
  por el llamador; implementa replay, conflictos y conciliaciones permitidas
  sin llamar a un PSP ni ejecutar commits internos.
- Focal portable y regresiones PSP/orquestador: 55/55. Gate PostgreSQL real:
  6/6 en una base reservada descartable. Suite completa: 359 ejecutadas, 354
  aprobadas, 5 omisiones historicas, 0 fallos y 0 errores. `compileall` y head
  Alembic `20260910_01`: aprobados.
- PR #9 fue integrado mediante
  `c78c5176cf3c43cdbab673454fc6a625b1b3c0fa`. Este incremento no conecta
  Mercado Pago ni acredita checkout, webhooks, creditos, PRO, ARCA o una
  arquitectura 2.0 integral, que permanece `PROPUESTO_NO_APROBADO`.

## 2026-09-10 - Interfaz interna del simulador de pagos

Timestamp: 2026-09-10T21:46:04-03:00
Estado: PAYMENT_ORCHESTRATION_AND_SIMULATOR_UI_APROBADOS_PARA_COMMIT_Y_PR
Agente: Codex - implementador tecnico y frontend local
Dispositivo: laptop / Codex Desktop local
Rama: `feature/payment-orchestration-in-memory`
Commit base observado: `a4951a27f0f0bef5fa834ad25159abfc875ec59e`
Revision independiente: `APROBADO_PARA_SEGUNDO_COMMIT_Y_PR` del
`2026-09-10T22:02:38-03:00`; hallazgos P0-P3: ninguno.

- Se agrego `/dev/qa/payments/simulator` dentro del blueprint de desarrollo,
  protegido por ambiente y `ENABLE_DEV_QA_PANEL`; produccion no registra la
  ruta y el estado deshabilitado responde 404.
- La pantalla compone por solicitud un simulador aislado y el orquestador
  neutral para visualizar aprobado, rechazado, pendiente o conciliacion
  requerida. No conserva historial ni modifica datos.
- Usa componentes y tokens del Design System v2, formulario semantico,
  mensajes accesibles, `aria-live` y composicion responsive sin JavaScript
  propio.
- Focal interfaz + orquestador: 29/29; contrato/simulador: 24/24. Suite
  completa: 347 ejecutadas, 342 aprobadas, 5 omisiones historicas, 0 fallos y
  0 errores. `compileall`, HTML, enlaces y `git diff --check`: aprobados.
- QA visual aprobada en claro/oscuro, movil/desktop y teclado. PostgreSQL no
  aplica.
- No es checkout ni mueve dinero. Mercado Pago, persistencia, webhooks,
  creditos, PRO y revision juridica/contable siguen fuera de alcance; el
  diseño 2.0 permanece `PROPUESTO_NO_APROBADO`.

## 2026-09-10 - Orquestacion neutral de pagos en memoria

Timestamp: 2026-09-10T21:23:10-03:00
Estado: PAYMENT_ORCHESTRATION_IN_MEMORY_IMPLEMENTADA_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Dispositivo: laptop / Codex Desktop local
Rama: `feature/payment-orchestration-in-memory`
Commit base: `e7ec86f217ebbbd836f7434092041e6abefbbe4a`

- Se agrego una obligacion monetaria inmutable y un orquestador que depende
  exclusivamente de `PSPAdapter`, sin almacenamiento propio.
- Los resultados distinguen aprobacion, rechazo, pendiente financiero y
  conciliacion requerida por incertidumbre de transporte.
- La conciliacion explicita consulta por ID conocido o repite idempotentemente
  la misma creacion cuando el proveedor no entrego ID; no existen reintentos
  automaticos, esperas ni identificadores inventados.
- Focal del orquestador: 19/19. Focal PSP: 24/24. Suite completa Docker: 337
  ejecutadas, 332 aprobadas, 5 omitidas, 0 fallos y 0 errores. `compileall`:
  aprobado.
- Sin PostgreSQL, persistencia, modelos, migraciones, rutas, HTTP, SDK,
  webhooks o integracion productiva. Mercado Pago y revision juridica/contable
  continuan pendientes; el diseño 2.0 permanece `PROPUESTO_NO_APROBADO`.

## 2026-09-10 - Validacion local post-merge del contrato neutral PSP

Timestamp: 2026-09-10T13:42:55-03:00
Estado: PSP_ADAPTER_CONTRACT_INTEGRADO_POST_MERGE_VALIDADO_LOCALMENTE_PENDIENTE_DE_REVISION_DOCUMENTAL
Agente: Codex - implementador tecnico local
Rama: `develop`
Base previa: `2e7de49dfde6c20bc798089139ea235534ea0a75`
PR: #8
Merge validado: `f9c0e394af413cfcb0c1aa8142a85af16ad3729b`

- Se verifico que `develop` y `origin/develop` apuntan al merge de PR #8 y
  que su segundo padre es el commit correctivo
  `8f709e64149d7dfbdeb9c2e1a319f7134ae6f0f4`.
- Alcance integrado: contrato PSP neutral, DTO y estados inmutables, errores
  diferenciados, ID opcional ante incertidumbre, simulador determinista en
  memoria, controlador FIFO e idempotencia con consulta posterior.
- Focal: 24/24 aprobadas. Suite completa Docker: 318 ejecutadas, 313
  aprobadas, 5 omitidas, 0 fallos y 0 errores. `compileall`, enlaces relativos
  y `git diff --check`: aprobados.
- PostgreSQL no fue ejecutado porque no aplica. No se acreditan persistencia,
  concurrencia o atomicidad PostgreSQL, autenticidad u orden de webhooks ni
  viabilidad tecnica, contractual o comercial de un PSP.
- No se integraron Mercado Pago, ARCA, SDK, HTTP ni flujos productivos. El
  diseño 2.0 permanece `PROPUESTO_NO_APROBADO`; Mercado Pago y la revision
  juridica/contable continuan pendientes.

## 2026-09-09 - Correccion P2 de determinismo del simulador PSP

Timestamp: 2026-09-09T20:42:09-03:00
Estado: PSP_ADAPTER_CONTRACT_P2_CORREGIDO_PR_ACTUALIZADO_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Rama: `feature/psp-adapter-contract`
PR: #8
Commit observado: `64eed3fdbf16ff55f7994b246a87b514a41a31bb`

- P2: la ausencia de escenario permitia invocar antes la fabrica de IDs y el
  reloj, avanzando dependencias con estado pese a no crear un intento.
- Se agrego inspeccion no destructiva de la cola; el escenario se confirma y
  consume solo despues de validar ID y reloj, inmediatamente antes de almacenar.
- ID duplicado, reloj invalido, validacion, replay, conflicto y consulta no
  consumen escenarios; una creacion valida consume exactamente uno.
- Focal: 24/24. Suite completa Docker: 318/318 ejecutadas, 313 aprobadas,
  5 omisiones historicas, 0 fallos y 0 errores. `compileall`, enlaces relativos
  y `git diff --check`: aprobados.
- PostgreSQL no aplica. Persistencia, HTTP, SDK, webhooks, Mercado Pago, ARCA e
  integracion productiva permanecen fuera de alcance. PR #8 no aprobado para
  merge; requiere retest independiente.

## 2026-09-09 - Retest aprobado del contrato neutral PSP

Timestamp: 2026-09-09T20:23:34-03:00
Estado: PSP_ADAPTER_CONTRACT_APROBADO_PARA_COMMIT
Agente: Codex - ejecutor de integracion autorizado
Rama: `feature/psp-adapter-contract`
Commit base: `2e7de49dfde6c20bc798089139ea235534ea0a75`
Retest independiente: `APROBADO_PARA_COMMIT` del
`2026-09-09T20:14:06-03:00`

- P1 y P3: `RESUELTO`; hallazgos actuales P0-P3: ninguno.
- Focal: 22/22. Suite completa: 311/316, con 5 omisiones historicas,
  0 fallos y 0 errores.
- `compileall`, enlaces relativos y `git diff --check`: aprobados.
- PostgreSQL no fue ejecutado ni acreditado porque no aplica al incremento
  exclusivamente en memoria.
- Persistencia, webhooks, Mercado Pago, ARCA e integracion productiva siguen
  fuera de alcance. El diseño general 2.0 continua `PROPUESTO_NO_APROBADO`.
- Commit, push y PR permanecen pendientes en este registro.

## 2026-09-09 - Correcciones P1/P3 del contrato neutral PSP

Timestamp: 2026-09-09T20:01:57-03:00
Estado: PSP_ADAPTER_CONTRACT_CORREGIDO_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: 02 - Implementacion - Builder
Rama: `feature/psp-adapter-contract`
Commit base: `2e7de49dfde6c20bc798089139ea235534ea0a75`
Revision independiente: `REQUIERE_CORRECCIONES`, emitida el
`2026-09-09T19:53:36-03:00`

- P1 corregido: `UncertainResponseError.attempt_id` es opcional, usa `None`
  cuando el adaptador no conoce un ID y conserva exactamente cualquier ID opaco
  valido. El simulador sigue adjuntando el suyo porque crea el intento.
- La conciliacion sin ID externo puede continuar mediante la clave idempotente
  conocida por el llamador; no se inventan identificadores.
- P3 corregido: pruebas AST cubren imports de contrato y simulador, las
  reexportaciones historicas se verifican por identidad, `enqueue` se prueba en
  orden, aislamiento y rechazo atomico, y los errores neutrales se distinguen
  mediante comportamientos observables.
- Focal: 22/22. Suite completa Docker: 311/316, con 5 omisiones historicas,
  0 fallos y 0 errores. `compileall`, enlaces y `git diff --check`: aprobados.
- Persistencia, PostgreSQL, HTTP, SDK, webhooks, Mercado Pago, ARCA e
  integracion productiva permanecen fuera de alcance. El diseño 2.0 continua
  `PROPUESTO_NO_APROBADO`.

## 2026-09-08 - Contrato neutral PSP y control separado de escenarios

Timestamp: 2026-09-08T23:01:15-03:00
Estado: PSP_ADAPTER_CONTRACT_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: 02 - Implementacion - Builder
Rama: `feature/psp-adapter-contract`
Commit base: `2e7de49dfde6c20bc798089139ea235534ea0a75`

- Se agrego un contrato PSP neutral con `Protocol`, intento inmutable, tres
  estados financieros y errores neutrales diferenciables.
- `create_attempt` ya no recibe resultados artificiales. El simulador consume
  escenarios deterministas desde un controlador FIFO separado y local a cada
  instancia; validaciones, replay y conflictos no consumen escenarios.
- En el simulador, la incertidumbre conserva un intento `PENDING`, informa el
  identificador que conoce y permite consulta y replay sin duplicacion. El
  contrato neutral no exige que todo adaptador disponga de ese identificador.
- Pruebas focales: 17/17 aprobadas. Suite completa Docker: 306/311 aprobadas,
  5 omisiones historicas, 0 fallos y 0 errores. `compileall`, enlaces relativos
  y `git diff --check`: aprobados.
- No se agregaron dependencias, persistencia, PostgreSQL, HTTP, SDK, webhooks ni
  integraciones productivas. El diseño 2.0 continua `PROPUESTO_NO_APROBADO`;
  Mercado Pago, ARCA y revision juridica/contable permanecen pendientes.

## 2026-09-08 - Integracion del simulador PSP en memoria

Timestamp: 2026-09-08T22:40:33-03:00
Estado: SIMULADOR_PSP_EN_MEMORIA_INTEGRADO
Agente: Codex - ejecutor de integracion autorizado
Rama: `develop`
Commit del simulador: `50babd206369d47d68765e0dbf0fd3f2f42c21d0`
Hash remoto observado: `50babd206369d47d68765e0dbf0fd3f2f42c21d0`

- El commit `feat: add deterministic in-memory PSP simulator` fue publicado
  mediante push normal a `origin/develop`.
- Validaciones: focal 21/21; suite completa 310/315 con 5 omisiones historicas,
  0 fallos y 0 errores; `compileall`, enlaces y `git diff --check` aprobados.
- Integrado refiere unicamente al simulador aislado y sus pruebas; no esta
  conectado a flujos productivos.
- No se acreditan persistencia, concurrencia o atomicidad PostgreSQL,
  autenticidad de webhooks ni viabilidad PSP. Mercado Pago, ARCA y revision
  juridica/contable continúan pendientes, y el diseño general 2.0 permanece
  `PROPUESTO_NO_APROBADO`.

## 2026-09-08 - Aprobacion independiente del simulador PSP

Timestamp: 2026-09-08T22:37:42-03:00
Estado: SIMULADOR_PSP_EN_MEMORIA_APROBADO_PARA_COMMIT
Agente: Codex - revisor tecnico y funcional independiente
Rama y commit base: `develop` en
`1e85c6e592f970b2640a1e71d5b9a7019f8b3383`

- La revision independiente del `2026-09-08T22:28:13-03:00` emitio
  `APROBADO_PARA_COMMIT`, sin hallazgos P0, P1, P2 ni P3.
- Focal: 21/21 aprobadas. Suite completa en Docker: 310/315 aprobadas,
  5 omisiones historicas, 0 fallos y 0 errores.
- `compileall`, enlaces relativos y `git diff --check`: aprobados.
- La evidencia no acredita persistencia, concurrencia o atomicidad PostgreSQL,
  autenticidad de webhooks ni viabilidad de Mercado Pago; tampoco implementa o
  valida ARCA. El diseño general 2.0 continua `PROPUESTO_NO_APROBADO`.
- Commit, push e integracion permanecen pendientes en este registro.

## 2026-09-08 - Reanudacion y revalidacion del simulador PSP

Timestamp: 2026-09-08T21:46:39-03:00
Estado: SIMULADOR_PSP_EN_MEMORIA_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: 02 - Implementacion - Builder
Rama y commit base: `develop` en
`1e85c6e592f970b2640a1e71d5b9a7019f8b3383`

- Se inspecciono y conservo el trabajo local previo del mismo incremento; no
  requirio correcciones funcionales.
- Pruebas focales repetidas: 21 ejecutadas, 21 aprobadas, 0 fallidas y 0
  omitidas. `compileall` volvio a aprobar.
- La suite completa repitio la limitacion de entorno: 54 pruebas descubiertas,
  21 aprobadas, 0 fallos de asercion, 33 errores de importacion y 0 omitidas por
  ausencia de Flask, SQLAlchemy, Alembic y Werkzeug en el runtime disponible.
- No se instalaron dependencias ni se uso Docker. Los limites y exclusiones
  registrados el `2026-09-07T22:40:12-03:00` permanecen vigentes.

## 2026-09-07 - Simulador PSP determinista en memoria

Timestamp: 2026-09-07T22:40:12-03:00
Estado: SIMULADOR_PSP_EN_MEMORIA_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: 02 - Implementacion - Builder
Rama y commit base: `develop` en
`1e85c6e592f970b2640a1e71d5b9a7019f8b3383`

- Se agrego un simulador PSP generico, determinista y aislado por instancia,
  con intentos inmutables, importes `Decimal`, idempotencia canonica, estados
  configurables y respuesta incierta separada del estado almacenado.
- No se integro con rutas, modelos, bases, entitlement, contratos, creditos,
  suscripciones, webhooks ni proveedores externos.
- Pruebas focales: 21 ejecutadas, 21 aprobadas, 0 fallidas y 0 omitidas.
- Suite completa con el Python incluido en Codex Desktop: 54 descubiertas, 21
  aprobadas, 0 fallos de asercion, 33 errores de importacion y 0 omitidas. La
  causa es la ausencia de Flask, SQLAlchemy, Alembic y Werkzeug en ese runtime;
  no se instalaron dependencias ni se uso Docker.
- `compileall`, enlaces relativos y `git diff --check`: aprobados.
- Estas pruebas no acreditan persistencia, atomicidad o concurrencia
  PostgreSQL, autenticidad, entrega u orden de webhooks, ni viabilidad tecnica,
  contractual o comercial de Mercado Pago. No seleccionan proveedor ni
  arquitectura productiva.

## 2026-09-07 - Cierre documental de Sprint 1 PRO

Timestamp: 2026-09-07T21:54:36-03:00
Estado: CERRADO_DOCUMENTALMENTE_INTEGRACION_GIT_PENDIENTE
Agente: 01 - Documentation Engineer
Rama y commit observados: `develop` en
`1d22f87adc358eae20121ea727142b0276cf337e`

- La revision independiente del Agente 02, emitida el
  `2026-09-07T21:41:54-03:00`, no encontro hallazgos, aprobo el diff para commit
  y considero satisfechos los criterios documentales de cierre.
- Sprint 1 queda `CERRADO_DOCUMENTALMENTE`, con staging, commit e integracion
  Git pendientes de autorizacion y ejecucion separadas.
- Mercado Pago, la revision juridica/contable y la aclaracion de la estimacion
  de 25-43 horas permanecen como pendientes selectivos.
- El diseño 2.0 permanece `PROPUESTO_NO_APROBADO`; su implementacion no esta
  autorizada.
- La referencia a la ausencia de reviews nativas de GitHub conserva su
  atribucion al informe disponible y no se presenta como verificacion propia.

## 2026-09-07 - Preparacion del cierre documental de Sprint 1 PRO

Timestamp: 2026-09-07T21:31:53-03:00
Estado: LISTO_PARA_REVISION_DE_DIFF
Agente: 01 - Documentation Engineer
Rama y commit observados: `develop` en
`1d22f87adc358eae20121ea727142b0276cf337e`
Motivo: actualizar la trazabilidad posterior al merge de PR #7 y preparar, sin
aprobar, el cierre documental de Sprint 1.

- Git local confirma que PR #7 integro el commit documental `817fb4f` mediante
  el merge `1d22f87`, fechado `2026-09-06T20:11:47-03:00`.
- Se recupero el `APROBADO_PARA_COMMIT` informado en la conversacion de
  revision focalizada previa. Se registra como evidencia conversacional,
  distinta de una review nativa de GitHub; el informe del Agente 02 indico que
  PR #7 no registra reviews nativas.
- Se agregaron responsables propuestos, sin presentarlos como asignaciones
  aceptadas, y bloqueos especificos para PSP, creditos, suscripcion y
  facturacion.
- Se registraron como `PROPUESTO_NO_APROBADO` las correcciones del diseño 2.0
  sobre pago mixto versus cobertura total con creditos, atomicidad interna,
  unicidad por obligacion/periodo e importe y consumo parcial por lote.
- El rango de 25-43 horas queda pendiente de aclarar como total o restante y
  de mapear contra entregables; no se genero una nueva estimacion.
- Mercado Pago y la revision juridica/contable siguen pendientes. No se
  implemento ni aprobo arquitectura, integracion, modelo o migracion.
- Tests de aplicacion: NO EJECUTADOS - alcance exclusivamente documental.
- Cierre de Sprint 1: PENDIENTE de revision del presente diff.

## 2026-09-06 - Refinamiento comercial PRO, PSP y expediente juridico

Timestamp: 2026-09-06T19:22:08-03:00
Estado: DOCUMENTACION_CONSOLIDADA_PENDIENTE_DE_REVISION
Responsable de producto: Cristian Sánchez
Agente: 01 - Documentation Engineer
Rama: `docs/pro-commercial-psp-refinement`
Commit base observado: `1548935`

### Consolidado

- Se registro el cierre post-merge de PR #5: merge `1548935`, resultado
  informado `APROBADO_POST_MERGE`, suite 294/289/0/5, Alembic `20260904_01`,
  sin P0/P1 y con `trax_db` preservada.
- REQ-001 reemplaza prospectivamente la regla de 60 dias por operacion con
  lotes de creditos de 40 dias y un umbral para periodos transaccionales de 30
  dias. La regla anterior se conserva como historia.
- Se documentaron periodos de suscripcion de 30 dias, pagos total/parcial con
  creditos, prueba inicial, gracia de 10 dias y transiciones, sin declararlos
  implementados.
- Se incorporaron el [expediente Mercado Pago](CONSULTAS/MERCADO_PAGO_v0_1.md)
  y la [base juridica/contable](LEGAL/BASE_REVISION_JURIDICA_v0_2.md) como
  borradores pendientes, no enviados y sin valor de dictamen.
- Se documento la secuencia PRO de tres sprints sin reiniciar la numeracion
  historica ni agregar ARCA/IA al Sprint 3.

### Limites

- No se eligio producto/API, Split, arquitectura PSP, integracion fiscal,
  proveedor de IA, precio, porcentaje ni formula economica.
- No se modificaron codigo, migraciones, tests, configuracion o bases.
- Tests de aplicacion: NO EJECUTADOS - alcance exclusivamente documental.

### Correccion posterior a revision focalizada

Timestamp: 2026-09-06T19:38:40-03:00
Estado: CORRECCIONES_DOCUMENTALES_LISTAS_PARA_REVISION

- REQ-001 distingue trabajo externo pagado mediante MANDOBRA de pagos fuera de
  la plataforma; solo estos ultimos y el efectivo quedan sin creditos.
- Se consolidaron reserva sin consumo, consumo tras pago completo, liberacion,
  vencimiento, conciliacion y reintentos de pagos mixtos.
- Se incorporaron tarjeta vinculada, contrato del switch de renovacion,
  responsabilidad sistemica contra duplicados y presentacion economica previa.
- Se explicitaron la obligacion unica de pago para contratos internos y el
  efectivo configurable sin creditos.
- Master Spec retiro la referencia vigente ambigua a “extensiones”.
- Esta correccion no esta aprobada todavia; queda lista para revision focalizada.

## 2026-09-05 - Correccion responsive y teclado en admin usuarios

Timestamp: 2026-09-05T20:27:36-03:00
Estado: CORRECCION_IMPLEMENTADA_VALIDADA_LOCALMENTE_PENDIENTE_RETESTING_QA
Rama: `feature/pro-entitlement-foundation`
Commit base: `fe048c4810cc337dfd1c3498d9f96579453cd065`

- Causa raiz: la tabla era su propio contenedor de overflow solo bajo 820px;
  su ancho minimo ampliaba el documento en desktop y no existia una region
  focalizable que gestionara el desplazamiento al navegar por teclado.
- Se incorporo un wrapper exclusivo de admin usuarios con region accesible,
  nombre, foco, overflow horizontal local y scroll padding mediante tokens.
  La tabla conserva semantica nativa, ocho columnas y todos sus controles.
- Implementacion valido en 1440x900 y 390x844, claro y oscuro: el ancho del
  documento no supera el viewport, la tabla mantiene scroll interno y
  `Suspender` queda dentro del viewport y del wrapper al recibir foco por Tab.
  No hubo errores de consola ni respuestas 500.
- Focal Design System/Admin/PRO: 30/30 PASS. Suite completa: 294 ejecutados,
  289 aprobados, 5 omitidos y 0 fallidos. `compileall`, Alembic head
  `20260904_01` y `git diff --check`: PASS.
- Playwright y axe-core no estan versionados y no se instalaron. Propuesta
  pendiente de autorizacion: `@playwright/test@1.62.1` y
  `@axe-core/playwright@4.13.0`, con `package.json`, lock, configuracion y un
  spec E2E focal; ejecucion mediante `npx playwright test`.
- El P1/P2/P3 visual requiere retesting independiente en 05 - QA funcional.
  El PR #5 permanece bloqueado para merge hasta ese resultado.

## 2026-09-05 - Correccion focal de contraste oscuro en PRO

Timestamp: 2026-09-05T19:45:29-03:00
Estado: CORRECCION_IMPLEMENTADA_VALIDADA_LOCALMENTE_PENDIENTE_RETESTING_QA
Rama: `feature/pro-entitlement-foundation`
Commit base: `f35797a1852e4b0293b1618ac03fdbbdba0510ae`

- Se reemplazaron fondos, bordes y textos blancos heredados por tokens
  canonicos del Design System v2, con alcance limitado a la pantalla de
  upgrade PRO y a la gestion administrativa de usuarios.
- Se agrego una clase de alcance a la pantalla administrativa y un test de
  regresion que exige los tokens de tema en ambas superficies.
- Implementacion realizo la medicion visual claro/oscuro: contraste principal
  de 17.74:1 en claro y 16.98:1
  en oscuro; texto secundario de 6.93:1 en oscuro. Las vistas moviles de
  390x844 no presentan desbordamiento de documento.
- Implementacion comprobo la revocacion mediante la ruta administrativa real:
  el profesional quedo en WORK y la pantalla de upgrade lo mostro como
  Elegible, sin errores de consola. La prueba uso una base SQLite efimera;
  `trax_db` no fue modificada.
- Validacion focal: 30/30. Suite completa: 294 ejecutados, 289 aprobados,
  5 omitidos y 0 fallidos. `compileall`, Alembic head `20260904_01` y
  `git diff --check`: PASS.
- El P1 requiere retesting independiente en 05 - QA funcional. El PR #5
  permanece bloqueado para merge hasta obtener ese resultado.

## 2026-09-04 - Fundacion del entitlement PRO

Timestamp: 2026-09-04T09:56:46-03:00
Estado: IMPLEMENTACION_PARCIAL_VALIDADA
Rama: `feature/pro-entitlement-foundation`
Commit base: `18e46fd6bf6d05b73884b7ba3fdbb335f66d7d7e`

- Se centralizo el acceso PRO con elegibilidad profesional, fuente reconocida,
  vencimiento obligatorio y politica UTC.
- Se agrego `subscriptions.source_type` mediante Alembic `20260904_01`, sin
  convertir ni borrar registros legacy.
- Se deshabilitaron concesiones por puntos, verificacion aislada y acciones
  manuales profesional/administrativa.
- El seed QA conserva un unico PRO temporal y sigue bloqueado en produccion.
- PSP, pagos, Facturacion, ARCA, IA y ENTERPRISE operativo no se implementaron.
- Decision: [ADR-001](ADR/ADR-001-pro-entitlement-foundation.md).

## 2026-09-03 - Especificacion de PRO y Facturacion MVP

Timestamp: 2026-09-03T21:47:10-03:00
Estado: DOCUMENTACION_APROBADA_IMPLEMENTACION_PENDIENTE
Documento: requisitos de PRO y Facturacion MANDOBRA MVP
Motivo: formalizar por separado la activacion y vigencia PRO y el beneficio
opcional de Facturacion PRO MVP.
Responsable: Cristian Sánchez
Rama: `docs/spec-pro-facturacion-mvp`
Commit base: `e0eed2`

### Agregado

- Se creo [REQ-001](REQUISITOS/REQ-001-activacion-y-vigencia-pro.md) para el
  catalogo `FREE`, `PRO`, `ENTERPRISE`, la elegibilidad profesional y las
  modalidades transaccional y por suscripcion del mismo entitlement PRO.
- Se creo [REQ-002](REQUISITOS/REQ-002-facturacion-pro-mvp.md) para el modulo
  opcional de Facturacion, limitado en el MVP a persona humana, monotributo
  activo y Factura C.

### Aclarado

- `Plus` no pertenece al catalogo aprobado y los puntos legacy no determinan
  elegibilidad PRO.
- Facturacion no activa PRO y exige entitlement vigente para nuevas emisiones.
- `ENTERPRISE` permanece conceptual y no autoriza crear el actor `EMPRESA`.
- Proveedores PSP, integracion ARCA, custodia de credenciales, modelos e IA
  permanecen pendientes de evaluacion y decisiones posteriores.

### Trazabilidad

- Se actualizaron Master Spec, Roadmap, Backlog, indice documental e indice de
  requisitos sin declarar capacidades implementadas.
- Tests de aplicacion: NO EJECUTADOS - no aplican al alcance documental.

## 2026-09-02 - Consolidacion documental de trazabilidad

Timestamp: 2026-09-02T21:18:48-03:00
Estado: DOCUMENTACION_VALIDADA
Documento: documentacion canonica de MANDOBRA
Motivo: registrar el contraste estatico de `develop` contra Master Spec,
decisiones, Roadmap y Backlog.
Evidencia: rama `docs/documentation-traceability-consolidation`, commit base
`f63c8db` y auditoria tecnica del 2026-09-02.
Responsable: Codex / Documentation Engineer Senior
Rama: `docs/documentation-traceability-consolidation`
Commit base: `f63c8db`

### Aclarado

- El check de Emergencias cubre solicitud y directorio, no asignacion
  persistente, resolucion operativa completa ni contrato `EMERGENCY`.
- Design System v2 es la capa canonica, pero la migracion visual total sigue
  pendiente.
- La ausencia de P0/P1/P2 documentada corresponde al cierre historico de
  Sprint 7 y no acredita preparacion productiva general.

### Trazabilidad

- Se registro una revision posterior del Master Spec sin alterar su revision
  historica `d07d95`.
- Se incorporo la auditoria tecnica estatica de `f63c8db` al indice.
- Se consolidaron pendientes de Planes/PRO, Emergencias, cobertura de pruebas
  e identificadores internos TRAX sin convertirlos en requisitos aprobados.
- Se eliminaron duplicados no rastreados bajo `docs/RUNBOOKS/` despues de
  verificar contenido y preservar las fuentes canonicas en
  `docs/DECISIONES_ARQUITECTURA.md` y `docs/PLANTILLAS/`.
- Tests de aplicacion: NO EJECUTADOS - no aplican al alcance documental.

## 2026-08-04 - Sprint 7 Contractual Trust Fases 2E-2F (cierre aprobado)

Estado: la auditoría independiente de integración fue aprobada. Sprint 7 está
técnicamente cerrado y aprobado para PR hacia `develop`. Esta aprobación no
autoriza publicación ni despliegue productivo.

### Agregado

- Se vincularon las reviews nuevas a un único `ContractRequest` confirmado.
- Se agregó `create_contract_review()` como operación cerrada, atómica e idempotente.
- Se agregó `ReputationEvent` neutral con rating observado y `puntos = NULL`.
- Se agregaron visibilidad pública separada, elegibilidad del rating y moderación cerrada.
- Se agregó la migración Alembic `20260726_06` con constraints y triggers físicos para reviews y reputación.
- Se agregó `20260726_07` como head para exigir discriminadores explícitos,
  reparar ownership profesional legacy y preservar `_06` sin reescribirla.
- Se agregaron gates PostgreSQL para concurrencia, rutas, CSRF, privacidad, moderación y rollback.

### Mejorado

- El perfil público consume exclusivamente `comment_public` y métricas neutrales reconstruibles.
- Las reviews contractuales y legacy verificadas se distinguen explícitamente.
- La lectura de comentarios originales pendientes exige `SUPER_ADMIN` activo también dentro del servicio.
- PostgreSQL y SQLite impiden nuevas filas reputacionales con puntos, preservando las filas históricas existentes.

### Corregido

- Se bloqueó con `410` la ruta legacy de creación de reviews.
- Se retiró `add_reputation_event()` como API pública y no quedan callers productivos.
- Se eliminó la presentación pública del score histórico como reputación contractual.
- Se verificó que el flujo nuevo no crea `ContractEvent` ni puntos arbitrarios.
- Se cerró el bypass de `NULL`/orígenes desconocidos en `Review` y
  `ReputationEvent` mediante checks requeridos y triggers `v2` de inserción
  y actualización en PostgreSQL y SQLite.
- Las métricas admiten sólo `CONTRACTUAL` y `LEGACY` verificada; ningún
  origen nulo o desconocido se interpreta como legacy.
- El seed de desarrollo dejó de fabricar eventos reputacionales legacy con puntos.
- `20260726_06` conserva su clasificación histórica mediante un snapshot
  migratorio versionado y autocontenido. No es una API productiva: su
  aislamiento es un contrato arquitectónico verificado por dependencias, no
  una frontera contra imports de Python arbitrarios. El adaptador vigente
  exige ambos IDs de ownership y falla ante payloads incompletos.
  `20260726_07` usa exclusivamente esa API fail-closed y es el
  único estado operativo soportado. Un downgrade a `_06`
  reinstala defensas históricas más débiles y no equivale a `_07` para
  operación normal.

### Validación

- Auditoría independiente de integración: aprobada.
- Hallazgos abiertos: P0/P1/P2 ninguno. P3 no bloqueante: contraseña demo
  predecible pendiente de endurecimiento futuro.
- PostgreSQL 16.14, Alembic `20260726_07`: 59/59 pruebas finales aprobadas.
- Gate contractual 8/8; negociación 8/8; reviews 10/10; rutas/moderación 8/8; migración parcial 21/21; legacy 4/4.
- Suite Sprint 7 con PostgreSQL habilitado: 165 ejecutadas, 164 aprobadas y 1 omisión deliberada; cero fallos.
- Suite completa con PostgreSQL habilitado: 266 ejecutadas, 265 aprobadas y la misma omisión deliberada; cero fallos.
- Los warnings por `Query.get()` y `datetime.utcnow()` quedan como deuda no bloqueante.
- `20260726_07` es el único estado operativo soportado. Un downgrade a `_06`
  restaura defensas históricas más débiles.

## 2026-07-26 - Sprint 7 Contracting Core Fase 2A

### Agregado

- Se agrego `OperationCommand` como fuente canonica de idempotencia para comandos contractuales sensibles.
- Se agregaron `contracting_mode = EXTERNAL` y `version` a `ContractRequest`.
- Se agregaron secuencia, correlacion, causacion e idempotencia a `ContractEvent`.
- Se agrego correlacion estructurada a `AuditLog` y `ActivityNotification`.
- Se agrego la migracion Alembic `20260726_02_sprint7_contracting_foundations`.
- Se agrego la migracion Alembic `20260726_03_sprint7_single_hiring_mode`.
- Se agregaron pruebas de estados, ownership, idempotencia, rollback y
  constraints; la validacion de locks reales queda pendiente de PostgreSQL.
- Se agrego un gate PostgreSQL E2E explicito para carreras de comandos,
  transiciones y creaciones derivadas con dos sesiones independientes.
- Se agregaron pruebas integradas de reparacion y bloqueo de esquemas parciales
  de `operation_commands`.
- Se valido el gate contra PostgreSQL 16: 8 escenarios E2E, 4 pruebas
  legacy y 21 escenarios de migracion parcial aprobados sin omisiones.
- Se agregaron pruebas negativas para impedir la fabricacion externa de
  eventos contractuales y para validar o reparar el generador PostgreSQL de
  `operation_commands.id`.

### Mejorado

- `CONFIRMADA` es el unico estado terminal exitoso para contratos nuevos.
- `CERRADA` contractual se migra a `CONFIRMADA` y deja de ser un estado valido de escritura.
- Las transiciones contractuales usan operaciones explicitas, lock pesimista y version esperada.
- Evento, auditoria, notificacion interna y resultado idempotente se confirman en una unica transaccion.
- Las notificaciones contractuales obligatorias quedan listas para una futura outbox sin implementar canales externos.
- La creacion derivada de contratos conserva correlacion comun entre eventos, auditoria y notificaciones.
- Las creaciones derivadas autorizan al actor owner antes del replay y recuperan
  colisiones unicas mediante savepoint sin commits internos.
- `hiring_mode = MULTIPLE` queda bloqueado tambien por constraint hasta Fase 2C.
- La migracion ya no considera completa una `operation_commands` solo porque
  exista la tabla: valida estructura, datos, constraints e indices antes de
  reparar.
- El preflight PostgreSQL valida identity/default, ownership y permisos de la
  secuencia de `operation_commands.id`; sincroniza el generador por encima de
  `MAX(id)` o bloquea antes de otras mutaciones si no puede repararlo.
- La validacion del generador incluye incremento ascendente, `NO CYCLE`,
  limites compatibles con `INTEGER`, siguiente valor efectivo y ausencia de
  consumidores compartidos. Las secuencias propias reparables se normalizan a
  incremento 1 y se reinician en `MAX(id) + 1`.
- Las secuencias creadas por la migracion quedan marcadas; el downgrade
  preserva secuencias preexistentes o ajenas.

### Corregido

- Se retiro el mutador generico `update_contract_status`.
- Se elimino la transicion posterior `CONFIRMADA -> CERRADA`.
- Los servicios validan rol y ownership sin depender exclusivamente de las rutas.
- Los actores ausentes, inexistentes, suspendidos, inactivos, con rol incorrecto
  o sin ownership no pueden crear ni consultar por replay un contrato derivado.
- Se elimino la API generica publica `create_contract_event`: los eventos
  iniciales de presupuesto y propuesta solo se emiten dentro de sus operaciones
  cerradas, junto con auditoria y notificacion correlacionadas.

## 2026-07-26 - Sprint 7 Contracting Core Fase 1

### Agregado

- Se agrego `ContractEvent` como historial de dominio para contrataciones.
- Se agrego `contracting_core_service.py` como puerta central para crear contratos desde presupuestos y propuestas.
- Se agrego trazabilidad de origen en `ContractRequest` para `DIRECT`, `BUDGET` y `PROPOSAL`.
- Se agrego migracion Alembic `20260726_01_sprint7_contracting_core`.
- Se agregaron pruebas de contratacion directa, presupuesto a contrato y propuesta a contrato.

### Mejorado

- Una `BudgetOffer` adjudicada crea un `ContractRequest` canonico en estado `CREADA`.
- Una `ProposalApplication` aceptada crea un `ContractRequest` canonico en estado `CREADA`.
- Las creaciones derivadas son idempotentes y conservan referencias a la entidad origen.
- Los reintentos de adjudicacion o aceptacion no duplican eventos, auditorias ni notificaciones.
- Las propuestas usan `hiring_mode = SINGLE` por defecto: la primera postulacion aceptada cierra la propuesta y descarta otras activas.
- La migracion incorpora checks de consistencia de origen y bloqueo seguro de downgrade si ya existe trazabilidad contractual.
- Las transiciones de contrato generan eventos de dominio.

### Corregido

- Se corrigio el contrato de estados de `BudgetRequest` para incluir `CANCELADA` y estados canonicos de publicacion.
- Se normaliza el estado legacy `CERRADO` de presupuestos a `CERRADA`.

## 2026-07-24 - UX/UI General & Design System v2

### Agregado

- Se agrego carga explicita de `design-system-v2.css` desde `base.html`.
- Se agrego `design-system-v2.js` para cierre accesible de alertas globales.
- Se agregaron componentes canonicos para flashes, estados vacios, layout utilities y modal compartido.
- Se creo la documentacion de cierre del sprint en `docs/SPRINTS/2026-07-24_UX_UI_General_Design_System_v2.md`.

### Mejorado

- Login, registro, rubro solicitado, notificaciones, flashes globales y modal WhatsApp quedaron alineados al contrato `.trax-*`.
- `styles.css` dejo de importar el Design System v2 y queda como capa legacy posterior.
- `DESIGN_SYSTEM_V2.md` documenta jerarquia CSS, mapa de impacto, deuda pendiente y estrategia de migracion futura.

### Corregido

- Se redujo duplicacion visual en notificaciones y modal WhatsApp sin cambiar rutas ni logica de negocio.
- Se protegio por tests la carga del Design System v2 antes de estilos legacy.

## 2026-07-24 - Rediseño de Login y Registro

### Agregado

- Se agrego una experiencia dedicada de autenticacion con `auth-ux-v1.css` y `auth-ux-v1.js`.
- Se agregaron labels visibles, errores inline accesibles, toggle de contraseña, estado de carga y feedback de fortaleza.
- Se agrego validacion centralizada de login y registro en `auth_service.py`.
- Se conecto `TermsAcceptance` al registro con version centralizada.
- Se agregaron pruebas de login, registro, CSRF, rate limiting, redirects, roles, terminos y accesibilidad basica.

### Mejorado

- `auth_routes.py` quedo orientado a request, servicio, sesion y redirect.
- El registro crea cuenta basica y redirige por rol: cliente al destino seguro, profesional a completar perfil.
- El login rechaza usuarios suspendidos o inactivos antes de crear sesion.
- Los mensajes de registro evitan confirmar explicitamente si un email ya existe.

### Corregido

- Se evita dejar una cuenta parcialmente creada si falla el registro de consentimiento.
- Se bloqueo `next` externo tambien en el flujo de registro con sesion inmediata.

## 2026-07-23 - Identidad y Portfolio Profesional

### Agregado

- Se agrego el modelo `ProfessionalMedia` para gestionar avatar, portada y galeria profesional.
- Se creo la migracion Alembic `20260723_01_professional_media_v1`.
- Se agregaron servicios para procesar imagenes, almacenar archivos y administrar media profesional.
- Se agregaron rutas privadas para subir, reemplazar, editar, reordenar, marcar principal y eliminar media.
- Se agregaron acciones de moderacion administrativa para publicar, rechazar, ocultar y restaurar imagenes.
- Se agregaron pruebas de validacion de imagenes, ownership, CSRF, moderacion, fallback legacy y almacenamiento.

### Mejorado

- El perfil privado profesional incorpora gestion basica de identidad visual y portfolio sin redisenar la UX general.
- El perfil publico, galeria y cards profesionales priorizan media publicada y mantienen campos legacy como fallback.
- Las imagenes se reprocesan para eliminar EXIF/GPS y generar miniaturas.
- El almacenamiento local queda validado para desarrollo y Cloudinary queda configurable por entorno sin secretos versionados.

### Corregido

- Se evita exponer imagenes rechazadas, ocultas o eliminadas en el perfil publico.
- Se rechazan archivos corruptos, MIME falso, extensiones no permitidas, tamanos excesivos y dimensiones invalidas.

## 2026-07-22 - Cierre de WhatsApp y Geolocalizacion

### Agregado

- Se agrego respuesta JSON segura en `POST /whatsapp/iniciar` para abrir la URL autorizada desde la interaccion del usuario.
- Se agrego validacion central de disponibilidad de `GOOGLE_MAPS_API_KEY`.
- Se agregaron pruebas de cierre para WhatsApp, Google Maps, privacidad, CSRF, ownership, radios y coordenadas.
- Se documento el cierre operativo de WhatsApp y Geolocalizacion.

### Mejorado

- El modal de WhatsApp ya no depende exclusivamente de submit programatico y redirect backend.
- El flujo conserva redirect HTML como fallback compatible.
- El fallback del modal funciona en navegadores sin soporte de `<dialog>`.
- Google Maps ignora placeholders y cae a fallback si falta la key, falla la carga o Google informa error de autenticacion.
- Docker Compose expone `GOOGLE_MAPS_API_KEY` sin hardcodear claves.

### Corregido

- Se evita que una key placeholder active el mapa interactivo.
- Se evita aceptar telefonos tecnicamente invalidos para construir URLs de WhatsApp.
- Se redujo el riesgo de dobles envios desde el frontend mediante bloqueo de submit en curso.

## 2026-07-22 - Security & Compliance Foundation v1

### Agregado

- Se agregaron claves reutilizables de rate limiting por IP, usuario e IP+usuario.
- Se agregaron limites especificos para login, registro, busquedas, WhatsApp, solicitudes, propuestas, reportes y POST administrativos.
- Se agregaron handlers seguros para `400`, `403`, `404`, `413`, `429` y `500`.
- Se agregaron limites configurables de tamano de request y memoria de formularios.
- Se agregaron pruebas de seguridad, privacidad publica, headers, errores seguros y consentimientos versionados.

### Mejorado

- Se reforzaron cookies de sesion, headers de seguridad, CSP y HSTS condicionado a produccion HTTPS.
- Se amplio `.gitignore` para artefactos locales sensibles.
- Se documento Docker Compose como entorno local con credenciales no reutilizables en produccion.
- Se redujo la precision de coordenadas publicas aproximadas de cobertura.

### Corregido

- Produccion ya no acepta placeholders inseguros de `SECRET_KEY`.
- Los errores internos no exponen detalles ni payloads sensibles al usuario.

## 2026-07-21 - Consolidacion Arquitectonica v1

### Agregado

- Se agregaron servicios internos para separar view models, permisos, formularios y notificaciones operativas de las rutas principales.
- Se agregaron pruebas de configuracion por entorno, ownership y servicios extraidos.

### Mejorado

- `main_routes.py` y `operation_routes.py` redujeron responsabilidades y quedaron orientados a request, permisos, servicios y render.
- Se consolidaron `DevelopmentConfig`, `TestingConfig` y `ProductionConfig`.
- Se establecio Alembic como autoridad del esquema fuera de tests.
- Se documento Docker como flujo principal de ejecucion local.

### Corregido

- Se elimino el fallback inseguro de `SECRET_KEY` para produccion.
- Se restringio `db.create_all()` a tests o desarrollo explicitamente habilitado.

## 2026-07-15 - WhatsApp Contact Privacy v1

### Agregado

- Se agregaron `whatsapp_username` y `whatsapp_contact_preference` al modelo `Professional`.
- Se agregaron `contact_identifier_type` y `contact_identifier_masked` a `WhatsAppContactSession`.
- Se creo la migracion Alembic `20260715_01_whatsapp_contact_privacy_v1`.
- Se agregaron helpers para normalizar, validar y resolver identificadores de contacto por WhatsApp.
- Se agregaron campos de username y preferencia en el perfil privado profesional.
- Se agregaron pruebas unitarias para el esquema hibrido de contacto.

### Mejorado

- El flujo central de WhatsApp prioriza username de forma conceptual cuando existe y la preferencia lo permite.
- Mientras no exista URL publica estable por username, el telefono se mantiene como fallback tecnico de apertura.
- Las sesiones registran solo tipo de identificador y valor enmascarado.
- El perfil publico informa contacto protegido sin exponer telefono ni username completo.

### Corregido

- Se evita duplicar telefonos completos en nuevas sesiones de contacto.

## 2026-07-15 - Public Profile Map UX v1

### Agregado

- Se agrego el marcador SVG reutilizable `trax-worker-marker.svg` para mapas publicos de cobertura.
- Se agrego modal "Ver cobertura ampliada" en el perfil publico profesional.
- Se agrego card vacia para profesionales sin zona de cobertura configurada.

### Mejorado

- Se rediseño la seccion publica "Zona de cobertura" con experiencia visual tipo marketplace.
- El perfil publico muestra mapa, anillo de cobertura, centro aproximado, radio y zona base sin exponer direccion exacta.
- El mapa publico usa marcador TRAX personalizado en lugar del pin clasico de Google.
- La seccion queda adaptada a claro, oscuro, desktop, tablet y mobile.

### Corregido

- Se reemplazo el bloque textual largo por un resumen breve orientado a privacidad.

## 2026-07-15 - Matching Geografico por Distancia v1

### Agregado

- Se creo `app/services/geographic_matching_service.py` con calculo Haversine en backend.
- Se agregaron pruebas unitarias para distancia, cobertura, coordenadas ausentes e invalidas.
- Se integro el resultado de cobertura en Resultados de profesionales y Directorio de Emergencias.
- Se agrego visualizacion publica de estado de cobertura y distancia aproximada en cards compatibles.

### Mejorado

- Los resultados con coordenadas validas priorizan profesionales dentro de cobertura.
- Las busquedas sin coordenadas conservan el matching textual actual por servicio y zona.
- La interfaz informa cobertura sin exponer coordenadas ni punto base profesional.

### Corregido

- Sin correcciones registradas.

## 2026-07-14 - WhatsApp Integration Foundation v1

### Agregado

- Se creo el modelo `WhatsAppContactSession` para registrar aperturas de WhatsApp iniciadas desde TRAX.
- Se agrego la migracion Alembic `20260714_01_whatsapp_contact_sessions`.
- Se creo `app/services/whatsapp_contact_service.py` como servicio unico para validar operaciones, crear sesiones, generar URLs y actualizar estados.
- Se agrego la ruta central `POST /whatsapp/iniciar` con CSRF, consentimiento obligatorio y redireccion controlada.
- Se agrego modal de consentimiento previo a abrir WhatsApp.
- Se agregaron resumenes de contactos iniciados en Dashboard Cliente y oportunidades de contacto en Dashboard Profesional.

### Mejorado

- Se reemplazaron enlaces directos de WhatsApp en perfiles, tarjetas profesionales, emergencias, presupuestos adjudicados y propuestas aceptadas.
- Las aperturas de WhatsApp ahora generan notificaciones internas para cliente y profesional.
- El flujo queda preparado para futuras integraciones sin almacenar mensajes, archivos ni conversaciones.

### Corregido

- Se elimino la generacion dispersa de enlaces `wa.me` desde templates.

## 2026-07-13 - Cobertura Inteligente v2 Google Maps

### Agregado

- Se agrego soporte frontend para Google Maps JavaScript API en cobertura profesional.
- Se creo `app/static/js/professional-coverage-map.js` como modulo aislado del proveedor visual.
- Se agrego consentimiento explicito para uso de ubicacion de cobertura.
- Se agrego `coverage_location_consent_at` al modelo `Professional`.
- Se agrego la migracion Alembic `20260713_01_google_maps_coverage_v2`.
- Se documento `GOOGLE_MAPS_API_KEY` en `.env.example`.

### Mejorado

- El perfil privado puede persistir latitud, longitud y radio cuando existe consentimiento.
- El perfil publico usa centro aproximado para no exponer el punto exacto del profesional.
- Sin API key, la pantalla mantiene fallback visual y edicion textual.
- Se ajusto CSP para permitir la carga acotada de Google Maps JavaScript API.

### Corregido

- Se evita guardar coordenadas nuevas cuando el profesional no presta consentimiento.

## 2026-07-12 - Cobertura Inteligente v1

### Agregado

- Se agregaron campos de cobertura al modelo `Professional`.
- Se creo la migracion Alembic `20260712_02_smart_coverage_v1`.
- Se creo `app/services/coverage_service.py` para normalizar radios y describir cobertura profesional.
- Se agrego la seccion editable "Zona de cobertura" al perfil privado profesional.
- Se agrego visualizacion publica de cobertura con mapa placeholder y anillo representativo.
- Se agrego resumen operativo de cobertura al Dashboard Profesional.

### Mejorado

- El perfil publico informa zona principal, localidad/provincia, modalidad, radio y notas cuando existen.
- La cobertura queda preparada para futura integracion con mapas, geocoding y matching por distancia.

### Corregido

- Se reemplazo el placeholder estatico de cobertura por datos persistentes y validados.

## 2026-07-12 - Centro de Actividad + Notificaciones v1

### Agregado

- Se creo el modelo `ActivityNotification` para registrar actividad historica y notificaciones internas.
- Se agrego el servicio central `notification_service.py` con constantes, consultas y marcado de lectura.
- Se agregaron rutas `/notificaciones`, `/notificaciones/<id>/leer` y `/notificaciones/marcar-todas-leidas`.
- Se agrego campana de notificaciones en el navbar para usuarios autenticados.
- Se integraron eventos reales de presupuestos, propuestas y emergencias.

### Mejorado

- Dashboard Cliente y Dashboard Profesional muestran actividad reciente basada en notificaciones reales.
- El sistema queda preparado para canales futuros como Email, WhatsApp y Push sin implementarlos todavia.

### Corregido

- Sin correcciones registradas.

## 2026-07-12

### Agregado

- Se implemento el Dashboard Cliente v1 como centro de operaciones para solicitudes y contrataciones.
- Se agrego una hoja de estilos dedicada para el dashboard cliente basada en Design System v2.
- Se agregaron resumen, centro de actividad, accesos rapidos, mis solicitudes, recomendaciones y estado operativo del cliente.

### Mejorado

- Se reutilizaron datos reales de presupuestos, emergencias, propuestas y contrataciones existentes.
- Se incorporaron placeholders elegantes cuando todavia no hay actividad suficiente.

### Corregido

- Sin correcciones registradas.

## 2026-07-10

### Agregado

- Se creo `app/static/css/design-system-v2.css` como capa central de variables semanticas para temas Light y Dark.
- Se agregaron variables para fondos, superficies, cards, bordes, texto, marca, estados, sombras, radios, espaciados y transiciones.

### Mejorado

- Se conectaron tokens legacy globales con el Design System v2.
- Se adapto el comportamiento visual de Home publico, Home logueado, Perfil profesional, Perfil privado, Dashboard profesional, Presupuestos, Emergencias, Propuestas, Explorar rubros, Planes y formularios principales.
- Se mejoro la respuesta de cards, botones, inputs, selects, textareas, badges, alertas, links, focus y hover al cambio de tema.

### Corregido

- Se redujeron superficies e inputs hardcodeados que no respondian correctamente al modo oscuro.

## 2026-07-09

### Agregado

- Se incorporo la estructura permanente de documentacion del proyecto en `docs/`.
- Se agrego el registro de sprints en `docs/SPRINTS/`.
- Se agrego `docs/BACKLOG.md` para registrar funcionalidades pendientes, mejoras y deuda tecnica.
- Se agrego `docs/ESTANDARES_DESARROLLO.md` como manual permanente de desarrollo del proyecto.
- Se creo la politica de documentacion viva para cambios implementados, probados, documentados, versionados y mergeados.

### Mejorado

- Se formalizo el seguimiento de cambios, roadmap y decisiones importantes del proyecto.
- Se definio la convencion de nombres de sprint por fecha y nombre descriptivo, sin numeracion.
- Se incorporo el checklist obligatorio para cierre oficial de cada sprint.
- Se documentaron reglas permanentes de ramas, commits, flujo Git, estructura, UX/UI, seguridad, Docker, Alembic y Pull Requests.

### Corregido

- Sin correcciones registradas.
# 2026-09-04 - Correcciones de auditoria del nucleo PRO

Timestamp: 2026-09-04T10:29:16-03:00

### Corregido

- La revocacion solo cancela fuentes PRO reconocidas, activas y vigentes, y se
  confirma atomicamente junto con su AuditLog.
- El seed QA no extiende una vigencia futura y renueva la misma fila tras su
  vencimiento.
- El gate PostgreSQL rechaza cualquier base fuera del namespace reservado
  `trax_pro_entitlement_test[_sufijo]` antes de crear el engine.
- Se centralizo la frontera UTC naive del nucleo PRO y se documento la perdida
  de `source_type` durante downgrade.
- REQ-001 declara canonicamente `IMPLEMENTACION_PARCIAL`.
