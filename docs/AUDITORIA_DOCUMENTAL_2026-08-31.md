---
titulo: Auditoria documental inicial de MANDOBRA
estado: VERIFICADO
fecha: 2026-08-31
rama: feature/mandobra-transition
revision: d07d95
---

# Auditoria documental inicial de MANDOBRA

## Veredicto

La documentacion existente es una base tecnica valiosa y el cierre de Sprint 7
esta razonablemente alineado con el codigo actual. El principal vacio no era la
falta de historia, sino la ausencia de una especificacion maestra que separara
con claridad funcionalidad operativa, prototipos visibles, deuda y trabajo
futuro.

Como resultado de esta auditoria se creo el
[Master Spec](REQUISITOS/MASTER_SPEC.md) y se establecio `docs/` como boveda
canonica de MANDOBRA.

## Alcance y evidencia revisada

- Rama: `feature/mandobra-transition`.
- Revision base inspeccionada: `d07d95`.
- Aplicacion Flask organizada en modelos, rutas, servicios y dominio.
- 26 modelos SQLAlchemy.
- 18 revisiones Alembic lineales desde `20260527_01` hasta `20260726_07`.
- Rutas publicas, autenticadas, operativas, administrativas y de desarrollo.
- 37 archivos bajo `tests/`, incluidos gates especificos para PostgreSQL.
- Documentacion permanente, changelog, roadmap, backlog y 21 documentos de
  sprint previos a esta auditoria.

La modificacion preexistente en `app/templates/home_logged.html` no fue
alterada ni evaluada como una nueva decision funcional durante esta auditoria.

## Validacion ejecutada hoy

- `python -m unittest discover tests`: 266 pruebas, 266 sin fallos, 5 omitidas.
- `python -m compileall -q app scripts tests`: correcto.
- `alembic heads`: `20260726_07 (head)`.
- Docker no estaba iniciado; no se ejecuto hoy un gate PostgreSQL real.

Las cinco omisiones locales corresponden a pruebas que requieren un entorno
PostgreSQL habilitado o a placeholders que documentan limites de SQLite. Los
resultados PostgreSQL 16.14 registrados en los documentos de cierre son
evidencia historica y no se presentan como revalidados el 2026-08-31.

## Hechos confirmados

- La marca visible actual es MANDOBRA.
- Persisten identificadores internos `trax-*`, nombres Docker, variables y
  rutas de archivos por compatibilidad historica.
- Alembic es la autoridad del esquema fuera de tests.
- El head operativo documentado y presente es `20260726_07`.
- Los actores implementados son visitante, cliente, profesional y
  `SUPER_ADMIN`.
- Presupuestos y propuestas pueden producir contratos canonicos.
- La negociacion formal directa es opcional y exige verificacion de ambas
  partes.
- El contrato opera en modalidad exclusivamente `EXTERNAL`; MANDOBRA no cobra
  ni custodia pagos.
- Las reviews nuevas nacen de un contrato `CONFIRMADA` y alimentan metricas
  neutrales.
- WhatsApp se abre mediante una sesion controlada, pero la conversacion sucede
  fuera de la plataforma.
- Mercados y precios es una experiencia mock, no inteligencia de mercado real.
- Planes muestra una comparativa comercial provisoria, no una facturacion
  implementada.

## Obligatorios antes de ampliar producto

### 1. Resolver el contrato funcional de MANDOBRA PRO

La elegibilidad de upgrade todavia consulta puntos historicos, mientras que la
reputacion contractual nueva prohibe un score propietario. El catalogo correcto
confirmado por producto es `FREE`, `PRO` y `ENTERPRISE`, tal como admite el
modelo. La pantalla publica sigue mostrando `Free`, `Plus` y `Pro`, por lo que
la inconsistencia esta en esa superficie y no en el enum del modelo.

Antes de monetizar, prometer beneficios o ampliar limites se debe aprobar una
especificacion unica para:

- nombres de planes;
- reglas de elegibilidad;
- limites y beneficios reales;
- relacion con verificacion y reputacion neutral;
- administracion manual versus facturacion;
- migracion de suscripciones existentes.

### 2. Definir el alcance real de Emergencias

La aplicacion permite crear emergencias y consultar un directorio. El modelo
declara estados de asignacion y resolucion, pero no persiste un profesional
asignado y no existe un flujo productivo que origine un contrato desde una
emergencia. `ContractRequest` reserva `source_type = EMERGENCY`, pero hoy es
solo una capacidad estructural.

Se debe decidir si Emergencias termina en contacto externo, asignacion
operativa o contrato canonico antes de presentar ese ciclo como completo.

### 3. Mantener requisitos verificables por modulo

Toda funcionalidad nueva debe partir de un requisito con alcance y criterios
de aceptacion. El Master Spec define la linea base, pero no reemplaza los
requisitos detallados de futuros cambios.

## Obligatorios solo antes de staging o produccion

- Servidor WSGI productivo.
- Redis u otro backend compartido para rate limiting.
- Secretos gestionados fuera de Git y configuracion por entorno.
- HTTPS, HSTS en conexiones seguras y WAF o equivalente.
- Backups automaticos y prueba real de restauracion.
- Monitoreo, alertas y politica de logs sin datos sensibles.
- Revision profesional de terminos, privacidad, cookies y consentimientos.
- Recuperacion segura de contrasena y verificacion de email para flujos
  sensibles.
- Validacion real de Cloudinary y Google Maps con credenciales restringidas.
- Gate PostgreSQL completo sobre una base descartable y aislada.

## Opcionales o no bloqueantes

- Completar la migracion visual al Design System v2.
- Geocoding, PostGIS, tiempos de viaje o zonas avanzadas.
- Moderacion automatizada y limpieza asincronica de media.
- Auditoria por cada lectura administrativa de comentarios originales.
- Componentes visuales avanzados, mapas de marca y refinamientos de UX.

## Otros sprints o iniciativas futuras

- `hiring_mode = MULTIPLE`.
- Pagos, custodia, garantias, disputas y facturacion.
- Agenda.
- WhatsApp Business API y webhooks.
- Mercados con datos reales.
- Email, push o tiempo real.
- Funcionalidades de inteligencia artificial.
- Produccion y despliegue.

## Deuda tecnica confirmada

- Usos de `Query.get()` deben migrar a `db.session.get()`.
- Usos de `datetime.utcnow()` deben pasar a timestamps UTC conscientes de zona.
- `main_routes.py`, `operation_routes.py` y algunos servicios concentran
  demasiadas responsabilidades; conviene dividirlos por dominio en cambios
  incrementales con pruebas.
- Los identificadores internos TRAX deben conservarse hasta aprobar una
  migracion de nombres que contemple Docker, variables, CSS, storage, datos y
  compatibilidad.
- La elegibilidad PRO depende de puntos legacy hasta que producto apruebe una
  regla neutral sustituta.

## Inconsistencias documentales y funcionales

### Politica de nombres de sprints

El documento inicial de documentacion permanente afirma que no se usara
numeracion de sprints, pero la historia posterior adopto `Sprint 7`. La regla
vigente debe ser la practica real: conservar fecha y nombre, permitiendo el
numero cuando forme parte de la identidad historica de la iniciativa.

### Planes publicos versus modelo

El catalogo correcto es `Free`, `Pro` y `Enterprise`. La UI incluye `Plus` por
error y no presenta `Enterprise`. Los precios y beneficios siguen siendo
placeholders hasta aprobar su contrato comercial detallado.

### Emergencias

El modelo no tiene `professional_id`, aunque el servicio contiene una funcion
de asignacion condicionada a la existencia de ese atributo. No hay callers
productivos para asignar ni crear un contrato desde emergencia.

### Evidencia PostgreSQL

Los documentos de cierre conservan resultados PostgreSQL validos como registro
historico. La auditoria actual solo confirmo la suite local SQLite y el grafo de
migraciones porque Docker no estaba disponible.

## Clasificacion de la documentacion

### Canonica y viva

- `REQUISITOS/MASTER_SPEC.md`.
- `DECISIONES_ARQUITECTURA.md` y futuros ADR aceptados.
- `ESTANDARES_DESARROLLO.md`.
- `alembic.md` y `postgres_dev.md`.
- `DESIGN_SYSTEM_V2.md`.
- `ROADMAP.md` y `BACKLOG.md` como planificacion viva.

### Historica

- `CHANGELOG.md`.
- `SPRINTS/`.
- `design-system-v1.md` cuando contradiga al contrato v2.

Los documentos historicos no deben reescribirse para ocultar decisiones
anteriores. Una correccion nueva debe enlazar el documento reemplazado o
explicar la divergencia.

## Proximo paso recomendado

Crear requisitos independientes para resolver primero PRO/Planes y el alcance
de Emergencias. Ninguno debe implementarse hasta que producto apruebe sus
reglas, exclusiones y criterios de aceptacion.
