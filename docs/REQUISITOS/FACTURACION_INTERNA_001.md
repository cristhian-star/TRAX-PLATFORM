# Cierre técnico independiente de FACTURACION_INTERNA_001

Registro documental: 2026-11-01T21:57:16-03:00. Responsable: agente técnico Facturación MANDOBRA.
Dictamen independiente: **2026-11-01T21:42:54-03:00**, comunicado por Producto.
Estado técnico: **BACKEND INTERNO VERIFICADO EN EL ALCANCE EVALUADO**.
Estado de este cierre documental: COMPLETED, en la rama; sin integración Git.
Rama: `feature/professional-workspace-ux`.
HEAD: `2e552f2fdc57c152c97f0486050574696f6b250e`; staging vacío.

Este cierre sustituye únicamente el pendiente de QA independiente del backend
registrado en los antecedentes inferiores. Conserva los resultados históricos,
la propuesta del formulario y todas sus dependencias. No habilita captura pública
de datos reales, emisión fiscal ni producción.

## Resultados independientes, con conteos separados

| Categoría | Resultado | Evidencia durable |
| --- | --- | --- |
| Focales de preparación, acceso y servicio | **19/19 aprobadas** | [focal-tests.log](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/facturacion-interna-independent-20261101/focal-tests.log) |
| PostgreSQL exclusivo | **9/9 aprobadas** | [postgres-gate.log](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/facturacion-interna-independent-20261101/postgres-gate.log) |
| Reproducciones adversariales | **Cuatro escenarios**, con incidencias del harness y repetición focal documentadas abajo | [script](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/facturacion-interna-independent-20261101/postgres-adversarial.py), [repetición de cuatro escenarios](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/facturacion-interna-independent-20261101/postgres-adversarial-retry.log), [nodo repetido](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/facturacion-interna-independent-20261101/postgres-adversarial-failed-node-retry.log) |
| Regresión proporcional | **122/123 aprobadas**; un P3 externo pendiente | [proportional-regression.log](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/facturacion-interna-independent-20261101/proportional-regression.log) |

Los conteos no se suman entre sí ni con las tandas del implementador.
Las cuatro reproducciones abarcan: carrera con igual contenido (una fila, una
auditoría y replay recuperable); carrera con contenido distinto (un ganador y
conflicto); rollback ante integridad no reconocida con reutilización de sesión;
y fallo de auditoría con rollback de entidad y recuperación de sesión.

Se conservan los intentos fallidos: la primera corrida adversarial registró
cuatro errores de fixture por FK; la repetición registró tres escenarios OK y
un error del harness al no capturar `BillingConflict` en la carrera con contenido
distinto. Tras ajustar únicamente el harness externo, ese nodo pasó en su
repetición focal (1/1). No existió una única corrida final limpia de cuatro casos;
no se presenta como 4/4 ni se suman las repeticiones como escenarios nuevos.
Estos ajustes no modificaron código del repositorio.

## P3 externo pendiente

La aserción de `tests/test_budget_request_ux06a.py:310`, en
`test_professional_never_has_client_contract_capabilities`, está desactualizada:
exige `PermissionError` para una capacidad de Propuestas admitida por el flujo
vigente. El escenario de autoridad propia de Propuestas pasó por separado.
El P3 sigue **PENDIENTE**, fuera del incremento fiscal; no se corrigió esa prueba.
No se declara la regresión global aprobada ni se atribuye esta falla a Facturación.

Evidencia: [falla actual](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/facturacion-interna-independent-20261101/budget-failure-current.log),
[falla en el estado exacto anterior](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/facturacion-interna-independent-20261101/budget-failure-before-fiscal.log),
[comparación SHA-256 del baseline](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/facturacion-interna-independent-20261101/budget-baseline-comparison.txt) y
[autoridad de Propuestas](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/facturacion-interna-independent-20261101/proposal-authority-comparison.log).
El estado anterior reconstruido coincide con el SHA esperado
`fa9a809689eaaa563c98c1f2236146178ddaf5d2ae65ecde7ba2c6b0ed110ba4`.

## Migración y entorno acreditados

`20261101_01`, padre `20261030_01`, validada **exclusivamente en PostgreSQL 16
exclusivo y descartable**. Se verificaron head, downgrade/upgrade, tablas fiscales
y preservación de usuarios preexistentes. El downgrade elimina perfiles y
borradores internos; no implica preservación de esos datos fiscales.
La base habitual **no fue migrada**.

Evidencia: [ciclo independiente](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/facturacion-interna-independent-20261101/migration-independent.log),
[preservación de usuarios](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/facturacion-interna-independent-20261101/migration-preservation.log) y
[esquema evaluado](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/facturacion-interna-independent-20261101/postgres-schema.txt).
El contenedor independiente `mandobra-billing-qa-independent-20261101`, su volumen
y el listener 55591 fueron retirados según [docker-cleanup.log](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/facturacion-interna-independent-20261101/docker-cleanup.log).
Esta sesión documental solo leyó esa evidencia; no ejecutó Docker ni migraciones.

## Integridad y alcance del cierre

[Inventario fiscal evaluado](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/facturacion-interna-independent-20261101/fiscal-files-evaluated.json),
[manifiesto inicial independiente](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/facturacion-interna-independent-20261101/source-manifest-initial.json),
[manifiesto final independiente](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/facturacion-interna-independent-20261101/source-manifest-final.json) y
[comparación independiente](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/facturacion-interna-independent-20261101/external-concurrency-diff.txt) preservan
la identidad del árbol evaluado. El QA registró 661 archivos sin cambios, altas
ni bajas durante su revisión; ese inventario histórico no es el de este cierre.

En este cierre se verificaron contra el inventario de QA los diez archivos de
aplicación/migración/pruebas fiscales, ADR-005 y los documentos fiscales previos:
todos coincidieron antes de escribir. Solo se actualizan este requisito,
`docs/HANDOFFS/ACTIVE_HANDOFF.md` y `docs/CHANGELOG.md`; el control inicial de
663 archivos permite comprobar que los otros 660 permanecen idénticos.
La entrada concurrente IA-READ-001 y los antecedentes se conservan íntegros.
Validación de cierre: SHA-256, UTF-8, referencias de evidencia y diff documental;
no son nuevas pruebas funcionales.

No hubo cambios productivos, nuevas pruebas, Docker, migraciones, cambios de
configuración/dependencias ni operaciones Git mutables. Sin commit, push, PR,
merge o deploy. No hubo merge porque este encargo autoriza solo cierre documental;
no se afirma sincronización remota actual.

## Límites y decisiones pendientes de Producto

Continúan pendientes el **formulario operativo**, las decisiones fiscales
restantes y la **integración ARCA**. El dictamen no acredita UI/navegador/AA,
snapshot fiscal confirmado, emisión, certificados, CAE, numeración, PDF/QR,
timeouts/reconciliación fiscal, homologación, producción ni suite completa.
Un borrador y un perfil declarado no son factura ni verificación fiscal.
La auditoría original del 30/10 sigue sin referencia canónica localizada.

Producto debe definir datos obligatorios y categorías/documentos del receptor;
alcance de moneda y límites del formulario; consentimiento y retención/exportación
antes de capturar datos reales; integración directa o intermediada y representación;
punto de venta por ambiente/canal y uso externo de la secuencia; verificación y
renovación de inscripción; custodia/rotación/revocación de certificados; y operación
de correcciones, contingencias y soporte antes de producción. La preparación ARS
actual no constituye aprobación de todas esas políticas.

Próximo paso: resolver esas definiciones y preparar el formulario con CSRF,
conservación segura de valores y nueva validación independiente. La eventual
integración Git del backend debe ser selectiva, preservar el árbol mixto y contar
con autorización expresa. El P3 externo requiere un trabajo separado.

<!-- FIN CIERRE DOCUMENTAL FACTURACION_INTERNA_001 -->

# FACTURACION-INTERNA-001 — Perfil declarado y borradores

Timestamp: 2026-11-01T21:15:58-03:00.
Estado: READY_TO_RESUME. Responsable: agente técnico MANDOBRA local.
Rama: `feature/professional-workspace-ux`.
Base: `2e552f2fdc57c152c97f0486050574696f6b250e`.

## Revalidación y autoridad

La solicitud de esta sesión autoriza preparar e implementar componentes internos;
supera la prohibición histórica de implementar contenida en REQ-002 solamente
para este incremento. No autoriza homologación ni producción.
[REQ-002](REQ-002-facturacion-pro-mvp.md) y Master Spec conservan persona humana,
monotributo activo, PRO vigente, Factura C opcional y confirmación humana.
Declarar esos datos no acredita las condiciones necesarias para emitir.

No se encontró la auditoría fiscal del 30/10/2026 en el inventario documental
local ni una referencia inequívoca en el handoff. Se solicitó su ubicación;
su contenido y conclusiones no se dan por revalidados. Esta es una revisión
actual del requisito y código disponibles, pendiente de contrastar aquel informe.

Fuentes oficiales consultadas el 2026-11-01:

- [ARCA: facturación del monotributo](https://arca.gob.ar/monotributo/ayuda/facturacion.asp):
  comprobantes C para operaciones locales; la exportación corresponde a E y está excluida.
- [ARCA: datos a informar](https://www.arca.gob.ar/fe/emision-autorizacion/datos-comprobantes.asp):
  reglas de receptor que deberán contrastarse para la emisión futura.
- [ARCA: modalidades](https://www.arca.gob.ar/facturacion/monotributo/modalidades.asp):
  canales y puntos de venta. Este incremento no selecciona canal ni habilita un punto.

No se implementan umbrales fiscales variables ni se adopta un catálogo técnico
de otro webservice como si fuera el contrato de una integración ya elegida.
Facturitas sigue siendo referencia de experiencia, sin dependencia incorporada.

## Inventario actual y separación

`professional_billing_view_service.py` y sus templates presentan destinos
preparatorios. No existían modelos fiscales ni transporte ARCA. Se conserva esa UI.
`subscription_service.has_pro_access` verifica actor profesional activo,
verificación profesional aprobada y suscripción PRO activa con fuente y vencimiento.
Se reutiliza; la política fiscal no concede ni extiende PRO.

Cobros mantiene `payment_order_application_service`, entrega, reservas,
conciliación y efectos separados. La ruta de entrega obtiene su servicio desde
`app.extensions`; el arranque normal no lo construye. No se modifican esas piezas,
sus flags, sus importes, webhooks ni políticas comerciales.
Contratos y registros de trabajos no se copian ni cambian automáticamente.

## Propuesta concreta del formulario

La UI siguiente es propuesta para revisión, todavía no publicada:

| Sección | Campos | Tratamiento |
| --- | --- | --- |
| Perfil opcional | CUIT, nombre legal, domicilio fiscal | Declarados; CUIT con formato y checksum, sin acreditar identidad |
| Declaración | Soy persona humana y monotributista | Aceptación explícita, nunca preseleccionada |
| Estado | Datos declarados, sin verificar ante ARCA | Sin sello de habilitación fiscal |
| Borrador interno | Descripción, importe, receptor opcional, período del servicio | Nunca completa datos ausentes con IA ni con contratos |
| Moneda | ARS en esta preparación técnica | Propuesta inicial acotada; otras monedas pendientes de definición |
| Acción | Guardar borrador interno | Texto visible: no es una factura ni fue enviado a ARCA |
| Error | Mensaje por campo y valores escapados conservados | Sin logs con datos fiscales ni aceptación restaurada automáticamente |

Los límites de longitud y Numeric(14,2) son capacidades técnicas internas,
no topes fiscales, comerciales ni autorización para facturar esos importes.
La entrada decimal usa punto, rechaza float, exponentes y no finitos;
ROUND_HALF_UP a dos decimales es explícito. La UI deberá mostrar ese resultado
antes de guardar y, en un incremento posterior, antes de confirmar emisión.

Decisiones que sí necesitan definición de Producto/operación antes de ampliar:

| Decisión | Propuesta para resolver | Gate |
| --- | --- | --- |
| Receptor | Seleccionar categoría y documento usando catálogo oficial de la integración elegida; pedir datos condicionales, no inferir consumidor final | Revisión fiscal y formulario de emisión |
| Canal/representación | Evaluar directa vs intermediada con costos y responsabilidades explícitas | Antes de cualquier conexión |
| Punto de venta | Configuración por ambiente y canal; relevar operaciones fuera de MANDOBRA | Antes de numeración |
| Inscripción | Adaptador verificable con evidencia fechada y política de renovación | Antes de habilitar emisión |
| Certificados | Referencias a custodia aprobada, rotación, vencimiento y revocación; nunca contraseña ARCA | Antes de capturar material secreto |
| Privacidad | Aprobar consentimiento, retención, exportación, respaldo y eliminación | Antes de capturar datos reales por UI |
| Operación | Correcciones, contingencia, soporte e incidentes definidos | Antes de producción |

## Componentes implementados

- `app/services/billing_preparation.py`: validaciones comunes y valores inmutables
  de preparación. No representan el snapshot confirmado del incremento 3.
- `app/services/billing_access_policy.py`: actor persistido y política PRO reutilizada.
  La lectura devuelve identidad autorizada; cada consulta debe filtrar ownership.
- `app/models/billing_preparation.py`: un perfil por usuario y borradores internos.
  El CUIT no se cambia mediante este servicio; no se admiten múltiples CUIT por usuario.
- `app/services/billing_preparation_service.py`: alta/actualización de perfil,
  alta idempotente y consulta propia de borrador; auditoría sin datos fiscales.
- `app/__init__.py`: solamente se agrega el registro de esos modelos.
  Se preserva el resto del archivo local; sin flags, dependencias ni rutas nuevas.
- `migrations/versions/20261101_01_billing_preparation.py`:
  padre `20261030_01`; tablas `billing_profiles` y `billing_drafts`.
- Pruebas: `test_billing_preparation.py`, `test_billing_access_policy.py`,
  `test_billing_preparation_service.py`, `postgresql_billing_preparation.py`.
- Documentación: este requisito, ADR-005 y ACTIVE_HANDOFF.

No hay endpoints nuevos, UI operativa, IA, confirmación, intento externo,
CAE, numeración, PDF, QR, credenciales ni habilitación ARCA.
La preparación admite datos insuficientes para emitir; no existe función que los envíe.
La consulta interna de borradores propios permanece disponible tras perder PRO;
no decide la futura política legal de retención de comprobantes autorizados.

## Transacciones y recuperación

Los comandos hacen `flush`, nunca `commit`. El llamador controla la transacción
que incluye entidad y auditoría. Si falla cualquier paso, debe hacer rollback.
No registrar payloads, excepciones SQL con parámetros ni modelos privados.
Los retornos públicos son diccionarios mínimos; `read_draft` solo devuelve datos propios.

Actualizaciones de perfil exigen versión esperada y control optimista SQLAlchemy.
La base garantiza un perfil por dueño y una clave UUID por dueño/borrador.
Concurrencia puede producir `IntegrityError` o `StaleDataError`: rollback completo;
para un alta de borrador incierta en la base, repetir solo con la misma clave y
contenido. Un replay exige nuevamente PRO vigente y otro contenido es conflicto.
No se transforma un error de base en éxito. El futuro controlador debe traducir
conflictos sin exponer información SQL y conservar el formulario escapado.

El perfil puede cambiar después de crear un borrador: se guarda su versión de origen,
pero todavía no hay snapshot fiscal confirmado. No usar estos registros para emitir.
Futuro incremento 3 debe copiar emisor, receptor e importes al snapshot inmutable,
exigir nueva revisión ante cambios y vincular actor, contenido y vencimiento.

## Validación y evidencia

PostgreSQL 16 exclusivo: `mandobra-billing-20261101-01a19993`,
contenedor `9a00769fc562bbdde18e594a0009a48c96ea2f66e36785a22e83e1ea881b4bd5`,
base `billing_qa`, `127.0.0.1:55591`. Datos y contraseña sintéticos descartables.
Upgrade de toda la cadena desde base vacía hasta `20261101_01` satisfactorio.
Gate PostgreSQL: **9/9**, incluye seis escenarios del servicio, carreras de
actualización/alta y downgrade/upgrade preservando usuarios preexistentes.
No acredita la seguridad de una futura llamada externa ni un snapshot confirmado.

Intentos iniciales del gate: cero pruebas ejecutadas con `psycopg` no instalado;
se corrigió a `psycopg2`, dependencia existente. El sandbox negó TCP local;
la ejecución autorizada contra el contenedor exclusivo pasó. No se instalaron paquetes.
El inventario AST preliminar omitió asignaciones anotadas y sugirió dos heads;
`alembic heads` confirmó una sola cadena. No se creó merge de migraciones.

Validación focal inicial: 24/24 (9 validación, 4 acceso, 11 UI existente).
Servicio interno adicional: 6/6. No sumar estas tandas a la ejecución final de regresión.
Resultado final y preservación de hashes se registran en ACTIVE_HANDOFF.
Evidencia externa: `C:\Users\Cristhian\.codex\visualizations\2026\11\02\01a19993-4bcb-7750-b189-6d7ae9319569`.
`billing-baseline.json` conserva el manifiesto inicial y `billing-tests-final.log`
la ejecución final focal/regresiones.

No ejecutados: navegador del formulario nuevo (no implementado), AA, suite completa,
homologación, certificados, llamadas fiscales, timeout/reconciliación externa,
QR/PDF y QA independiente. Advertencias legacy de SQLAlchemy/datetime no corregidas.
La base habitual no se migró. No se administraron recursos Docker compartidos.

## Operación y continuación

Antes de usar servicios: obtener actor de la sesión autenticada, validar por servicio,
abrir transacción y completar commit/rollback; no tomar owner de formularios.
No correr esta migración sobre la base habitual por el solo registro en el arranque.
El downgrade elimina toda la preparación fiscal: exportar y aprobar pérdida primero.

Prueba pura/SQLite:
` .venv\Scripts\python.exe -m unittest tests.test_billing_preparation tests.test_billing_access_policy tests.test_billing_preparation_service `.
Gate PG exige `TRAX_BILLING_TEST_URL` apuntando únicamente al host/puerto/base/usuario
indicados y `TRAX_BILLING_ALLOW_RESET=billing-01a19993`; ejecutar
` .venv\Scripts\python.exe -m unittest tests.postgresql_billing_preparation -v `.
El gate trunca datos: recrear primero el contenedor exclusivo descartable; nunca
modificar sus guardas para apuntar a otro recurso. No instalar scheduler.

Siguiente entrega: contrastar la auditoría faltante, resolver datos de receptor y
política de captura/retención, coordinar inicialización con el agente de IA,
publicar formulario interno con CSRF, recuperación y QA independiente.
Después: snapshot/confirmación y orquestación durable con adaptador de prueba;
homologación oficial separada; representación/consulta/soporte; habilitación productiva.
No integrar a develop antes de la revisión independiente del paquete.

## Cierre de validación y coordinación

Ejecución ampliada final: 123 pruebas, 122 aprobadas y una falla en
`tests.test_budget_request_ux06a.BudgetRequestUX06ATest.test_professional_never_has_client_contract_capabilities`,
línea 310: esperaba PermissionError. Las 19 pruebas nuevas pasaron; los 11
escenarios de UI de Facturación existentes también. El fallo se reprodujo
con el app/__init__.py inicial exacto reconstruido en memoria y cotejado por
SHA-256 contra el manifiesto inicial, sin editar archivos para esa reproducción.
No es una regresión introducida por el registro del modelo. Causa funcional
del fallo no diagnosticada; no se corrigió código ajeno. No se declara gate global verde.
Evidencia: billing-tests-final.log y billing-baseline-failure.log.

Alembic heads confirma solo 20261101_01. git diff --check sin errores. El contenedor
exclusivo fue retirado con sus volúmenes; no se tocó infraestructura compartida.
Se detectaron cambios externos en docs/.obsidian/graph.json, workspace.json y
la entrada IA-READ-001 del handoff, además del nuevo IA_READ_001.md; se preservaron.
De 625 archivos del manifiesto inicial, 621 permanecen idénticos; los otros son
app/__init__.py, ACTIVE_HANDOFF y los dos archivos Obsidian externos.

Se leyó IA_READ_001: IA propone módulos nuevos y coordinar compartidos antes del piloto.
El intento de mensaje al chat Integrar asistencia de IA en MANDOBRA fue rechazado
por revisión automática por falta de autorización explícita para ese hilo. No fue
enviado; no hay acuerdo bilateral confirmado. Se conserva la propuesta de reparto,
sin cambiar configuración, rutas, dependencias, autenticación ni templates compartidos.
La única edición de inicialización propia es el registro de los dos modelos.

Estado final: backend interno implementado; propuesta del formulario preparada;
UI operativa, contraste con auditoría original, coordinación bilateral y QA independiente
pendientes. Sin commit, push, PR, merge ni deploy. No se recomienda integrar todavía.
