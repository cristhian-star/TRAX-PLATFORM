# UX-06A — corrección P1/P2 para retest

Registro: 2026-09-27T22:04:02-03:00; rama `feature/ux-ui-foundation`; HEAD `7af47a2`.
Estado: pendiente de retest independiente, no aprobado.

Implementado: transacción única de creación/notificación INTERNAL/OperationCommand,
clave criptográfica ligada al actor y operación, replay durable y conflicto de payload;
recuperación temporal del borrador saneado tras caducar autenticación, login real,
CSRF mantenido, aislamiento por actor/navegador/pestaña y descarte/TTL de 15 minutos.
Se conservan permisos CLIENTE/PROFESIONAL aprobados y diseño UX-06A.

Validación de Implementación: 132 PASS + 1 SKIP en 133 Python relacionados, 4 PASS
en PostgreSQL exclusivo real y 5 PASS Node. Pendientes: retest independiente y
suite completa por Testing; matriz visual completa no repetida en esta corrección.

Dependencias operativas futuras, fuera del incremento:
- decidir política de purga periódica y límites globales del almacenamiento temporal;
  hoy la expiración se aplica al acceder y no permite restaurar un borrador vencido;
- verificar almacenamiento privado compartido antes de escalar horizontalmente;
  recuperación actual local, sin promesa de durabilidad distribuida;
- si Producto necesita recuperar más allá de 15 minutos o entre dispositivos,
  diseñar un borrador persistente con política de privacidad y aprobación previa;
- rotación de secretos invalida formularios emitidos; definir continuidad de claves
  antiguas solo si el despliegue lo requiere. No se agrega infraestructura para ello.

Sin migraciones nuevas, Redis, colas ni outbox. El historial siguiente se conserva;
las menciones antiguas a atomicidad y borrador pendientes quedan superadas solo por
esta implementación, nunca por una aprobación de Testing.

---

# BACKLOG MANDOBRA

## P1 UX-06A — Corrección de facultades de propietario

Corrección aprobada: 2026-09-27T19:49:55-03:00; registro: 2026-09-27T20:00:55-03:00.
Estado: IMPLEMENTADO; RETEST INDEPENDIENTE PENDIENTE, sin aprobación de UX-06A.
Testing: 2026-09-27T19:48:47-03:00, P1 REQUIERE_CORRECCIONES.

Se descarta la ampliación CLIENTE/PROFESIONAL del registro histórico siguiente.
Solo CLIENTE activo puede crear y administrar solicitudes propias y ejercer el
actor cliente del contrato BUDGET. Profesional conserva oportunidades, ofertas y
actuación como contraparte contratada. Rutas y servicios rechazan rol incorrecto;
se cubren datos heredados, sesión desactualizada, acceso horizontal e idempotencia.
El rediseño visual, JS, validaciones, visitantes y CSRF se conservan.

El pendiente histórico de reseñas de solicitante PROFESIONAL queda descartado,
no es una autorización futura. Permanecen los pendientes de borrador recuperable,
adjuntos, taxonomía, matching, distribución, IA, edición, atomicidad, métricas,
expiración e idempotencia durable de creación, fuera de esta corrección.
No se borraron ni reasignaron datos creados bajo la implementación rechazada.

Pruebas: 117 Python (116 PASS, 1 SKIP preexistente PostgreSQL), 5 Node PASS;
compileall, sintaxis JS y diff check correctos. No hubo fallos en esta tanda.
Pendientes: retest P1 por Testing y suite completa por ese agente. El registro
histórico de validación de ambos roles no constituye evidencia de aceptación actual.


## UX-06A — Solicitudes de presupuestos

Timestamp: 2026-09-27T18:43:08-03:00. Rama `feature/ux-ui-foundation`; base `7af47a25a59efcb64f70c2596d9f6818ace298bc`.
Estado: implementado localmente; aprobación visual y Testing independiente pendientes.

Visitantes ven una entrada informativa con login/registro y next interno a
/presupuestos/nuevo; no completan ni previsualizan formularios anónimos. CLIENTE
y PROFESIONAL activos pueden solicitar y administrar exclusivamente solicitudes
propias. El profesional conserva sus oportunidades y no puede autoofertar.
Formulario breve, opcionales desplegables, revisión local, publicación nativa,
validación del servidor, valores conservados y confirmación con contador real.

Pendientes de dominio, fuera de UX-06A:

- Borrador recuperable tras login/caducidad de sesión; hoy no hay persistencia de borradores.
- Adjuntos y su seguridad/almacenamiento.
- Taxonomía de rubros y catálogo administrable.
- Matching geográfico y distribución automática: hoy no se prometen respuestas.
- IA de asistencia o clasificación.
- Edición posterior a publicar y reglas sobre ofertas existentes.
- Política definitiva de visibilidad: no se amplía la exposición de ofertas privadas.
- Atomicidad solicitud/notificación: siguen siendo commits separados; evaluar outbox.
- Métricas de publicación, búsquedas, respuestas y conversión.
- Expiración real; no mostrar temporizadores sin soporte de dominio.
- Reseñas contractuales del solicitante PROFESIONAL: el permiso vigente es CLIENTE.
  UX-06A no lo amplía ni muestra un CTA que terminaría en 403.
- Idempotencia de creación de solicitud ante reenvío de red/recarga: el bloqueo de
  doble clic es local. No confundirlo con la idempotencia canónica BUDGET existente.

Validación: 157 pruebas Python relacionadas, 156 PASS y 1 SKIP preexistente de
concurrencia PostgreSQL; 16 Node PASS (5 nuevas + 11 skeleton). Matriz real:
30 combinaciones (visitante/CLIENTE/PROFESIONAL × claro/oscuro ×
1440/1024/768/390/320), 200 controles >=44×44; cero overflow estable.
La suite completa y el gate concurrente PostgreSQL quedan para Testing.


## UX-04B/04C — Estados de carga y errores amigables

Timestamp: 2026-09-27T16:12:05-03:00. Rama feature/ux-ui-foundation; base 18c422e.
Estado: implementado localmente; aprobación visual y Testing independiente pendientes.

Skeleton global: enlaces internos elegibles y submits válidos, espera 300 ms,
mensaje a 8 s, cleanup pageshow/bfcache/Escape/Navigation API y fail-safe 30 s.
Excluye externos, protocolos especiales, descargas, targets nuevos, anclas locales,
modificadores, eventos cancelados, data-no-loading y formularios inválidos.
Sin SPA/intercepción/reenvío; no opera antes de la primera respuesta HTML absoluta.
Sin Navigation API, cancelaciones no observables dependen de Escape/pageshow/límite.

403/404/500/503 comparten template seguro, marca, temas, acciones reales y SVG
local original animado suavemente; movimiento reducido desactiva animaciones.
TESTING/JSON, health, webhooks, CSRF, headers y logs genéricos preservados;
render de errores no consulta notificaciones. QA aislado en /dev/qa/estados.

Evidencia: 143 Python PASS tras corregir orden de CSS, última tanda focal/seguridad/
webhook 65 PASS (solapada, no sumar), Node final40 PASS; compileall, sintaxis,
UTF-8, enlaces y diff-check. Chrome48 casos errores +12 skeleton en seis anchos y
ambos temas; mínimos44px, sin overflow estable. Alcances exactos en ACTIVE_HANDOFF.

Pendientes: aprobación visual; suite completa/retest independiente; AT, JS apagado,
bfcache real y navegadores legacy; reduced motion del SO y zoom real (720px equiv.
200% ya revisado). No confundir estas reservas con un PASS de Testing.
No migraciones ni nuevas dependencias. Sin staging/commit/push/merge.

## UX-05A: ajuste visual exclusivo de Explorar

Timestamp: 2026-09-27T14:30:36-03:00. Implementado localmente, revision visual pendiente.
Capa azul superior reforzada; sin controles visibles de pausa/anterior/siguiente.
Autoplay8s y fade750ms conservados; pausas de accesibilidad automaticas.
Home congelado por instruccion de Producto, hashes verificados sin cambios.
19 Python y6 Node PASS. Sin staging/commit/push/merge. Evidencia y limites en handoff.

## UX-05A: bandas grandes enlazadas, sin las seis tarjetas fijas

Timestamp: 2026-09-27T14:18:48-03:00. Estado: implementado localmente, revision visual pendiente.
Decision nueva de Producto: las bandas reemplazan las seis tarjetas fijas del home.
376/248px por tarjeta, titulos enlazados a /buscar?servicio=..., velocidad lineal
aproximadamente12% menor; hover/foco pausa y teclado expone originales desplazables.
Doce assets intactos. Sin cambios al hero principal, Explorar ni backend.
64 Python y13 Node PASS;16 focales repetidos tras corregir especificidad del foco,
PASS. Chrome siete anchos x dos temas,12 enlaces visibles por Tab a320/escritorio.
Sin staging/commit/push/merge. Handoff conserva resultados, mapeo y limitaciones.
Aprobacion visual, Testing/suite completa y CLS instrumental pendientes.

## UX-05A refinado: Explorar sereno y bandas dentro del home

Timestamp: 2026-09-27T14:00:27-03:00. Rama `feature/ux-ui-foundation`; base `85a7f22`.
Estado: implementado localmente; NUEVA APROBACION VISUAL PENDIENTE.
La aprobacion visual anterior queda retirada por exceso de movimiento en Explorar.
La autorizacion de los doce assets y sus excepciones se conserva.

Explorar: siete escenas, fundido750ms/intervalo8s, controles laterales, pausas por
interaccion/visibilidad y modo reducido; sin bandas, pausa visible ni contador.
Home: dos bandas opuestas60s dentro de Oficios destacados, despues del texto y
antes de las seis tarjetas intactas. Hero principal, buscador y veinte rubros sin
cambios funcionales. Doce WebP reutilizados con SHA-256 identicos, sin duplicacion.

94 Python +28 Node PASS; compileall/sintaxis/UTF-8/relativos/diff-check PASS.
Chrome:28 combinaciones (dos paginas x dos temas x siete anchos),42 controles
>=44x44, sin overflow persistente; capturas y trazabilidad en
[handoff activo](HANDOFFS/ACTIVE_HANDOFF.md). Compose descartable5050 disponible.
Pendientes: revision visual del responsable, Testing independiente y suite
completa posterior; CLS instrumental y emulacion visual sin JS/reduced-motion.
No declarar aprobado ni integrado. Sin staging/commit/push/merge/migraciones.

### Registro historico: primera composicion supersedida

## UX-05A: doble carrusel decorativo de Explorar rubros

Timestamp: 2026-09-27T12:48:26-03:00. Estado: implementado localmente, aprobacion visual PENDIENTE.
Rama feature/ux-ui-foundation; base 85a7f22c50e07fcc37e2f6bacce866d920736c12.
Producto autorizo las doce imagenes actuales y sus excepciones visuales; PNG
externos intactos. Doce WebP 960x540, RGB, sin metadatos, total 1021870 bytes.
Dos filas con seis escenas y copias decorativas, sentidos opuestos, 60s; pausa
accesible, fallback estatico sin JS, reduced-motion y print. Sin cambios al
catalogo, busqueda ni backend. Orden y procesamiento completos en el
[handoff activo](HANDOFFS/ACTIVE_HANDOFF.md).

77 Python y 24 Node PASS; matriz Chrome 14 combinaciones sin overflow, control
44x44 y contraste de texto >=15,9:1. Suite completa y retest independiente
pendientes. Completar CLS instrumental y emulacion visual sin JS/reduced-motion/
print; no confundir cobertura estructural con medicion real. Entorno descartable
5050/explorar disponible. Sin staging/commit/push/merge.


## UX-04A: navbar adaptable con drawer vertical

Timestamp: 2026-09-26T21:03:18-03:00. Rama: `feature/ux-ui-foundation`.
Base: `263a158dfec83d280e3686edd5ca34271992b3fc`. Estado: implementado localmente,
pendiente de aprobacion visual e integracion Git. No hubo commit, push ni merge.

- Una sola navegacion, reubicada en dialog modal a la derecha cuando la fila no
  cabe completa. El ancho se mide nuevamente ante resize, fuentes o cambios de
  texto; no se comprimen etiquetas ni se elige un breakpoint fijo por dispositivo.
- Con los usuarios demo actuales: minimo util 1141 px (claro) / 1146 px (oscuro)
  visitante; 1301 / 1306 px CLIENTE y PROFESIONAL. Incluye logo, opciones, controles,
  separaciones y padding. Comparacion contra el ancho real del header, descontando
  el espacio ocupado por scrollbar. Los numeros son evidencia, no constantes JS.
- Dialog nativo con backdrop, Escape, foco contenido/restaurado, bloqueo de scroll,
  botones de acordeon, acciones de cuenta al final y fallback HTML/CSS sin JS.
- Verificacion focal: 62 unittest PASS y 18 casos/archivos Node PASS; matriz visual
  de tres perfiles y dos temas entre 320 y 1440 px, extremos del umbral y reflow
  equivalente a 200 % (720 CSS px desde una base de 1440).
- Pendiente: aprobacion humana, revision visual real sin JS y emulacion visual de
  movimiento reducido. La apertura del fixture local sin scripts fue rechazada por
  la politica de URL del navegador; no se eludio. Esos contratos tienen pruebas
  estructurales/controlador, no evidencia visual equivalente a un navegador sin JS.
- Pendiente posterior: retest independiente y compatibilidad en otros motores.
  Suite completa no ejecutada por alcance. Panel privado, skeletons, paginas de
  error, backend y migraciones permanecen fuera de UX-04A.

Detalle y continuidad: [ACTIVE_HANDOFF.md](HANDOFFS/ACTIVE_HANDOFF.md).

## Futuro: datos reales y metodología de Precios de mercado

Timestamp: 2026-09-22T22:33:48-03:00. Rama: `feature/ux-ui-foundation`.
UX-03 presenta una guía pública con datos ficticios y estables para validar la
experiencia. No implementa analítica, persistencia nueva ni mediciones reales.
Antes de reemplazar la demostración se deberá definir y aprobar:

- búsquedas anonimizadas por oficio y zona, con privacidad y retención explícitas;
- presupuestos emitidos y aceptados, y precios finalmente acordados;
- distribución por oficio y zona, separando mano de obra y materiales;
- detección y tratamiento de valores atípicos;
- tamaño mínimo de muestra antes de publicar una referencia;
- fecha de actualización visible;
- metodología versionada y trazable;
- revisión administrativa de métricas y calidad de datos.

Las referencias futuras deberán distinguir estimaciones de cotizaciones y no
afirmar representatividad cuando la muestra sea insuficiente.

## Futuro: evolución de búsqueda y catálogo de rubros

Timestamp: 2026-09-21T20:18:54-03:00. Rama: `feature/ux-ui-foundation`.
UX-02 presenta veinte rubros editoriales y mantiene correspondencias de búsqueda
explícitas, sin ampliar la taxonomía canónica ni afirmar oferta, demanda o
popularidad. Quedan para incrementos posteriores:

- sinónimos y aliases revisados para cada rubro;
- catálogo canónico administrable y su gobierno editorial;
- búsqueda por especialidades;
- normalización territorial de CABA y AMBA;
- métricas de búsquedas con criterios de privacidad y retención;
- registro y análisis de búsquedas sin resultados;
- medición de oferta real por región;
- conversión desde búsqueda a perfil y contratación;
- ranking basado en evidencia y resistente a manipulación;
- revisión del tratamiento global de errores.

## Futuro: identidad legal y perfiles sociales del footer

Timestamp: 2026-09-20T16:31:28-03:00. Rama: `feature/ux-ui-foundation`.
El footer UX-01 es una **presentación demostrativa**. Los documentos legales y perfiles externos todavía no están disponibles ni se anuncian como vigentes. Pendientes: crear y verificar perfiles oficiales de Instagram, Facebook y LinkedIn; conectar únicamente URLs oficiales verificadas; definir propiedad, recuperación, autenticación reforzada y responsables internos de las cuentas. Redactar Términos y condiciones, Política de privacidad, Política de cookies, reglas de pagos, cancelaciones y reembolsos, Normas de la comunidad, y política de contenido, imágenes y autorizaciones. Someterlas a revisión legal y fiscal antes de producción; crear rutas reales y retirar cada indicación «Próximamente» cuando el recurso correspondiente esté aprobado y habilitado. No se incorporan redes, rastreadores, cookies ni enlaces legales ficticios en este incremento.

## Futuro: asistencia documentada y soporte humano

Timestamp: 2026-09-20T16:08:46-03:00. Rama: `feature/ux-ui-foundation`.
El FAQ del home UX-01 filtra seis preguntas y respuestas **exclusivamente en el navegador**; no transmite ni conserva consultas. Incremento posterior: asistente RAG restringido a documentación aprobada, respuestas con fuentes, derivación a soporte humano, tickets de consulta con estados y responsables, consentimiento y privacidad, retención de mensajes, límites de frecuencia y protección contra abuso, notificaciones de respuesta, vinculación opcional con WhatsApp y métricas anonimizadas de preguntas no resueltas. Definir políticas y autorización antes de incorporar persistencia, servicios externos o IA.

## Futuro: búsqueda territorial y ranking de oficios con evidencia

Timestamp: 2026-09-20T15:39:04-03:00. Rama: `feature/ux-ui-foundation`.
Las seis tarjetas de "Oficios destacados" del home UX-01 son una **selección editorial inicial**, no un ranking basado en métricas. No afirmar popularidad, demanda o volumen hasta diseñar y validar:

- eventos anonimizados de búsquedas por oficio y zona, con criterios de privacidad y retención;
- normalización territorial de Capital Federal y AMBA;
- cantidad de profesionales activos y verificados por especialidad y relación entre oferta y demanda;
- búsquedas sin resultados y conversión de búsqueda a contacto, presupuesto y contratación;
- ranking dinámico con ventana temporal, tamaño mínimo de muestra y protección contra manipulación;
- fallback editorial explícito cuando la muestra sea insuficiente.

La captura de eventos, el ranking y la evolución del catálogo/filtros quedan para un incremento posterior. En UX-01 no se implementa analítica ni persistencia de búsquedas.

## Cierre técnico local 4F aprobado por Testing

Timestamp de registro documental: 2026-09-18T09:50:28-03:00
Rama: `feature/payment-effects-pro-commission`; commit técnico: `83581b3`.
Política versionada obligatoria, sin defaults: comisión neta efectiva acumulada
equivalente al precio mensual PRO genera 1 crédito; su consumo concede 30 días.
Remanente Decimal exacto, FIFO, lotes de 40 días, idempotencia, locks y auditoría
atómica. Reloj posterior a locks: un lote vencido durante la espera no concede PRO.
Sin política/evidencia confiable: PENDING_POLICY. Suscripción paga no genera
comisión transaccional. Pagos tardíos, temporalidad incierta y reversos quedan a
revisión, sin compensación ni revocación automática. Ambos flags False.
Migración `20260917_03`, descendiente de `20260917_02`.
Evidencia final suministrada de Testing: focales 66/66, regresiones 363/363,
PostgreSQL 42/42 + 3/3 adversariales; suite 694 aprobadas y 5 omisiones históricas.
Ambos P2 corregidos, sin hallazgos pendientes. Historia preservada.
REQ-001 y REQ-003 siguen APROBADO/PENDIENTE; Sprint 2 productivo continúa abierto.
Este cierre supera únicamente la pendencia técnica local 4F de registros previos;
no habilita disponibilidad productiva, cobros reales, contabilidad ni facturación.
Gate futuro: [producción 4F](DECISIONES_ARQUITECTURA.md#gate-futuro-obligatorio-de-producción).
Detalle: [REQ-001](REQUISITOS/REQ-001-activacion-y-vigencia-pro.md#cierre-técnico-local-4f-aprobado-por-testing)
y [REQ-003](REQUISITOS/REQ-003-creacion-de-ordenes-de-cobro-checkout-pro.md#cierre-técnico-local-4f-aprobado-por-testing).

## Ordenes de cobro Checkout Pro

### Cierre técnico local 4E aprobado por Testing

Timestamp de registro documental: 2026-09-17T21:24:48-03:00
Rama: `feature/mercadopago-payment-reconciliation`; commit técnico: `8dc0e12`.
4E técnico local aprobado: webhook `order` firmado con data.id case-sensitive,
inbox/trabajo durable, cuarentena y leases; consulta Orders con OAuth confiable
inyectado por profesional, sin fallback global. Evidencia verificada de pagos,
reembolsos y reversos, incluidos contracargos y pagos tardíos, sin efectos PRO,
contables o comerciales. Firma válida fuera de ±10 minutos: cuarentena durable
TIMESTAMP_OUTSIDE_WINDOW y 200 después del commit; firma inválida: 401 sin persistir.
Lease 60 s, recuperación desde 120 s y límites Decimal de reembolso por pago y
orden, deduplicados y verificados sobre evidencia acumulada bajo lock.
Migración/head `20260917_02`, descendiente de `20260917_01`; ambos flags False.
Evidencia final suministrada de Testing: focales 96/96, regresiones 197/197,
PostgreSQL 37/37; suite 653 ejecutadas, 648 aprobadas y 5 omisiones históricas.
Migraciones SQLite/PostgreSQL, compileall, Alembic y diff check aprobados;
sin hallazgos P0–P3 pendientes. Hallazgos y correcciones históricos preservados.
Este cierre supera únicamente 4E local y su retest pendientes en registros
anteriores; REQ-003 sigue APROBADO/PENDIENTE y Sprint 2 productivo permanece abierto.
Pendientes: OAuth completo/custodia/renovación, fórmula de comisión, retornos,
credenciales/prueba real, activación productiva y efectos 4F sobre pagos tardíos,
reversos, PRO y contabilidad. No habilita cobros productivos.
Detalle y límites: [cierre 4E](REQUISITOS/REQ-003-creacion-de-ordenes-de-cobro-checkout-pro.md#cierre-técnico-local-4e-aprobado-por-testing).

### Cierre técnico local 4D aprobado por Testing

Timestamp: 2026-09-17T16:14:10-03:00
Rama: `feature/checkout-pro-payment-order-delivery`; commit técnico: `763eee3`.
Verificador: `03 - Testing - Test Executor`; registro documental: Codex.
POST autenticado de creación/replay con sesión, CSRF y ownership; GET autorizado
sin creación ni llamada PSP; checkout y QR PNG con endpoint separado autenticado,
`segno==1.6.6` local en memoria y exactamente la misma URL validada del enlace.
Rechazo de órdenes no entregables por vencimiento/bloqueo, headers privados y
errores genéricos; feature flags deshabilitados por defecto. No habilita cobros
productivos ni cierra Sprint 2 o REQ-003: APROBADO / implementación PENDIENTE.
Evidencia acreditada: 26/26 focales 4D, 52/52 4B–4C, 119/119 regresiones;
PostgreSQL 6/6 más 3/3 reproducciones HTTP; suite 594 ejecutadas, 589 aprobadas,
5 omisiones históricas y 0 fallos. Compileall, Alembic head `20260917_01`,
UTF-8, enlaces, whitespace y git diff --check aprobados. Sin migración nueva.
Supera únicamente endpoint/presentación 4D y su Testing pendientes en registros
históricos. Pendientes: OAuth real, fórmula de comisión, retornos, webhooks,
conciliación, pagos tardíos, efectos PRO/contables, credenciales reales y
validación/activación en entornos de staging y producción.
Detalle y límites: [cierre 4D](REQUISITOS/REQ-003-creacion-de-ordenes-de-cobro-checkout-pro.md#cierre-técnico-local-4d-aprobado-por-testing).

### Actualización posterior - cierre técnico local 4C

Timestamp: 2026-09-17T15:07:04-03:00
Rama: `feature/mercadopago-payment-order-create-adapter`; commit técnico: `b859e6a`.
Verificador: `03 - Testing - Test Executor`; registro documental: Codex.
4C interno implementado y aprobado, deshabilitado por defecto; P2 de secretos
corregido y revalidado, sin hallazgos P0–P3 pendientes. Se supera únicamente
la creación HTTP interna y su retest pendientes en los registros históricos;
no se cierra Sprint 2 ni la implementación productiva de REQ-003 (`APROBADO` / `PENDIENTE`).
Evidencia final acreditada de Testing: focales 52/52,
regresiones 119/119, PostgreSQL 12/12; suite 568 ejecutadas, 563 aprobadas,
5 omisiones históricas, 0 fallos y 0 errores; compileall, Alembic head único
`20260917_01`, whitespace y git diff --check aprobados. Sin migración nueva.
Pendientes: OAuth completo y custodia/renovación; fórmula de comisión;
endpoint/UI 4D; retornos, webhook y conciliación; tratamiento productivo de
pagos tardíos; credenciales y prueba real; activación en producción.
Recuperación incierta y sucesoras permanecen separadas. No hay cobros disponibles.
Evidencia, trazabilidad y alcance: [cierre 4C](REQUISITOS/REQ-003-creacion-de-ordenes-de-cobro-checkout-pro.md#cierre-técnico-local-4c-aprobado-por-testing).

### Actualización vigente - incremento técnico 4B completado

Timestamp: 2026-09-17T11:04:24-03:00
Agente: Codex - implementador documental local
Rama: `feature/checkout-pro-payment-order-application`; commit técnico: `1ba5ab1`.
REQ-003 conserva `APROBADO` e implementación productiva completa `PENDIENTE`.

- 4B completado y aprobado por Testing: servicio de aplicación, actor profesional
  activo, ownership en contrato/perfil, contratos `CONFIRMADA`, obligación final
  única y reserva durable antes del adaptador, con finalización atómica y replay.
- El próximo paso 4B del registro histórico siguiente queda cumplido en ese
  alcance técnico interno. No se acredita un flujo productivo para usuarios.
- Pendientes: Mercado Pago real y creación HTTP, endpoints, UI/checkout/QR,
  recuperación de incertidumbre, creación de sucesoras desde la aplicación,
  integración de órdenes con webhooks/conciliación y efectos PRO/comisiones/facturación.
  Publicación, PR, merge y producción pendientes. Próximo paso con planificación
  y revisión separadas: creación real y frontera pública.
- Evidencia aprobada y límites: [REQ-003](REQUISITOS/REQ-003-creacion-de-ordenes-de-cobro-checkout-pro.md#actualización-vigente---incremento-técnico-local-4b).

### Actualización posterior - incremento 4A

Timestamp: 2026-09-16T22:40:04-03:00
Agente: 01 - Documentation Engineer
Motivo: separar persistencia interna completada de capacidades futuras.
Rama: `feature/checkout-pro-payment-order-persistence`; commit: `4373b64`.
REQ-003 conserva `APROBADO` e implementación productiva `PENDIENTE`.

- 4A implementado y aprobado localmente: `PaymentOrder`, migración/head
  `20260916_01`, replay durable, unicidad activa, ciclo local y auditoría atómica,
  constraints/contexto PSP, concurrencia PostgreSQL y rollback SQLite.
- Próximo incremento 4B: aplicación y ownership desde sesión/`ContractRequest`,
  todavía sin Mercado Pago real. Snapshot profesional no equivale a autorización.
- Pendientes posteriores: HTTP real, recuperación externa incierta, interfaz
  checkout/QR, integración de órdenes con webhook/conciliación, correlación de
  pagos, PRO, comisiones y facturación. Publicación, PR, merge y producción pendientes.
- Cancelación local no cancela preferencias remotas; no hay flujo para usuarios.
- Evidencia y criterios internos: [REQ-003](REQUISITOS/REQ-003-creacion-de-ordenes-de-cobro-checkout-pro.md#actualización-posterior---incremento-técnico-4a).

### Actualización del avance técnico

Timestamp: 2026-09-14T20:43:27-03:00
Estado del requisito: `APROBADO`
Implementación productiva completa: `PENDIENTE`

- Avance técnico parcial implementado y probado: contrato neutral, DTOs
  inmutables, validaciones puras y adaptador determinista en memoria
  (`6d6dd2f`, `12c6418`).
- Pendientes: persistencia durable, ownership, unicidad activa entre procesos,
  Mercado Pago real, HTTP, checkout productivo, QR/interfaz, conciliación y
  efectos financieros o PRO.

### Registro histórico de especificación

Timestamp: 2026-09-14T10:21:05-03:00
Estado: ESPECIFICACION_PREPARADA_IMPLEMENTACION_PENDIENTE

- Revisar [REQ-003](REQUISITOS/REQ-003-creacion-de-ordenes-de-cobro-checkout-pro.md).
- Primer incremento previsto: protocolo neutral, DTOs inmutables, validaciones
  puras, errores mínimos, fake determinista y pruebas unitarias.
- Diferir HTTP/SDK, credenciales, ORM, migraciones, concurrencia PostgreSQL, QR
  gráfico, frontend, WhatsApp, webhooks, conciliación, PRO y producción.
- Diseñar después la persistencia durable de una orden activa por obligación y
  la derivación efectiva de ownership desde contratos internos.

## Infraestructura de coverage pendiente

Timestamp: 2026-09-04T19:50:24-03:00

- PENDIENTE no bloqueante: evaluar `coverage.py` como dependencia de desarrollo
  despues de aprobar un baseline. Esta iteracion no instala la dependencia ni
  define un porcentaje minimo.

## PRO y Facturacion - requisitos aprobados, implementacion pendiente

Timestamp de refinamiento: 2026-09-06T19:22:08-03:00

- Completar [REQ-001 - Activacion y vigencia de MANDOBRA PRO](REQUISITOS/REQ-001-activacion-y-vigencia-pro.md):
  el nucleo calculado, la eliminacion de puntos legacy y las fuentes temporales
  reconocidas quedaron implementados parcialmente; faltan onboarding PSP,
  prueba de 30 dias, lotes de creditos de 40 dias, consumo de umbral para
  periodos de 30 dias, pagos mixtos, suscripcion y transiciones seguras.
- La regla historica de 60 dias por operacion fue reemplazada; no implementarla.
- Resolver antes de implementar REQ-001: porcentaje y base de comision; precio,
  conversion y moneda de creditos; beneficios; reversas; cambios de precio;
  reservas, aprobaciones tardias, reintentos, consentimiento y cargos en
  transito; migracion de accesos y modelo futuro de `ENTERPRISE`.
- Resolver [MP-01 a MP-16](CONSULTAS/MERCADO_PAGO_v0_1.md). El expediente esta
  pendiente y no fue enviado; Mercado Pago es direccion de evaluacion, no
  integracion validada.
- Obtener revision de producto, juridica y contable de la
  [base comercial](LEGAL/BASE_REVISION_JURIDICA_v0_2.md), incluida naturaleza
  de creditos, precio total, baja, consentimiento, devoluciones, retencion,
  responsabilidades y tratamiento fiscal.
- Implementar [REQ-002 - Facturacion MANDOBRA PRO MVP](REQUISITOS/REQ-002-facturacion-pro-mvp.md)
  como modulo opcional para PRO vigente, limitado inicialmente a persona
  humana, monotributo activo y Factura C, con borrador asistido, vista previa,
  confirmacion humana, CAE, auditoria e idempotencia.
- Resolver antes de implementar REQ-002: integracion directa o proveedor;
  custodia y rotacion de certificados; validacion fiscal; datos del receptor;
  almacenamiento, entrega y retencion; limites; correcciones, anulaciones y
  notas de credito; contingencia ARCA; IA, costos y revisiones legal, fiscal,
  contable y de seguridad.
- Crear los ADR necesarios cuando se decidan PSP, integracion fiscal, custodia
  de secretos, modelo de datos, idempotencia externa y proveedor de IA. Ninguna
  de esas decisiones esta aprobada todavia.
- Plan vigente: [tres sprints PRO](SPRINTS/2026-09-06_PRO_REFINAMIENTO_COMERCIAL_Y_PSP.md).
  Sprint 1 es documental; Sprint 2 y Sprint 3 no estan autorizados para codigo.

## Alta prioridad

- Alinear la UI publica con el catalogo aprobado `FREE`, `PRO`, `ENTERPRISE` en
  una fase de implementacion autorizada; `Plus` permanece como contradiccion
  visible y no pertenece al catalogo aprobado.
- Definir el alcance objetivo de Emergencias: solicitud y descubrimiento,
  asignacion operativa o integracion con el contrato canonico de origen
  `EMERGENCY`.
- Diseñar en una fase futura `hiring_mode = MULTIPLE`; Sprint 7 conserva exclusivamente `SINGLE`.
- Diseñar en una fase futura cancelaciones consensuadas y correcciones ampliadas sin alterar el cierre exitoso `CONFIRMADA`.
- Definir, mediante decisión de producto futura, si MANDOBRA necesita badges plata/oro o una proyección propietaria; no forman parte de la reputación neutral.
- Diseñar hitos, evidencias, disputas y modificaciones de contrato sin implementar pagos todavia.
- Sustituir almacenamiento en memoria de Flask-Limiter por Redis u otro backend compartido.
- Definir WSGI productivo para despliegues fuera del servidor Flask de desarrollo.
- Revisar politicas legales con profesional: terminos, privacidad, cookies y consentimientos.
- Configurar Cloudflare/WAF o equivalente antes de exposicion publica.
- Implementar checklist productivo en staging con secretos reales, HTTPS, backups, monitoreo y prueba de restauracion.
- Implementar recuperacion de contraseña con tokens seguros y expiracion.
- Implementar verificacion de email antes de activar flujos sensibles.
- Incorporar pruebas especificas para Emergencias, suscripciones/PRO,
  mutaciones del centro de notificaciones y operaciones administrativas que
  hoy no tienen cobertura directa equivalente al Contracting Core.

## Media prioridad

- Implementar oferta profesional como segundo tipo de publicacion de propuestas.
- Migrar navbar completo a Design System v2 en un sprint especifico sin cambiar rutas ni comportamiento.
- Migrar Home, Resultados y Perfil Profesional completo a Design System v2 con validacion visual dedicada.
- Migrar Dashboards, Presupuestos, Propuestas, Emergencias, Admin y tablas a componentes `.trax-*` por fases.
- Reducir `styles.css` legacy despues de cubrir visualmente las pantallas migradas.
- Unificar breakpoints dispersos bajo tokens `--trax-ds-breakpoint-*`.
- Eliminar CSS muerto cuando exista mapa de cobertura por pantalla.
- Revisar uso del servidor Flask de desarrollo dentro de Docker y separar perfil local de perfil productivo.
- Reemplazar usos legacy de `Query.get()` por `db.session.get()`.
- Reemplazar `datetime.utcnow()` deprecated por timestamps timezone-aware.
- Auditar la lectura administrativa de comentarios originales con un evento de acceso si el volumen y la política de privacidad lo requieren.
- Evaluar una outbox transaccional cuando se habilite el primer canal externo; `INTERNAL` permanece sin dispatcher.
- Definir politica de retencion y limpieza de `OperationCommand` sin perder capacidad de auditoria.
- Agregar `source` explicito al modelo de consentimientos si producto requiere trazabilidad separada del contexto tecnico.
- Incorporar escaneo automatizado de dependencias y secretos en CI.
- Evaluar Redis futuro para rate limiting, cache o colas cuando el volumen lo justifique.
- Restringir la clave de Google Maps por origen autorizado, API permitida y cuotas.
- Validar Google Maps con una API key real restringida en staging.
- Confirmar apertura de WhatsApp en Chrome escritorio y dispositivo movil fisico antes de produccion.
- Validar Cloudinary con credenciales reales de staging, URLs seguras, thumbnails, reemplazo, eliminacion y rollback.
- Incorporar escaneo antivirus o analisis externo de imagenes antes de produccion publica.
- Implementar limpieza asincronica de imagenes huerfanas en storage.
- Evaluar `PortfolioItem` futuro si el portfolio necesita agrupar trabajos con multiples imagenes y narrativa propia.
- Evaluar soporte de videos solo si producto define moderacion, storage y costos.
- Evaluar moderacion automatica de imagenes cuando exista politica aprobada y proveedor definido.
- Evaluar el actor o flujo `EMPRESA` solo durante la futura definicion de
  `ENTERPRISE`; REQ-001 no autoriza crearlo.
- Implementar geocoding de ubicaciones base.
- Evolucionar matching geografico hacia PostGIS o indices espaciales cuando escale el volumen.
- Implementar rutas, tiempos de viaje o distancia real por calle solo si producto lo requiere.
- Incorporar poligonos avanzados y zonas personalizadas multiples.
- Evaluar estilos avanzados de Google Maps si MANDOBRA define un mapa de marca propio.
- Crear listado dedicado de emergencias del cliente para reemplazar enlaces operativos provisorios.
- Crear vista consolidada de solicitudes del cliente que incluya presupuestos, emergencias y propuestas.
- Implementar Agenda.
- Implementar canal Email para notificaciones transaccionales.
- Integrar WhatsApp Business API cuando exista definicion de producto y proveedor.
- Implementar webhooks de WhatsApp Business Cloud API solo si se aprueba el alcance de eventos externos.
- Validar apertura directa por username si WhatsApp publica una URL estable para esa capacidad.
- Evaluar grupos automaticos de WhatsApp solo con una API oficial y consentimiento explicito.
- Evaluar Push notifications cuando exista estrategia mobile/browser.
- Evaluar polling moderado o WebSockets solo cuando el producto requiera tiempo real.
- Planificar la migracion gradual de identificadores internos `TRAX` sin
  romper taxonomia, tokens CSS, rutas, datos persistidos ni compatibilidad
  historica.

## Baja prioridad

- Incorporar Mercados.
- Incorporar funcionalidades de IA.
# Deuda tecnica posterior al nucleo PRO

Timestamp: 2026-09-04T10:29:16-03:00

- Revisar en un incremento separado la atomicidad de las acciones
  administrativas legacy que todavia combinan servicios con commits propios.
  La revocacion PRO ya fue corregida; este registro no autoriza refactorizar las
  demas acciones dentro del alcance actual.
