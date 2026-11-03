---
id: ADR-003
titulo: Contexto comercial y obligaciones múltiples de cobro
estado: PROPUESTO
fecha: 2026-10-18T19:41:35-03:00
implementacion: NO_AUTORIZADA
---

# ADR-003 — Contexto comercial y obligaciones múltiples de cobro

Registro: 2026-10-18T19:41:35-03:00. Responsable: Codex local; laptop.
Encargo 2026-10-18T19:30:09-03:00. Rama `feature/professional-workspace-ux`;
HEAD `2e552f2fdc57c152c97f0486050574696f6b250e`.
**PROPUESTO, pendiente de decisión arquitectónica y de Producto.** No es una decisión
aceptada ni autoriza código, migraciones, nuevos servicios externos o activación.
Contrato funcional propuesto: [REQ-005](../REQUISITOS/REQ-005-cobros-anticipos-parciales-externos.md).
Secciones y nombres futuros son diseño conceptual; no representan tablas ya existentes.

## 1. Contexto y evidencia comprobada

El monolito Flask/SQLAlchemy tiene capas de persistencia, aplicación, adaptadores y entrega.
PROF-UX-004 conecta el total contractual sólo con proveedor simulado aislado. La app normal
no compone operación remota. Se necesitan varias porciones por trabajo y trabajos externos
sin contaminar contratación/reputación ni relajar el tratamiento de incertidumbre.

| Fuente actual | Hecho que condiciona el diseño |
| --- | --- |
| [PaymentObligation](../../app/models/payment_obligation.py), líneas 12–25 | FK nullable RESTRICT contract_request_id; UNIQUE uq_payment_obligations_contract_request y uq_payment_obligations_reference; amount positivo. Sin owner directo ni contexto externo. |
| [PaymentOrderReservation](../../app/models/payment_order_reservation.py), líneas 7–18 | UNIQUE obligation_id, local_order_id, idempotency_key, external_reference y payment_order_id; PREPARED/CALL_IN_PROGRESS/SUCCEEDED/UNCERTAIN. Una reserva durable por obligación. |
| [PaymentOrder](../../app/models/payment_order.py), líneas 12–64 | IDs/claves/referencias únicos; identidad PSP provider/live_mode/external_order_id; índice parcial uq_payment_orders_active_obligation; ARS, escala exacta, expiración 72 h y coherencia de timestamps. |
| [PaymentAttemptRecord](../../app/models/payment_attempt.py) | Intento financiero con idempotencia e identidad PSP contextual; no es una orden Checkout. |
| [Evidencia 4E](../../app/models/payment_order_reconciliation.py) | Snapshots únicos por orden/hash y trabajo/attempt de conciliación; varios snapshots pueden describir el mismo pago. No sumar snapshots como ingresos. |
| [Servicio 4B](../../app/services/payment_order_application_service.py), líneas 72–137 y 203–231 | Busca una obligación por contrato, monto igual a precio_acordado, exige CONFIRMADA y ambos owners. Reserva/claim antes de llamada y sesión dedicada; incertidumbre bloquea. |
| [Servicio 4A](../../app/services/payment_order_persistence_service.py) | Admite sucesión local de órdenes; esta capacidad no se expone desde 4B ni equivale a invalidación remota. |
| [Migración 4B](../../migrations/versions/20260917_01_payment_order_application.py) | Introdujo FK nullable/única y reservas; legacy NULL se conserva expresamente. |
| [Pruebas de aplicación](../../tests/test_payment_order_application.py) | Rechazo de estados no CONFIRMADA, precio canónico, replay tras reinicio, owners y bloqueo; futuras pruebas deben diferenciar legacy de nueva política. |

Complementan el fundamento [Master Spec](../REQUISITOS/MASTER_SPEC.md),
[REQ-001](../REQUISITOS/REQ-001-activacion-y-vigencia-pro.md),
[REQ-002](../REQUISITOS/REQ-002-facturacion-pro-mvp.md),
[REQ-003](../REQUISITOS/REQ-003-creacion-de-ordenes-de-cobro-checkout-pro.md),
[ADR-001](ADR-001-pro-entitlement-foundation.md),
[decisiones de arquitectura](../DECISIONES_ARQUITECTURA.md),
[anexo precursor](../REQUISITOS/PROF_UX_004_AMPLIACION_PROPUESTA.md),
[PROF-UX-004](../REQUISITOS/PROF_UX_004.md) y
[auditoría de Cobros](../../../.codex/visualizations/2026/09/17/01a0afe3-1eed-7981-8e70-6afbac0e721e/auditorias/cobros-20261018/INFORME_AUDITORIA_COBROS.md).
Su evidencia de 246 pruebas es histórica recibida, no ejecutada para este ADR.

Distinción de límites: quitar UNIQUE por sí solo no sirve; one_or_none y _same_price
siguen asumiendo obligación final única. Una interfaz con importe editable no supera ese
contrato ni resuelve exposición. La FK nullable no constituye soporte comercial externo.

## 2. Alternativas incrementales

| Alternativa | Ventajas | Costos / riesgos | Recomendación |
| --- | --- | --- | --- |
| A. Sólo quitar unicidad por contrato y añadir tipo/secuencia a obligación | Cambio corto para parciales internos | No resuelve contraparte/origen externo; duplica ownership/reglas; servicio actual falla con varias filas; saldo global ausente | No elegir como solución completa; posible etapa interna sólo dentro del diseño B. |
| B. Contexto comercial propio, obligaciones múltiples y reservas conservadas | Una autoridad para exposición/ownership; externos sin contratos ficticios; reutiliza 4A–4F con fronteras explícitas | Nueva estructura, backfill y servicio por obligación; debe coordinar estado contractual con contexto | Recomendada con implementación gradual y gates. |
| C. Contrato ficticio o contracting_mode EXTERNAL como canal | Reutiliza filtros existentes | Inventa consentimiento, reputación y semántica; no resuelve parciales ni unicidad | Rechazar. |
| D. Reemplazar todo por ledger/event sourcing o múltiples intentos desde el inicio | Flexibilidad amplia | Reescritura innecesaria, más superficie de concurrencia, recuperación y migración | No adoptar; usar asignaciones auditables mínimas sobre evidencia existente. |

B amplía el anexo precursor sin aprobarlo retrospectivamente. Introducir contexto interno
primero permite después externos sin otro modelo paralelo. No requiere framework, broker,
SDK o biblioteca nueva; mantener servicios de dominio y consultas fuera de rutas/templates.

## 3. Decisión recomendada, aún no aceptada

### Entidades y cardinalidades conceptuales

1. **Contexto comercial (CollectionWork, nombre provisional):** dueño profesional y usuario,
   origen INTERNAL_CONTRACT/EXTERNAL_CHANNEL, vínculo opcional único a contrato, concepto,
   contraparte mínima, total opcional, moneda, procedencia y versión/evidencia del acuerdo.
   Un contexto interno por contrato; muchos contextos externos por profesional. Versiones
   aceptadas inmutables; no sobrescribir historia al cambiar el total. Para interno el contexto
   referencia la versión contractual: snapshot no se transforma en segunda autoridad del precio.
2. **Obligación (PaymentObligation):** una solicitud/porción identificable y auditable del
   contexto; tipo anticipo/parcial/saldo/total, amount inmutable, moneda, referencia opaca,
   versión de acuerdo y clave de confirmación lógica. Varias obligaciones por contexto.
   «Obligación» es nombre técnico: procedencia declarada no afirma deuda legal aceptada.
3. **Reserva de creación (PaymentOrderReservation):** comando y claim durables para obtener
   una orden. Una por obligación en la primera etapa; no es intento de pago. PREPARED o
   incertidumbre consumen exposición. La renovación requiere otro ADR/paquete de recovery;
   no borrar reserva ni cambiar su clave para sortear UNCERTAIN.
4. **Orden (PaymentOrder):** enlace/QR y ciclo técnico de checkout. Conserva identidad PSP,
   snapshots y vigencia; éxito de creación no acredita dinero. Una activa por obligación,
   histórica sucesión permitida en 4A pero bloqueada en aplicación hasta definición segura.
5. **Intento financiero (PaymentAttemptRecord):** no almacenar order ID como attempt ID.
   Mantener correlación con evidencia financiera, identidad PSP y resultados existentes.
   Intento técnico de conciliación tampoco es un pago.
6. **Pago/evidencia:** conservar snapshots 4E y derivar una identidad de pago autoritativa
   (proveedor, entorno, cuenta receptora e ID de pago) con moneda e importe verificados.
   Una observación de estado no es un pago nuevo. No duplicar evidencia en un ledger general.
7. **Aplicación/imputación propuesta:** relación auditable del pago verificado con obligación
   y trabajo, importe y clave única de hecho aplicado. Para primera fase pago de una orden
   se imputa sólo a su obligación; extender repartos requerirá autorización. La relación
   soporta correcciones/reversiones explícitas, no ediciones destructivas. Suma imputada no
   puede superar monto acreditado aplicable ni cruzar propietario/moneda.

Factura futura relacionable por asignaciones fiscales separadas, opcionales y con cobertura
no duplicada; no se almacena como pago u obligación nueva. Suscripciones a MANDOBRA tienen
otro sujeto y no se agregan al saldo de trabajos. ARCA y relación fiscal se diseñan después.

### Ownership y contrato

Owner deriva de sesión persistida y del perfil, nunca de parámetros confiados. Interno exige
además ContractRequest.professional_user_id y Professional.user_id coherentes; revalidar al
preparar y finalizar. Externo exige contexto propio; no actor ficticio. Desconocido/legacy no
se expone por fallback. Proponer claves compuestas/FK para coherencia contexto-obligación,
pero no confiar sólo en snapshots de owner. El diseño final de constraints se revisa antes
de migrar; no debilitar filtros si la DB no puede expresar un invariante entre tablas.

Cobros no ejecuta transiciones contractuales. Los estados propuestos de REQ-005 requieren
política nueva y consentimiento de condiciones; CONFIRMADA sigue confirmación de finalización
por cliente. Cualquier versión desactualizada o permiso perdido bloquea nuevo envío sin
borrar evidencia remota que pueda llegar luego. contracting_mode EXTERNAL permanece intacto.

### Exposición, idempotencia y concurrencia

Una raíz de lock por trabajo serializa decisiones entre distintas obligaciones; bloquear sólo
cada obligación permite sobreexposición por carreras. Orden recomendado uniforme: actor/perfil
cuando corresponda → contrato interno → contexto → obligaciones/reservas en ID estable →
órdenes/asignaciones. Revisar orden contra todos los escritores existentes para evitar deadlocks.
Cambios contractuales concurrentes deben comprobar versión/estado bajo el mismo protocolo.
Si eso exige adaptar escritores de acuerdos, incluirlos expresamente en el paquete futuro.

Dentro de una transacción corta: cargar autoridad, validar versión, calcular imputado y exposición,
validar q según REQ-005, deduplicar confirmación lógica y persistir obligación/reserva/exposición
más auditoría atómicamente. Constraints de unicidad resuelven doble envío. Consulta/credencial y
política deben ser válidas antes del claim conforme 4B. Commit del claim antes de llamar PSP;
ninguna sesión/lock abierto durante I/O remoto. Finalizar con nueva transacción revalidando
contexto y respuesta; fallo/caída después del claim mantiene exposición e identidad.

Si el contrato cambia mientras la llamada está en vuelo, no descartar el resultado ni liberar
la reserva: conservar inconsistencia para recovery/conciliación con la misma identidad.
Un cambio local no invalida remotamente el enlace. Definir en el paquete de implementación
el estado auditable correspondiente sin reutilizar éxito falso ni retry automático.

Cada obligación compromete q una sola vez. Pago aplicado sustituye exposición por imputación
atómicamente, con deduplicación de evento y de identidad financiera entre snapshots. Los importes
permanecen Decimal exactos (ARS, dos decimales, límites existentes, sin float) y UTC aware en
fronteras, normalización legacy UTC naive existente en persistencia; no cambiar zonas silenciosamente.
Saldo/estimación/desconocido y revisión siguen REQ-005. No mantener una columna editable de saldo
como fuente independiente; proyección reconstruible y comprobable desde acuerdos y hechos.

Cancelación/expiración local mantiene evidencia y no libera capacidad automáticamente. Primero
recovery autoritativo y conciliación, después resolución auditada. Mantener una reserva por
obligación evita introducir sucesión remota prematura. Crear otra obligación por el mismo
importe no es mecanismo de recuperación. En pagos tardíos, refunds o chargebacks, congelar
nuevas solicitudes afectadas hasta decidir imputación/ajuste; no eliminar evidencia ni conceder
PRO por renderizar o repartir un pago. No afirmar reversibilidad de dinero desde rollback SQL.

## 4. Constraints: cambios propuestos y conservación

| Constraint / relación | Tratamiento recomendado |
| --- | --- |
| uq_payment_obligations_contract_request | Sustituir para v2, no eliminar sin reemplazo: contexto interno único por contrato; unicidad parcial legacy por contract_request_id y unicidad (contexto, secuencia/clave lógica) para nuevas obligaciones. |
| FK payment_obligations.contract_request_id nullable RESTRICT | Conservar columna/transición legacy; nuevas filas v2 referencian contexto y no duplican contrato en dos autoridades. Discriminador separa legacy/v2. |
| Contexto nuevo | FK owner/perfil; FK contrato RESTRICT; UNIQUE contrato cuando no NULL; CHECK origen INTERNAL requiere contrato y EXTERNAL no lo tiene; moneda/total válido o NULL; autoridad/evidencia de acuerdo coherentes. |
| Obligación v2 | FK contexto RESTRICT, importe positivo exacto/ARS; tipo y versión; UNIQUE referencia global conservada y clave lógica por contexto. Legacy sin contexto permitido sólo por discriminador explícito. |
| uq_payment_order_reservations_obligation | Conservar. Múltiples obligaciones no significan múltiples reservas de una misma obligación. |
| Unicidades de reserva/orden (IDs, idempotency, external_reference, payment_order_id) | Conservar; no regenerar ni reciclar. |
| uq_payment_orders_active_obligation | Conservar; por sí solo no protege el total del trabajo, requiere lock agregado/exposición. |
| Identidad PSP de orden/intento, FKs RESTRICT, checks de estado/fecha/ARS/72 h | Conservar. Revisar ámbito de cuenta receptora antes de cualquier extensión de identidad, sin relajar identidad histórica. |
| Aplicación nueva | FK a evidencia/pago correlacionado y obligación, owner/moneda compatibles; identidad única de aplicación; monto positivo y reversión referenciada. Sumatorias protegidas por transacción/locks, no CHECK entre filas simulado. |

Para legacy, indicador explícito de versión de origen y mapping de contexto sin alterar el monto.
Nueva obligación v2 no usa contract_request_id directamente. Una constraint impide mezclar ambas
rutas; el validador bloquea contrato con obligaciones legacy expuestas/inciertas antes de crear
porciones nuevas. La conservación de unicidad legacy impide que un caller viejo cree un segundo
total. Debe existir además barrera de modo por contexto para que un caller legacy no cree un total
junto con porciones v2 cuando todavía no tenía obligación; ver compatibilidad siguiente.

## 5. Migración, registros actuales y compatibilidad

Plan a aprobar y después implementar mediante Alembic, sin SQL ejecutado en este encargo:

1. Inventario de esquema/head real, conteos/huellas, ownership y coherencia en copia autorizada.
   No asumir que una migración histórica es el head aplicado. Identificar NULL, duplicados,
   importes ambiguos, incongruencias con contrato, órdenes activas, claims inciertos y pagos.
2. Expandir columnas/tablas con defaults fail-closed, sin activar escritura v2. Añadir contexto,
   mapping, versión legacy/v2 y asignaciones; checks/índices revisados, backfill reanudable.
3. Por obligación legacy con contrato coherente, asociar contexto interno determinista uno a uno;
   conservar PK, referencia, importe, moneda, timestamps, órdenes, reservas, claves, auditorías y
   evidencia. No reemplazar amount por el precio actual si cambiaron: marcar revisión, no revaluar.
4. Legacy contract_request_id NULL queda legacy sin contexto o en cuarentena administrativa
   restringida; NO inventar owner, contraparte u origen externo. Datos ambiguos no se habilitan.
   No inferir «pagado» desde ACTIVE/SUCCEEDED, ni reconstruir saldo completo sin evidencia.
5. Incorporar lector dual con proveniencia explícita y validar igualdad de resultados legacy.
   Backfill no ejecuta PSP ni efectos, no extiende URLs ni consentimientos. Validar lotes y
   completitud antes de sustituir UNIQUE por índice legacy/restricciones v2.
6. Activar escritores nuevos sólo después de desplegar barrera para todos los escritores legacy.
   Modo del contexto legacy/v2 serializado: una vez usado v2, POST por contrato sin obligación
   explícita no crea total automáticamente. Rechaza con conflicto seguro y acceso a selector.
   No coexistir con binarios antiguos que ignoran modo/exposición: ventana controlada o bloqueo
   de creación durante transición, lectores permitidos. No llamar a esto rolling upgrade seguro
   sin prueba. Contratos legacy preservan replay exacto de orden existente.
7. Nuevas rutas/DTO por obligación/contexto, sin ID manipulable para ajenos. URLs contractuales
   existentes GET/QR conservan acceso a la orden legacy autorizada; nunca eligen arbitrariamente
   «la última porción». Contrato v2 sin legacy ofrece selección explícita, sin escritura GET.
   POST legacy conserva CSRF y semántica de replay; no redirección genérica que cree otra orden.
8. Habilitar interno gradual con flag apagado por defecto; después externos y, separadamente,
   conciliación/recuperación y operación remota. No habilitar dinero real por finalizar backfill.

No se reinterpretan filas previas como anticipos/partes de un plan. Legacy total mantiene su
significado; una nueva negociación requiere nueva versión y tratamiento explícito de exposición.
Los contratos confirmados no se reabren ni generan reviews por migración.

### Reversibilidad

Antes de escrituras v2, rollback estructural sólo tras comprobar que datos agregados no son
necesarios y conservar backup/mapping verificado. Después de múltiples obligaciones o externos,
volver a UNIQUE por contrato es potencialmente imposible sin pérdida: downgrade debe negarse
si existen esos datos o referencias, nunca borrar ni fusionar importes. Preferir desactivar
creación nueva, mantener lectura/conciliación y corregir hacia adelante. Mantener claims/IDs
para toda incertidumbre; restaurar backup no deshace una llamada PSP. Runbook y plan de incidente
son gates previos, no una autorización de reset o downgrade en el entorno compartido.

## 6. Política comercial, fiscal y dependencias

Preservar reglas de REQ-001/ADR-001: entitlement calculado y exención de comisión MANDOBRA
por suscripción efectivamente pagada, costos PSP separados, créditos sólo con comisión neta
verificada bajo política versionada. 4F actual requiere importe completo de orden y contexto
correlacionado: no derivar efectos de nuevas asignaciones sin adaptar/testear explícitamente
su resolución de contexto y temporalidad. No reutilizar un contrato ficticio para pasar esa
validación. Doble origen/aplicación no duplica crédito. No cambiar tarifas ni fórmula vigente.

Facturación conserva REQ-002 y revisión fiscal; pagos manuales o por fuera no son evidencia
PSP. Asociación opcional de documentos y obligaciones no duplica importe facturado. Notas de
crédito/debito y tratamiento tributario de anticipos requieren aprobación fiscal separada.
Cobros no requiere ARCA configurada, pero no declara ausencia de obligaciones fiscales.

Gates sin cambios: OAuth por receptor, storage cifrado, refresh/revocación, account binding,
política de comisión y precio, credenciales/URLs HTTPS, webhook autenticado, worker 4E,
recovery, retornos informativos, observabilidad, soporte, pruebas remotas autorizadas y
aprobaciones legal/fiscal/productiva. Mantener los flags actuales; nunca instalar fake como
fallback por OAuth faltante. La propuesta no selecciona un nuevo proveedor ni dependencia.

## 7. Riesgos y validación necesaria

| Riesgo | Mitigación y criterio antes de habilitar |
| --- | --- |
| Sobrecobro entre obligaciones | Lock raíz común, modo legacy/v2, versiones y límite agregado; carreras reales PostgreSQL. |
| Pago tardío tras cancelación local | No liberar exposición por estado local; correlación/recovery y revisión de excedente. |
| Doble aplicación de snapshots/refunds | Identidad financiera estable y claves únicas; probar duplicados y eventos fuera de orden. |
| Dos contextos externos para mismo servicio | Aviso de posible duplicado/confirmación; no prometer deduplicación semántica perfecta ni fusionar personas. |
| Backfill adjudica deuda/owner inexistente | Legacy NULL aislado, sin inferencia, comparación de hashes/campos y muestra de casos ambiguos. |
| Retorno a binario viejo | Bloqueo de escritores incompatibles y downgrade condicionado, no pérdida de datos. |
| Exposición de PII | DTOs mínimos, ownership backend, referencias opacas, sin PII en URL/logs; política de retención pendiente. |
| Cambio contractual en vuelo | Persistir identidad y bloqueo aunque finalización falle; conciliar sin repetir creación. |

Plan de pruebas propuesto, NO ejecutado: unitarias de cantidades/decimales, estados/acuerdo,
exposición e imputaciones; integración de app normal y simulada/roles/CSRF/read-only GET;
migraciones upgrade/backfill/reanudar y downgrade con rechazo seguro; regresión total legacy.
PostgreSQL exclusivo y autorizado: dos obligaciones concurrentes sobre mismo trabajo,
legacy versus v2, cambio de total versus claim, dos pagos que compiten por saldo,
refund versus aplicación, rollback de auditoría y creación, reinicio tras claim/PSP/commit,
locks y deadlocks, índices parciales e identidad. SQLite no sustituye estos gates.

Reutilizar pruebas [4A](../../tests/test_payment_order_persistence.py),
[4B](../../tests/test_payment_order_application.py),
[entrega](../../tests/test_payment_order_delivery.py),
[efectos](../../tests/test_payment_effect_credits.py),
[UX aislada](../../tests/test_professional_collection_ux.py) y
[gate PostgreSQL](../../tests/postgresql_payment_order_application_e2e.py).
Comparar con normas actualizadas; no debilitar pruebas legacy para hacer pasar nueva semántica.

## 8. Decisiones pendientes y consecuencias

Recomendación B depende de D1–D10 de REQ-005. Arquitectura debe elegir además:

- Contexto común vs tablas interna/externa separadas: recomendar común con origen y constraints,
  reduce duplicación sin borrar autoridad contractual.
- Una reserva vs múltiples generaciones por obligación: conservar una inicialmente; generación
  múltiple sólo con protocolo de cancelación/recovery y gate remoto específicos.
- Proyección vs saldo editable/event sourcing: proyección reconstruible de hechos mínimos,
  sin framework nuevo; auditoría atómica, claves e invariantes explícitas.
- Compatibilidad total automática vs selección explícita: replay legacy exacto y selección
  obligatoria para v2; evitar que un enlace viejo solicite todo el precio por segunda vez.

Consecuencias positivas: origen externo real, porciones trazables, separación fiscal/financiera,
reutilización de servicios. Costos aceptables sólo tras aprobación: migración, ajuste de
resolución de contexto 4B/4D/4E/4F, lector dual, protocolo común de locks y estados de revisión.
El mecanismo de aceptación externa, pagos manuales y efectos fiscales sigue pendiente;
no lo resuelve una FK o una firma de token de navegador.

No reemplaza ADR-001/002 ni decisiones aprobadas. Tras aceptar, actualizar REQ-003, Master
Spec y referencias REQ-001/002 conforme sección 10 de REQ-005; registrar ADR aceptado con
fecha/autoridad y paquete de implementación propio. No editar retrospectivamente PROF-UX-004.
En este encargo sólo se crean Spec/ADR y se referencia desde handoff, sin tocar INDEX.

## 9. Estado y evidencia documental

Inspección de archivos, no ejecución de tests/migraciones ni conexión DB. Sin nuevas garantías
PostgreSQL, certificación fiscal/AA o preparación productiva. Cierre de QA PROF-UX-004 y P2
preservado; no es evidencia de esta ampliación. Pendiente revisión de Producto, Arquitectura,
Seguridad y fiscal/legal, decisiones explícitas y autorización de un incremento acotado.
