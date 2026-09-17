# ROADMAP MANDOBRA

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
