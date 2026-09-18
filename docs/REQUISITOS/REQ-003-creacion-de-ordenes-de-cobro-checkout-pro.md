---
id: REQ-003
titulo: Creacion de ordenes de cobro Checkout Pro
estado: APROBADO
fecha_aprobacion: 2026-09-14T10:05:02-03:00
responsable: Cristian Sánchez
rama_documental: feature/checkout-pro-payment-order-contract
implementacion: PENDIENTE
ultima_revision: 2026-09-18T09:50:28-03:00
---

# REQ-003 - Creacion de ordenes de cobro Checkout Pro

## Cierre técnico local 4F aprobado por Testing

Timestamp de registro documental: 2026-09-18T09:50:28-03:00
Estado técnico local: APROBADO
Implementación productiva: PENDIENTE
Rama: `feature/payment-effects-pro-commission`.
Commit técnico: `83581b3`.
Registro documental: Codex; dispositivo: laptop.
Evidencia final de Testing suministrada para este cierre, sin repetir su ejecución.

4F implementa el motor interno durable de créditos y comisión comercial separado
de evidencia PSP, contabilidad y facturación. Solo evidencia 4E correlacionada,
acreditada, completa en ARS y sin contradicciones permite evaluar efectos.
La política económica inyectada es versionada, explícita y obligatoria: precio
mensual/umbral y moneda sin valores predeterminados. Comisión neta efectiva
acumulada equivalente al precio mensual PRO genera 1 crédito; su consumo concede
30 días PRO. No se reintroduce la regla histórica de 60 días.

Acumulación y remanente Decimal exactos, consumo FIFO y lotes que vencen
individualmente a los 40 días, sin rejuvenecer saldos anteriores. Idempotencia
por evidencia e identidad financiera, locks y auditoría atómica protegen la
aplicación durable. El reloj efectivo se obtiene después de todos los locks:
se revalidan vencimiento y elegibilidad de lotes; un lote vencido durante la
espera no se consume ni concede PRO. Concesión y auditoría comparten ese instante.

Sin política o evidencia confiable de comisión neta efectiva: `PENDING_POLICY`,
sin crédito ni extensión; no se presume comisión cero ni se infiere comisión
neta de `marketplace_fee`. Suscripción paga no genera comisión transaccional.
Pagos tardíos, temporalidad incierta, reembolsos, reversos y contracargos quedan
`PENDING_REVIEW`, sin compensación ni revocación automática de efectos anteriores.
La temporalidad UNKNOWN de 4E no se convierte automáticamente en pago puntual.

`PAYMENT_EFFECTS_ENABLED=False` y `TRANSACTIONAL_COMMISSION_ENABLED=False`.
Migración `20260917_03`, descendiente de `20260917_02`.
No habilita disponibilidad productiva, cobros reales, contabilidad ni facturación.

### Evidencia final y cierre de hallazgos

- Testing aprobado: focales **66/66** y regresiones **363/363**.
- PostgreSQL **42/42** más **3/3** reproducciones adversariales.
- Suite completa: **694 aprobadas** y **5 omisiones históricas**.
- Ambos P2 corregidos y sin hallazgos pendientes: tiempo efectivo tras locks y
  claves generadas compatibles con el validador vigente. Tokens internos iniciados
  con `_` y `-` generan claves válidas; dos POST secuenciales conservan la misma
  clave estable, sin debilitar validación ni duplicar efectos.
- La historia de ambos hallazgos, sus correcciones y validaciones previas se conserva.

Este cierre acredita únicamente implementación técnica local 4F y su retest.
Supera la pendencia técnica de 4F en los registros anteriores, que se conservan
como historia de su fecha. REQ-001 y REQ-003 permanecen APROBADO/PENDIENTE para
la implementación productiva; el Sprint 2 productivo continúa abierto.

### Gate futuro obligatorio de producción

La activación productiva permanece bloqueada hasta acreditar y aprobar:

- Constitución/CUIT y asesoramiento fiscal.
- Cuenta bancaria empresarial.
- Cuenta empresarial Mercado Pago, aplicación y OAuth completo, incluida
  custodia y renovación de credenciales por profesional.
- Precio mensual, moneda y política comercial explícita y versionada.
- Fórmula/tasa real de comisión, evidencia confiable de comisión neta efectiva
  y tratamiento fiscal; no existen tasas o importes predeterminados aprobados.
- Dominios HTTPS, URLs públicas y secretos con custodia adecuada.
- Pruebas staging/live, monitoreo, soporte y respuesta a incidentes.
- Aprobación legal, privacidad y términos.

También siguen pendientes la integración operativa autorizada, retornos,
tratamiento productivo de pagos tardíos y reversos, resolución de revisiones,
contabilidad y facturación. El cierre local no satisface estos gates ni autoriza
activar flags o emplear credenciales reales.

Registro del frontmatter anterior: ultima_revision `2026-09-17T21:24:48-03:00`;
implementacion `PENDIENTE`. El estado APROBADO se conserva.

## Cierre técnico local 4E aprobado por Testing

Timestamp de registro documental: 2026-09-17T21:24:48-03:00
Estado técnico local: APROBADO
Implementación productiva: PENDIENTE
Rama: `feature/mercadopago-payment-reconciliation`.
Commit técnico: `8dc0e12`.
Registro documental: Codex; dispositivo: laptop.
Evidencia final de Testing suministrada para este cierre.

4E implementa recepción y conciliación verificada de evidencia durable de
Orders, sin efectos PRO, contables o comerciales. POST
`/api/webhooks/mercadopago` acepta únicamente el tópico `order`; HMAC-SHA256
con comparación constante conserva `data.id` case-sensitive. Inbox y trabajo
durables, deduplicación, cuarentena e intentos son independientes de los
estados informados por el webhook. La confirmación HTTP 200 ocurre únicamente
después del commit durable; firma inválida responde 401 sin persistencia.

La validación criptográfica está separada de la temporal: firma válida con
timestamp en milisegundos fuera de la ventana inclusiva ±10 minutos queda en
cuarentena durable `TIMESTAMP_OUTSIDE_WINDOW`, sin trabajo ejecutable ni consulta
PSP. Colisiones preservan la primera recepción y quedan en cuarentena.
`LEASE_DURATION_SECONDS = 60` y `STALE_LEASE_RECOVERY_SECONDS = 120` separan
vencimiento del permiso de despacho/finalización y recuperación del trabajo
abandonado. Entre 60 y 119 segundos no hay consulta; desde 120 segundos puede
recuperarse con otro token. Fencing impide finalizar con lease vencido;
ocho intentos programados como máximo, sin retries del transporte HTTP.

Consulta `GET /v1/orders/{id}` fuera de una transacción local abierta, con
credencial OAuth por profesional suministrada por un proveedor confiable
inyectado, vinculada a profesional, cuenta PSP y entorno; sin fallback global.
El onboarding, la custodia y la renovación OAuth permanecen pendientes.
Se correlacionan orden externa, PaymentOrder, obligación, contrato y reserva;
solo una respuesta autoritativa validada permite registrar evidencia normalizada
de pagos, reembolsos y reversos, incluidos contracargos y pagos tardíos.
El vencimiento contractual local sigue siendo la autoridad de entrega del
checkout; registrar un pago tardío no habilita automáticamente efecto alguno.

Suma Decimal exacta de reembolsos por pago asociado y por orden, deduplicada por
identidad externa. El snapshot remoto y la evidencia acumulada durable deben
respetar ambos límites. La validación acumulada se serializa bajo lock de
PaymentOrder y fence SQLite: contradicciones quedan en cuarentena sin insertar
nueva evidencia financiera válida; se conserva la evidencia histórica válida.

Migración `20260917_02`, descendiente de `20260917_01`, incorpora trabajo,
intentos, evidencia y cuarentena durables. Feature flags
`MERCADOPAGO_ORDER_WEBHOOK_ENABLED=False` y
`MERCADOPAGO_ORDER_RECONCILIATION_ENABLED=False` permanecen deshabilitados por
defecto. No se declaran credenciales reales, cobros productivos ni conciliación
financiera con efectos habilitados.

Evidencia final acreditada de Testing:

- Focales 4E: **96/96**.
- Regresiones relacionadas: **197/197**.
- PostgreSQL: **37/37**.
- Suite completa: **653 ejecutadas, 648 aprobadas y 5 omisiones históricas**.
- Migraciones SQLite/PostgreSQL, `compileall`, Alembic y `git diff --check`:
  aprobados; head `20260917_02`.
- Sin hallazgos P0–P3 pendientes.

Los hallazgos P1/P2 y su corrección de `2026-09-17T21:04:23-03:00`, junto con
la implementación de `2026-09-17T20:42:27-03:00`, se conservan en el
[historial del handoff](../HANDOFFS/ACTIVE_HANDOFF.md). Los resultados de aquella corrección
(207/207 regresiones) son históricos; este cierre acredita los **197/197**
del paquete final suministrado, sin reemplazar la evidencia anterior.

Se cierra únicamente 4E técnico local y su retest: supera esos pendientes en
registros anteriores, conservados íntegramente. REQ-003 continúa
`estado: APROBADO` e `implementacion: PENDIENTE`; no se cierra Sprint 2 productivo.
Pendientes reales: OAuth completo y custodia/renovación, fórmula de comisión,
retornos, credenciales y prueba real, validación/activación productiva de la
recepción y consulta PSP. Los efectos PRO, comerciales y contables de evidencia
conciliada, pagos tardíos y reversos corresponden a 4F; producción permanece
pendiente. La recepción y evidencia local de webhook/Orders ya están
implementadas en 4E; no confundirlas con su activación productiva.

## Cierre técnico local 4D aprobado por Testing

Timestamp de aprobación de Testing: 2026-09-17T16:14:10-03:00
Estado: APROBADO
Implementación productiva: PENDIENTE
Rama: `feature/checkout-pro-payment-order-delivery`.
Commit técnico: `763eee3`.
Agente verificador: `03 - Testing - Test Executor`.
Registro documental: Codex; dispositivo: laptop.
Implementación técnica: `2026-09-17T16:06:04-03:00`.

Alcance acreditado: POST `/contratacion/<int:id>/orden-de-cobro` de creación/replay
con sesión, actor desde `session["user_id"]`, CSRF y ownership contractual/perfil
del profesional activo; solo contratos CONFIRMADA. Importe y clave durable
proceden de 4B, sin overrides del navegador. Éxito/replay responde 303.
GET de esa ruta y GET `/contratacion/<int:id>/orden-de-cobro/qr.png` requieren
autorización y solo leen: no crean órdenes ni llaman al PSP ni resuelven OAuth/comisión.

Checkout y QR PNG están limitados al profesional propietario, reserva exitosa,
orden activa/coherente y vencimiento contractual vigente. `segno==1.6.6` genera
localmente el PNG en memoria, desde exactamente la misma checkout_url HTTPS
validada del enlace. Endpoint QR separado y autenticado; sin servicios externos,
JavaScript remoto, SVG safe, data URI ni archivos persistentes. Componentes
Design System V2, enlace alternativo, texto accesible y formato Decimal exacto.
Abrir el enlace o escanear el QR no acredita pago.

Órdenes vencidas, canceladas, bloqueadas, inciertas o no disponibles no entregan
checkout ni QR. Vencimiento revalidado al finalizar render/generación; autoridad
contractual local, sin afirmar igualdad con vencimiento remoto. Clave durable,
replay, cero retries y bloqueo 4B preservados; sin renovación ni recuperación
automáticas. Headers privados `Cache-Control: no-store, private`,
`Referrer-Policy: no-referrer` y nosniff cubren errores y redirects.
Errores públicos genéricos sin datos sensibles. Feature flags
`CHECKOUT_PRO_DELIVERY_ENABLED=False` y `MercadoPagoOrderConfiguration.enabled=False`
por defecto, composición explícita con proveedores confiables inyectados.

Evidencia final acreditada de `03 - Testing - Test Executor`:

- Focales 4D: **26/26**; focales 4B–4C: **52/52**.
- Regresiones relacionadas: **119/119**.
- PostgreSQL: **6/6**, más **3/3 reproducciones HTTP**.
- Suite: **594 ejecutadas, 589 aprobadas, 5 omisiones históricas y 0 fallos**.
- `compileall`, Alembic head `20260917_01`, UTF-8, enlaces, whitespace y
  `git diff --check`: aprobados. Sin migración nueva en 4D.

Se cierra únicamente el incremento técnico 4D: deshabilitado por defecto,
sin habilitar cobros productivos. REQ-003 conserva `estado: APROBADO` e
`implementacion: PENDIENTE`. Continúan pendientes OAuth real y custodia/renovación,
fórmula de comisión, retornos, webhooks, conciliación, tratamiento de pagos
tardíos, efectos PRO/contables, credenciales reales y validación/activación en
entornos de staging y producción. El cierre supera endpoint/presentación 4D y
Testing final pendientes en registros anteriores, preservados íntegramente.

## Cierre técnico local 4C aprobado por Testing

Timestamp de aprobación final: 2026-09-17T15:07:04-03:00
Estado: APROBADO
Implementación productiva: PENDIENTE
Rama: `feature/mercadopago-payment-order-create-adapter`.
Commit técnico: `b859e6a`.
Agente verificador: `03 - Testing - Test Executor`.
Registro documental: Codex; dispositivo: laptop.

Trazabilidad preservada:

- Implementación: `2026-09-17T12:58:58-03:00`.
- Hallazgo P2 de Testing: `2026-09-17T14:57:30-03:00`.
- Corrección P2: `2026-09-17T15:02:03-03:00`.
- Aprobación final: `2026-09-17T15:07:04-03:00`.

Alcance acreditado por Testing: adaptador Orders API interno, deshabilitado
por defecto. Credencial OAuth por profesional suministrada por un proveedor confiable inyectado. El onboarding, la custodia y la renovación OAuth permanecen pendientes.
Configuración válida y comisión
obtenida de política confiable antes del claim, enviada como `marketplace_fee`.
Sin defaults de comisión ni
fallback a token global de MANDOBRA. POST `/v1/orders`, importe ARS decimal
exacto, `X-Idempotency-Key` durable sin truncar/regenerar y `expiration_time=PT72H`.
Respuesta 201 validada: persistencia de `id` y `checkout_url` HTTPS con host
permitido `www.mercadopago.com.ar`. Cero retries y bloqueo durable tras error
o incertidumbre; ninguna llamada adicional automática.

Doble vencimiento: `expires_at = created_at + 72 horas` conserva la autoridad
contractual local; `PT72H` cuenta desde la creación remota. No se afirma que
coincidan. Se rechaza entregar o reutilizar el checkout local vencido.
Los pagos tardíos requieren conciliación/revisión y no generan automáticamente
efectos PRO, contractuales, contables ni de comisión local.

P2 corregido y revalidado: la excepción sensible retenida en `__context__`
se elimina lanzando el error neutral después de salir del `except`, sin
conservar la excepción original ni copiar sus argumentos. Secretos neutralizados,
incluidos `__context__` y `__cause__`; sin hallazgos P0–P3 pendientes.

Evidencia final acreditada de `03 - Testing - Test Executor`:

- Focales: **52/52**.
- Regresiones: **119/119**.
- PostgreSQL: **12/12**.
- Suite: **568 ejecutadas, 563 aprobadas, 5 omisiones históricas,
  0 fallos y 0 errores**.
- `compileall`, Alembic head único `20260917_01`, whitespace y
  `git diff --check`: aprobados. 4C no agrega migraciones.

REQ-003 conserva `APROBADO` con implementación productiva `PENDIENTE`.
Se cierra únicamente el incremento técnico interno; no se declaran producción
ni cobros disponibles. Pendientes: OAuth completo y custodia/renovación;
fórmula de comisión; endpoint/UI 4D; retornos, webhook y conciliación;
tratamiento productivo de pagos tardíos; credenciales y prueba real;
activación en producción. La recuperación de incertidumbre sigue
separada y deberá reutilizar la misma clave durable.

Este cierre supera los pendientes históricos de implementación del adaptador
y retest P2, preservando registros, timestamps y evidencia de etapas anteriores.

## 2026-09-17 - Política aprobada de doble vencimiento 4C

Timestamp: 2026-09-17T12:51:16-03:00
Estado: APROBADO
Implementación: PENDIENTE
Responsable: Cristian Sánchez; dispositivo: laptop; agente: Codex.
Rama: `feature/mercadopago-payment-order-create-adapter`; base: `fc5eb0c`.

MANDOBRA conserva `expires_at = created_at + 72 horas` como autoridad
contractual exacta. Mercado Pago recibe `expiration_time = PT72H`, contado
desde la creación remota. No se afirma igualdad entre ambos vencimientos.
Después del vencimiento local no se debe entregar ni reutilizar el checkout.
Un eventual pago tardío no genera automáticamente efectos PRO, contractuales,
contables ni de comisión: queda pendiente de conciliación/revisión.
La activación productiva permanece bloqueada hasta implementar esa política
completa; 4C sigue limitado al adaptador interno deshabilitado por defecto.
Esta decisión supera el bloqueo de diseño por igualdad de vencimientos,
preservando los registros anteriores y sin crear migraciones.

Fuente de semántica remota:
[Vigencia de Orders](https://www.mercadopago.com.ar/developers/es/docs/checkout-pro-orders/additional-settings/define-order-validity).



## Realineación vigente 4C: Orders API y marketplace

Timestamp: 2026-09-17T12:14:36-03:00
Estado: APROBADO
Implementación: PENDIENTE
Responsable: Cristian Sánchez; agente documental: Codex; dispositivo: laptop.
Rama: `feature/mercadopago-payment-order-create-adapter`.
Commit base: `ad9ce5964f09919990b30cbf31df4efcfb709b0e`.

Checkout Pro utilizará Orders API moderna: `POST /v1/orders`.
Preferences API queda descartada para esta integración nueva. Sus menciones
anteriores se conservan como historia y no gobiernan el incremento 4C.

- `X-Idempotency-Key` obligatorio: usar la clave durable reservada por 4B.
  Sin reintentos automáticos.
  La política queda aprobada; una recuperación futura, todavía no implementada, deberá reutilizar la misma clave durable.
  No regenerarla ni liberar el bloqueo durable ante errores o incertidumbre.
- Persistir `id` en `PaymentOrder.external_order_id` y `checkout_url`
  mediante 4A/4B; no almacenar la orden en `external_attempt_id`.
- El profesional recibe el cobro en su cuenta: usar su token OAuth como receptor.
  Ningún token global de MANDOBRA será receptor productivo.
- MANDOBRA percibe comisión como marketplace mediante `marketplace_fee`,
  importe monetario calculado por una política aprobada, no porcentaje directo.
- 4C solo incluye adaptador interno y cableado con 4B; permanece deshabilitado
  sin OAuth del receptor y configuración válida, sin fallback a token global.
- OAuth completo (onboarding, custodia y renovación), endpoint público/UI (4D),
  retornos, recuperación y conciliación permanecen separados.
- No se requiere migración por esta decisión documental; ya existen los campos
  de ID externo y URL. Futuras necesidades de OAuth/comisión tendrán alcance propio.
- ARS, vencimiento exacto de 72 horas, orden única y ausencia de confirmación
  por apertura/redirect siguen vigentes. No exponer tokens en documentos o logs.

### Comisión pendiente

No se encontró tasa ni fórmula aprobada en la búsqueda documental.
[REQ-001, RESTRICCIONES](REQ-001-activacion-y-vigencia-pro.md#restricciones)
mantiene pendientes porcentaje y base; su sección PREGUNTAS ABIERTAS también
mantiene el porcentaje pendiente. Fórmula, base y redondeo deberán aprobarse:
bloquean activación productiva, pero no el adaptador interno deshabilitado.
No se inventa porcentaje ni importe. Se preserva la exención por suscripción
paga de REQ-001; esta decisión no aprueba recargo al cliente ni cambia importe 4B.

### Fuentes oficiales consultadas y límites

Consulta: 2026-09-17T12:14:36-03:00.
[Orders API](https://www.mercadopago.com.ar/developers/es/reference/online-payments/checkout-pro-orders/overview),
[Crear order](https://www.mercadopago.com.ar/developers/es/reference/online-payments/checkout-pro/create-order/post),
[Marketplace/OAuth](https://www.mercadopago.com.ar/developers/es/docs/checkout-api-payments/how-tos/integrate-marketplace).

Crear order confirma header obligatorio, `id`, `checkout_url` y
`marketplace_fee`. La guía marketplace aún ejemplifica Preferences:
se utiliza como fuente de OAuth por vendedor, no como payload Orders.
La validación operativa conjunta sigue pendiente antes de producción.
La clave Orders admite hasta 128 caracteres; el puerto neutral admite 160:
validar compatibilidad sin truncar ni regenerar. La sugerencia genérica de
nueva clave ante 409 no autoriza cambiar la reserva MANDOBRA.
El mapeo de vigencia y datos mínimos del pagador requiere diseño posterior;
no trasladar campos Preferences ni ampliar privacidad silenciosamente.



## Problema

La dirección vigente de integración se define en la realineación 4C anterior;
las referencias anteriores a preferencias describen el diseño histórico.

Un profesional necesita cobrar el importe acordado de un contrato interno tanto
a distancia como presencialmente, sin que presentar dos canales genere dos
ordenes o permita interpretar una apertura del checkout como pago confirmado.

## Objetivo

Definir el contrato neutral y puro para crear una unica orden temporal de cobro
en ARS, cuya URL de Checkout Pro pueda compartirse directamente o codificarse en
un QR. Esta especificacion no implementa el contrato, la persistencia, Mercado
Pago ni efectos financieros o PRO.

## Actores

- Profesional: introduce el importe acordado y solicita la orden correspondiente
  a un contrato propio.
- Cliente: abre el mismo enlace desde un canal remoto o desde el QR presencial.
- MANDOBRA: deriva propiedad e identidad, valida el comando y genera referencias
  opacas e idempotencia interna.
- PSP: capacidad futura que creara la preferencia y devolvera su identificador y
  URL; no queda conectado por esta especificacion.

## Flujos

### Presencial

1. El profesional solicita una orden para la obligacion autorizada.
2. MANDOBRA crea o reutiliza la unica orden activa.
3. La interfaz futura representa la URL de esa orden como QR.
4. Escanear o abrir el QR no confirma el pago.

### A distancia

1. El profesional solicita la misma orden.
2. Copia o comparte su URL de Checkout Pro.
3. Mostrar, copiar o compartir la URL no crea una orden adicional.
4. Abrirla o recibir un redirect no confirma el pago.

## Reglas funcionales aprobadas

1. El profesional introduce el importe acordado.
2. La moneda inicial es exclusivamente `ARS`.
3. El importe debe ser `Decimal`, positivo, finito y con hasta dos decimales.
4. La orden vence exactamente 72 horas después de su creación.
5. Solo puede existir una orden activa por obligación.
6. Una sucesora solo puede generarse después de vencer o cancelar la anterior.
7. Una orden ofrece una única URL reutilizable como enlace remoto o contenido
   del QR presencial.
8. Mostrar, copiar o compartir una presentación no crea otra orden.
9. Este MVP no usa el producto QR presencial del PSP basado en sucursales o
   cajas.
10. Redirect, apertura del checkout o visualización del QR no confirman pago.
11. Solo un pago aprobado y conciliado idempotentemente puede producir efectos
    financieros o PRO en incrementos futuros autorizados.

## Contrato neutral previsto

```text
PSPPaymentOrderCreationAdapter.create_payment_order(command)
    -> PaymentOrderCreationResult
```

- `PaymentOrderCreationCommand`: DTO inmutable de entrada.
- `PaymentOrderCreationResult`: DTO inmutable de salida.
- `PSPPaymentOrderCreationAdapter`: protocolo separado de `PSPAdapter` y
  `PSPPaymentQueryAdapter`.

No se reutiliza `PSPAdapter.create_attempt()` para preferencias, no se amplía la
capacidad de consulta y el ID de preferencia no se guarda como
`PaymentAttemptRecord.external_attempt_id`.

## Campos y autoridad

| Dato | Autoridad | Regla |
| --- | --- | --- |
| obligación/contrato | `ContractRequest` | Fuente vigente de propiedad en contratos internos. |
| importe y moneda | `PaymentObligation` | Proyección monetaria actual; moneda inicial `ARS`. |
| `professional_id` | actor autenticado o contrato | Nunca elegido libremente por el navegador. |
| `external_reference` | MANDOBRA | Opaca, no secuencial y sin datos personales. |
| `idempotency_key` | MANDOBRA | Generada internamente; no controlada por el navegador. |
| `concept` | backend MANDOBRA | Generado o saneado, acotado y sin datos sensibles innecesarios. |
| ambiente | configuración del adaptador | Explícita e inmutable. |
| `created_at` | reloj controlado del servicio | Instante UTC de creación. |
| `expires_at` | MANDOBRA | Exactamente `created_at + 72 horas`. |
| ID y URL de preferencia | PSP futuro | Resultado de creación; no son prueba de pago. |

Los nombres finales de campos del DTO podrán ajustarse durante la implementación
sin cambiar estas autoridades ni incorporar datos fuera del contrato aprobado.

## Validaciones e invariantes del contrato puro

- Rechazar tipos ambiguos; en particular, no aceptar `float` para importes.
- Exigir `Decimal` positivo, finito y con escala máxima de dos.
- Exigir moneda canónica exactamente `ARS`.
- Exigir identificadores, referencias, idempotencia y concepto no vacíos,
  acotados y sin caracteres de control.
- Exigir fechas conscientes de zona horaria y calcular 72 horas exactas.
- Mantener DTO, resultado y configuración inmutables.
- Exigir que `checkout_url` sea una URL absoluta, use exclusivamente HTTPS,
  tenga hostname válido y no vacío, y no contenga usuario, contraseña,
  fragmento, caracteres de control ni whitespace inseguro. Esquemas
  alternativos y URLs estructuralmente inválidas se rechazan antes de exponer
  el resultado.
- La validación neutral de `checkout_url` garantiza seguridad estructural, no
  que la URL pertenezca a Mercado Pago. La allowlist exacta de hosts confiables
  corresponde al futuro adaptador Mercado Pago.
- Un replay del fake con la misma idempotencia y contenido devuelve el mismo
  resultado; contenido diferente con la misma clave produce conflicto.
- El fake usa reloj, identificadores y escenarios inyectables y no se presenta
  como garantía de persistencia o producción.

## Correspondencia entre comando y resultado

Cada `PaymentOrderCreationResult` debe corresponder inequívocamente al
`PaymentOrderCreationCommand` que originó la creación. La frontera pura compara
de forma exacta todos los campos compartidos definidos por los DTO definitivos,
incluidos:

- `local_order_id`;
- `obligation_reference`;
- `external_reference`;
- `amount`;
- `currency`;
- `concept`;
- `idempotency_key`;
- `created_at`;
- `expires_at`.

Los campos aportados por el adaptador —`external_order_id`, `checkout_url`,
`provider` y `live_mode`— se validan independientemente. Ninguno puede cambiar
la identidad ni los valores canónicos del comando. Un eco alterado convierte el
resultado en inválido, aunque los campos externos sean estructuralmente válidos.
La URL nunca confirma un pago.

## Invariantes diferidas

Requieren persistencia y no pueden acreditarse por el primer incremento puro:

- unicidad durable de una orden activa por obligación;
- sucesión segura solo tras vencimiento o cancelación;
- ownership efectivo contra sesión y contrato persistido;
- idempotencia entre procesos, locks, constraints y concurrencia PostgreSQL;
- persistencia del ID/URL de preferencia y su ciclo de vida;
- cancelación auditable;
- idempotencia durable entre procesos y reinicios;
- correlación completa entre preferencia, pago, obligación y
  `PaymentAttemptRecord`;
- efectos financieros exactamente una vez;
- conciliación con eventos y efectos financieros o PRO.

Todas estas garantías, además de ownership efectivo, persistencia, unicidad
durable de una orden activa, sucesión, locks, constraints y carreras
concurrentes, permanecen diferidas. Ni el contrato puro ni el fake las
acreditan.

## Errores tipados del primer incremento

- `InvalidPaymentOrderCreationRequestError`: comando, importe, moneda,
  identificadores, concepto o timestamps inválidos.
- `InvalidPaymentOrderCreationResultError`: resultado incoherente, eco
  alterado, identidad externa inválida, URL insegura o expiración inconsistente.
- `PaymentOrderIdempotencyConflictError`: el fake recibe la misma clave para
  contenido canónico diferente.
- `PaymentOrderCreationUncertainError`: el fake o futuro puerto informa que no
  puede determinar si la creación ocurrió.

Las excepciones deben ser neutrales y no exponer secretos, referencias internas,
payloads del proveedor ni datos personales.

Quedan diferidos los errores específicos de ownership, orden activa,
persistencia, concurrencia, cancelación, autenticación de Mercado Pago,
transporte HTTP, rechazo del proveedor y allowlist específica de hosts. No
forman parte de la taxonomía del primer incremento.

## Criterios de aceptación observables

- [x] Existen protocolo y DTOs inmutables separados de creación de intentos y
  consulta de pagos.
- [x] Los importes válidos usan `Decimal`; cero, negativos, no finitos, `float`
  y más de dos decimales son rechazados.
- [x] Solo `ARS` es aceptada.
- [x] `expires_at` equivale exactamente a `created_at + 72 horas`.
- [x] `checkout_url` se rechaza si no es HTTPS absoluta con hostname válido, si
  incluye credenciales o fragmento, o si contiene controles o whitespace
  inseguro; no se aceptan esquemas alternativos.
- [x] Una URL estructuralmente válida no se presenta como URL comprobada de
  Mercado Pago y nunca se interpreta como confirmación de pago.
- [x] El resultado coincide exactamente con todos los campos compartidos del
  comando y rechaza cualquier eco alterado.
- [ ] El fake determinista demuestra creación, consulta y replay idempotente.
- [x] La misma clave con contenido material distinto produce conflicto.
- [ ] Enlace y QR representan una sola URL y no crean órdenes adicionales.
- [ ] Ninguna presentación, apertura o redirect se interpreta como pago.
- [x] Las pruebas no atribuyen al fake persistencia, concurrencia ni integración
  productiva.

## Matriz de pruebas prevista

| Área | Casos mínimos |
| --- | --- |
| Importe | válido; cero; negativo; infinito; NaN; `float`; más de dos decimales. |
| Moneda | `ARS`; moneda diferente; casing/whitespace no canónico. |
| Tiempo | reloj controlado; UTC; vencimiento exacto a 72 horas. |
| Identidad | referencia opaca; campos vacíos; controles; límites. |
| Correspondencia | cada campo compartido coincide; casos negativos para `local_order_id`, obligación, referencias, importe, moneda, concepto, idempotencia y timestamps alterados. |
| URL | HTTPS absoluta válida; hostname vacío; HTTP y otros esquemas; credenciales; fragmento; controles; whitespace; URL estructural válida fuera de la futura allowlist. |
| Idempotencia | creación; replay idéntico; conflicto material. |
| Fake | estados deterministas; IDs/reloj inyectados; aislamiento entre instancias. |
| Inmutabilidad | intento de reasignar DTO, resultado y configuración. |
| Seguridad | mensajes neutrales; ausencia de secretos y datos personales. |

## Seguridad y privacidad

- El navegador no elige `professional_id`, referencias externas ni claves de
  idempotencia.
- `external_reference` no contiene IDs secuenciales, nombres, emails, teléfonos
  ni otros datos personales.
- No se registran secretos, credenciales, URLs sensibles ni payloads crudos.
- La URL de checkout no acredita identidad, autorización ni pago.
- Ownership y autorización deben comprobarse en backend cuando exista la capa
  de aplicación; no se delegan a controles visuales.

## Alcance del primer incremento

Incluye protocolo neutral, DTOs inmutables, validaciones puras, errores tipados
mínimos, fake determinista en memoria, pruebas unitarias y documentación.

## Fuera de alcance

- HTTP, SDK, credenciales o creación real en Mercado Pago.
- Persistencia ORM, migraciones, locks o constraints PostgreSQL.
- QR gráfico, frontend o compartir por WhatsApp.
- Workers, retries, nuevos webhooks o conciliación automática.
- Activación PRO, créditos, comisiones, ARCA, deploy o producción.

## Dependencias futuras

- Servicio de aplicación que derive ownership desde `ContractRequest`.
- Modelo durable de orden y unicidad activa por obligación.
- Adaptador HTTP de creación de preferencias y configuración segura.
- Superficie de enlace/QR y controles de autorización.
- Conciliación idempotente antes de cualquier efecto financiero o PRO.

## Estado de implementación

### Actualización vigente - incremento técnico local 4B

Timestamp: 2026-09-17T10:57:38-03:00
Agente: Codex - implementador documental local
Rama: `feature/checkout-pro-payment-order-application`
Commit técnico: `1ba5ab10c4606903f59b0562c698e233ff0dfbe5`
Implementación: 2026-09-17T10:39:29-03:00
Testing aprobado: 2026-09-17T10:46:15-03:00
Agente verificador: `03 - Testing - Test Executor`
Estado formal: `APROBADO`; implementación productiva completa: `PENDIENTE`.

Al contrato puro, fake determinista y persistencia 4A se suma el servicio de
aplicación `PaymentOrderApplicationService`. Recarga al actor profesional activo,
comprueba ownership en contrato y perfil y autoriza únicamente `CONFIRMADA`.
La obligación final tiene FK nullable y única a `ContractRequest`, conservando
filas legacy sin vínculo inventado. El importe procede exclusivamente de
`precio_acordado`, moneda ARS; no se acepta importe ni professional_id del cliente.
Esto concreta la fuente backend aprobada sin modificar las reglas comerciales.

La reserva durable conserva comando, referencias, concepto no sensible,
timestamps UTC y clave idempotente generados una sola vez. Confirma el claim antes
del adaptador y cierra la sesión/transacción durante la llamada. La segunda
transacción revalida contexto y registra orden, auditoría y resultado atómicamente.
Replay exitoso devuelve la misma orden; contenido material incompatible genera
conflicto. Error, incertidumbre o caída tras el claim conservan el bloqueo y no
generan otra clave ni llamada automática. Recuperación/conciliación y renovación
desde esta capa de aplicación quedan diferidas. 4B no expone desde el servicio de
aplicación la creación de órdenes sucesoras después de expiración o cancelación;
esa evolución permanece pendiente.
Migración/head único `20260917_01`, descendiente de `20260916_01`.

Evidencia histórica aprobada de Testing, suministrada para este registro y no
reejecutada: focales 26/26; regresiones PSP/pagos 141/141; PostgreSQL 6/6;
suite 531 ejecutadas, 526 aprobadas, 5 omisiones históricas, 0 fallos y 0 errores.
Compileall, Alembic, upgrade–downgrade–upgrade y git diff --check aprobados;
ningún hallazgo P0–P3. La inspección directa del commit confirma modelo,
migración, servicio y pruebas; no constituye una nueva ejecución de Testing.

No existe flujo productivo disponible para usuarios. Continúan pendientes
endpoints, creación HTTP real en Mercado Pago, checkout/QR, integración de órdenes
con webhooks y conciliación, efectos PRO, comisiones, facturación, publicación,
PR, merge y producción. Próximo paso: planificar/revisar creación real y frontera
pública. Se preservan los criterios originales sin marcar y los registros
históricos siguientes; sus garantías diferidas describen cada incremento anterior,
no niegan las capacidades internas 4A/4B ahora acreditadas.

### Registro histórico inicial

Al `2026-09-14T10:21:05-03:00` no existe implementación de este contrato. Esta
Feature Spec autoriza preparar el primer incremento delimitado, pero no acredita
ninguna capacidad productiva ni autoriza commit, publicación o despliegue.

## Registro de corrección documental

Timestamp: 2026-09-14T10:30:15-03:00
Agente: 02 - Implementación y Refinación
Motivo: corrección de hallazgos documentales P1/P2
Documento: REQ-003
Estado: CORREGIDO_PENDIENTE_DE_REVALIDACION

Hallazgos atendidos:

- seguridad estructural de `checkout_url`;
- garantías diferidas;
- correspondencia entre comando y resultado;
- taxonomía exacta de errores.

La revisión histórica `REQUIERE_CORRECCIONES` del
`2026-09-14T10:27:58-03:00` se conserva mediante este registro; no se presenta
la corrección como implementación ni como revalidación aprobada.

## Actualización del avance técnico

Timestamp: 2026-09-14T20:43:27-03:00
Agente: Codex - implementador documental local
Rama: `feature/checkout-pro-payment-order-contract`
HEAD observado: `12c64187bce3137057c6e3e4a261b1f600b2867b`
Estado: `APROBADO`
Implementación productiva completa: `PENDIENTE`

El commit `6d6dd2f97ed6e891b4efbfae67aca25398f28e60` implementó el
contrato neutral de creación, `PaymentOrderCreationCommand`,
`PaymentOrderCreationResult`, sus validaciones puras, correspondencia canónica
y errores tipados, junto con sus pruebas unitarias. El commit
`12c64187bce3137057c6e3e4a261b1f600b2867b` agregó el adaptador determinista
en memoria, idempotencia aislada por instancia, conflicto por contenido
material y cobertura de concurrencia local.

El contrato puro y el fake determinista constituyen un avance técnico parcial
implementado y probado.
Persistencia durable, ownership efectivo, unicidad activa entre procesos,
integración real con Mercado Pago, HTTP, checkout productivo, QR o interfaz,
conciliación, efectos financieros y efectos sobre PRO continúan pendientes.
Por ello la implementación productiva completa de REQ-003 permanece pendiente
y no está disponible como capacidad para usuarios.

## Actualización posterior - incremento técnico 4A

Timestamp: 2026-09-16T22:40:04-03:00
Agente: 01 - Documentation Engineer
Motivo: cierre documental controlado de la fundación interna de persistencia.
Rama: `feature/checkout-pro-payment-order-persistence`
Commit técnico: `4373b64e419360f7ca3f649efc8f97580c6b42d8`
Estado del requisito: `APROBADO`
Implementación productiva completa: `PENDIENTE`

El incremento 4A está implementado y aprobado localmente. Agrega el modelo
independiente `PaymentOrder`, tabla `payment_orders`, servicio
`payment_order_persistence_service.py` y migración `20260916_01`,
descendiente de `20260911_02`. El nuevo head Alembic único es
`20260916_01`. No reutiliza `PaymentAttemptRecord` ni almacena una
preferencia en `external_attempt_id`.

La fundación registra comandos y resultados previamente validados; no invoca
al adaptador externo. Persiste identificador externo, `checkout_url`,
`provider`, `live_mode`, referencias, importe, timestamps y ciclo de vida.
Acredita replay durable, conflictos materiales, bloqueo de obligación,
unicidad activa por obligación, identidad PSP contextual, estados `ACTIVE`,
`EXPIRED` y `CANCELLED`, vencimiento de 72 horas y sucesión local tras
vencimiento o cancelación. Un replay terminal conserva la orden histórica.

La creación, expiración y cancelación local incluyen auditoría atómica. Los
helpers usan `flush()` y no ejecutan commit ni rollback global; la transacción
pertenece al llamador. PostgreSQL utiliza un savepoint para recuperar carreras
de inserción, además de locks y constraints concurrentes.
SQLite acredita compatibilidad y rollback transaccional, no equivalencia de
garantías concurrentes con PostgreSQL. El contrato calcula 72 horas exactas y
PostgreSQL las exige mediante constraint; SQLite utiliza la comprobación
temporal con tolerancia implementada, sin afirmar exactitud submilisegundo de
su constraint.

### Evidencia aprobada del commit técnico

Evidencia suministrada por el usuario para este cierre, no ejecutada nuevamente
en esta sesión documental:

- Focales de persistencia y migración: 11/11.
- Regresiones relacionadas: 141/141.
- PostgreSQL real: 6/6.
- Suite completa: 515 ejecutadas, 510 aprobadas, 5 omitidas históricas,
  0 fallos y 0 errores.
- `compileall`, Alembic y `git diff --check`: aprobados.
- Revalidación independiente: sin hallazgos P0-P3.
- Head Alembic único aprobado: `20260916_01`.

### Criterios técnicos internos acreditados en 4A

- [x] Existe `PaymentOrder` independiente de los intentos financieros y una
  migración que crea su persistencia sin sobrecargar `PaymentAttemptRecord`.
- [x] El registro durable conserva el comando y resultado canónicos; replay
  idéntico devuelve la misma orden y contenido material distinto produce conflicto.
- [x] El servicio bloquea la obligación y el índice único parcial impide dos
  registros `ACTIVE` de la misma obligación en PostgreSQL.
- [x] El servicio materializa expiración, conserva cierres históricos y admite
  sucesión local solo cuando no queda una orden activa.
- [x] La cancelación local y las transiciones de creación/expiración registran
  auditoría en la transacción del llamador.
- [x] Se almacenan identidad externa de orden, URL, proveedor, ambiente y
  timestamps, con identidad PSP contextual separada de la identidad de pago.
- [x] Existen pruebas de migración, regresión, concurrencia PostgreSQL y
  rollback transaccional SQLite con la evidencia aprobada indicada.

Los criterios originales sin marcar se conservan: el fake no implementa una
operación de consulta, y presentación QR/enlace o retorno del navegador son
criterios más amplios que esta persistencia. Las invariantes diferidas de los
registros previos describen el alcance histórico del contrato puro; esta
actualización acredita solo las garantías internas delimitadas de 4A.

### Pendientes y próximo incremento

4B debe preparar el servicio de aplicación y ownership contractual derivados
de sesión y `ContractRequest`, todavía sin Mercado Pago real. Almacenar
`professional_id` es un snapshot con FK, no prueba de autorización.

Continúan pendientes el servicio público/autorizado, creación HTTP real,
recuperación de resultados externos inciertos, checkout/QR visibles,
integración de las órdenes con webhooks y conciliación, correlación con pagos,
efectos PRO, comisiones y facturación. La infraestructura PSP previa no queda
extendida por 4A. Cancelar localmente una orden no cancela una preferencia remota.

Publicación, PR, merge de esta rama y producción permanecen pendientes. No
existe un flujo de cobro disponible para usuarios ni se completa REQ-003.
