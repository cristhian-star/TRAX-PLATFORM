---
titulo: Auditoria tecnica estatica de MANDOBRA
estado: VERIFICADO_ESTATICAMENTE
fecha: 2026-09-02
timestamp: 2026-09-02T21:18:48-03:00
rama: docs/documentation-traceability-consolidation
revision: f63c8db
---

# Auditoria tecnica estatica de MANDOBRA

## Trazabilidad

Timestamp: 2026-09-02T21:18:48-03:00
Estado: VERIFICADO_ESTATICAMENTE
Documento: `docs/AUDITORIA_TECNICA_2026-09-02.md`
Motivo: establecer una linea base tecnica para Planificacion Cloud.
Evidencia: codigo, modelos, servicios, rutas, migraciones, archivos de pruebas
y documentacion canonica presentes en `f63c8db`.
Responsable: Codex / Senior Technical Auditor y Documentation Engineer Senior
Rama: `docs/documentation-traceability-consolidation`
Commit base: `f63c8db`

## Metodo y limitaciones

- Se inspeccionaron estaticamente el Master Spec, decisiones de arquitectura,
  Roadmap, Backlog, codigo, migraciones y archivos de pruebas.
- No se ejecutaron tests, migraciones ni la aplicacion.
- La existencia de un test se registra como evidencia estatica, no como un
  resultado vigente de ejecucion.
- No se ejecuto `git fetch`; el estado de `origin/develop` es el de las
  referencias locales.
- No se modifico codigo funcional, configuracion, migraciones ni tests.

## Linea base verificada

### Implementado

- Cuenta, autenticacion, consentimiento y control basico de estado de usuario.
- Perfil, verificacion, identidad y media profesional con fallback legacy.
- Directorio, taxonomia, cobertura, matching Haversine y Google Maps opcional.
- Presupuestos y propuestas `SINGLE` con creacion de contrato canonico.
- WhatsApp mediante entrada central, consentimiento y sesion enmascarada.
- Negociacion directa versionada e idempotente.
- Contratacion canonica para `DIRECT`, `BUDGET` y `PROPOSAL`.
- Reviews contractuales y reputacion neutral.
- Notificaciones internas y administracion base.

### Implementado parcialmente o provisional

- Emergencias: solicitud y directorio solamente. `EmergencyRequest` no
  persiste un profesional asignado y no existe contrato productivo de origen
  `EMERGENCY`.
- Suscripciones y PRO: el modelo admite `FREE`, `PRO` y `ENTERPRISE`, mientras
  la UI publica conserva `Free`, `Plus` y `Pro`. La elegibilidad PRO todavia
  puede depender de puntos legacy.
- Design System v2: capa canonica establecida, con pantallas y CSS legacy aun
  pendientes de migracion visual.
- Google Maps, Cloudinary y apertura de WhatsApp: integraciones preparadas o
  configurables, sin validacion real de staging registrada para este corte.

### No implementado o fuera de alcance

- Pagos, custodia, facturacion y disputas financieras.
- Contratacion `MULTIPLE`.
- Asignacion y despacho contractual completo de Emergencias.
- Recuperacion de contraseña y verificacion de email.
- WSGI productivo, rate limiting compartido y checklist de staging validado.
- Email, push, outbox operativa y tiempo real.
- Agenda, Mercados con datos reales e inteligencia artificial productiva.

## Hallazgos clasificados

### HECHO VERIFICADO - Emergencias

El Roadmap marcaba Emergencias como completa sin delimitar el alcance. El
modelo declara estados `ASIGNADA`, `EN_CAMINO` y `RESUELTA`, pero no contiene
una referencia persistente al profesional. El servicio puede cambiar el estado
a `ASIGNADA` aunque no persista la identidad asignada. No se encontro una
suite funcional especifica del dominio.

Decision aplicada: conservar el check historico y explicitar que cubre captura
de solicitud y directorio. El comportamiento futuro queda como pregunta de
producto.

### HECHO VERIFICADO - Planes y reputacion legacy

`Subscription` admite `FREE`, `PRO` y `ENTERPRISE`; la pantalla publica muestra
`Free`, `Plus` y `Pro`. La reputacion contractual nueva es neutral, pero el
flujo de elegibilidad PRO conserva un lector de puntos legacy.

Decision aplicada: registrar ambos problemas en Backlog. No se cambio la UI ni
se aprobo una politica comercial nueva.

### HECHO VERIFICADO - Preparacion productiva

El contenedor inicia el servidor Flask mediante `python run.py`, Flask-Limiter
usa almacenamiento en memoria por defecto y no existe un workflow CI
versionado en el corte inspeccionado.

Decision aplicada: conservar WSGI, Redis, staging y controles operativos como
pendientes; no se introdujo infraestructura.

### HECHO VERIFICADO - Cobertura de pruebas desigual

El Contracting Core, negociacion y reviews tienen cobertura estatica extensa,
incluidos gates PostgreSQL. No se encontraron pruebas directas equivalentes
para Emergencias, el servicio de suscripciones/PRO ni las mutaciones de lectura
de notificaciones.

Decision aplicada: agregar un pendiente consolidado de cobertura. No se afirma
que la suite actual falle.

### HECHO VERIFICADO - Persistencia legacy paralela

`app/database/db.py` conserva acceso directo a SQLite y creacion manual de
tablas al margen de SQLAlchemy y Alembic. Su funcion de busqueda presenta una
estructura incompleta. No se encontro evidencia de uso productivo durante la
revision estatica.

Decision aplicada: registrar el riesgo en esta auditoria sin modificar codigo.

### INFERENCIA - Riesgo de regresion

La concentracion de responsabilidades en rutas y servicios de gran tamano, la
coexistencia de CSS legacy y v2 y los dominios con cobertura desigual elevan el
riesgo de regresion al ampliar producto. Esta conclusion es una inferencia
arquitectonica; no proviene de una ejecucion fallida.

### PENDIENTE - Decisiones de producto

1. Beneficios, limites y activacion de `FREE`, `PRO` y `ENTERPRISE`.
2. Sustituto neutral para la elegibilidad PRO basada en puntos legacy.
3. Alcance final de Emergencias y relacion con `ContractRequest`.
4. Politica de produccion, operacion y cumplimiento legal.
5. Migracion gradual de identificadores internos TRAX.

## Condicionantes arquitectonicos

- Mantener el monolito modular y los servicios internos concretos.
- Usar `ContractRequest` como unico nucleo contractual.
- Conservar `CONFIRMADA` como terminal exitoso y `CERRADA` como legacy.
- Mantener `contracting_mode = EXTERNAL` y `hiring_mode = SINGLE` hasta una
  decision aprobada.
- Aplicar actor, ownership, version esperada, lock, idempotencia, correlacion y
  transaccion unica en operaciones sensibles.
- Mantener Alembic como autoridad del esquema.
- No convertir puntos legacy en reputacion contractual canonica.
- Mantener WhatsApp centralizado y Google Maps opcional con fallback.
- Migrar el Design System de forma incremental sin eliminar compatibilidad en
  masa.

## Recomendacion para Planificacion Cloud

Priorizar un ciclo de consolidacion antes de Agenda, Mercados, IA, pagos o
`MULTIPLE`:

1. Aprobar requisitos de Planes/PRO y Emergencias.
2. Resolver contradicciones visibles y el criterio legacy de PRO.
3. Agregar cobertura de pruebas en dominios debiles.
4. Definir y validar el gate de staging/produccion.
5. Validar proveedores externos con configuracion real restringida.
6. Continuar la reduccion incremental de deuda estructural y visual.

## Resultado

La base tecnica es funcional y especialmente robusta en contratacion,
negociacion y reviews. La ampliacion de producto esta condicionada por
decisiones pendientes de Planes/PRO y Emergencias y por la falta de validacion
operativa de produccion. Esta auditoria no aprueba requisitos nuevos.
