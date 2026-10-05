# ROADMAP MANDOBRA

## Corrección focal de Testing — 2026-10-01

Registro: 2026-10-01T20:07:29-03:00. Responsable técnico: agente MANDOBRA, laptop.
Responsable de Producto: Cristian Sánchez. Fecha de sustitución: 2026-10-01.
Fuente: retest 2026-10-01T20:00:59-03:00, RECHAZADO_REQUIERE_CORRECCIONES.
Estado: CORREGIDO DOCUMENTALMENTE / PENDIENTE DE RETEST FOCAL.

**Regla vigente: TURNOS FIJOS DE 12 HORAS CON MÚLTIPLES BLOQUES PROGRAMADOS.**

- GUARDIA_DIURNA: 07:00–19:00; GUARDIA_NOCTURNA: 19:00–07:00 del día siguiente.
- Múltiples bloques futuros, diurnos/nocturnos y consecutivos; nunca duplicar el mismo bloque.
- Reserva hasta T−2 minutos inclusive; después se rechaza. No incorporación al bloque iniciado.
- Confirmación inmediata con aceptación expresa; avisos T−6 h y T−1 h solo si aún son futuros.
  En T−6 h se omite ese aviso; en T−1 h se omiten ambos. No avisos retroactivos.
- Disponibilidad temporal derivada del bloque activo: starts_at <= ahora < ends_at;
  además se mantienen las condiciones de elegibilidad aprobadas. No requiere cron para expirar.
- Zona America/Argentina/Buenos_Aires, instantes UTC; 06:58:00/18:58:00 exactos se admiten,
  un microsegundo posterior se rechaza. Sin redondeos.
- Tarifas bajo autonomía profesional; no cálculo automático por horario.

**SUSTITUIDAS:** reglas de 2/4/8 horas, duración libre, activación/renovación desde ahora
y una única fila mutable por profesional. Los antecedentes inferiores que las describen
son históricos, no normativa activa; sus referencias a activar/renovar/desactivar no
autorizan tales operaciones en este incremento. Cancelar/modificar/abandonar turnos sigue
pendiente. Se conserva el resto de las decisiones de seguridad, matching, pagos,
sanciones, privacidad y soporte sin modificación. Las afirmaciones históricas de
«sin cambios normativos» describen sus sesiones originales, no esta sustitución.
Alcance actual: lógica pura y corrección focal, sin persistencia, migración ni interfaz.

## UX-07A — Secuencia autorizada tras aceptación — 2026-09-28

Fecha y hora: `2026-09-28T21:10:35-03:00` (America/Argentina/Buenos_Aires).
Responsable: agente documental (Codex), laptop.
Rama: `feature/ux-ui-foundation`.
HEAD base: `a7391a87db200e678ba4320e74c0075b365df649`.
Documento/decisión: ADR-002.
Motivo: registrar aceptación arquitectónica posterior al retest independiente final.
Decisión de Producto: Cristian Sánchez, `2026-09-28T20:59:57-03:00`.
Estado: ADR-002 APROBADO. Alcance siguiente: PREFLIGHT UX-07A.1.
Implementación UX-07A.1: NO AUTORIZADA. UX-07A.2: BLOQUEADO POR DEPENDENCIA.
Captura y persistencia de coordenadas exactas: BLOQUEADAS.
Esta entrada actualiza los estados vigentes; las entradas anteriores conservan su
valor histórico. No modifica la normativa aprobada ni declara trabajo técnico iniciado.

Secuencia vigente, conforme a [ADR-002](ADR/ADR-002-emergencias-guardia-vigente.md):

1. ADR-002 APROBADO por Producto; retest final APROBADO del `2026-09-28T20:55:50-03:00`.
2. Preflight técnico de UX-07A.1 AUTORIZADO, todavía no ejecutado por esta operación documental.
3. Implementación UX-07A.1 PENDIENTE DE AUTORIZACIÓN POSTERIOR; no iniciada.
4. Testing PostgreSQL PENDIENTE, sin ejecución en esta sesión.
5. UX-07A.2 BLOQUEADO hasta completar y aprobar UX-07A.1.

REQ-004 permanece APROBADO COMO ESPECIFICACIÓN / IMPLEMENTACIÓN PENDIENTE.
La aceptación arquitectónica no acredita disponibilidad operativa ni habilita la interfaz
de .2 a afirmar disponibilidad sin la verificación previa de .1.

## UX-07A — Precondiciones residuales — 2026-09-28

Fecha y hora: `2026-09-28T20:45:39-03:00` (America/Argentina/Buenos_Aires).
Responsable: agente de corrección documental (Codex), laptop.
Rama: `feature/ux-ui-foundation`.
HEAD base: `a7391a87db200e678ba4320e74c0075b365df649`.
Motivo: incorporar las decisiones aprobadas para cerrar los P2 residuales sobre
contrato territorial y confianza de IP/proxy.
Estado: CORREGIDO / PENDIENTE DE RETEST INDEPENDIENTE.
Autorización de Producto: Cristian Sánchez, `2026-09-28T20:42:54-03:00`.
Los dos P2 están corregidos documentalmente, no cerrados ni aprobados por este agente.
ADR-002: PROPUESTO / EN CORRECCIÓN; UX-07A.1: BLOQUEADO;
UX-07A.2: BLOQUEADO POR DEPENDENCIA. Implementación pendiente, sin autorización.
Esta entrada precisa exclusivamente esos dos contratos y prevalece sobre sus
formulaciones previas; conserva las demás decisiones, las 27 filas CA y el historial.

Fuente: [ADR-002](ADR/ADR-002-emergencias-guardia-vigente.md#p2-residuales-territorio-e-ip-confiable--2026-09-28) y
[REQ-004](REQUISITOS/REQ-004-emergencias-guardia-vigente.md#p2-residuales-contrato-aplicable--2026-09-28).
Secuencia preservada: retest final → decisión de ADR-002 → preflight .1 → autorización
explícita → implementación/verificación .1 → posible .2. No adelantar ejecución.
Preflight debe resolver datos territoriales separados y todas las dimensiones de cuota
y proxies por entorno antes de implementar/desplegar. Coordenadas exactas bloqueadas.
Ninguna garantía distribuida se deriva de memory://.

## UX-07A — Secuencia corregida y bloqueada — 2026-09-28

Registro de corrección: `2026-09-28T20:15:29-03:00`.
Decisión de Producto: `2026-09-28T20:12:39-03:00`, Cristian Sánchez,
APROBADO PARA CORRECCIÓN DOCUMENTAL. Autor: agente documental local (Codex), laptop.
Rama: `feature/ux-ui-foundation`; HEAD base: `a7391a87db200e678ba4320e74c0075b365df649`.
Motivo: incorporar las recomendaciones arquitectónicas adoptadas sobre 2 hallazgos P1
y 4 hallazgos P2. Estado de la corrección: CORREGIDO / PENDIENTE DE RETEST.
ADR-002: PROPUESTO / EN CORRECCIÓN, no aceptado.
UX-07A.1: BLOQUEADO. UX-07A.2: BLOQUEADO POR DEPENDENCIA.
Implementación, migraciones y pruebas técnicas/funcionales: PENDIENTES, sin autorización.
Esta entrada expresa el contrato vigente para retest y prevalece sobre las alternativas
y próximos pasos de registros anteriores, que se conservan como historia.
La adopción de recomendaciones no acepta ADR-002 ni autoriza implementar UX-07A.1.

Fuente: [ADR-002 corregido](ADR/ADR-002-emergencias-guardia-vigente.md#corrección-arquitectónica-adoptada--2026-09-28).
Secuencia vigente, sin fechas de implementación ni autorización implícita:

1. Retest documental y arquitectónico independiente de los 2 P1 y 4 P2 corregidos.
2. Decisión explícita de Cristian Sánchez sobre ADR-002; continúa PROPUESTO.
3. Preparar preflight UX-07A.1: escritores/locks, contratos de endpoint, cuotas nuevas,
   resultado durable/retención, esquema e índices candidatos y PostgreSQL descartable.
4. Autorizar expresamente .1 antes de código, migraciones o pruebas funcionales.
5. Implementar y verificar .1 únicamente cuando se autorice; hasta entonces BLOQUEADO.
6. UX-07A.2: BLOQUEADO POR DEPENDENCIA; no afirmar disponibilidad antes de .1 verificado.

Captura exacta bloqueada hasta política de ubicación/contexto privado; no sustituirla
por cookies firmadas ni afirmar cifrado inexistente. No sumar Redis/PostGIS/colas.
Todos los trabajos técnicos permanecen pendientes. La aprobación de la especificación
y esta corrección documental no equivalen a aceptación arquitectónica ni implementación.

## Cierre de revisión documental UX-07A — 2026-09-28

Registro: `2026-09-28T19:42:16-03:00`. Dictamen: `2026-09-28T19:31:39-03:00`.
Responsable de Producto: Cristian Sánchez. Revisor: agente documental local.
Estado: APROBADO COMO ESPECIFICACIÓN. Hallazgos: P0: 0; P1: 0; P2: 0; P3: 0.
Implementación: PENDIENTE. Pruebas técnicas y funcionales: PENDIENTES.
ADR-002: PROPUESTO / PENDIENTE DE DECISIÓN ARQUITECTÓNICA; no aceptado ni implementado.
UX-07A.1 permanece pendiente de aprobación arquitectónica y autorización de implementación.
UX-07A.2 depende de UX-07A.1 implementado y verificado antes de afirmar disponibilidad.
Próximo paso: decidir ADR-002 y preparar el paquete UX-07A.1. Ninguna implementación iniciada.
Este cierre aprueba la especificación documental; no acredita implementación ni pruebas
funcionales, ni acepta las soluciones técnicas propuestas. Los 27 criterios se conservan.
Los registros fechados anteriores mantienen su estado histórico; este cierre expresa el vigente.
Las tareas de implementación y sus gates conservan su estado PENDIENTE.

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

## MVP

[x] Login

[x] Registro

[x] Rediseño de Login y Registro

[x] Directorio

[x] Perfil Profesional

[x] Presupuestos

[x] Emergencias

Alcance verificado: captura de solicitud y directorio de profesionales con
contexto de cobertura. No se consideran completas ni aprobadas la asignacion
persistente de un profesional, la resolucion operativa de punta a punta ni la
creacion de contratos con origen `EMERGENCY`.

[x] Propuestas

[x] Dashboard Profesional

[x] Home Privado

[x] Dashboard Cliente

[x] Notificaciones

[x] Cobertura Inteligente v1

[x] Cobertura Inteligente v2 - Google Maps

[x] Public Profile Map UX v1

[x] Matching Geografico por Distancia v1

[x] WhatsApp Integration Foundation v1

[x] WhatsApp Contact Privacy v1

[x] Cierre de WhatsApp y Geolocalizacion

[x] Identidad y Portfolio Profesional

[x] Consolidacion Arquitectonica v1

[x] Sprint 7 - Contracting Core Fase 1

[x] Sprint 7 - Contracting Core Fase 2A - Fundaciones transversales

[x] Sprint 7 - Contracting Core Fase 2B - Negociacion directa MVP

[x] Sprint 7 - Contracting Core Fases 2E-2F - Reviews contractuales y reputacion neutral

[x] Sprint 7 - Contracting Core MVP cerrado en `CONFIRMADA`

[x] Sprint 7 - Auditoria independiente de integracion aprobada

[x] Sprint 7 - Cierre tecnico aprobado para PR hacia `develop`

Estado operativo soportado: Alembic `20260726_07`. Un downgrade a
`20260726_06` restaura defensas historicas mas debiles. El cierre tecnico no
autoriza despliegue productivo. P0/P1/P2: ninguno. P3 no bloqueante: contrasena
demo predecible pendiente de endurecimiento futuro.

La clasificacion P0/P1/P2 anterior pertenece exclusivamente al cierre
historico de Sprint 7. No representa una evaluacion general de preparacion para
staging, produccion o ampliacion del producto.

[ ] Agenda

[ ] WhatsApp Business API

[ ] Mercados

[ ] IA

## PRO y Facturacion

[x] Especificacion funcional de activacion y vigencia PRO aprobada en
[REQ-001](REQUISITOS/REQ-001-activacion-y-vigencia-pro.md)

[x] Fundacion del entitlement PRO: evaluador central, fuentes reconocidas,
vencimiento UTC, desactivacion de concesiones legacy/manuales y seed QA aislado

[ ] Sprint 1 PRO comercial - cerrar especificacion, viabilidad PSP, revision
juridica/contable y evaluacion fiscal

Estado previo a la revision al `2026-09-07T21:31:53-03:00`:
`LISTO_PARA_REVISION_DE_DIFF`. PR #7 integro la especificacion y trazabilidad;
la revision focalizada previa informo `APROBADO_PARA_COMMIT`, sin review nativa
registrada en GitHub. El check permanece abierto hasta revisar el diff de
cierre. Mercado Pago, revision juridica/contable y aclaracion de la estimacion
25-43 horas siguen pendientes y bloquean solo las capacidades dependientes.
Ver la [matriz de cierre y las correcciones propuestas al diseño
2.0](SPRINTS/2026-09-06_PRO_REFINAMIENTO_COMERCIAL_Y_PSP.md#matriz-de-cierre-de-sprint-1).

Estado actualizado al `2026-09-07T21:54:36-03:00`:
`CERRADO_DOCUMENTALMENTE_INTEGRACION_GIT_PENDIENTE`. La revision independiente
del Agente 02 del `2026-09-07T21:41:54-03:00` no encontro hallazgos, aprobo el
diff para commit y considero satisfechos los criterios documentales de cierre.
Mercado Pago, revision juridica/contable y aclaracion de la estimacion de 25-43
horas permanecen como pendientes selectivos. El diseño 2.0 sigue
`PROPUESTO_NO_APROBADO` y no autoriza implementacion.

[ ] Sprint 2 PRO comercial - cobros transaccionales, checkout/enlace/QR, lotes
de creditos y periodos de 30 dias por umbral

Estado documental al `2026-09-14T10:21:05-03:00`: REQ-003 define la orden de
cobro Checkout Pro y el primer incremento puro, todavía sin implementación.
La única URL se reutiliza como enlace o QR; persistencia, interfaz, PSP real,
conciliación y efectos PRO permanecen pendientes.

Actualización al `2026-09-14T20:43:27-03:00`: REQ-003 permanece `APROBADO` y
su implementación productiva completa está `PENDIENTE`. El contrato puro y el
adaptador determinista en memoria son un avance técnico parcial implementado y
probado en `6d6dd2f` y `12c6418`. Sprint 2 continúa abierto: faltan
persistencia, ownership, Mercado Pago real, HTTP, checkout productivo,
interfaz, conciliación y efectos PRO.

Actualización posterior al `2026-09-16T22:40:04-03:00`, agente 01 - Documentation
Engineer, motivo: cierre técnico interno de 4A en `4373b64`. La fundación
durable `PaymentOrder` está implementada y aprobada localmente: replay,
conflictos materiales, unicidad activa, ciclo local de 72 horas, auditoría
atómica y concurrencia PostgreSQL; head Alembic único `20260916_01`.
Este registro supera únicamente la persistencia interna pendiente del registro
anterior; no cierra Sprint 2 ni REQ-003 (`APROBADO` / `PENDIENTE`).
Próximo incremento: 4B, servicio de aplicación y ownership contractual, todavía
sin Mercado Pago real. Siguen pendientes PSP HTTP, recuperación externa incierta,
checkout/QR visibles, integración con webhooks y conciliación, correlación de
pagos, efectos PRO/comisiones/facturación, publicación, PR, merge y producción.
La cancelación local no cancela una preferencia remota; almacenar
`professional_id` no autoriza al actor. Evidencia y límites:
[REQ-003](REQUISITOS/REQ-003-creacion-de-ordenes-de-cobro-checkout-pro.md#actualización-posterior---incremento-técnico-4a).

Actualización al `2026-09-17T11:04:24-03:00`, Codex - implementador documental
local, rama `feature/checkout-pro-payment-order-application`, commit `1ba5ab1`:
4B está completado y aprobado por Testing. Servicio de aplicación y ownership en
contrato/perfil, actor profesional activo y contratos `CONFIRMADA`, obligación
final única y reserva durable antes del adaptador, finalización atómica y replay.
Supera el próximo paso 4B del registro anterior, no cierra Sprint 2 ni REQ-003:
`APROBADO`, implementación productiva completa `PENDIENTE`.
Continúan pendientes Mercado Pago real, creación HTTP, endpoints, UI/checkout/QR,
recuperación incierta, sucesoras desde la aplicación, integración de órdenes con
webhooks/conciliación y efectos PRO/comisiones/facturación; publicación, PR, merge
y producción pendientes. Próximo paso: creación real y frontera pública, con
planificación y revisión separadas. Evidencia aprobada y límites:
[REQ-003](REQUISITOS/REQ-003-creacion-de-ordenes-de-cobro-checkout-pro.md#actualización-vigente---incremento-técnico-local-4b).

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

[ ] Sprint 3 PRO comercial - suscripcion de 30 dias, pagos mixtos, renovacion,
exencion, gracia y retorno transaccional

Los tres nombres anteriores pertenecen a la secuencia PRO iniciada el
2026-09-06 y no reinician la numeracion historica. Sprint 1 es documental; los
sprints 2 y 3 requieren decisiones, viabilidad externa y autorizacion futura.

[x] Facturacion PRO MVP aprobada para especificacion en
[REQ-002](REQUISITOS/REQ-002-facturacion-pro-mvp.md)

[ ] Implementacion de Facturacion PRO MVP para persona humana, monotributo
activo y Factura C, sujeta a decisiones tecnicas y revisiones previas

[ ] Definir un incremento fiscal separado despues de comparar ARCA directo y
proveedores; no agregar ARCA o IA silenciosamente al Sprint 3 PRO

[ ] Definicion e implementacion futura de `ENTERPRISE`; permanece conceptual y
no autoriza crear el actor `EMPRESA`

## Documentacion del Proyecto

[x] CHANGELOG

[x] ROADMAP

[x] Decisiones de arquitectura

[x] BACKLOG

[x] Estandares de desarrollo

[x] Documentacion de sprints

## Design System

[x] Theme System Light/Dark

[x] Design System v2 - Fase 1

[x] UX/UI General & Design System v2

Alcance verificado: Design System v2 esta establecido como capa canonica y
coexiste con capas legacy. La migracion visual completa de todas las pantallas
no forma parte de este check y permanece pendiente en los items siguientes y
en el Backlog.

[ ] Design System v2 - Componentes avanzados

[ ] Auditoria visual completa de pantallas complejas restantes

## Arquitectura y Plataforma

[x] Servicios internos para view models, permisos y operaciones

[x] Configuracion por entorno

[x] Alembic como autoridad del esquema

[x] Security & Compliance Foundation v1

[x] WhatsApp y Google Maps configurables con fallback seguro

[x] Storage profesional local y Cloudinary configurable

[ ] WSGI productivo

[ ] Redis para rate limiting, cache o colas futuras

[ ] Checklist productivo completo validado en staging

## UX-07A — Secuencia documental y de implementación

Registro: `2026-09-27T23:14:25-03:00`. Responsable de Producto: Cristian Sánchez; redacción: Codex, laptop MANDOBRA.
Rama: `feature/ux-ui-foundation`. HEAD: `4489c5c208245368a2a9bfd1672a261cf3004c93`.
Motivo: formalizar el preflight UX-07A aprobado y la decisión de Producto de
`2026-09-27T23:03:15-03:00`, `APROBADO PARA ESPECIFICACIÓN`.
Estado: especificación para revisión; implementación PENDIENTE. El preflight es el
antecedente de inspección del chat, no evidencia de guardias implementadas.
Orden neutral: PRO no habilita ni prioriza Emergencias; verificación es filtro obligatorio,
no privilegio adicional de orden. Próximo paso: revisar REQ-004/ADR-002 y autorizar
UX-07A.1; UX-07A.2 depende de su verificación.


1. Revisar [REQ-004](REQUISITOS/REQ-004-emergencias-guardia-vigente.md) y
   [ADR-002](ADR/ADR-002-emergencias-guardia-vigente.md), resolver detalles propuestos y
   autorizar paquete .1 con criterios, entorno y alcance concreto.
2. UX-07A.1: catálogo, guardia real y controles mínimos del profesional, permisos,
   migración, matching, privacidad, atomicidad/idempotencia y contacto seguro.
3. Gate .1: PostgreSQL y seguridad; evidencia independiente de reglas temporales y carreras.
4. UX-07A.2: imágenes, carrusel, formulario, skeleton, listado y vacío, responsive/accesibilidad.
5. Retest funcional/visual y decisión explícita de integración. Sin fecha ni aprobación
   de implementación, commit o despliegue inferida desde este registro.

No publicar disponibilidad antes del gate .1. La dirección aprobada no acredita trabajo
implementado. Presupuestos y demás flujos conservan contratos; dependencias compartidas
requieren regresión focal. Excluidos despacho, aceptación, ETA, pagos y agenda recurrente.
