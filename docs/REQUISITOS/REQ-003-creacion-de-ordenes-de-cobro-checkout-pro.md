---
id: REQ-003
titulo: Creacion de ordenes de cobro Checkout Pro
estado: APROBADO
fecha_aprobacion: 2026-09-14T10:05:02-03:00
responsable: Cristian Sánchez
rama_documental: feature/checkout-pro-payment-order-contract
implementacion: PENDIENTE
ultima_revision: 2026-09-14T20:43:27-03:00
---

# REQ-003 - Creacion de ordenes de cobro Checkout Pro

## Problema

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
