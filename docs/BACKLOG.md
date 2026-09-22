# BACKLOG MANDOBRA

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
