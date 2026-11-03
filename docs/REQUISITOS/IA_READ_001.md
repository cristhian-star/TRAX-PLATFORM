## IA-READ-001 — cierre técnico independiente — 2026-11-01T22:12:27-03:00

Estado: **COMPLETED (cierre técnico y documental local; sin activación)**.
Dictamen independiente: **2026-11-01T21:49:11-03:00**,
**VERIFICADO EN EL ALCANCE EVALUADO**. Responsable del cierre: agente de Integración IA,
Windows local. Este registro sustituye los pendientes de Testing del núcleo en las
entradas anteriores, que se conservan como antecedentes. No cierra QA de Mis trabajos.

**Núcleo local de ayuda y lectura privada verificado:** help.search,
work_records.list, work_records.get y followups.list. Ausencia de hallazgos
**P0: 0; P1: 0; P2: 0; P3: 0**, exclusivamente en ese núcleo evaluado.

Resultados del dictamen, conservados por separado:

- **46/46 del paquete declarado**, repetido por Testing: 23 adaptadores, 10 corpus
  y 13 regresiones de Mis trabajos; sin fallos, errores u omisiones.
- **5/5 adversariales independientes**, distintos del paquete anterior.
- **Total único: 51/51**. Las ejecuciones del implementador no se agregan otra vez.

La preparación inicial del harness adversarial tuvo falta de PYTHONPATH y una tanda
intermedia incluyó 23 pruebas repetidas y dos aserciones incorrectas del harness.
Esas tandas se excluyen del conteo; el log final corregido ejecuta únicamente 5/5.
Estos resultados son evidencia histórica de Testing, no pruebas nuevas de este cierre.

Evidencia durable independiente, verificada en lectura:

- [Paquete declarado 46/46](<C:/Users/Cristhian/.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/ia-read-independent-20261101/declared-46-tests.log>).
- [Adversariales independientes 5/5](<C:/Users/Cristhian/.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/ia-read-independent-20261101/adversarial-tests-final.log>).
- [Manifiesto inicial de 661 archivos](<C:/Users/Cristhian/.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/ia-read-independent-20261101/source-manifest-initial.json>).
- [Integridad final de contenido](<C:/Users/Cristhian/.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/ia-read-independent-20261101/integrity-final.json>) y
  [comparación Git final](<C:/Users/Cristhian/.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/ia-read-independent-20261101/git-integrity-final.json>).
- [Comparación con hashes del implementador](<C:/Users/Cristhian/.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/ia-read-independent-20261101/implementer-hash-comparison.json>)
  y [timestamp del dictamen](<C:/Users/Cristhian/.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/ia-read-independent-20261101/timestamp-final.txt>).

Testing informó cero archivos modificados/ausentes y diez hashes IA coincidentes.
El campo status_match=false del informe inicial de integridad de contenido no se toma
como delta Git: el informe específico git-integrity-final.json registra 160 paths
iniciales/finales y status_delta=0. Se conservan ambos artefactos, sin alterarlos.
En este cierre se comprobaron también los ocho archivos de código/tests/corpus contra
los hashes independientes: coinciden; sólo cambian los tres documentos autorizados.

### Límites y dependencias que permanecen

- Corpus productivo vacío; pendiente de aprobación editorial individual y versionada.
  No se incorporan artículos ni propuestas de ayuda al corpus aprobado en este cierre.
- Habilitación para usuarios pendiente del cierre de QA de Mis trabajos, incluido el
  **P3 visual del enlace «Trabajos contratados en MANDOBRA →»**: área interactiva
  observada de 21 px (42 px a 320 px), inferior al objetivo de 44 × 44 px.
  [Evidencia de Mis trabajos](<C:/Users/Cristhian/.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/mis-trabajos-independent-20261030/>). Ese P3 es una dependencia de interfaz
  distinta de los cero hallazgos del núcleo IA; no se corrige ni se declara cerrado.
- Sin interfaz de asistente, proveedor generativo, WhatsApp, MCP remoto, búsqueda
  pública por IA ni herramientas fiscales o financieras habilitadas.
- **PostgreSQL y producción no quedan acreditados por este dictamen**. La evidencia
  del núcleo corresponde a SQLite temporal y recursos sintéticos; no prueba locking,
  concurrencia PostgreSQL, despliegue o uso real. No se heredan gates fiscales.
- Suite completa, navegador/AA y Node no ejecutados en este cierre; Testing justificó
  navegador/Node por ausencia de interfaz/controlador nuevos. No hay validación nueva.

### Inventario, coordinación e integridad de este cierre

Rama feature/professional-workspace-ux; HEAD
2e552f2fdc57c152c97f0486050574696f6b250e. Preflight: 160 paths pendientes, staging vacío.
Facturación y el implementador de Presupuestos confirmaron por coordinación que sus
ediciones de ACTIVE_HANDOFF.md y CHANGELOG.md terminaron, sin escrituras previstas.
Se conservan íntegros sus registros, incluido el P3 de Presupuestos (distinto del P3
visual de Mis trabajos), y el resto del árbol mixto.

Único inventario documental de esta sesión:

1. docs/REQUISITOS/IA_READ_001.md: dictamen, evidencia, conteos separados y límites.
2. docs/HANDOFFS/ACTIVE_HANDOFF.md: continuidad y estado final local.
3. docs/CHANGELOG.md: cierre técnico sin activación.

Control de integridad: 661 archivos iniciales, 658 restantes idénticos por SHA-256;
tres documentos modificados, sin archivos nuevos ni ausentes. Contenido previo de los
tres documentos conservado íntegramente; UTF-8, enlaces de las entradas nuevas y
whitespace/diff focal verificados. La propuesta de artículos se entrega sólo en la
respuesta al usuario, no se publica como contenido aprobado.

Sin cambios productivos, nuevas pruebas, Docker, bases, migraciones, proveedores ni
operaciones Git mutables. Sin commit, push, PR, merge o deployment; no hubo merge por
falta de autorización de integración. Sync remota no consultada; trabajo local pendiente
de versionado. Próximo paso: aprobación editorial del corpus y cierre/retest de QA de
Mis trabajos antes de proponer habilitación; este dictamen no autoriza esa activación.

---

Registro: 2026-11-01T21:12:40-03:00

# IA-READ-001 — Revalidación y paquete inicial

Estado: PREPARADO PARA DEFINICIÓN DE PRODUCTO Y AUTORIZACIÓN DE IMPLEMENTACIÓN.
Responsable: agente técnico de Integración de IA; origen: escritorio local Windows.
Rama: feature/professional-workspace-ux. HEAD: 2e552f2.

## Alcance y evidencia

Revisión estática del árbol local completo, incluidos archivos sin commit; no se usó
un checkout basado exclusivamente en HEAD. Preflight: 149 paths pendientes; staging
vacío. El handoff conserva 140 paths como evidencia histórica de Mis trabajos: no
representa el inventario actual. No se sincronizaron referencias ni se modificó Git.

Antecedente: auditoría del 30/10/2026 disponible en memoria de sesión, sin informe
canónico localizado bajo docs con ese nombre. Se revalidaron sus conclusiones contra
código actual; no se importan sus conteos de pruebas como evidencia nueva.

Fuentes: MASTER_SPEC, REQ-002, ADR-004, ESTANDARES_DESARROLLO,
DECISIONES_ARQUITECTURA, DESIGN_SYSTEM_V2 y ACTIVE_HANDOFF.

| Área | Evidencia actual | Consecuencia |
| --- | --- | --- |
| Búsqueda pública | professional_service.search_professionals usa query.all, devuelve ORM y no filtra estado del usuario | No exponerla directamente como herramienta; resolver visibilidad pública antes del adaptador |
| Perfil público | main_routes.perfil_profesional sólo rechaza profesional inexistente | No existe aquí una política común de publicación que pueda asumirse como validada |
| Lectura privada | work_record_service.authorize, own_record y list_records comprueban actor activo, rol y propietario | Reutilizar esos servicios; lista de diez filas, DTO acotado y detalle por ownership |
| Seguimientos | list_records admite follow; own_record devuelve relación followup | Separar resumen de lectura del historial de avisos; no ejecutar dispatch |
| Identidad | Decoradores y rutas privadas usan session.user_id | Actor exclusivamente del servidor y autorización en cada llamada |
| WhatsApp | whatsapp_routes POST /whatsapp/iniciar y servicio construyen wa.me | Contacto saliente; no acredita bot, vinculación ni webhook entrante |
| IA | Sin módulos identificados de orquestación/herramientas por búsqueda estática en app y requirements | No se acredita integración operativa; preparar módulos nuevos aislados |
| Cuotas | config define RATELIMIT_STORAGE_URI memory:// por defecto | No acreditar cuota global multiproceso; piloto sin proveedor primero |

## Primer incremento propuesto

1. Núcleo local de lectura sin proveedor, persistencia conversacional ni red externa.
2. Ayuda textual sobre corpus explícito aprobado, no sobre todo docs.
3. Lectura de resúmenes y detalle propios mediante servicios existentes.
4. Búsqueda pública supeditada a definición de visibilidad común.
5. Piloto web autenticado separado, deshabilitado por defecto, después de validar
   núcleo, corpus y coordinación de archivos compartidos.

Este paquete no autoriza IA fiscal ni deduce permisos PRO de REQ-002. Tampoco incluye
escrituras, pagos, contratación, WhatsApp conversacional, MCP remoto o proveedores.

## Contratos propuestos v1

Todos los objetos rechazan claves desconocidas, tipos coercibles y booleanos como
enteros; JSON máximo 4096 bytes. Actor no es argumento del modelo. Texto UTF-8;
respuestas estructuradas máximo 16384 bytes. Límites técnicos propuestos para revisión.

| Herramienta | Entrada estricta | Salida mínima |
| --- | --- | --- |
| help.search | query string 1..200; limit integer 1..3 | artículos: id, título, extracto hasta 800 caracteres, versión, fuente y enlace interno aprobado |
| professionals.search | servicio/zona strings 0..100; page integer 1..1000 | máximo 10: id, nombre hasta 160, servicio hasta 160, zona hasta 160, enlace canónico; has_next |
| work_records.list | q string 0..160; follow enum all/with/without; page integer 1..1000 | máximo 10: id, título hasta 160, fecha, seguimiento habilitado, enlace y has_next |
| work_records.get | record_id integer positivo | id, título, fecha, notas hasta 10000, seguimiento propio, enlace |

No devolver contactos, datos fiscales, credenciales, URLs arbitrarias, ORM ni historial
de mensajes. Las notas sólo se leen en detalle a pedido del propietario, permanecen
locales en este incremento y nunca entran al corpus. Mapear filtros a list_records;
no duplicar reglas de propiedad. El detalle vuelve a llamar own_record.

Errores controlados: INVALID_INPUT, UNAUTHENTICATED, FORBIDDEN, NOT_FOUND,
LIMIT_EXCEEDED, UNAVAILABLE. Identificadores ajenos e inexistentes comparten NOT_FOUND.
Enlaces mediante url_for y endpoints reales comprobados al implementar; ninguna URL
suministrada por modelo/documento pasa directamente al navegador.

## Corpus y seguridad

Manifest explícito con id, audiencia, versión, approved_by, approved_at, valid_from,
valid_until y ruta canónica. Sólo artículos aprobados/vigentes; ayuda inicial propuesta:
navegación, búsqueda pública y consulta de Mis trabajos. La aprobación del corpus sigue
pendiente; los specs internos no son automáticamente ayuda aprobada. Recuperación
textual determinista con biblioteca estándar, sin dependencia ni base vectorial.
Ausencia/contradicción: respuesta de límite y enlace a recorrido existente.

Documentos y notas son datos, no instrucciones. No ejecutan herramientas. Sin caché
privada compartida, almacenamiento de conversaciones ni localStorage de resultados.
Piloto: limpiar DOM y resultados al cerrar sesión/cambiar cuenta; Cache-Control no-store,
revalidación de actor por solicitud y exclusión de BFCache privado por prueba específica.
Renderizar como texto, nunca HTML del modelo. Sin logs de argumentos/resultados privados.

## Archivos y coordinación propuesta con Facturación

Nuevos y de propiedad IA: app/services/assistant_read_tools.py,
app/services/assistant_help_service.py, app/content/assistant_help/manifest.json,
tests/test_assistant_read_tools.py y tests/test_assistant_help.py.
Piloto posterior: rutas, template, CSS y controlador específicos assistant.

Compartidos ya modificados: app/__init__.py, app/routes/main_routes.py,
app/templates/base.html y requirements.txt. Compartidos potenciales: config,
autenticación, professional_service y navegación profesional. Modelos/migraciones
vigentes de trabajos y Facturación son dependencias de lectura, no archivos a modificar.

Propuesta de reparto: IA crea módulos nuevos; responsable de Facturación conserva
los archivos compartidos hasta acordar una ventana de integración; registro mínimo
del blueprint/config por IA sólo en esa ventana. No hay coordinación confirmada con
otro agente, ni se enviaron mensajes. No cambiar dependencias, auth o migraciones.
El núcleo se puede probar sin registrar rutas ni tocar inicialización compartida.

## Criterios de aceptación y pruebas pendientes

- Schemas, límites, claves desconocidas, tipos, tamaño y errores sin datos sensibles.
- Dos propietarios, usuario inactivo, cliente y anónimo; IDs ajenos y resultados vacíos.
- DTO sin contactos/notas en listados; detalle sólo propio; ausencia de ORM en salida.
- Inyección en artículos, nombres y notas sin cambios de permisos ni ejecución.
- Corpus vencido/no aprobado/audiencia incorrecta excluido; fuente/versionado verificable.
- SQL acotado y paginado; lectura sin escrituras, commits, avisos ni llamadas externas.
- Piloto: CSRF según método, sesión expirada, logout/cambio de cuenta/BFCache, XSS,
  navegación alternativa, claro/oscuro y móvil con Design System v2.
- Límite de cuatro herramientas por solicitud y timeout local propuesto de cinco
  segundos; cualquier proveedor requiere presupuesto/cuota global antes de activación.

Pruebas funcionales, PostgreSQL y navegador NO EJECUTADAS: no hubo implementación.
No se reutilizan gates históricos para acreditar este incremento. Para el núcleo,
unittest con fixtures sintéticas y SQLite descartable; PostgreSQL para consultas reales
cuando se amplíe evidencia. Sin Docker/base habitual. QA independiente posterior.

## Definiciones necesarias

Producto debe definir qué perfiles puede recuperar la IA: el buscador general y el
perfil actual no comprueban usuario activo/perfil completo como hace el buscador de
urgencias. Aplicar silenciosamente otra regla cambiaría visibilidad. Propuesta:
centralizar política aprobada antes de habilitar professionals.search.

Solicitar autorización del núcleo de ayuda y lectura privada con contratos anteriores;
corpus requiere aprobación editorial antes del piloto. Proveedor, retención, costos y
canales externos se deciden en entregas posteriores. No hay activación productiva.

## Autorización de Producto conciliada — 2026-11-01T21:26:15-03:00

Estado vigente: IMPLEMENTACIÓN LOCAL AUTORIZADA; sustituye el pedido de autorización
anterior exclusivamente para help.search, work_records.list, work_records.get y
followups.list. Se incorpora followups.list con filtros inclusivos from/to por fecha
tentativa y paginación; no confundir con fecha del trabajo.

Búsqueda pública, escrituras, notificaciones, piloto/pantallas, proveedores, WhatsApp,
MCP remoto y activación real quedan fuera. Sin requisitos PRO nuevos, migraciones ni
infraestructura. Implementación en módulos propios; sin registro de rutas. Mensaje de
coordinación enviado al responsable de Facturación para preservar archivos compartidos
y coordinar la entrada final del handoff. No se solicita que edite componentes.

El corpus de aplicación quedará vacío mientras no existan artículos individualmente
aprobados y versionados; las pruebas utilizarán un corpus sintético explícito.
La autorización técnica no se interpreta como aprobación editorial de textos nuevos.
El adaptador se desarrolla aislado: habilitar Mis trabajos para usuarios reales requiere
revisar su dictamen independiente vigente. Esta entrega pasa a Testing independiente.

## Entrega local implementada — 2026-11-01T21:31:53-03:00

Estado: READY_TO_RESUME — núcleo implementado y probado localmente; pendiente de
Testing y QA independiente. Este registro sustituye el estado de implementación
pendiente del paquete original, sin habilitar usuarios reales.

### Inventario propio

- app/services/assistant_contracts.py: schemas estrictos JSON de entrada y datos de
  salida, validador sin dependencias, 4096 bytes de entrada y 16384 de respuesta.
- app/services/assistant_read_tools.py: dispatcher execute(name, arguments,
  context=...) y ActorContext interno; errores sanitizados, cuenta/rol persistidos.
- app/services/assistant_work_record_reader.py: adaptación a list_records/own_record
  y lectura de seguimientos con autorización existente y SQL acotado.
- app/services/assistant_help_service.py: recuperación textual determinista sobre
  manifest explícito; audiencia, aprobación, versión y vigencia verificadas.
- app/services/assistant_links.py: enlaces relativos desde rutas registradas,
  compatibles con contexto de aplicación sin SERVER_NAME y prefijo de montaje.
- app/content/assistant_help/manifest.json: versión 1, sin artículos aprobados aún.
- tests/test_assistant_read_tools.py: 23 pruebas con ORM real sintético en SQLite.
- tests/test_assistant_help.py: 10 pruebas de corpus sintético temporal identificado.
- docs/REQUISITOS/IA_READ_001.md y docs/HANDOFFS/ACTIVE_HANDOFF.md: autorización,
  operación, evidencia, pendientes y cierre.

Sin cambios de inicialización, rutas, configuración, dependencias, autenticación,
modelos, migraciones, navegación ni servicios de dominio existentes. El responsable de
Facturación confirmó por el chat de coordinación que no tenía otra edición del
handoff prevista; se preservan sus entradas. No hay nuevo endpoint ni interfaz.

### Contratos vigentes y comportamiento

El único catálogo expuesto por INPUT_SCHEMAS es help.search, work_records.list,
work_records.get y followups.list. La función execute devuelve un diccionario JSON:
status ok con data; empty con data.items vacío para consultas sin resultados; error
con error.code y error.message. Error NOT_FOUND unifica identificador ajeno/inexistente
para no revelar existencia; FORBIDDEN diferencia cuenta/rol denegados; UNAVAILABLE
diferencia indisponibilidad de ausencia. Sesión inválida usa UNAUTHENTICATED.
Entrada inválida usa INVALID_INPUT; exceso de respuesta usa LIMIT_EXCEEDED.

La salida se valida también contra OUTPUT_DATA_SCHEMAS antes de devolverla. No ORM.
Los límites de notas se concilian con el máximo en bytes: hasta 10000 caracteres y
12000 bytes UTF-8, con notes_truncated explícito; escaping JSON que exceda el total
produce LIMIT_EXCEEDED. Motivo de seguimiento: hasta 300 caracteres y 600 bytes UTF-8.
Listados: diez filas, páginas 1..1000; búsqueda privada q hasta 160 caracteres y
follow all/with/without. Consulta de seguimientos: from/to opcionales ISO YYYY-MM-DD,
inclusivos por fecha tentativa; sólo habilitados, orden fecha tentativa/id estable,
consulta con LIMIT 11 para detectar próxima página. No se despachan recordatorios.

El actor se lee de la sesión Flask vigente o ActorContext construido sólo por código
confiable del servidor. Nunca deserializar ActorContext desde argumentos del modelo.
Si hay petición HTTP, un contexto explícito también debe coincidir con la sesión
actual; logout/cambio de cuenta no permite reutilizarlo. Si no hay petición, se exige
contexto servidor explícito y contexto de aplicación Flask. No se usa user_role del
cliente; se refresca rol/estado desde base en cada ejecución y se reutiliza autorización
de dominio para lecturas privadas. No se agrega requisito PRO.

No hay conversación, caché, persistencia privada adicional ni cliente de proveedor.
El caller debe entregar una sesión SQLAlchemy limpia: con new/dirty/deleted pendientes
se devuelve UNAVAILABLE sin flush, commit ni rollback. Tras un error SQL, el caller
conserva responsabilidad de recuperar/cerrar su transacción. Ninguna herramienta
confirma ni descarta cambios ajenos. Usar la integración futura dentro de una unidad
normal de lectura del servidor y no exponer la función como API sin su gate específico.

El corpus real vacío produce empty; no se copiaron textos internos ni notas privadas.
El manifest permite como fuente canónica únicamente work_records, resuelta por backend
a la ruta registrada. Para incorporar ayuda: obtener aprobación editorial individual,
registrar id/title/text/version/audience/approved_by/approved_at/valid_from/valid_until/
status/source, revisar el diff y ejecutar tests. Máximo 50 artículos, 128 KiB, texto
hasta 8000 caracteres; devuelve hasta tres extractos de 800 caracteres con fuente y
versión. Vigencia inicio inclusivo/final exclusivo; fechas con zona. Metadatos de un
artículo aprobado inválidos provocan indisponibilidad segura. El manifest es un artefacto
confiable de publicación del servidor: sus marcas de aprobación requieren revisión,
no constituyen una firma ni pueden modificarse mediante argumentos de herramientas.

### Validación y evidencia

Tanda final única, después de las correcciones: **46/46 aprobadas**, 7.550 segundos:
33 nuevas (23 adaptadores + 10 corpus) y 13 existentes de tests.test_work_records.
No se suman tandas anteriores ni subtests como casos adicionales.
Comando desde raíz, con runtime existente:

    .venv/Scripts/python.exe -m unittest tests.test_assistant_read_tools tests.test_assistant_help tests.test_work_records -v

Evidencia externa de esta sesión:
C:\Users\Cristhian\.codex\visualizations\2026\11\02\01a19998-3763-7601-aa07-72e547b40630
Archivos: ia-implementation-baseline.json, ia-tests-first.log, ia-tests-final.log,
ia-integrity.json, ia-contracts.json e ia-static-checks.json.

Comprobaciones: dos propietarios y manipulación de IDs/actor; cliente, administrador,
rol desconocido, suspendido/baneado/inexistente; sesión ausente/tipos inválidos/logout/
cambio de cuenta; entrada estricta y fechas, límites/paginación, SQL LIMIT 11; corpus
sintético aprobado/no aprobado/vencido/futuro/audiencia, fuentes, inyección como datos;
DTO/campos extra/ORM rechazados; tamaño UTF-8 y escaping. Monitor SQL sólo SELECT durante
las cuatro lecturas; snapshots de todas las tablas idénticos; commit, save_record,
dispatch y conexión socket bloqueados durante esa prueba. Sin proveedores reales.

Advertencias legacy existentes de SQLAlchemy Query.get y datetime.utcnow durante
regresiones. No se corrigieron módulos ajenos. Sin fallas focales pendientes.
No ejecutados: PostgreSQL, Docker, migraciones, navegador/AA, suite completa, QA
independiente ni carga/multiproceso. No se reclaman esas coberturas. SQLite verifica
contratos/ownership y compatibilidad ORM; no acredita locking o concurrencia PostgreSQL.

### Diagnóstico de la primera tanda

Primera tanda: 27 casos, dos fallos y un error; no es el resultado final. Causas:
NFKD separaba letras con acento al tokenizar; url_for fuera de petición requería
SERVER_NAME; el test suponía que '_' no estaba en notas, pero PRIVATE_NOTES lo contiene.
Soluciones: retirar marcas combinantes; construir enlaces relativos con el mapa Flask;
corregir expectativa de búsqueda literal. La tanda final cubre esas correcciones.
No se instalaron runtimes ni dependencias; se usó el Python existente de .venv.

### Límites y continuación

Este núcleo determinista no es un asistente generativo operativo. Los límites de pasos,
tiempo y presupuesto del piloto propuesto anteriormente no pertenecen al dispatcher
local de una llamada y quedan pendientes junto con ese piloto. No hay proveedor ni
cuota global que puedan activarse. No se procesaron cuentas/datos reales ni se usaron
bases habituales. El corpus requiere contenido editorial aprobado; la consulta de
ayuda está implementada, pero actualmente no entrega artículos en el corpus real.

Revisado MIS_TRABAJOS_UX_001: su encabezado sigue pendiente de revisión independiente;
esta entrega no lo cierra ni hereda un dictamen. Antes de habilitar lecturas reales,
confirmar el dictamen vigente y completar QA del adaptador. Próximo paso: entregar este
paquete a Testing/QA independiente con el comando anterior y corpus sintético. No se
solicita integración a develop hasta ese gate. Sin commit/push/PR/merge/deploy.

Integridad final de esta entrega: 653 archivos iniciales; 651 idénticos por SHA-256;
únicos existentes modificados: requisito IA y handoff. Ocho archivos nuevos propios.
Estado final: 160 paths pendientes, staging vacío, rama y HEAD conservados.

## Borradores de ayuda para revisión editorial — 2026-11-01T22:16:26-03:00

Estado editorial: **BORRADOR — NO APROBADO — NO PUBLICABLE**. Versión del conjunto:
0.1. Autor: agente de Integración IA, Windows local. Revisor/aprobador: pendiente de
asignación por Producto. Aprobación, fecha de publicación y vigencia: no otorgadas.
Los IDs ED-IA-01..05 son identificadores editoriales, no artículos del manifest.

Estos cinco borradores se conservan en este requisito, separados de
app/content/assistant_help/manifest.json. No son parte del corpus aprobado y no pueden
ser recuperados por help.search. Las fuentes enlazadas son trazabilidad interna para
revisión: no se propone indexar esos documentos completos ni publicarlos como ayuda.

La redacción describe reglas y capacidades verificadas para evaluar su contenido;
**no anuncia disponibilidad de un asistente ni habilitación para usuarios**. Antes de
publicar: aprobar cada texto, audiencia y versión, fijar vigencia y confirmar el cierre
de QA de Mis trabajos, incluido el P3 visual pendiente. No cambia el cierre técnico
de IA-READ-001 ni acredita PostgreSQL o producción. No incorpora acciones de escritura,
proveedores generativos, canales externos ni herramientas fiscales o financieras.

### ED-IA-01 — Qué es un registro privado de trabajo

Audiencia propuesta: profesionales con cuenta activa. Versión: 0.1; estado: BORRADOR.
Preguntas: ¿Para qué sirve? ¿Es un contrato? ¿Necesito PRO? ¿Quién puede consultarlo?

**Texto propuesto**

Un registro privado te permite organizar información de un trabajo, aunque no provenga
de una contratación dentro de MANDOBRA. Puede reunir un título, la fecha del trabajo,
notas y, si corresponde, un seguimiento.

El registro pertenece a tu cuenta profesional. No necesitás PRO ni un contrato para
usar esta función; el acceso requiere una cuenta profesional activa. Una cuenta cliente
u otro profesional no obtiene acceso a tus registros.

Guardar información en un registro no crea un contrato, no modifica la reputación ni
genera un pago o una factura. Si ya existe un trabajo contratado en MANDOBRA, su
información contractual se consulta en el recorrido de trabajos contratados.

La lectura privada de IA-READ-001 sólo consulta información autorizada: no crea ni
edita registros y no modifica el estado de una contratación.

**Fuentes explícitas para revisión**

- [MIS-TRABAJOS-UX-001](MIS_TRABAJOS_UX_001.md), «Alcance y separación de contratos»:
  finalidad, propiedad, cuenta activa, ausencia de requisito PRO y separación contractual.
- [ADR-004](../ADR/ADR-004-registro-privado-trabajos.md), «Decisión»: registro privado
  independiente del contrato, sin cambios de reputación o pagos.
- IA-READ-001, «Autorización de Producto conciliada» y cierre técnico vigente:
  alcance de consulta, sin escrituras conversacionales.

### ED-IA-02 — Encontrar mis registros

Audiencia propuesta: profesionales con cuenta activa. Versión: 0.1; estado: BORRADOR.
Preguntas: ¿Cómo busco por título o notas? ¿Cómo filtro por seguimiento? ¿Cómo funcionan
las páginas? ¿Por qué puedo encontrar un texto que no aparece en el resumen?

**Texto propuesto**

La búsqueda de registros propios puede encontrar coincidencias en el título o en las
notas. Por eso, un registro puede aparecer aunque el texto buscado no esté visible en
su resumen. Para revisar las notas, consultá el detalle del registro propio.

Podés consultar registros con seguimiento, sin seguimiento o ambos. Los resultados se
ordenan por fecha del trabajo, de más reciente a más antigua; cuando comparten fecha,
se utiliza el identificador del registro para mantener un orden estable.

Cada página contiene hasta diez registros. Si existe una página siguiente, continuá
allí para revisar más resultados. Una página sin resultados no significa que se hayan
borrado registros: también puede corresponder a filtros sin coincidencias o a una
página posterior a la última disponible.

La consulta local de lectura admite texto, filtro de seguimiento y página. Los filtros
por cliente y por fecha del trabajo pertenecen al listado web de Mis trabajos; no
forman parte de esa consulta local. En ninguno de los recorridos podés cambiar el
propietario para buscar registros de otra cuenta.

**Fuentes explícitas para revisión**

- [MIS-TRABAJOS-UX-001](MIS_TRABAJOS_UX_001.md), «Datos, validación y presentación»:
  búsqueda en título/notas, filtros web, orden estable, páginas y resultados vacíos.
- IA-READ-001, «Contratos vigentes y comportamiento»: subconjunto de filtros de
  work_records.list, diez filas y páginas 1..1000. El rango web más amplio no se
  traslada a esta herramienta.
- Contraste de implementación: [assistant_work_record_reader.py](../../app/services/assistant_work_record_reader.py)
  y [work_record_service.py](../../app/services/work_record_service.py), list_records.

### ED-IA-03 — Consultar el detalle y su privacidad

Audiencia propuesta: profesionales con cuenta activa. Versión: 0.1; estado: BORRADOR.
Preguntas: ¿Qué devuelve una consulta de detalle? ¿Quién puede verla? ¿Por qué pueden
aparecer notas acortadas? ¿Vincular un cliente le permite leer el registro?

**Texto propuesto**

La consulta local de un registro propio puede devolver su título, fecha del trabajo,
notas y datos del seguimiento: si está habilitado, su motivo y su fecha tentativa.
También incluye un enlace al detalle web del registro.

El listado ofrece un resumen. Los datos de contacto, la referencia libre del cliente,
la ubicación y los datos fiscales no forman parte de las respuestas de estas consultas
locales. La vista web del registro tiene su propio contenido y sus controles de acceso.

Las notas pueden devolverse acortadas para respetar el límite de tamaño de la consulta.
Ese recorte se identifica en el resultado y no modifica el texto guardado. El detalle
web del registro propio es el recorrido previsto para revisar su contenido completo.

Sólo el profesional propietario con cuenta activa puede consultar el registro. Vincular
un cliente no le concede permiso para leer las notas privadas. Conocer un identificador
o copiar un enlace tampoco concede acceso. Un registro inexistente o perteneciente a
otra cuenta se comunica como «Registro no encontrado», sin revelar datos ajenos.

**Fuentes explícitas para revisión**

- [MIS-TRABAJOS-UX-001](MIS_TRABAJOS_UX_001.md), «Alcance y separación de contratos»,
  «Datos, validación y presentación» y «Seguimiento y destinatarios»: ownership,
  detalle privado y ausencia de permiso de lectura para el cliente vinculado.
- IA-READ-001, «Contratos vigentes y comportamiento»: campos de work_records.get,
  notes_truncated, límites y error NOT_FOUND para registro ajeno o inexistente.
- Contraste de implementación: [assistant_work_record_reader.py](../../app/services/assistant_work_record_reader.py),
  get_record y summary. La ayuda no incluye notas ni contactos reales como ejemplos.

### ED-IA-04 — Consultar seguimientos por fecha tentativa

Audiencia propuesta: profesionales con cuenta activa. Versión: 0.1; estado: BORRADOR.
Preguntas: ¿Qué fecha se usa para buscar? ¿Se incluyen los extremos del intervalo?
¿Qué seguimientos aparecen? ¿Consultar confirma una visita o envía un aviso?

**Texto propuesto**

La fecha del trabajo indica cuándo se realizó el trabajo registrado. La fecha tentativa
del seguimiento indica cuándo se prevé retomarlo. Son datos diferentes.

La consulta local de seguimientos utiliza la fecha tentativa. Podés indicar una fecha
desde, una fecha hasta o ambas. Si indicás ambas, la primera no puede ser posterior a
la segunda. Los dos extremos se incluyen en la búsqueda.

Sólo se devuelven seguimientos habilitados de tus propios registros. Los resultados
incluyen el registro relacionado, el motivo acotado, la fecha tentativa y el enlace al
detalle. Se ordenan por fecha tentativa de menor a mayor, con un orden estable entre
los de igual fecha, y se presentan en páginas de hasta diez resultados.

Un seguimiento habilitado puede tener una fecha pasada. Si querés consultar un período
específico, indicá sus fechas; la consulta no agrega por sí sola un filtro de «futuros».

Consultar un seguimiento no lo reprograma, no envía recordatorios y no confirma que una
visita esté acordada con el cliente. La fecha tentativa tampoco acredita que un aviso
haya sido enviado: esa consulta no devuelve el historial de envíos.

**Fuentes explícitas para revisión**

- [MIS-TRABAJOS-UX-001](MIS_TRABAJOS_UX_001.md), «Seguimiento y destinatarios»:
  seguimiento vigente, fecha tentativa y distinción entre programación y avisos.
- IA-READ-001, autorización de followups.list y «Contratos vigentes y comportamiento»:
  intervalo inclusivo por tentative_date, orden fecha/id, diez filas y ausencia de despacho.
- Contraste de implementación: [assistant_work_record_reader.py](../../app/services/assistant_work_record_reader.py),
  list_followups: no aplica filtro automático por fecha actual ni devuelve historial.

### ED-IA-05 — Entender consultas vacías y errores

Audiencia propuesta: usuarios autenticados para ayuda general; las consultas de
registros y seguimientos siguen reservadas al profesional propietario con cuenta activa.
Versión: 0.1; estado: BORRADOR.
Preguntas: ¿No hay coincidencias o falta acceso? ¿Qué pasa si la sesión no es válida?
¿Qué hago si la consulta no está disponible? ¿Una consulta fallida cambia mis datos?

**Texto propuesto**

Una consulta sin resultados significa que no se encontraron elementos para esa búsqueda
o página. Podés revisar los filtros o volver a la primera página. No demuestra que se
hayan eliminado datos. En la ayuda, también puede significar que no hay un artículo
aprobado y vigente para esa consulta y audiencia.

Si falta una sesión válida, se requiere iniciar sesión. Un mensaje de acceso denegado
indica que la cuenta o el rol no están habilitados para esa consulta; no concede acceso
cambiar el identificador o declarar otro propietario. Para los registros privados, la
cuenta debe ser profesional, activa y propietaria del registro. No se exige PRO.

«Registro no encontrado» puede corresponder a un identificador inexistente o a un
registro de otra cuenta. El mensaje no revela cuál de esas situaciones ocurrió.

Una solicitud inválida requiere revisar los datos, por ejemplo una fecha incorrecta o
un intervalo invertido. Si se excede el tamaño permitido de respuesta, la consulta
informa el límite. Si la consulta está indisponible, no debe interpretarse como una
lista vacía; el recorrido web habitual es la alternativa prevista, sujeto a su propia
habilitación y permisos.

Estas consultas de lectura no guardan cambios ni envían avisos, tanto si responden
correctamente como si devuelven un error.

**Fuentes explícitas para revisión**

- IA-READ-001, «Contratos vigentes y comportamiento» y cierre independiente: estados
  ok/empty/error, errores controlados, permisos y ausencia de efectos de escritura.
- [MIS-TRABAJOS-UX-001](MIS_TRABAJOS_UX_001.md), «Alcance y separación de contratos» y
  «Datos, validación y presentación»: acceso profesional propio y filtros vacíos/inválidos.
- Contraste de implementación: [assistant_read_tools.py](../../app/services/assistant_read_tools.py),
  mensajes, comprobación persistida de cuenta/rol y dispatcher de lectura.

### Revisión editorial pendiente del conjunto

Validar claridad y terminología; aprobar o corregir cada texto y su audiencia; confirmar
que la distinción entre recorrido web y núcleo local no anuncie una interfaz de IA
existente. La aprobación de uno no aprueba los otros. El enlace de fuente que el backend
puede devolver sigue limitado a la ruta canónica configurada; estas referencias internas
no se copian automáticamente a resultados de ayuda.

No se rellenan approved_by, approved_at ni vigencia ficticios. La eventual conversión
a artículos del manifest requiere aprobación explícita y una entrega posterior; este
encargo sólo prepara borradores. Sin nuevas pruebas funcionales, Docker, migraciones,
proveedores, cambios de aplicación ni operaciones Git mutables.
