# Handoff tecnico: especificacion PRO y Facturacion MVP

Timestamp: 2026-09-03T21:55:15-03:00
Estado: COMPLETED
Resultado del ciclo: COMPLETED
Alcance: especificacion funcional documental de activacion y vigencia PRO y de
Facturacion MANDOBRA PRO MVP

## Identificacion

- Dispositivo/origen: Codex Desktop local.
- Agente o sesion de origen: Codex / Documentation Engineer Senior.
- Rama actual: `docs/spec-pro-facturacion-mvp` (estado provisto y verificado
  antes de iniciar esta tarea; no se repitio el preflight por instruccion).
- Commit base y ultimo commit informado: `e0eed2`.
- Cambios sin commit: SI; nueve archivos Markdown bajo `docs/` enumerados en
  este handoff.
- Rama subida a GitHub: NO; no se ejecuto push ni se verificaron remotos por
  restriccion expresa.
- Destino previsto: `02 - Implementacion y Refinacion`.

## Objetivo de la sesion

Formalizar como requisitos separados y aprobados la activacion y vigencia de
MANDOBRA PRO y Facturacion MANDOBRA MVP como beneficio opcional de PRO, sin
implementar codigo, proveedores, integraciones, migraciones, tests ni cambios
visuales.

## Trabajo completado

- Se creo [REQ-001](../REQUISITOS/REQ-001-activacion-y-vigencia-pro.md) con
  catalogo `FREE`, `PRO`, `ENTERPRISE`, elegibilidad profesional y reglas para
  PRO transaccional y por suscripcion.
- Se creo [REQ-002](../REQUISITOS/REQ-002-facturacion-pro-mvp.md) con el alcance
  fiscal MVP de persona humana, monotributo activo y Factura C.
- Se separaron expresamente Facturacion, entitlement PRO y configuracion ARCA.
- Se registro el contraste con el codigo actual: activacion inmediata/manual,
  lector de puntos legacy, falta de control de vencimiento y ausencia de PSP,
  ARCA, facturacion e IA productiva.
- Se actualizaron Master Spec, Roadmap, Backlog, Changelog e indices con
  implementacion marcada como `PENDIENTE`.
- Se conservaron preguntas abiertas separadas de las decisiones aprobadas.

## Trabajo parcialmente completado

Ninguno dentro del alcance documental autorizado.

## Pendientes

- Porcentaje de comision; precio, periodicidad, beneficios y limites completos
  de PRO; renovacion, cancelacion, mora, contracargos y periodo de gracia.
- Politica de migracion de accesos PRO actuales y concesiones administrativas.
- Seleccion y validacion del PSP y estrategia del entitlement.
- Integracion directa con ARCA o proveedor; custodia y rotacion de
  certificados; validacion de monotributo; datos del receptor; retencion,
  almacenamiento, entrega, limites, correcciones, anulaciones, notas de credito
  y contingencia.
- Proveedor y modelo de IA, costos y revisiones legal, fiscal, contable y de
  seguridad.
- Modelo futuro de `ENTERPRISE`; no se autorizo crear el actor `EMPRESA`.
- Implementacion y pruebas de ambos requisitos, sujetas a nueva autorizacion.

## Bloqueantes

- BLOQUEANTE para implementar PRO transaccional: seleccionar y validar PSP y
  cerrar politicas comerciales y de contracargos.
- BLOQUEANTE para implementar Facturacion: resolver integracion fiscal,
  custodia de credenciales, politicas de datos y revisiones legal, fiscal,
  contable y de seguridad.
- No existen bloqueantes para el cierre de esta especificacion documental.

## Archivos creados

- `docs/REQUISITOS/REQ-001-activacion-y-vigencia-pro.md`: requisito aprobado;
  implementacion pendiente, sin commit.
- `docs/REQUISITOS/REQ-002-facturacion-pro-mvp.md`: requisito aprobado;
  implementacion pendiente, sin commit.

## Archivos modificados

- `docs/REQUISITOS/README.md`: indice de requisitos aprobados, sin commit.
- `docs/REQUISITOS/MASTER_SPEC.md`: resumen, actores, estado actual, capacidades
  aprobadas y pendientes, sin commit.
- `docs/ROADMAP.md`: especificaciones aprobadas e implementaciones pendientes,
  sin commit.
- `docs/BACKLOG.md`: pendientes consolidados y enlazados, sin commit.
- `docs/INDEX.md`: enlaces a REQ-001 y REQ-002, sin commit.
- `docs/CHANGELOG.md`: cambios exclusivamente documentales, sin commit.
- `docs/HANDOFFS/ACTIVE_HANDOFF.md`: reemplazo del handoff activo para este
  ciclo, sin commit.

## Migraciones relacionadas

Ninguna. No se crearon ni ejecutaron migraciones.

## Tests y validaciones ejecutados

- Inspeccion estatica dirigida de `Subscription`, `subscription_service`,
  verificacion, decoradores, ruta de upgrade, administracion, Planes y puntos
  legacy: EJECUTADA; confirma el contexto registrado en los requisitos.
- Verificacion de las 16 secciones obligatorias en REQ-001 y REQ-002:
  EJECUTADA; resultado `HEADINGS_OK` para ambos documentos.
- Comprobacion de enlaces Markdown relativos en los documentos creados o
  actualizados: EJECUTADA; resultado `RELATIVE_LINKS_OK`.
- Comprobacion de identificadores: EJECUTADA; `REQ-001` y `REQ-002` son los
  primeros identificadores de requisito y no reutilizan un `REQ-NNN` previo.
- `git status --short`: EJECUTADO; cambios exclusivamente Markdown bajo
  `docs/`.
- `git diff --check`: EJECUTADO; sin errores, con advertencias informativas de
  conversion futura LF a CRLF para archivos rastreados.
- `git diff --stat`: EJECUTADO; revisado antes del cierre del handoff.
- `git diff -- docs`: EJECUTADO; revisado antes del cierre del handoff.

## Tests y validaciones no ejecutados

- Tests de aplicacion: NO EJECUTADOS - no aplican al alcance documental.
- Aplicacion: NO EJECUTADA; no aplica al alcance documental.
- Migraciones: NO EJECUTADAS; no existen cambios de esquema.
- Integraciones PSP, ARCA e IA: NO EJECUTADAS; no estan implementadas ni fueron
  autorizadas.

## Resultados de tests

- Aprobados: validaciones documentales de estructura, enlaces, alcance y diff.
- Fallidos: ninguno.
- Omitidos: suite de aplicacion, por no aplicar al alcance documental.
- Resultado general: PASS documental; implementacion NO EJECUTADA.

## Errores conocidos

- Ninguno durante la edicion documental.
- CONTRADICCION vigente y no corregida en codigo: la UI publica conserva
  `Plus`, mientras el catalogo aprobado es `FREE`, `PRO`, `ENTERPRISE`.
- CONTRADICCION vigente y no corregida en codigo: el upgrade usa puntos legacy
  o verificacion, mientras REQ-001 exige cuenta activa, verificacion aprobada y
  una fuente de entitlement vigente.

## Troubleshooting relacionado

Ninguno.

## Decisiones tomadas

- APROBADO: `FREE`, `PRO`, `ENTERPRISE` es el catalogo canonico; `Plus` queda
  fuera.
- APROBADO: la primera implementacion PRO corresponde a profesionales con
  cuenta activa y verificacion aprobada; puntos legacy no conceden PRO.
- APROBADO: modalidad transaccional y suscripcion mantienen el mismo
  entitlement `PRO`.
- APROBADO: Facturacion es un modulo separado, opcional y exclusivo de PRO
  vigente; no activa ni extiende PRO.
- APROBADO: el alcance fiscal inicial es persona humana, monotributo activo y
  Factura C, con borrador asistido y confirmacion humana obligatoria.
- PENDIENTE: proveedor PSP, integracion fiscal, custodia de secretos, proveedor
  de IA, modelos, precios y porcentajes.
- PENDIENTE: crear ADR cuando se aprueben decisiones arquitectonicas con impacto
  transversal o costosas de revertir.

## Documentacion actualizada

- [REQ-001](../REQUISITOS/REQ-001-activacion-y-vigencia-pro.md).
- [REQ-002](../REQUISITOS/REQ-002-facturacion-pro-mvp.md).
- [Indice de requisitos](../REQUISITOS/README.md).
- [Master Spec](../REQUISITOS/MASTER_SPEC.md).
- [Roadmap](../ROADMAP.md).
- [Backlog](../BACKLOG.md).
- [Indice documental](../INDEX.md).
- [Changelog](../CHANGELOG.md).
- Este handoff activo.

## Riesgos

- Implementar antes de cerrar politicas abiertas puede producir accesos,
  cobros o efectos fiscales incorrectos.
- Webhooks duplicados o fuera de orden pueden degradar vigencia e idempotencia.
- Una custodia inadecuada puede exponer secretos y datos fiscales.
- IA sin limites estrictos puede inventar datos o aparentar asesoramiento
  fiscal.
- El codigo legacy puede seguir concediendo PRO por puntos hasta que una
  implementacion autorizada aplique REQ-001.

## Proximo paso recomendado

Iniciar `02 - Implementacion y Refinacion` con una revision tecnica de REQ-001
y REQ-002 que produzca un plan de implementacion por fases y ADR pendientes,
sin escribir codigo hasta cerrar las decisiones bloqueantes y obtener
autorizacion explicita.

## Handoff exacto para 02 - Implementacion y Refinacion

1. Verificar estado Git, rama y ultimo commit antes de actuar.
2. Confirmar que los nueve cambios Markdown sin commit enumerados siguen
   presentes e intactos.
3. Leer completos REQ-001, REQ-002, Master Spec y este handoff.
4. Contrastar nuevamente el plan con el codigo y migraciones vigentes si cambia
   el commit base.
5. Separar la implementacion de entitlement PRO del modulo de Facturacion.
6. Proponer fases, invariantes, migraciones, pruebas PostgreSQL, controles de
   seguridad y ADR, sin seleccionar proveedores no aprobados.
7. Resolver o elevar las preguntas bloqueantes antes de implementar.
8. No modificar codigo, migraciones o UI sin autorizacion explicita para la
   fase de implementacion.

## Acciones que NO deben realizarse

- No asumir que REQ-001 o REQ-002 ya estan implementados.
- No elegir Mercado Pago, otro PSP, integracion ARCA ni proveedor de IA sin
  evaluacion y aprobacion.
- No almacenar claves fiscales en texto plano.
- No usar puntos legacy como elegibilidad PRO.
- No crear el actor `EMPRESA` por la sola existencia conceptual de
  `ENTERPRISE`.
- No ejecutar commit, push, PR, merge, rebase, reset, clean, stash ni cambios
  de rama sin autorizacion expresa.
- No mezclar cambios ajenos o fuera de `docs/` con este ciclo documental.

## Criterio de cierre

Este ciclo queda `COMPLETED` cuando los dos requisitos y su trazabilidad
documental estan presentes, los cambios permanecen exclusivamente bajo
`docs/`, las validaciones documentales no informan errores y se entrega este
handoff. El cierre no requiere ni autoriza commit, push, PR, merge o
implementacion.

---

# Actualizacion posterior al merge de PRO y Facturacion MVP

Timestamp: 2026-09-04T08:27:58-03:00
Estado: COMPLETED
Estado vigente: MERGED
Resultado: COMPLETED
Documento: `docs/HANDOFFS/ACTIVE_HANDOFF.md`
Motivo: cerrar la trazabilidad posterior a la integracion del ciclo documental
de PRO y Facturacion MVP.
Evidencia: commit documental, Pull Request y merge commit verificados; `develop`
local y `origin/develop` sincronizados en `e26e598` desde la laptop.
Responsable: Codex / Documentation Engineer Senior
Dispositivo: laptop
Rama de esta actualizacion: `docs/close-pro-facturacion-handoff`
Commit base: `e26e5989e259ad142dfe994817566c3b6d5ff8d1`

## Registro superado

El registro original de `2026-09-03T21:55:15-03:00` se conserva integro porque
describe correctamente el estado previo al commit. Su estado operativo queda
SUPERSEDED por esta actualizacion posterior: los nueve archivos Markdown que
entonces estaban sin commit ya fueron versionados e integrados en `develop`.

## Integracion verificada

- Commit documental: `9f3b20899704e2667411c45fde3b529909bd53ca`.
- Pull Request: `#3`.
- URL: `https://github.com/cristhian-star/TRAX-PLATFORM/pull/3`.
- Rama origen: `docs/spec-pro-facturacion-mvp`.
- Rama destino: `develop`.
- Merge commit: `e26e5989e259ad142dfe994817566c3b6d5ff8d1`.
- Merge realizado: `2026-09-04T00:52:14-03:00`.
- Cambios integrados: nueve archivos Markdown bajo `docs/`.
- Sincronizacion posterior: verificada en la laptop.
- `develop` local y `origin/develop`: sincronizados en `e26e598`.
- Arbol de trabajo previo a esta actualizacion: limpio.

## Alcance y validacion

- Esta actualizacion modifica exclusivamente
  `docs/HANDOFFS/ACTIVE_HANDOFF.md`.
- No cambia decisiones funcionales ni declara implementados REQ-001 o REQ-002.
- Tests de aplicacion: NO EJECUTADOS - no aplican al alcance documental.
- No se ejecutaron migraciones ni la aplicacion.
- No se realizo commit, push, Pull Request ni merge como parte de esta
  actualizacion.

## Proximo paso

Transferir el analisis a `02 - Implementacion y Refinacion` para preparar el
plan tecnico por fases de REQ-001 y REQ-002. Esta transferencia no autoriza
todavia implementacion, cambios de codigo, migraciones, seleccion de
proveedores ni decisiones funcionales adicionales.

## Restricciones vigentes

- No asumir que PRO o Facturacion MVP ya estan implementados.
- No iniciar implementacion sin autorizacion expresa.
- No seleccionar PSP, integracion fiscal o proveedor de IA sin evaluacion y
  aprobacion.
- No realizar commit, push, PR o merge durante este cierre local.
