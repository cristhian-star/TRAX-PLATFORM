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
