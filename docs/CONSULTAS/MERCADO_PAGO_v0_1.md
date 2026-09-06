# MANDOBRA - Consultas tecnicas y comerciales a Mercado Pago

Version: 0.1  
Timestamp de incorporacion: 2026-09-06T19:22:08-03:00  
Estado: BORRADOR_DE_CONSULTA_NO_ENVIADO  
Responsable de producto: Cristian Sánchez  
Pais y moneda previstos: Argentina, ARS  
Rama: `docs/pro-commercial-psp-refinement`  
Commit base observado: `1548935`

## Proposito y limites

Validar dos circuitos distintos: cobro de servicios del profesional al cliente
mediante MANDOBRA y cobro de la suscripcion propia de MANDOBRA al profesional.
Las respuestas deben identificar producto/API, pais y tipo de cuenta; una
capacidad de Checkout no se presume disponible en Suscripciones o Split.

El checkout podra abrirse por enlace o por un QR que contenga ese enlace. No se
promete compatibilidad con el lector QR nativo de Mercado Pago. Se estudia el
reparto entre profesional y plataforma, sin darlo por contratado ni validado.
Los creditos son internos de MANDOBRA; no se presume que el PSP los admita como
medio de pago. Este borrador no autoriza contactar al proveedor ni implementar.

## Comportamiento que se necesita validar

- Periodos de suscripcion de exactamente 30 dias e inicio futuro.
- Medio de pago vinculado aun cuando creditos cubran un periodo, distinguiendo
  registro de medio y autorizacion de debito.
- Creditos aplicables total o parcialmente; diferencia cero sin cargo ficticio.
- Reserva durante pago mixto y consumo solo con pago completo confirmado.
- Inicio inmediato desde prueba/gracia e inicio diferido desde periodo
  transaccional obtenido con creditos.
- Renovacion automatica o manual con confirmacion efectiva del cambio.
- Prevencion de doble financiacion entre pago manual, automatismo y reintentos.
- Al vencer suscripcion impaga, gracia PRO transaccional de 10 dias, con
  comision MANDOBRA y reintentos coordinados.

## Cuestionario

| ID | Consulta | Evidencia requerida |
| --- | --- | --- |
| MP-01 | Producto que admite recurrencia de 30 dias exactos, inicio futuro y cambio de fecha. | API, parametros, restricciones y prueba de calendario. |
| MP-02 | Detencion de proximos cobros/reintentos y efecto sobre cobros iniciados. | Estados, punto de corte, confirmacion y carrera temporal. |
| MP-03 | Antelacion tecnica obligatoria, unidad y zona horaria. | Documento o respuesta escrita; separar requisito y recomendacion. |
| MP-04 | Coordinacion de pago manual con debito o reintento pendiente. | Identificador comun, consulta autoritativa y cancelacion. |
| MP-05 | Cargo variable al aplicar descuento interno y diferencia monetaria cero. | Limites de modificacion y fecha de corte. |
| MP-06 | Vinculacion/autorizacion cuando creditos cubren el primer periodo. | Flujo sin cargo ficticio y eventuales verificaciones/reversas. |
| MP-07 | Medios admitidos en Argentina, incluida tarjeta MP prepaga, credito y saldo. | Matriz por producto, cuenta y escenario. |
| MP-08 | Demora de aprobacion, notificacion y disponibilidad del dinero. | Tiempos documentados, garantias y excepciones. |
| MP-09 | Aprobacion tardia de intento expirado o cancelado. | Estados definitivos y fuente autoritativa. |
| MP-10 | Idempotencia y entrega de notificaciones. | Claves, duplicados, orden, firma, autenticacion y reenvios. |
| MP-11 | Calendario y control de reintentos de Suscripciones. | Suspension y prevencion de cobro tras baja/cambio de modalidad. |
| MP-12 | Marketplace con comision variable o cero segun entitlement. | Elegibilidad, OAuth, Split/reparto, costos, limites y revocacion. |
| MP-13 | Enlaces para servicios no originados en el marketplace. | Condiciones, actividades permitidas y responsabilidades. |
| MP-14 | Costos, impuestos, retenciones y tiempos de cada circuito. | Tarifario, sujeto que soporta cada cargo y devoluciones. |
| MP-15 | Reversion de pago, comision y reparto. | Reembolsos parciales/totales, contracargos, eventos y plazos. |
| MP-16 | Prueba previa a produccion. | Sandbox, limitaciones y casos que requieren soporte. |

Todos los MP-ID tienen estado inicial `PENDIENTE`. No son requisitos globales.

## Pruebas de aceptacion a acordar

1. Apagar renovacion antes del cobro no crea otro intento.
2. Apagar durante un cobro conserva estado pendiente y exige conciliacion.
3. Pago manual simultaneo con reintento financia un solo periodo.
4. Pago mixto aprobado consume una vez los creditos reservados y cobra la diferencia.
5. Pago mixto rechazado no consume; libera conforme al vencimiento original.
6. Vencimiento de creditos durante espera PSP contempla cancelacion y aprobacion tardia.
7. Cobertura 100% con creditos no crea cargo indebido y preserva autorizacion futura valida.
8. Notificaciones duplicadas, tardias o desordenadas convergen al mismo saldo y vigencia.
9. Inicio de suscripcion al final del periodo transaccional no duplica financiacion.
10. Pago aprobado se distingue de dinero disponible para retiro.

## Comunicacion y coordinacion juridica

No existe antelacion aprobada para desactivar renovacion ni debe prometerse un
plazo generico de 24-72 horas. La UI debe distinguir solicitud, confirmacion y
cobro en curso, preservar la fecha y no responsabilizar al usuario por
duplicados. Un timeout visual no acredita fracaso.

Cruzar MP-02/03/04/11 con baja, consentimiento y cargos en transito;
MP-05/06/09/15 con creditos, restituciones y pagos mixtos; MP-12/13/14 con
comision al cliente, responsabilidad, impuestos y facturacion. Ver
[base de revision juridica](../LEGAL/BASE_REVISION_JURIDICA_v0_2.md).

## Registro de respuestas

Por cada MP-ID registrar fecha, area y responsable del proveedor, ticket,
producto/API y version, pais, tipo de cuenta, respuesta o adjunto, enlace
oficial, limites, prueba reproducible, conclusion y pendiente. MP-01 a MP-11
condicionan renovacion y creditos; MP-12 a MP-15 condicionan marketplace y
calculo economico. Una respuesta comercial general no acredita compatibilidad.

Referencias iniciales, no confirmacion del flujo compuesto:
[Gestion de suscripciones](https://www.mercadopago.com.ar/developers/es/docs/subscriptions/subscription-management)
y [Resumen de Suscripciones](https://www.mercadopago.com.ar/developers/es/docs/subscriptions/overview).

No se contacto al proveedor ni se publicaron condiciones.
