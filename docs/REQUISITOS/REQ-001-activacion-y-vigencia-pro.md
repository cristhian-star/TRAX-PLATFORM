---
id: REQ-001
titulo: Activacion y vigencia de MANDOBRA PRO
estado: APROBADO
fecha_aprobacion: 2026-09-03T20:38:47-03:00
responsable: Cristian Sánchez
rama_documental: docs/spec-pro-facturacion-mvp
implementacion: IMPLEMENTACION_PARCIAL
---

# REQ-001 - Activacion y vigencia de MANDOBRA PRO

## PROBLEMA

MANDOBRA necesita una regla unica, comprensible y verificable para conceder y
mantener el entitlement `PRO`. El flujo actual permite activar PRO de forma
inmediata mediante verificacion o puntos legacy, no representa las dos
modalidades comerciales aprobadas y no gobierna su vigencia real.

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

Estado verificado estaticamente en el commit base `e0eed2`:

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
9. Cada operacion aprobada que genere una comision efectiva para MANDOBRA debe
   extender la vigencia hasta 60 dias corridos desde la operacion efectiva.
10. La extension debe aplicar la regla:

    ```text
    pro_valid_until = max(pro_valid_until_actual, fecha_operacion_efectiva + 60 días)
    ```

11. Operaciones rechazadas, canceladas, reembolsadas, simuladas o sin comision
    efectiva no deben extender PRO.
12. Al vencer la vigencia transaccional, si no existe otra operacion elegible
    ni una suscripcion activa, el usuario debe volver a `FREE`.
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

## REQUISITOS NO FUNCIONALES

- La evaluacion del entitlement debe ser consistente en todas las superficies
  protegidas y no depender de controles visuales.
- Las altas, extensiones, cambios de modalidad y bajas deben ser trazables y
  auditables.
- Los eventos externos repetidos no deben duplicar activaciones ni extensiones.
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
4. Solo una comision efectiva de MANDOBRA extiende la modalidad transaccional.
5. Una nueva fecha calculada nunca puede reducir `pro_valid_until`.
6. Una suscripcion efectivamente pagada mantiene PRO durante su periodo valido
   y excluye la comision transaccional de MANDOBRA sobre las operaciones.
7. Al perder todas las fuentes vigentes de entitlement, el plan funcional
   vuelve a `FREE`.
8. Verificacion, reputacion y plan comercial son ejes independientes.

## RESTRICCIONES

- El porcentaje de comision no esta definido.
- Precio, periodicidad, renovacion, cancelacion, mora y periodo de gracia de la
  suscripcion no estan definidos.
- No se selecciona PSP ni se define una estrategia tecnica de integracion.
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
- Reembolso o contracargo posterior a una operacion que extendio vigencia.
- Dos o mas operaciones elegibles procesadas simultaneamente o fuera de orden.
- Operacion realizada durante una suscripcion paga.
- Vencimiento de la prueba sin otra fuente de entitlement.
- Cambio entre modalidad transaccional y suscripcion.
- Superposicion entre prueba, extensiones y periodo suscripto.
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
- [ ] Una operacion con comision efectiva extiende la fecha aplicando `max` y
  nunca reduce una vigencia existente.
- [ ] Operaciones rechazadas, canceladas, reembolsadas, simuladas o sin comision
  efectiva no extienden la vigencia.
- [ ] Una suscripcion mantiene PRO solo durante el periodo efectivamente pagado.
- [ ] Durante una suscripcion paga, las operaciones no generan comision de
  MANDOBRA por la modalidad transaccional.
- [ ] Sin prueba, extension ni suscripcion vigente, el usuario vuelve a `FREE`.
- [ ] Ambas modalidades habilitan exactamente el mismo entitlement `PRO`.
- [ ] Reintentos y notificaciones duplicadas no duplican efectos.
- [ ] Operaciones simultaneas preservan la mayor vigencia valida.
- [ ] `ENTERPRISE` no habilita actores ni capacidades nuevas en este feature.

## PREGUNTAS ABIERTAS

### PRO

- Porcentaje de comision.
- Precio y periodicidad de la suscripcion.
- Catalogo completo de beneficios y limites.
- Renovacion, cancelacion y mora.
- Tratamiento de contracargos.
- Periodo de gracia.
- Politica ante revocacion de verificacion o credenciales PSP.
- Politica de concesion administrativa y migracion de accesos existentes.
- Modelo futuro de `ENTERPRISE`.

## DECISIONES APROBADAS

- Catalogo canonico: `FREE`, `PRO`, `ENTERPRISE`.
- `Plus` no pertenece al catalogo aprobado.
- La primera implementacion de PRO corresponde a profesionales prestadores de
  servicios con cuenta activa y verificacion aprobada.
- Los puntos legacy no determinan elegibilidad ni vigencia PRO.
- Existen una modalidad transaccional y otra por suscripcion para el mismo
  entitlement `PRO`.
- La prueba transaccional dura 30 dias corridos y la operacion con comision
  efectiva extiende hasta 60 dias desde su fecha efectiva sin reducir vigencia.
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
- Permanecen pendientes PSP, prueba de 30 dias, extensiones de 60 dias, pagos,
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
