---
id: REQ-005
titulo: Cobros de anticipos, parciales y trabajos externos
estado: BORRADOR
fecha: 2026-10-18T19:38:52-03:00
implementacion: NO_AUTORIZADA
---

# REQ-005 — Feature Spec propuesta de ampliación de Cobros

Registro: 2026-10-18T19:38:52-03:00. Responsable de redacción: Codex local, laptop.
Encargo: 2026-10-18T19:30:09-03:00. Rama: `feature/professional-workspace-ux`.
HEAD base: `2e552f2fdc57c152c97f0486050574696f6b250e`.
**PROPUESTA PARA REVISIÓN; no aprobada, no implementada, no autoriza migraciones ni activación.**
Cada «debe» de este documento expresa un criterio propuesto, no una regla vigente.
Decisión técnica asociada: [ADR-003](../ADR/ADR-003-contexto-comercial-obligaciones-cobro.md).

## 1. Necesidad, alcance y exclusiones

Permitir al profesional solicitar el total o una parte del precio de un trabajo interno,
o de uno conseguido por recomendación u otro canal. Preservar entradas principales
«Crear factura» y «Crear cobro». Dentro de Crear cobro: «Usar un trabajo de MANDOBRA»
o «Cargar otro trabajo» → concepto e importe → revisión → confirmación → enlace/QR.
La segunda entrada no crea una publicación, cuenta CLIENTE o ContractRequest ficticios.

Incluye como objetivo futuro obligaciones diferenciadas de anticipo, parcial, saldo y total,
historial propio, cálculo explicable cuando exista información suficiente, autorización,
prevención de duplicados e independencia fiscal. Anticipo significa una porción solicitada
antes de la finalización; no establece por sí solo una seña, garantía, penalidad, financiación
ni un plan de cuotas. Parcial refiere a parte del trabajo; cada checkout cobra el importe
completo de su obligación, sin ampliar silenciosamente la aceptación de importes 4E.

Excluye implementación en este encargo; custodia de dinero, préstamos, cuotas automáticas,
débitos recurrentes de trabajos, intereses, disputas financieras resueltas por MANDOBRA,
tarifas nuevas, nuevos planes, empresas, multimoneda, instrumentos fiscales nuevos y
activación remota. OAuth, retornos, recuperación de incertidumbre y worker de conciliación
requieren sus paquetes y gates. No se amplía el MVP fiscal de REQ-002.

## 2. Base comprobada y diferencias normativas

Fuentes leídas: [Master Spec](MASTER_SPEC.md), [REQ-001](REQ-001-activacion-y-vigencia-pro.md),
[REQ-002](REQ-002-facturacion-pro-mvp.md), [REQ-003](REQ-003-creacion-de-ordenes-de-cobro-checkout-pro.md),
[ADR-001](../ADR/ADR-001-pro-entitlement-foundation.md),
[decisiones vigentes](../DECISIONES_ARQUITECTURA.md),
[estándares](../ESTANDARES_DESARROLLO.md), [guía documental](../GUIA_DOCUMENTACION.md),
[PROF-UX-004](PROF_UX_004.md) y [anexo propuesto](PROF_UX_004_AMPLIACION_PROPUESTA.md).
Auditoría recibida del 2026-10-18T14:25:11-03:00:
[informe y matriz](../../../.codex/visualizations/2026/09/17/01a0afe3-1eed-7981-8e70-6afbac0e721e/auditorias/cobros-20261018/INFORME_AUDITORIA_COBROS.md).
Su descripción de la UI precede PROF-UX-004: el recorrido ya está conectado sólo en preview
simulado. No se reinterpreta esa auditoría como estado productivo actual.

| Capa | Evidencia actual | Límite que requiere decisión |
| --- | --- | --- |
| Esquema | PaymentObligation.contract_request_id nullable, FK RESTRICT y UNIQUE uq_payment_obligations_contract_request | Una obligación por contrato no nulo; NULL permite legacy sin contrato, pero no prueba existencia de un trabajo externo ni ownership. |
| Reserva | UNIQUE uq_payment_order_reservations_obligation | Una reserva durable por obligación; no equivale a varias solicitudes ni reintentos libres. |
| Órdenes | Índice parcial uq_payment_orders_active_obligation, estados ACTIVE/EXPIRED/CANCELLED | Una activa por obligación; 4A permite sucesión local, no prueba cancelación remota. |
| Servicio 4B | _authorized_contract, _same_price y _prepare | Sólo CONFIRMADA; importe total precio_acordado; consulta one_or_none por contrato; sin sucesión expuesta. |
| Presentación | PROF-UX-004 y professional_collection_service | Total de contratos propios, únicamente con composición aislada. App habitual preparada. |
| Finanzas | Evidencia 4E y efectos 4F | Clases internas no equivalen a conciliación operativa, dinero acreditado ni permisos productivos. |

Rutas de evidencia: [obligación](../../app/models/payment_obligation.py),
[reserva](../../app/models/payment_order_reservation.py), [orden](../../app/models/payment_order.py),
[servicio 4B](../../app/services/payment_order_application_service.py),
[contratación](../../app/services/contract_service.py),
[pruebas 4B](../../tests/test_payment_order_application.py).
Los tests existentes rechazan todo estado distinto de CONFIRMADA y montos suministrados por
caller: ampliarlos será un cambio de contrato explícito, no una corrección de UI.

`CONFIRMADA` es conformidad final expresa del cliente, posterior a COMPLETADA declarada
por el profesional. No significa acuerdo inicial ni pago. `contracting_mode=EXTERNAL`
es modalidad contractual vigente; no identifica el canal comercial. La propuesta amplía
Cobros, no la máquina contractual ni las condiciones de reviews.

## 3. Actores, autoridad e importe

Profesional activo y propietario: consultar y solicitar sobre sus trabajos; CLIENTE no
administra cobros ajenos. Revalidar rol persistido, estado, ownership de contexto, perfil,
contrato, obligación y cuenta receptora en cada operación; CSRF y destino seguro. Para
producción, credencial OAuth propia válida y gates económicos/seguridad independientes.
No usar PRO como sustituto de ownership ni imponer ARCA como permiso de Cobros.
La política de elegibilidad comercial final se resuelve en D1; no se relajan permisos actuales.

### Trabajo interno

Contrato y acuerdo/versiones autorizadas son autoridad del total. El navegador propone
sólo la porción, nunca modifica precio_acordado, moneda, receptor ni contrato. Registrar
versión del acuerdo revisada, propósito, monto Decimal ARS positivo de dos decimales,
confirmación del solicitante y referencia. Si falta total canónico válido, bloquear la
solicitud interna y remitir al acuerdo; no copiar un importe libre a ContractRequest.

| Estado canónico | Habilitación propuesta para nuevas solicitudes | Motivo |
| --- | --- | --- |
| CREADA | No | Aún no aceptada; falta la base para este primer alcance. |
| ACEPTADA | Sí, anticipo o porción/total expresamente pactados | Inicio de la relación aceptada; no presume aceptación de condiciones económicas añadidas. |
| EN_PROGRESO | Sí, parcial o saldo/total pactados | Permitir pagos durante ejecución sin declararla terminada. |
| COMPLETADA | Sí, porción pendiente pactada | Declaración del profesional; mostrar «pendiente de conformidad», nunca trabajo confirmado. |
| CONFIRMADA | Sí, porción pendiente/saldo/total | Preserva significado terminal y recorrido total legacy. |
| CORRECCION_SOLICITADA | Bloquear nuevas solicitudes hasta resolver o aprobar una política específica | Evitar automatizar cobros incompatibles con corrección abierta; no borrar obligaciones/pagos anteriores. |
| RECHAZADA / CANCELADA | No nuevas solicitudes | Conciliar las anteriores; cancelación contractual no prueba saldo cero ni cancelación PSP. |

Pactar importe y calendario de anticipo/parcial requiere evidencia de aceptación de la
contraparte sobre versión y condiciones; estado ACEPTADA por sí solo no prueba una
condición añadida. Proponer aceptación explícita de un desglose mediante el flujo de
acuerdo, sin reutilizar CONFIRMADA para ello. Si el flujo actual no puede representarlo,
ese subincremento queda bloqueado hasta definirlo; no fabricar consentimiento por un pago.

### Trabajo externo

Datos mínimos propuestos: propietario derivado de sesión, identificador opaco, título o
concepto breve, alias/nombre mínimo de contraparte, origen EXTERNAL_CHANNEL, fecha de
registro y moneda ARS. Total opcional y procedencia DECLARADO_POR_PROFESIONAL o
ACEPTADO_POR_CLIENTE con evidencia/versionado separados. Contacto opcional sólo si se
requiere para entrega consentida; no exigir DNI, CUIT, domicilio ni cuenta MANDOBRA para
crear la solicitud. Datos fiscales se solicitan sólo dentro del proceso fiscal pertinente.

No llamar «deuda aceptada» a una declaración unilateral. Proponer permitir una solicitud
rotulada «Importe solicitado por el profesional», con revisión del concepto por el pagador,
sin afirmar aceptación del total restante. Aceptación de total: prueba vinculada a versión,
fecha y contraparte mediante mecanismo revisado por Producto/Seguridad/Legal. Un pago,
click, apertura de WhatsApp o carga de un documento por el profesional no basta por sí solo.
No vincular personas por coincidencia de email/telefono ni crear una cuenta implícita.

## 4. Magnitudes y reglas de saldo propuestas

| Magnitud | Fuente / interpretación |
| --- | --- |
| Total acordado T | Versión aceptada del contrato o acuerdo externo con evidencia. Puede ser desconocido. Total declarado externo se muestra separado. |
| Importe solicitado por obligación q | Porción inmutable confirmada, no el total del trabajo ni una factura. |
| Solicitado histórico | Suma identificada de solicitudes emitidas, incluidas retiradas con etiqueta; no equivale a deuda actual ni ingresos. |
| Exposición E | Importes aún cobrables, reservados o inciertos; se cuenta una vez por obligación, no una vez por enlace/QR/replay. |
| Acreditado A | Pagos autoritativos únicos y correlacionados, no retornos de navegador ni estados de orden. |
| Devuelto D | Devoluciones verificadas correlacionadas por pago; separado de contracargos/reversos y sin doble conteo de snapshots. |
| Neto recibido | A menos D, separado de comisiones/costos PSP; requiere datos íntegros. Contracargos se informan separadamente y suspenden automatismos hasta resolución. |
| Imputado I | Importe de pagos aplicado una vez a obligaciones de ese trabajo, con origen y eventual reversión trazables. No deducirlo de múltiples snapshots. |
| Saldo pendiente S | T menos imputaciones netas válidas I, sólo con total acordado e historia completa y consistente. |
| Disponible para nueva solicitud | S menos exposición E, sólo cuando no hay incidencias sin resolver. No confundirlo con saldo pendiente. |

E incluye PREPARED reservado, CALL_IN_PROGRESS, UNCERTAIN y órdenes todavía pagables.
Cuando un pago verificado se imputa, su importe pasa de exposición a imputado atómicamente:
no se cuenta en ambos. Si hay evidencia no imputable, pago tardío, contradicción o PSP no
final, mantener bloqueo de nuevas solicitudes y mostrar «Requiere revisión». No presentar
una cifra automática fiable mientras la historia no lo permita.

T e I deben tener igual moneda, versión válida, y cobertura de medios de pago completa.
Pagos por otra vía declarados manualmente se registran, si se aprueba esa capacidad,
separados como «declarados, no verificados»: no elevan A ni créditos. Hasta confirmar cómo
se imputan, un registro manual bloquea nuevo cobro automático incompatible y exige revisión;
no ignorarlo para seguir solicitando el total. La primera fase no ofrece edición manual de A.

Sin T: «Total no definido» y «Saldo no calculable», nunca cero. Con total sólo declarado:
mostrar estimación declarada diferenciada, no saldo exigible; recomendar no generar una
acción «Cobrar saldo» hasta aceptar total. Permitir una solicitud externa de importe
explícito sin total, con una única obligación expuesta a la vez y confirmación de posible
duplicado. No se garantiza ausencia de duplicados comerciales entre trabajos externos
creados dos veces; advertencia y revisión, sin fusionar personas automáticamente.

Con T válido: bajo lock del trabajo comprobar I + E + nueva q <= T. No usar esta fórmula
como regla fiscal, cálculo de comisión ni reconocimiento legal de deuda. Un sobrepago real
se conserva como excedente pendiente de resolución; no ocultarlo con max(0, saldo), no
imputarlo a otro trabajo ni devolverlo automáticamente. Si el precio baja por debajo de
imputado/expuesto, bloquear nuevos cobros y reconciliar/acordar tratamiento antes de liberar.

## 5. Duplicados, cambios e incertidumbre

- Confirmación lógica estable: doble click/reenvío conserva obligación, reserva y clave;
  payload material distinto con la misma identidad falla. Una nueva porción requiere nueva
  confirmación explícita y la validación global, no otra clave para reintentar una incierta.
- Primer alcance: una reserva de creación por obligación, sin renovación automática.
  Vencimiento 72 h del checkout conservado; no define vencimiento de deuda o acuerdo.
- Cancelar o vencer localmente oculta entrega, pero no demuestra que el PSP no pueda cobrar.
  No liberar exposición ni emitir reemplazo hasta prueba remota definitiva y conciliación.
  Si tal prueba no está disponible, mantener revisión/bloqueo; timeout no es prueba.
- Cambio de acuerdo invalida revisiones pendientes. Órdenes emitidas no cambian de importe;
  conservar snapshots, conciliar exposición antigua y aceptar nueva versión antes de emitir.
- Pago tardío: registrar evidencia, deduplicar, congelar nuevas solicitudes y resolver
  imputación/excedente; no confirmar trabajo ni activar PRO automáticamente.
- Devolución o contracargo no reabre deuda automáticamente. Registrar evidencia y decidir
  si hay ajuste del total, reversión de imputación u obligación nueva con consentimiento.
  No borrar acreditación histórica ni repetir efectos 4F; sigue PENDING_REVIEW donde aplica.

## 6. Facturación y política PRO

Crear factura se mantiene independiente: puede facturarse según REQ-002 aunque el cliente
pague por transferencia, efectivo u otro medio; no exige PaymentOrder ni pago acreditado.
Crear cobro no obliga a configurar ARCA y no exonera obligaciones fiscales aplicables.
No se da asesoramiento tributario ni se presupone cuándo corresponde emitir por un anticipo.

Conservar persona humana, monotributo activo, Factura C, PRO vigente para nueva emisión,
autorización fiscal válida, borrador asistido, vista previa y confirmación humana de REQ-002.
No añadir notas de crédito/débito o anulación automática. Su eventual necesidad por devoluciones
es dependencia de revisión fiscal fuera del MVP aprobado; no simularlas.

Relación futura opcional muchos-a-muchos con asignaciones por importe/concepto: una factura
puede abarcar varias obligaciones y una obligación puede relacionarse con varios comprobantes
sólo si no se factura dos veces el mismo concepto/porción. El enlace es trazabilidad, no nueva
deuda ni acreditación. Validar cobertura fiscal y ajustes según política aprobada; nunca sumar
«importe de factura + importe de cobro» como ingreso o saldo. Facturas de suscripción MANDOBRA
permanecen separadas de facturas del profesional a clientes. No se implementa esa relación aquí.

Reglas vigentes REQ-001/4F que no cambia esta propuesta:

- Suscripción PRO efectivamente pagada: exención de comisión transaccional MANDOBRA en el
  período aplicable; no inferir exención de un badge PRO transaccional/prueba/gracia.
- Costos propios del PSP separados; no prometer cobro sin costos por la exención.
- Créditos sólo con evidencia íntegra y comisión neta efectiva verificada, política explícita
  versionada. La regla aprobada de umbral equivalente al precio mensual, crédito de 30 días,
  FIFO y lotes de 40 días se conserva; no se define precio/tasa/base nueva aquí.
- Trabajo externo cobrado mediante enlace admitido podrá aportar según REQ-001; no por mero
  registro externo, efectivo, pago fuera de MANDOBRA, simulación o importe bruto aprobado.
- Sin política/evidencia: PENDING_POLICY; tardíos/reversos: revisión. No prorratear créditos
  nuevos por etiqueta «anticipo» ni duplicarlos al imputar un pago en varias obligaciones.

## 7. Decisiones pendientes con opciones y recomendación

Todas requieren aceptación expresa de Producto; las indicadas también de Arquitectura,
Seguridad o fiscal/legal. Ninguna opción recomendada queda aprobada por este documento.

| ID | Pregunta / opciones | Recomendación y gate |
| --- | --- | --- |
| D1 | Cobros sólo PRO / profesional activo con gates PSP | Mantener activo/ownership como base, sin exigir PRO pagado; aplicar verificación/onboarding comercial conforme REQ-001 antes de activación. Facturación sigue PRO. Acordar elegibilidad exacta de FREE y gracia sin habilitar por omisión. |
| D2 | Sólo CONFIRMADA / estados de sección 3 / todos | Estados de sección 3 con acuerdo de porción explícito; corrección abierta bloquea. Producto debe aprobar cambio de REQ-003. |
| D3 | Externos sólo total aceptado / solicitudes declaradas diferenciadas | Admitir declaración sin afirmar deuda; saldo exige acuerdo verificable. Definir mecanismo/evidencia de aceptación y retención con Seguridad/Legal. |
| D4 | Sin total: bloquear / una solicitud expuesta / múltiples ilimitadas | Una expuesta; importes sucesivos requieren conciliación previa. Advertir ausencia de saldo calculable. |
| D5 | Devolución reabre deuda / revisión explícita | Revisión explícita con acuerdo, preservando evidencia; definir tratamiento de excedentes y quién autoriza resolución. |
| D6 | Manual equivale PSP / manual separado / no registrar | Separado en fase posterior, con procedencia y revisión de imputación. Nunca comisión/crédito por declaración. |
| D7 | Tarifas distintas por origen o propósito / misma política existente | Misma política versionada por operación elegible sin tarifas nuevas. Definir tasa/base, costos, instante efectivo de exención y tratamiento de reembolsos antes de producción. No adivinar desde fecha de creación. |
| D8 | Renovación/reintento libre / recovery autoritativo | Recovery de la misma identidad; sucesión como paquete posterior con garantías remotas, sin liberar por expiración local. |
| D9 | Factura 1:1 obligatoria / asociación opcional asignada | Asociación opcional muchos-a-muchos con cobertura no duplicada. Fiscal debe decidir tratamiento de anticipos, medio externo, documentación y devoluciones. |
| D10 | Retención indefinida / política por clase de dato | Minimizar contraparte y definir plazos, acceso/eliminación y comprobantes aceptables con Legal. No fijar plazo por conveniencia técnica. |

## 8. Matriz de escenarios y aceptación propuesta

Criterios pendientes de implementación y testing; ninguna casilla se declara satisfecha.

| ID | Dado / cuando | Entonces observable |
| --- | --- | --- |
| A01 | Abro Facturación y cobros | Dos entradas principales; origen del trabajo se elige dentro de Crear cobro. |
| A02 | Interno ACEPTADA con acuerdo de anticipo | Solicita porción validada sin pasar contrato a CONFIRMADA ni habilitar review. |
| A03 | COMPLETADA o EN_PROGRESO elegible | Permite porción pactada, etiqueta estado contractual real; pagar no lo modifica. |
| A04 | CREADA, corrección, cancelado o ajeno | Rechaza crear, sin reserva ni llamada; conserva evidencia anterior autorizada. |
| A05 | Externo sin total o sin cuenta cliente | Solicitud explícita sin contrato ficticio; saldo no calculable, procedencia declarada visible. |
| A06 | Importe externo sólo declarado | No aparece como deuda aceptada; factura/registro/pago no aceptan automáticamente todo el acuerdo. |
| A07 | T=100, imputado=20, expuesto=30, nueva q=60 (fixture) | Rechaza exceso; q=50 sería admisible sólo sin incidencias y con acuerdo válido. |
| A08 | Dos confirmaciones concurrentes agotan el disponible | PostgreSQL confirma sólo el conjunto que respeta límite; sin dos claims que excedan T. |
| A09 | Doble click, refresh o replay | Misma obligación/reserva/orden y clave; payload distinto conflictivo. |
| A10 | UNCERTAIN o enlace aún vigente | No hay nuevo intento/obligación para eludir exposición; estado recuperable por conciliación autorizada. |
| A11 | Expiración o cancelación local | No libera exposición por sí sola; sin prueba remota no permite reemplazo. |
| A12 | Cambio de total tras revisión | Confirmación antigua rechazada; órdenes anteriores conservadas, sin editar sus importes. |
| A13 | Pago tarde, duplicado o snapshot repetido | Un solo hecho aplicado; tardío/excedente en revisión, sin efectos contractuales/PRO automáticos. |
| A14 | Devolución/contracargo | Hecho separado; no deuda nueva ni crédito/reversa automática. |
| A15 | Registro manual por otra vía | No muestra «acreditado por PSP» ni crédito PRO; resuelve cobertura antes de otro cobro. |
| A16 | Facturar pago ajeno a Cobros / cobrar sin ARCA | Primera opción sujeta a REQ-002; segunda no pide configuración fiscal como barrera, sin afirmar exención tributaria. |
| A17 | Dos documentos relacionados con una porción | Detecta cobertura duplicada; no suma dos deudas ni emite sin confirmación. |
| A18 | Suscripción pagada / costo PSP / comisión no probada | Exención MANDOBRA diferenciada; costo PSP no oculto; sin créditos inferidos. |
| A19 | Anónimo, CLIENTE, suspendido, ID ajeno, CSRF ausente | Rechazo canónico sin información privada ni mutaciones financieras. |
| A20 | GET, QR, retorno, copia | No crea órdenes, paga, concilia ni finaliza; enlace/QR coherentes y seguros. |
| A21 | Historial legacy sin contrato o evidencia suficiente | Conserva dato e identidad; no inventa propietario, origen, deuda aceptada o saldo. |
| A22 | Error de consulta / cero movimientos / métrica no disponible | Tres estados distintos, sin convertir error o desconocido en cero. |

## 9. Implementación futura y validaciones por etapa

0. Revisar D1–D10, aprobar Spec/ADR y actualizar normas afectadas; hasta entonces sin código.
1. Contexto y obligaciones internas: migración expand/backfill revisada, ownership, versiones,
   precisión y proyección/exposición; validar compatibilidad legacy y gates PostgreSQL antes de
   permitir múltiples solicitudes. No activar interfaz si estados/acuerdo no están aprobados.
2. Caso externo y contraparte mínima, solicitudes declaradas vs acuerdos aceptados, límites sin
   total, privacidad y auditoría. Fakes sólo en bases descartables; no onboarding real todavía.
3. Recovery/conciliación e imputaciones: deduplicar evidencia, pagos tardíos, reversos, cambios
   y sobrepago. No habilitar renovación por adelantado. Worker y observabilidad con gates propios.
4. UX real de ambas entradas, resumen, historial y estados; accesibilidad, responsive/temas,
   teclado, no-JS, reduced-motion, errores, URLs y permisos con controladores productivos.
5. Trazabilidad fiscal opcional tras revisión fiscal; sin ampliar REQ-002 por implicación.
6. OAuth/custodia/refresh/revocación por profesional, políticas comerciales y prueba remota
   autorizada; sólo luego gates legales, fiscales, operativos y activación expresa.

Tests a reutilizar/expandir, no ejecutados aquí: test_payment_order_application,
test_payment_order_persistence, test_payment_order_delivery, test_professional_collection_ux,
test_payment_effect_credits; pruebas de conciliación y gates postgresql_payment_order_application_e2e,
postgresql_payment_order_persistence_e2e. Incluir concurrencia entre distintas obligaciones,
replay tras reinicio, interrupción antes/después de claim/call/commit, reordenamiento de evidencia,
redondeos/límites, migración con legacy NULL y downgrade bloqueado con datos nuevos.
SQLite acredita comportamiento aislado, nunca reemplaza el gate PostgreSQL real autorizado.

## 10. Actualizaciones normativas posteriores a una aprobación

- REQ-003: sujetos, estados habilitados, porciones y acuerdo, identidad, exposición, sucesión,
  entrega por obligación y compatibilidad de URLs contractuales. No cambiar sólo el frontmatter.
- Master Spec: distinguir límites productivos de capacidades aprobadas y nuevo contexto;
  mantener contratación EXTERNAL y CONFIRMADA. Aclarar reglas desactualizadas sobre conversión
  de créditos con referencia a la decisión vigente 4F, sin inventar otra fórmula.
- REQ-002: independencia de medio de pago, trazabilidad opcional y validación de cobertura;
  cualquier ampliación fiscal requiere requisito/ADR separado.
- REQ-001: referenciar elegibilidad externa/porciones y decisiones de política aprobadas;
  conservar exención, costos PSP y créditos. No sobrescribir historia ni fórmulas vigentes.
- Aceptar/versionar ADR-003 y enlazarlo desde registro ADR/INDEX únicamente en encargo autorizado.
  Este encargo preserva esos índices, Master Spec y requisitos aprobados.

## 11. Evidencia y límites de esta entrega

Inspección estática y validación documental únicamente; sin tests de aplicación, DB, Docker,
Git mutable, código ni migraciones. Cierre PROF-UX-004 del 2026-10-18T19:18:45-03:00 y dictamen
independiente «P2 CERRADO — VERIFICADO EN EL ALCANCE EVALUADO» conservados, sin extenderlos a
esta propuesta. PostgreSQL no revalidado, CSP heredada, proveedor simulado y producción pendiente.
Identificadores REQ-005/ADR-003 disponibles al preflight. Preguntas pendientes no bloquean la
redacción, sí la implementación de las decisiones afectadas. Sin aprobación propia ni integración.
