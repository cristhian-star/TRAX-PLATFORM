---
id: REQ-001
titulo: Activacion y vigencia de MANDOBRA PRO
estado: APROBADO
fecha_aprobacion: 2026-09-03T20:38:47-03:00
responsable: Cristian Sánchez
rama_documental: docs/spec-pro-facturacion-mvp
implementacion: IMPLEMENTACION_PARCIAL
ultima_revision: 2026-09-06T19:38:40-03:00
---

# REQ-001 - Activacion y vigencia de MANDOBRA PRO

## PROBLEMA

MANDOBRA necesita una regla unica, comprensible y verificable para conceder y
mantener el entitlement `PRO`. El flujo legacy permitia activarlo mediante
verificacion o puntos; la Foundation integrada en PR #5 ya retiro esas fuentes,
pero aun no implementa PSP, creditos, cobros ni suscripciones comerciales.

## OBJETIVO

Definir el catalogo canonico y las condiciones funcionales para activar,
extender, mantener y perder el mismo entitlement `PRO`, ya sea por actividad
transaccional que genere comision efectiva o por una suscripcion efectivamente
pagada.

## ACTORES

- Profesional prestador de servicios: unico destinatario de la primera
  implementacion de PRO.
- MANDOBRA: valida elegibilidad y vigencia antes de conceder capacidades PRO.
- PSP: sistema externo futuro que informara vinculacion y resultados de pagos;
  no se selecciona proveedor en este requisito.
- `SUPER_ADMIN`: conserva las herramientas administrativas existentes durante
  la transicion; su politica futura de concesion manual queda pendiente de la
  implementacion.
- Empresa: actor conceptual relacionado con `ENTERPRISE`; no se autoriza crear
  el actor `EMPRESA` en este feature.

## CONTEXTO ACTUAL

Estado historico verificado estaticamente en `e0eed2`, reemplazado en lo
relativo al lector PRO por la Foundation integrada en `1548935`:

- `Subscription.PLANES` admite `FREE`, `PRO` y `ENTERPRISE`.
- `has_pro_access()` considera PRO una suscripcion `ACTIVA` cuyo plan sea
  `PRO` o `ENTERPRISE`, sin evaluar una fecha de vencimiento.
- El upgrade profesional concede PRO si existe verificacion aprobada o si el
  lector legacy suma al menos 100 puntos.
- `upgrade_to_pro()` activa el plan inmediatamente y las herramientas
  administrativas permiten activarlo o quitarlo.
- La pantalla publica conserva `Free`, `Plus` y `Pro`; `Plus` contradice el
  catalogo canonico aprobado.
- No existen cobro, renovacion comercial, onboarding PSP ni vigencia
  transaccional implementados.

Estas capacidades son contexto existente, no evidencia de implementacion del
presente requisito.

## REQUISITOS FUNCIONALES

1. El catalogo canonico debe admitir exactamente `FREE`, `PRO` y `ENTERPRISE`.
2. `Plus` no debe tratarse como plan ni entitlement aprobado.
3. La primera implementacion de PRO debe estar disponible solo para
   profesionales prestadores de servicios que tengan cuenta activa y
   verificacion profesional aprobada.
4. Los puntos legacy no deben conceder, extender ni mantener PRO.
5. Deben existir dos formas de mantener el mismo entitlement funcional `PRO`:
   modalidad transaccional y modalidad por suscripcion.
6. En la modalidad transaccional, accionar el switch de cobros gestionados debe
   iniciar el onboarding con el PSP, sin conceder PRO por ese solo acto.
7. PRO transaccional debe activarse solamente cuando la vinculacion con el PSP
   haya sido completada y validada.
8. La activacion transaccional inicial debe conceder una prueba de 30 dias
   corridos.
9. Cada comision efectiva de MANDOBRA genera creditos internos sujetos a una
   conversion todavia pendiente; no extiende por si sola una cantidad fija de
   dias.
10. Cada lote de creditos vence individualmente a los 40 dias desde su
    acreditacion. Se consumen primero los mas antiguos; nuevos lotes no
    rejuvenecen los anteriores y el excedente conserva su vencimiento.
11. Operaciones rechazadas, canceladas, simuladas o sin comision efectiva no
    generan creditos. Un trabajo externo cobrado mediante un enlace admitido
    de MANDOBRA puede generarlos; efectivo y pagos procesados fuera de MANDOBRA
    no los generan. Reembolsos y contracargos requieren una politica de reversa
    aun pendiente.
12. Al vencer la prueba o un periodo transaccional, un saldo suficiente puede
    consumir un umbral equivalente al precio de 30 dias de suscripcion y
    conceder 30 dias transaccionales. Sin fuente vigente ni saldo suficiente,
    el usuario vuelve a `FREE`; pasar a FREE no borra creditos aun vigentes.
13. En la modalidad por suscripcion, PRO debe permanecer activo durante el
    periodo efectivamente pagado.
14. Una operacion realizada durante una suscripcion PRO no debe generar
    comision para MANDOBRA por la modalidad transaccional.
15. Las tarifas, retenciones o costos propios del PSP pueden seguir aplicando y
    no deben presentarse como comision de MANDOBRA.
16. Ambas modalidades deben conceder el mismo nivel funcional `PRO` y no deben
    mostrarse como planes visuales diferentes.
17. Facturacion MANDOBRA debe reconocerse como un beneficio opcional aprobado
    de PRO, sujeto a [REQ-002](REQ-002-facturacion-pro-mvp.md).
18. `ENTERPRISE` debe permanecer como definicion conceptual para empresas, sin
    implementacion, precios, beneficios, permisos ni modelo organizacional en
    este feature.
19. Los creditos pueden provenir de comisiones efectivas sobre cobros de la
    plataforma, incluidos enlaces independientes admitidos para trabajos
    externos. Efectivo y pagos fuera de MANDOBRA no generan creditos.
20. Los creditos vigentes pueden aplicarse a la primera suscripcion y a
    renovaciones: si cubren el total no se crea cargo monetario y, si cubren
    una parte, se cobra solo la diferencia. Al confirmar un pago mixto, los
    creditos se reservan y quedan indisponibles para otra operacion, pero no se
    consumen. Se consumen una sola vez exclusivamente al confirmar el pago
    completo. Un rechazo o cancelacion definitivos los libera con su
    vencimiento original; los que hayan vencido no vuelven a estar disponibles.
    Un resultado incierto debe conciliarse antes de habilitar otro cobro para
    el mismo periodo, y un rechazo aislado no es definitivo mientras el PSP
    conserve reintentos.
21. La suscripcion usa periodos fijos de 30 dias. Si se contrata durante un
    periodo transaccional obtenido con creditos, comienza al finalizarlo; si
    se paga durante prueba inicial o gracia, comienza inmediatamente.
22. La prueba inicial de 30 dias y la gracia de 10 dias son gratuitas, no
    consumen creditos y no quedan interrumpidas por alcanzar el umbral. Al
    vencer una suscripcion impaga se ingresa en gracia PRO transaccional, sin
    exencion de comision y sujeto a elegibilidad.
23. El switch `Renovacion automatica` controla la preferencia y autorizacion de
    renovacion y requiere confirmacion de sincronizacion efectiva con el PSP.
    Debe distinguirse de vincular un medio de pago. Apagarlo conserva el
    periodo ya pagado y no garantiza cancelar cobros ya iniciados; cobros y
    reintentos en curso requieren conciliacion. Antelacion tecnica y validez
    juridica permanecen pendientes.
24. El sistema, no el usuario, debe impedir que pago manual, automatico,
    reintentado o reserva de creditos para el mismo periodo financien dos veces
    o concedan dos vigencias. No se fija una antelacion ni se responsabiliza al
    usuario por no cumplir un plazo todavia desconocido.
25. Checkout y QR que contiene su enlace son la direccion de producto. No se
    presume compatibilidad con el lector QR nativo del PSP ni viabilidad de
    marketplace, Split o recurrencia hasta obtener evidencia externa.
26. Se requiere comercialmente un medio de pago con tarjeta vinculada incluso
    cuando creditos cubran el total del periodo. Su viabilidad tecnica y
    contractual esta pendiente. Vincularla no equivale a autorizar debitos
    automaticos ni autoriza inferir almacenamiento de datos sensibles.
27. Antes de aceptar un cobro, el cliente debe ver por separado el precio del
    servicio, el cargo MANDOBRA y el total. El profesional ve un neto estimado,
    no garantizado. Porcentaje, costos, retenciones, impuestos y validez
    juridica de trasladar el cargo permanecen pendientes.
28. En contratos internos, el acceso del cliente al pago y el QR/enlace del
    profesional representan la misma obligacion, no cobros independientes. Los
    medios aceptados del perfil pueden incluir efectivo, Mercado Pago o ambos;
    el efectivo no genera creditos.

## REQUISITOS NO FUNCIONALES

- La evaluacion del entitlement debe ser consistente en todas las superficies
  protegidas y no depender de controles visuales.
- Las altas, extensiones, cambios de modalidad y bajas deben ser trazables y
  auditables.
- Los eventos externos repetidos no deben duplicar dinero, creditos, consumo ni
  vigencia.
- Las operaciones simultaneas no deben reducir ni perder una vigencia valida.
- Las fechas deben almacenarse y compararse con una politica de zona horaria
  explicita, preservando el significado de dias corridos.
- Los errores de PSP deben manejarse de forma segura, sin exponer credenciales
  ni conceder acceso por estados ambiguos.
- Deben preservarse autorizacion por rol, estado de cuenta, verificacion,
  privacidad, idempotencia y aislamiento entre usuarios.
- La implementacion debe poder validarse con PostgreSQL real cuando intervengan
  concurrencia, locks, constraints o atomicidad dependiente del motor.

## REGLAS DE NEGOCIO

1. `PRO` es un entitlement funcional unico; su fuente no crea subplanes.
2. Cuenta activa y verificacion profesional aprobada son condiciones minimas de
   elegibilidad, no fuentes autonomas de PRO.
3. La vinculacion incompleta con un PSP no concede la prueba.
4. Solo una comision efectiva de MANDOBRA genera creditos para la modalidad
   transaccional; el lote no concede tiempo por si solo.
5. Un mismo pago, lote de creditos o periodo no puede consumirse ni concederse
   dos veces; las transiciones deben ser idempotentes y conciliables.
6. Una suscripcion efectivamente pagada mantiene PRO durante su periodo valido
   y excluye la comision transaccional de MANDOBRA sobre las operaciones.
7. Al perder todas las fuentes vigentes de entitlement, el plan funcional
   vuelve a `FREE`.
8. Verificacion, reputacion y plan comercial son ejes independientes.

## RESTRICCIONES

- El porcentaje de comision no esta definido.
- Precio, porcentaje, base de comision, conversion y moneda contable de los
  creditos no estan definidos. La periodicidad aprobada es de 30 dias fijos.
- Mercado Pago es la direccion de producto para evaluar, pero producto/API,
  marketplace, Split y estrategia tecnica no estan validados.
- No se aprueba un modelo de datos, migracion, servicio o interfaz concretos.
- El catalogo completo de beneficios y limites PRO permanece pendiente.
- La documentacion aprobada no autoriza implementacion ni promesa comercial.

## FUERA DE ALCANCE

- Implementar pagos, onboarding PSP, webhooks, suscripciones o cobros.
- Modificar la pantalla de Planes o eliminar `Plus` del template actual.
- Fijar precios, porcentajes de comision, impuestos o costos de proveedores.
- Crear el actor `EMPRESA` o capacidades operativas `ENTERPRISE`.
- Definir promociones pagas, ranking o reputacion.
- Diseñar modelos, migraciones, contratos de API o arquitectura definitiva.
- Implementar el modulo de facturacion descrito en REQ-002.

## DEPENDENCIAS

- Estado activo de la cuenta.
- Verificacion profesional aprobada.
- Modelo y servicio legacy `Subscription`, que deberan refinarse durante la
  implementacion sin asumir que satisfacen este requisito.
- Seleccion y validacion futura de un PSP.
- Politicas comerciales aun pendientes.
- [REQ-002 - Facturacion PRO MVP](REQ-002-facturacion-pro-mvp.md).
- Futuro ADR para fuente de entitlement, integracion PSP, concurrencia,
  idempotencia y custodia de credenciales.

## RIESGOS

- Conceder PRO antes de validar la vinculacion externa.
- Mantener accesos vencidos por depender solo del estado `ACTIVA`.
- Duplicar o extender incorrectamente la vigencia por notificaciones repetidas.
- Reducir una vigencia existente ante operaciones simultaneas o fuera de orden.
- Cobrar comision de MANDOBRA durante una suscripcion paga.
- Confundir costos del PSP con comisiones de MANDOBRA.
- Mantener puntos legacy como permiso oculto.
- Suspender beneficios sin una politica definida ante contracargos o
  revocaciones.
- Presentar `ENTERPRISE` como disponible cuando solo esta definido
  conceptualmente.

## CASOS LÍMITE

- Vinculacion iniciada pero incompleta.
- Credenciales o autorizacion del PSP revocadas.
- Cuenta suspendida durante una vigencia activa.
- Verificacion profesional revocada.
- Pago rechazado.
- Pago aprobado que no genera comision efectiva para MANDOBRA.
- Reembolso o contracargo posterior a una operacion que genero creditos.
- Dos o mas operaciones elegibles procesadas simultaneamente o fuera de orden.
- Operacion realizada durante una suscripcion paga.
- Vencimiento de la prueba sin otra fuente de entitlement.
- Cambio entre modalidad transaccional y suscripcion.
- Superposicion entre prueba, periodo transaccional y periodo suscripto.
- Diferencias de fecha, hora y zona horaria.
- Notificaciones duplicadas del PSP.

El comportamiento detallado de los casos cuya politica permanece abierta debe
resolverse antes de implementar; este requisito no inventa su solucion tecnica.

## CRITERIOS DE ACEPTACIÓN

- [ ] El catalogo funcional acepta `FREE`, `PRO` y `ENTERPRISE` y rechaza
  `Plus` como entitlement.
- [ ] Solo un profesional con cuenta activa y verificacion aprobada puede
  iniciar cualquiera de las modalidades PRO.
- [ ] Los puntos legacy no alteran la elegibilidad ni la vigencia PRO.
- [ ] Accionar el switch transaccional sin completar la vinculacion PSP no
  concede PRO.
- [ ] Una vinculacion PSP completada y validada inicia una prueba de 30 dias
  corridos.
- [ ] Una comision efectiva acredita exactamente un lote trazable de creditos,
  con vencimiento individual a 40 dias y consumo FIFO.
- [ ] Un umbral completo se consume una sola vez y concede 30 dias
  transaccionales; el excedente conserva su vencimiento original.
- [ ] Un trabajo externo pagado mediante MANDOBRA puede generar creditos;
  efectivo y pagos fuera de MANDOBRA no los generan.
- [ ] Operaciones rechazadas, canceladas, simuladas o sin comision no generan
  creditos; reversas siguen la politica que se apruebe.
- [ ] Una suscripcion mantiene PRO solo durante el periodo efectivamente pagado.
- [ ] Durante una suscripcion paga, las operaciones no generan comision de
  MANDOBRA por la modalidad transaccional.
- [ ] Sin prueba, periodo transaccional ni suscripcion vigente, el usuario
  vuelve a `FREE` sin perder creditos todavia vigentes.
- [ ] Ambas modalidades habilitan exactamente el mismo entitlement `PRO`.
- [ ] Reintentos y notificaciones duplicadas no duplican efectos.
- [ ] Operaciones simultaneas preservan la mayor vigencia valida.
- [ ] Un pago mixto deja los creditos reservados indisponibles pero no
  consumidos y los consume una sola vez solo al confirmar el pago completo.
- [ ] Rechazo o cancelacion definitivos liberan la reserva con vencimientos
  originales; creditos ya vencidos no reaparecen como disponibles.
- [ ] Un resultado incierto impide otro cobro del mismo periodo hasta
  conciliacion; un rechazo aislado no se trata como definitivo si quedan
  reintentos PSP.
- [ ] Prueba y gracia no consumen creditos; una suscripcion pagada durante ellas
  inicia inmediatamente y aplica la exencion.
- [ ] Creditos vigentes pueden cubrir total o parcialmente la primera
  suscripcion y renovaciones, cobrando solo la diferencia monetaria.
- [ ] El switch controla preferencia/autorizacion de renovacion, confirma su
  sincronizacion PSP y conserva el periodo pagado al apagarse; el sistema evita
  duplicados sin exigir al usuario una antelacion no definida.
- [ ] Existe tarjeta vinculada aun con cobertura total por creditos, sin
  confundir vinculacion con autorizacion de debito ni almacenar datos sensibles
  por inferencia.
- [ ] Antes de aceptar, el cliente ve servicio, cargo MANDOBRA y total; el
  profesional ve un neto expresamente estimado.
- [ ] En un contrato interno, cliente y profesional operan sobre la misma
  obligacion de pago; efectivo configurable no genera creditos.
- [ ] `ENTERPRISE` no habilita actores ni capacidades nuevas en este feature.

## PREGUNTAS ABIERTAS

### PRO

- Porcentaje de comision.
- Precio de la suscripcion y formula de conversion a creditos.
- Catalogo completo de beneficios y limites.
- Renovacion, cancelacion y mora.
- Tratamiento de contracargos.
- Alcance exacto, reintentos y unicidad de la gracia de 10 dias.
- Plazo de reserva y tratamiento de creditos que vencen durante un pago.
- Inicio diferido, cargos en transito y aprobaciones tardias.
- Cambios de precio y su efecto sobre umbral y saldos existentes.
- Consentimiento para aplicacion automatica de creditos.
- Viabilidad tecnica y contractual de vincular tarjeta sin cargo monetario.
- Antelacion y confirmacion efectiva del cambio de renovacion en el PSP.
- Costos, impuestos y validacion juridica del cargo presentado al cliente.
- Politica ante revocacion de verificacion o credenciales PSP.
- Politica de concesion administrativa y migracion de accesos existentes.
- Modelo futuro de `ENTERPRISE`.

## DECISIONES APROBADAS

- La orden de cobro de contratos internos usa inicialmente `ARS`, importe
  `Decimal` positivo y finito con hasta dos decimales, y vence a las 72 horas.
  Solo existe una activa por obligación; su única URL puede compartirse o
  representarse como QR. Esta decisión se detalla en
  [REQ-003](REQ-003-creacion-de-ordenes-de-cobro-checkout-pro.md) y no declara
  implementados el cobro, la conciliación ni la activación PRO.
- Catalogo canonico: `FREE`, `PRO`, `ENTERPRISE`.
- `Plus` no pertenece al catalogo aprobado.
- La primera implementacion de PRO corresponde a profesionales prestadores de
  servicios con cuenta activa y verificacion aprobada.
- Los puntos legacy no determinan elegibilidad ni vigencia PRO.
- Existen una modalidad transaccional y otra por suscripcion para el mismo
  entitlement `PRO`.
- La prueba transaccional dura 30 dias corridos tras onboarding PSP validado.
- La regla historica de 60 dias por operacion queda reemplazada: las comisiones
  efectivas generan creditos con lotes de 40 dias; un umbral concede 30 dias
  transaccionales y no existen extensiones de 15 dias.
- Los creditos vigentes pueden cubrir total o parcialmente la primera
  suscripcion y renovaciones posteriores sin duplicar financiacion.
- Los periodos de suscripcion son de 30 dias fijos y, al vencer sin pago, existe
  una gracia transaccional gratuita de 10 dias sin exencion de comision.
- La reserva de creditos es una decision aprobada; su plazo y el tratamiento de
  acreditaciones tardias permanecen pendientes.
- Se requiere comercialmente tarjeta vinculada aun con cobertura total por
  creditos, sin equipararla a autorizacion de debito y sujeto a viabilidad.
- El sistema debe prevenir financiacion o vigencia duplicadas entre pagos,
  reintentos y reservas; no se traslada esa responsabilidad al usuario.
- El cliente debe conocer servicio, cargo MANDOBRA y total antes de aceptar; el
  neto profesional es estimado y la validacion juridica/economica sigue abierta.
- La suscripcion mantiene PRO durante el periodo efectivamente pagado y excluye
  la comision transaccional de MANDOBRA.
- Facturacion MANDOBRA es un beneficio opcional aprobado de PRO.
- `ENTERPRISE` es conceptual y su implementacion permanece futura.

## DOCUMENTACIÓN AFECTADA

- [Indice documental](../INDEX.md).
- [Indice de requisitos](README.md).
- [MANDOBRA Master Spec](MASTER_SPEC.md).
- [Roadmap](../ROADMAP.md).
- [Backlog](../BACKLOG.md).
- [Changelog](../CHANGELOG.md).
- [Handoff activo](../HANDOFFS/ACTIVE_HANDOFF.md).

## ACTUALIZACION POSTERIOR - NUCLEO DE ENTITLEMENT

Timestamp: 2026-09-04T09:56:46-03:00
Estado: IMPLEMENTACION_PARCIAL
Rama: `feature/pro-entitlement-foundation`

- Todos los accesos legacy se reevaluan inmediatamente con el nuevo lector.
- Puntos, verificacion aislada y filas sin fuente o vencimiento no conceden PRO.
- Solo `electricidad.pro@demo.trax.local` conserva PRO en QA local mediante un
  registro demo `SUBSCRIPTION` temporal; no existe excepcion productiva por
  email, ID o usuario.
- Las nuevas activaciones manuales quedan deshabilitadas en esta fase.
- Permanecen pendientes PSP, prueba de 30 dias, creditos, pagos,
  suscripcion comercial, renovaciones y contracargos; REQ-001 no esta completo.
- Decision relacionada: [ADR-001](../ADR/ADR-001-pro-entitlement-foundation.md).

## ACTUALIZACION POSTERIOR - CORRECCION DE ESTADO CANONICO

Timestamp: 2026-09-04T10:29:16-03:00
Estado: IMPLEMENTACION_PARCIAL

- El frontmatter se corrigio de `PENDIENTE` a `IMPLEMENTACION_PARCIAL` para
  coincidir con el nucleo ya implementado y validado.
- El requisito conserva estado `APROBADO` y no se declara completamente
  implementado: PSP, pagos, renovaciones y politicas comerciales siguen
  pendientes.

## ACTUALIZACION COMERCIAL - CREDITOS Y TRANSICIONES

Timestamp: 2026-09-06T19:22:08-03:00
Estado: APROBADO_DOCUMENTAL_IMPLEMENTACION_PENDIENTE
Responsable de producto: Cristian Sánchez
Origen: decisiones comunicadas para el ciclo documental en
`docs/pro-commercial-psp-refinement`
Commit base observado: `1548935`

- Esta actualizacion reemplaza prospectivamente la regla de 60 dias por
  operacion sin borrar su registro historico.
- Las nuevas reglas de creditos, periodos de 30 dias, gracia y transiciones no
  forman parte de la Foundation ya implementada.
- Precio, porcentaje, formula economica, reversas y detalles de concurrencia
  permanecen pendientes; no existe autorizacion de implementacion.
- Consultas externas: [expediente Mercado Pago](../CONSULTAS/MERCADO_PAGO_v0_1.md)
  y [base de revision juridica](../LEGAL/BASE_REVISION_JURIDICA_v0_2.md).
