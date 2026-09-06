# MANDOBRA - Base comercial y encargo de revision juridica

Version de contenido: 0.2  
Origen local recibido: archivo rotulado `v0_1`  
Elaboracion original: 2026-09-06T16:42:32-03:00  
Timestamp de incorporacion: 2026-09-06T19:22:08-03:00  
Estado: BORRADOR_PARA_REVISION_DE_PRODUCTO_JURIDICA_Y_CONTABLE  
Responsable de producto: Cristian Sánchez  
Alcance territorial inicial a evaluar: Argentina  
Rama: `docs/pro-commercial-psp-refinement`  
Commit base observado: `1548935`

## Proposito y limites

Explicar el funcionamiento comercial aprobado o propuesto para que asesoria
juridica y contable determine encuadre, riesgos e instrumentos necesarios. No
es dictamen, contrato ni texto publicable. La Foundation PRO fue integrada por
PR #5, pero no implementa creditos, PSP, recurrencia ni estas transiciones.
La regla historica de 60 dias por operacion fue reemplazada documentalmente sin
borrar su historia. Este expediente no autoriza implementacion ni contacto.

## Decisiones comerciales aprobadas

- Catalogo `FREE`, `PRO`, `ENTERPRISE`; PRO inicial solo para profesional
  activo y verificado. ENTERPRISE sigue conceptual.
- Un solo entitlement PRO para modalidad transaccional y suscripcion. Solo la
  suscripcion vigente exime comision MANDOBRA; costos PSP son distintos.
- Direccion de producto: Mercado Pago, checkout por enlace y QR con ese enlace.
  No se promete QR nativo, marketplace, Split ni viabilidad contractual.
- El cliente debe conocer servicio, cargo MANDOBRA y total antes de aceptar; el
  neto profesional es estimado. Legalidad, fiscalidad, tasa y formula siguen
  pendientes.
- Cobros de plataforma, incluso enlaces admitidos para trabajos externos,
  pueden generar creditos por comisiones efectivas. Efectivo y pagos externos
  no generan creditos.
- Prueba inicial de 30 dias tras onboarding PSP validado.
- Lotes de creditos con vencimiento individual de 40 dias, consumo FIFO, sin
  rejuvenecimiento; excedente y saldo vigente sobreviven al paso a FREE.
- Un umbral equivalente a la suscripcion de 30 dias concede 30 dias
  transaccionales. Precio, base y conversion siguen pendientes. No hay
  extension de 15 dias.
- Creditos vigentes pueden cubrir total o parcialmente primera suscripcion y
  renovaciones. Diferencia cero no genera cargo ficticio.
- Suscripciones de 30 dias fijos. Durante su vigencia cesa la comision
  MANDOBRA y normalmente no nacen creditos nuevos.
- Pago durante prueba o gracia inicia suscripcion inmediatamente. Contratacion
  durante periodo transaccional obtenido con creditos inicia al finalizarlo.
- Vencida una suscripcion impaga, se ingresa en gracia PRO transaccional de 10
  dias, sin exencion. Periodos gratuitos no consumen creditos ni terminan por
  alcanzar el umbral.
- Vincular medio de pago no equivale a autorizar debitos automaticos. No deben
  persistirse datos sensibles de tarjeta innecesarios.
- Facturacion PRO es opcional y separada del cobro: trabajo confirmado, pago
  aprobado y comprobante autorizado son hechos distintos.

## Propuestas pendientes de aprobacion juridica y de producto

| ID | Propuesta | Revision necesaria |
| --- | --- | --- |
| P-01 | Renovacion automatica con aceptacion expresa y opcion manual diferenciada. | Importe, frecuencia, inicio, medio, baja y prueba del consentimiento. |
| P-02 | Baja ordinaria frena cargos futuros y conserva acceso pagado. | Separar baja, cuenta, arrepentimiento, incumplimiento y devolucion. |
| P-03 | Avisar fin de exencion y mostrar comision antes de cada cobro. | Ordenes y condiciones economicas ya aceptadas. |
| P-04 | Una sola gracia por periodo efectivamente pagado; reintentos no la reinician. | Alcance cuando el periodo fue financiado con creditos. |
| P-05 | Al terminar gracia, consumir umbral valido o pasar a FREE. | Prioridad frente a pagos y creditos pendientes. |
| P-06 | La gracia no genera deuda de suscripcion. | Relacion con reintentos autorizados. |
| P-07 | Un pago o credito no financia dos periodos. | Reserva, confirmacion, consumo y reversa trazables. |
| P-08 | Abandonar renovacion evita nuevos automatismos. | Cierre de autorizacion y cobros en transito. |
| P-09 | Comprobante de solicitudes de baja, devolucion y reclamo. | Canal y plazos legales. |

## Encargo juridico y contable

### Relaciones y derechos

Determinar entidad operadora, domicilio, identificacion fiscal y territorio;
distinguir cliente-profesional, cliente-MANDOBRA, profesional-MANDOBRA y PSP.
Evaluar relacion de consumo, informacion precontractual, publicidad, precios,
aceptacion electronica, renovacion y prueba de version. Definir baja,
arrepentimiento, excepciones y reintegros; no aprobar “sin devoluciones”.

### Comisiones, responsabilidades y fiscalidad

Determinar naturaleza, deudor, devengamiento y facturacion del cargo MANDOBRA;
revisar recargos por medio de pago y precio total. Delimitar responsabilidades
reales sin exclusion total ni promesas de custodia. Validar contratos PSP para
marketplace, reparto, enlaces externos, suscripcion y reversas. Separar
comprobantes del servicio profesional, cargo MANDOBRA y suscripcion.

### Creditos y reversas

Revisar naturaleza del beneficio, vencimiento de 40 dias, avisos y saldo; si
son personales, no transferibles o no canjeables requiere aprobacion. Resolver
restitucion de pagos mixtos, vencimiento de creditos restituidos, comisiones
reembolsadas o contracargadas y prohibicion de doble compensacion. No imponer
saldo negativo o deuda sin regla aprobada.

### Datos y seguridad

Inventariar identidad, verificacion, ubicacion, contratos, pagos y fiscalidad,
con finalidad, fundamento, acceso, proveedor y retencion. Definir derechos,
transferencias, encargados, consentimiento, cifrado, accesos e incidentes.
Evitar tarjeta o secretos en logs. Separar comunicaciones operativas de
publicidad. WhatsApp, IA, ARCA y uso promocional de imagenes requieren analisis
propio cuando exista flujo definitivo.

## Matriz minima de incidencias

| Caso | Comportamiento propuesto | Pendiente |
| --- | --- | --- |
| Pago pendiente | No mostrar exito ni conceder exencion; preservar derechos vigentes. | Espera, mensaje y resultado tardio. |
| Pago rechazado | Permitir regularizar sin crear periodo pagado. | Reintentos y estado definitivo. |
| Notificacion repetida | Un solo efecto economico y de vigencia. | Evidencia y conciliacion. |
| Pago manual y debito concurrentes | No sumar periodos involuntariamente. | Restitucion de excedente. |
| Reembolso | Ajuste coordinado de dinero, comision, creditos y acceso. | Base legal/fiscal y beneficios usados. |
| Contracargo | Registrar disputa y evidencia sin presumir fraude. | Riesgo y restricciones proporcionales. |
| Pago al terminar gracia | Una unica transicion. | Prioridad temporal y zona horaria. |
| PSP caido | Estado verificable y sin repeticion de cobros. | Recuperacion y responsabilidad. |
| Baja con cobro en curso | Registrar solicitud y conciliar. | Corte y eventual devolucion. |

## Decisiones abiertas antes de implementar

1. Precio, comision, base, conversion, impuestos y moneda de creditos.
2. Reserva/cobro de inicio diferido y vencimiento de creditos reservados.
3. Politica completa de saldo residual; no borrarlo por inferencia.
4. Inicio de vigencia al pagar despues de FREE.
5. Condiciones economicas de ordenes ya aceptadas al terminar exencion.
6. Reintentos durante gracia y retorno transaccional.
7. Compatibilidad real de medios, saldo y recurrencia de 30 dias.
8. Cambios de precio respecto de creditos y umbral existentes.
9. Retencion, atencion, restitucion y obligaciones fiscales.

## Fuentes iniciales para revision

- [Ley 24.240 actualizada](https://www.argentina.gob.ar/normativa/nacional/norma-638/actualizacion).
- [Normas complementarias de Ley 24.240](https://www.argentina.gob.ar/normativa/nacional/ley-24240-638/normas-modifican).
- [Ley 25.326 actualizada](https://www.argentina.gob.ar/normativa/nacional/ley-25326-64790/actualizacion).
- [AAIP - Datos personales](https://www.argentina.gob.ar/aaip/datospersonales).
- [Mercado Pago - Suscripciones](https://www.mercadopago.com.ar/developers/es/docs/subscriptions/overview).

Son puntos de partida, no un relevamiento exhaustivo ni validacion vigente.
Solicitar a legales un encuadre por relacion, matriz normativa, observaciones y
textos revisados; a contabilidad, flujo de facturacion, impuestos, comisiones,
creditos y reversas. Cada respuesta debe indicar responsable, fecha, fundamento
y punto resuelto.

Documento relacionado: [consultas a Mercado Pago](../CONSULTAS/MERCADO_PAGO_v0_1.md).
