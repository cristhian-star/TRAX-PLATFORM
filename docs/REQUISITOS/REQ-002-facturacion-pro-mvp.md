---
id: REQ-002
titulo: Facturacion MANDOBRA PRO MVP
estado: APROBADO
fecha_aprobacion: 2026-09-03T20:38:47-03:00
responsable: Cristian Sánchez
rama_documental: docs/spec-pro-facturacion-mvp
implementacion: PENDIENTE
---

# REQ-002 - Facturacion MANDOBRA PRO MVP

## PROBLEMA

Profesionales independientes necesitan emitir comprobantes por servicios
prestados a clientes que exigen factura, incluidos consorcios, barrios
privados, empresas, instituciones y particulares. El proceso manual en ARCA
para cada comprobante agrega friccion y riesgo operativo.

## OBJETIVO

Definir un modulo funcional separado que permita a un profesional persona
humana, con monotributo activo y entitlement PRO vigente, preparar y emitir
opcionalmente Factura C con asistencia de IA, revision completa y confirmacion
humana explicita, preservando seguridad, trazabilidad e idempotencia.

## ACTORES

- Profesional emisor: configura voluntariamente sus datos fiscales, revisa el
  borrador y confirma expresamente la emision.
- Cliente o receptor: destinatario del comprobante; los datos obligatorios y su
  tratamiento permanecen sujetos a definicion fiscal y legal.
- MANDOBRA: controla entitlement, orquesta el flujo y conserva trazabilidad sin
  sustituir el criterio fiscal humano.
- ARCA: autoridad externa que autoriza o rechaza la emision y devuelve el
  resultado fiscal correspondiente.
- Proveedor de integracion e IA: dependencias futuras posibles; ninguno queda
  seleccionado por este requisito.

## CONTEXTO ACTUAL

Estado verificado estaticamente en el commit base `e0eed2`:

- MANDOBRA opera contratos con `contracting_mode = EXTERNAL` y no procesa
  pagos ni facturacion.
- Existe un entitlement PRO provisional, pero no implementa las fuentes ni la
  vigencia aprobadas en [REQ-001](REQ-001-activacion-y-vigencia-pro.md).
- No existen integracion ARCA, validacion de monotributo, emision de Factura C,
  solicitud de CAE ni IA productiva.
- La facturacion figuraba como capacidad futura y pendiente de aprobacion
  funcional.

Este requisito aprueba el comportamiento esperado; no declara ninguna de esas
capacidades como implementada.

## REQUISITOS FUNCIONALES

1. Facturacion MANDOBRA debe ser un modulo funcional separado de la activacion
   y vigencia PRO.
2. Configurar o usar Facturacion no debe activar PRO ni iniciar o extender la
   prueba transaccional de 30 dias.
3. El modulo debe estar disponible opcionalmente solo con entitlement PRO
   vigente por prueba transaccional, extension por operacion con comision o
   suscripcion pagada.
4. Un usuario `FREE` no debe poder iniciar una nueva emision.
5. Un usuario PRO no debe estar obligado a configurar ni usar Facturacion.
6. El alcance fiscal inicial debe limitarse a profesionales personas humanas
   con monotributo activo que emitan Factura C.
7. La conexion con ARCA debe configurarse solo cuando el usuario decida
   facturar, con autorizacion valida y condicion fiscal compatible.
8. La configuracion fiscal debe ser independiente de la fuente y activacion del
   entitlement PRO.
9. El flujo funcional debe respetar esta secuencia:

   ```text
   PRO vigente
   → configuración fiscal opcional
   → validación fiscal
   → solicitud de factura
   → IA genera borrador
   → vista previa completa
   → confirmación humana explícita
   → solicitud de autorización fiscal/CAE
   → registro del resultado y auditoría
   → comprobante disponible
   ```

10. La asistencia de IA debe interpretar la intencion y ayudar a completar el
    borrador, pudiendo reutilizar datos existentes del servicio solo cuando su
    uso este permitido.
11. La IA no debe inventar datos fiscales, decidir tratamientos fiscales ni
    continuar silenciosamente cuando falten datos obligatorios.
12. Ante datos faltantes o ambiguos, el flujo debe solicitar aclaracion al
    usuario antes de permitir la confirmacion.
13. Debe mostrarse una vista previa completa antes de solicitar autorizacion
    fiscal.
14. Ninguna factura debe emitirse sin confirmacion humana explicita sobre la
    vista previa correspondiente.
15. Cada intento y resultado debe quedar trazado, auditado y protegido contra
    duplicacion.
16. Un rechazo, timeout o error de ARCA no debe registrarse ni presentarse como
    emision exitosa.
17. La perdida de PRO debe impedir nuevas emisiones, pero no la consulta y
    descarga de comprobantes propios ya emitidos, sujeto a la futura politica
    de retencion.
18. El modulo debe impedir que un usuario consulte, modifique, emita o descargue
    informacion fiscal o comprobantes pertenecientes a otro usuario.

## REQUISITOS NO FUNCIONALES

- Proteger los datos fiscales durante captura, transmision, persistencia,
  visualizacion, respaldo y eliminacion.
- Cifrar secretos y material de autenticacion; nunca almacenar claves fiscales
  en texto plano.
- Registrar auditoria suficiente para reconstruir actor, solicitud, borrador
  confirmado, intento externo y resultado sin exponer secretos.
- Aplicar idempotencia a cada solicitud de emision y a las respuestas externas.
- Mantener trazabilidad entre datos de origen, borrador, confirmacion humana,
  solicitud de CAE, respuesta y comprobante.
- Sanitizar errores externos y evitar que logs o respuestas filtren datos
  fiscales o credenciales.
- Obtener consentimiento informado para conectar ARCA y tratar los datos
  necesarios.
- Preservar privacidad, minimizacion y aislamiento estricto entre usuarios.
- Definir y aplicar una politica de retencion, acceso historico y eliminacion
  compatible con obligaciones legales.
- Definir objetivos de disponibilidad, contingencia, respaldo y recuperacion
  antes de produccion.
- Someter la implementacion a revision legal, fiscal, contable y de seguridad
  antes de habilitar produccion.

## REGLAS DE NEGOCIO

1. Facturacion es un beneficio opcional de un entitlement PRO ya vigente; no es
   una fuente de PRO.
2. Solo la combinacion persona humana, monotributo activo y Factura C pertenece
   al MVP.
3. La autorizacion fiscal valida es obligatoria antes de solicitar un CAE.
4. Un borrador asistido no es un comprobante emitido.
5. La confirmacion debe ser humana, explicita y referir a la vista previa que se
   enviara.
6. Una respuesta externa ambigua, fallida o no verificable no equivale a una
   emision exitosa.
7. Un mismo intento logico no debe originar comprobantes duplicados.
8. Perder PRO bloquea nuevas emisiones, no el acceso autorizado al historial
   propio existente.
9. La IA asiste en la preparacion; no ejerce criterio ni asesoramiento fiscal.

## RESTRICCIONES

- No se selecciona integracion directa con ARCA ni proveedor intermediario.
- No se define proveedor o modelo de IA.
- No se define custodia, rotacion o arquitectura de certificados y secretos.
- No se fijan limites, costos ni politica de almacenamiento o retencion.
- No se aprueba diseño de modelos, migraciones, servicios, endpoints o UI.
- La aprobacion documental no autoriza implementacion ni uso productivo.

## FUERA DE ALCANCE

- Responsables inscriptos.
- Facturas A y B.
- Empresas emisoras.
- Multiples CUIT por usuario.
- Facturacion masiva.
- Notas de credito o debito.
- Emision completamente automatica.
- Decisiones o asesoramiento fiscal mediante IA.
- Correcciones, anulaciones y contingencias fiscales no definidas.
- Implementar ARCA, PSP, IA, modelos, migraciones o cambios visuales.
- Copiar, contratar o integrar Facturitas, o adoptarlo como dependencia o
  proveedor.

## DEPENDENCIAS

- [REQ-001 - Activacion y vigencia de MANDOBRA PRO](REQ-001-activacion-y-vigencia-pro.md).
- Condicion fiscal valida y autorizacion del profesional ante ARCA.
- Evaluacion tecnica, legal, economica y de seguridad de integracion directa o
  proveedor.
- Politica de datos fiscales, consentimiento, retencion y recuperacion.
- Seleccion y evaluacion futura de asistencia de IA.
- Contratos y datos de servicio existentes solo cuando su reutilizacion sea
  legal, autorizada y pertinente.
- ADR futuros para integracion fiscal, custodia de credenciales, idempotencia,
  modelo de datos y proveedor de IA.

## RIESGOS

- Emitir con datos inventados, incompletos o fiscalmente incorrectos.
- Exponer claves fiscales, certificados, CUIT u otros datos sensibles.
- Duplicar comprobantes por reintentos, timeouts o respuestas externas tardias.
- Mostrar como exitosa una emision rechazada o indeterminada.
- Permitir nuevas emisiones sin PRO vigente o sin condicion fiscal valida.
- Confundir asistencia de IA con asesoramiento fiscal.
- Acceso cruzado a comprobantes o configuraciones de otro usuario.
- Retener informacion por menos o mas tiempo del legalmente requerido.
- Dependencia operativa de ARCA o de proveedores externos sin contingencia.
- Habilitar produccion sin revision legal, fiscal, contable y de seguridad.

## CASOS LÍMITE

- Usuario `FREE` que intenta emitir o acceder a la configuracion de emision.
- Usuario PRO vigente que decide no configurar Facturacion.
- Entitlement que vence durante la preparacion o antes de confirmar.
- Monotributo inactivo, no verificable o cambiado despues de la configuracion.
- Autorizacion ARCA ausente, vencida o revocada.
- Datos obligatorios del receptor ausentes o ambiguos.
- Datos del servicio incompatibles con el comprobante solicitado.
- IA que no puede interpretar la intencion o detecta datos insuficientes.
- Doble confirmacion humana o reintento de la misma solicitud.
- Timeout con resultado fiscal desconocido.
- Rechazo o indisponibilidad de ARCA.
- Respuesta externa duplicada, tardia o fuera de orden.
- Perdida de PRO despues de una emision valida.
- Solicitud de acceso o descarga por otro usuario.
- Necesidad posterior de correccion, anulacion o nota de credito.

## CRITERIOS DE ACEPTACIÓN

- [ ] Un usuario `FREE` queda bloqueado para iniciar una emision.
- [ ] Un profesional con PRO vigente puede optar por configurar y usar el
  modulo sin que esa configuracion altere su entitlement.
- [ ] La configuracion fiscal es independiente de la activacion, prueba y
  vigencia PRO.
- [ ] El flujo valida persona humana, monotributo activo y Factura C antes de
  habilitar la emision MVP.
- [ ] La IA genera solo un borrador asistido y solicita aclaracion cuando faltan
  datos.
- [ ] Ningun campo fiscal ausente se completa con informacion inventada.
- [ ] El profesional recibe una vista previa completa del comprobante.
- [ ] Sin confirmacion humana explicita no se solicita CAE ni se emite.
- [ ] Una autorizacion fiscal exitosa queda asociada al intento confirmado y al
  comprobante disponible.
- [ ] Un error, timeout o rechazo no produce ni muestra una emision exitosa.
- [ ] Reintentos y respuestas duplicadas no generan comprobantes duplicados.
- [ ] Cada paso relevante queda auditado y trazable sin registrar secretos.
- [ ] Perder PRO impide nuevas emisiones.
- [ ] El profesional que pierde PRO conserva acceso autorizado a consultar y
  descargar sus comprobantes ya emitidos, sujeto a retencion.
- [ ] Ningun usuario puede acceder a configuraciones o comprobantes ajenos.

## PREGUNTAS ABIERTAS

### Facturacion

- Integracion directa con ARCA o mediante proveedor.
- Custodia, renovacion y rotacion de certificados y secretos.
- Metodo y frecuencia para validar monotributo activo.
- Datos obligatorios del receptor y reglas por tipo de destinatario.
- Formato, almacenamiento, entrega y politica de retencion.
- Limites de emision.
- Correcciones y anulaciones.
- Notas de credito.
- Contingencia por caida o respuesta indeterminada de ARCA.
- Proveedor y modelo de IA.
- Costos de integracion y operacion.
- Resultado de la revision legal, fiscal y contable.

## DECISIONES APROBADAS

- Facturacion MANDOBRA es un modulo funcional separado.
- Es un beneficio opcional exclusivo de PRO vigente y no activa, inicia ni
  extiende PRO.
- El MVP cubre profesionales personas humanas con monotributo activo y Factura
  C.
- La conexion ARCA se configura al decidir facturar y requiere autorizacion y
  condicion fiscal validas.
- El flujo exige borrador, vista previa, confirmacion humana, solicitud de CAE,
  resultado auditable y comprobante disponible.
- La IA puede asistir, pero no inventar datos, decidir tratamientos fiscales ni
  emitir sin confirmacion humana.
- Toda emision debe ser trazable, auditable e idempotente.
- Perder PRO impide nuevas emisiones, pero no el acceso autorizado al historial
  propio, sujeto a retencion.
- Facturitas es solo referencia de producto y no un proveedor o dependencia
  aprobados.
- La estrategia de integracion fiscal permanece pendiente de evaluacion.

## DOCUMENTACIÓN AFECTADA

- [Indice documental](../INDEX.md).
- [Indice de requisitos](README.md).
- [MANDOBRA Master Spec](MASTER_SPEC.md).
- [Roadmap](../ROADMAP.md).
- [Backlog](../BACKLOG.md).
- [Changelog](../CHANGELOG.md).
- [Handoff activo](../HANDOFFS/ACTIVE_HANDOFF.md).
