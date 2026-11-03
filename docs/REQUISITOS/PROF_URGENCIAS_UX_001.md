# PROF-URGENCIAS-UX-001 — Urgencias en el espacio profesional

Registro: 2026-10-14T19:05:14-03:00. Responsable: implementador local. Dispositivo: laptop.
Estado: READY_TO_RESUME; implementado según informe local, revisión visual y testing independiente pendientes.
Boceto de escritorio aprobado por Cristian: 2026-10-14T18:27:41-03:00.
Rama inicial/final: `feature/professional-workspace-ux`.
HEAD inicial/final: `2e552f2fdc57c152c97f0486050574696f6b250e`.
Origin: https://github.com/cristhian-star/TRAX-PLATFORM.git.

## Alcance y precedencia

Presentación privada, sin habilitación del dominio pendiente. Reutiliza shell,
logos, navegación móvil, tema y campanita de PROF-UX-001. No cambia AUTH, PRO,
contratación, clientes, modelos, dependencias o migraciones. Las decisiones de
Producto de este encargo prevalecen sobre antecedentes incompatibles de REQ-004,
ADR-002 y diseño temporal; su aprobación no habilita operaciones técnicas ni
condiciones jurídicas. Esos documentos históricos no se reescribieron.

Ruta GET: `/profesional/oportunidades/urgencias`, protegida por role_required con
cuenta activa y rol PROFESIONAL persistido. Secciones por `vista=solicitudes`,
`vista=guardias`, `vista=actividad`. Valores repetidos/invalidos: 400; solicitud=id:
404 sin consulta de registros; POST: 405. La ruta no tiene efectos de negocio.
URL para Cristian tras reconstruir web: http://127.0.0.1:5050/profesional/oportunidades/urgencias

La composición conserva la navegación, resumen superior, pestañas y dos columnas
en escritorio. Sin bandeja autorizada, la columna izquierda indica recepción
pendiente y la derecha explica las cinco etapas previstas. En móvil se apilan,
con anclas para ir y volver. No se copian solicitudes, nombres, fechas o contadores
del boceto ni se presenta una integración inexistente como cero resultados.
No hay filtro pendientes/respondidas, CTA Ver urgencia ni respuesta WhatsApp
ficticios. No se renderizan estados cancelados de registros sin autorización.
Presupuestos/Propuestas enlazan a secciones privadas reales de Oportunidades;
se separan visualmente las publicaciones existentes sin cambiar sus consultas.

## Matriz de capacidades y evidencia

| Capacidad | Evidencia actual | Conexión en este incremento |
| --- | --- | --- |
| Shell y datos propios | professional_workspace_service.build_workspace; professional_workspace_base.html | Reutilizados, sin cambiar servicio ni panel de notificaciones. |
| Solicitud legacy | emergency_request.py:6,22–29: cliente_id, texto y estado, sin destinatario profesional | No se consulta ni expone. |
| Lista global legacy | emergency_service.py:get_active_emergencies, sin filtro de destinatario | No se utiliza como inbox. |
| Asignación legacy | emergency_service.py:assign_professional comprueba hasattr; modelo sin professional_id | No acredita asignación operativa; no se conecta. |
| Entrada pública manual | operation_routes.py /urgencias/nueva y /urgencias/directorio; entry_errors bloquea difusión | Intacta. No se convierte en recepción profesional. |
| Turnos | emergency_shift_service.py:plan_shift/plan_shifts, lógica pura | Se reutilizan constantes y zona; consulta de bloques sin llamar accepted=True ni reservar. |
| Reservas y recordatorios | No modelo/endpoints operativos de reservas encontrados | Pendiente; no se afirman turnos activos ni próximos. |
| Contratos | contract_request admite SOURCE_EMERGENCY; contracting_core_service materializa BUDGET/PROPOSAL | No acredita flujo bilateral de urgencia. Mis trabajos conserva contratos propios; no se crean ni enlazan urgencias por inferencia. |
| WhatsApp IA / llamadas | Sin flujo autorizado de respuesta para este inbox | Pendiente; sin mensajes ni enlaces de contacto inventados. |
| Historial / restricciones | Sin historial operativo de guardias y sanciones | Sección informativa pendiente, sin contadores ficticios. |

## Fechas y resiliencia

Mis guardias ofrece consulta GET de fecha si existe ZoneInfo de Buenos Aires:
bloques de doce horas con instantes aware, nocturno termina al día siguiente.
Fecha ISO estricta, sin duplicados de parámetro, no permite date.max que desborde.
Es consulta de horarios, no selección o reserva de múltiples bloques. No guarda
estado local ni aceptación. La reserva real y su compromiso siguen pendientes.

En este Python Windows falta tzdata/IANA: antes producía ZoneInfoNotFoundError.
Ahora la vista muestra error recuperable y Reintentar consulta, con horarios
nominales explícitos; no inventa fecha local ni usa offset fijo en producción.
No se instaló nada. La prueba de fechas usa un offset explícito como fixture,
no acredita disponibilidad IANA del entorno. El despliegue deberá proveer los
datos IANA existentes en su plataforma. GET inválido y excepciones conservan
las páginas de error seguras generales. No hay carga asíncrona nueva.

## Reglas aprobadas y pendientes conservados

La siguiente transcripción corresponde al encargo aprobado; no describe funciones
activadas. Se conserva el texto para trazabilidad y no constituye asesoría legal.

## 6. Reglas de producto para documentar

Estas decisiones orientan la interfaz y el futuro desarrollo. Su aprobación de producto no equivale a habilitación técnica ni jurídica de operaciones pendientes.

### Guardias

* Turnos de doce horas: diurno 07:00–19:00; nocturno 19:00–07:00 del día siguiente.
* Presentación en `America/Argentina/Buenos_Aires`.
* Bloques futuros múltiples y consecutivos, sin duplicados.
* Reserva hasta dos minutos antes del inicio inclusive; sin incorporación a un turno iniciado.
* Aceptación expresa del compromiso.
* Recordatorios de reserva previstos a seis horas y una hora, solamente cuando aún corresponden; sin avisos retroactivos.

El compromiso es mantenerse localizable y responder. No obliga a aceptar todos los servicios. Un rechazo justificado no genera apercibimiento.

No existe estado “ocupado”: puede seguir recibiendo convocatorias y responder que no está disponible, indicando el motivo.

### Recepción y respuesta

* Difusión inicial a todos los profesionales elegibles con guardia vigente, compatibles con rubro y zona.
* Sin prioridad por suscripción PRO.
* Si nadie responde, el cliente puede elegir ampliar la zona, con advertencia sobre posibles mayores costos de traslado.
* La búsqueda manual permite elegir un profesional específico.
* El cliente elige entre quienes respondieron disponibles.
* El profesional elegido también confirma; no hay asignación automática al primero que responda.

Las respuestas futuras se gestionarán mediante un bot de WhatsApp con IA: “Estoy disponible” o “No puedo atender”, con motivo.

Secuencia aprobada, contada desde el primer mensaje:

* WhatsApp: minutos 0, 1 y 2.
* Llamadas telefónicas comunes: minutos 5, 7 y 9.

La primera llamada comienza tres minutos después del último mensaje. Los avisos pendientes se detienen cuando responde el profesional, se cancela la solicitud o el servicio queda confirmado con otro profesional.

Estas cifras son distintas de los límites técnicos contra abuso. No implementes comunicaciones reales en este incremento.

### Visita, diagnóstico y reparación

* Precio acordado libremente entre las partes.
* El profesional puede cobrar traslado o traslado más diagnóstico, informando qué incluye.
* Puede proponer pago antes del viaje o al concurrir al domicilio.
* Ambos confirman el servicio, el importe y la modalidad.
* El importe confirmado no aumenta unilateralmente.
* Los pagos futuros deberán realizarse mediante MANDOBRA.
* La reparación se presupuesta después del diagnóstico y requiere aceptación separada.
* Se prevé fotografía de la entrada como evidencia de llegada.
* Si el profesional no concurre, se aprobó devolver íntegramente el pago inicial.
* La inasistencia justificada no genera apercibimiento; la injustificada corresponde al nivel 2.

La validación de fotografías, las condiciones contractuales y el tratamiento de prestaciones realizadas requieren definición posterior.

### Apercibimientos

| Nivel | Incumplimiento                            | Umbral            | Suspensión           |
| ----- | ----------------------------------------- | ----------------- | -------------------- |
| 1     | Falta de respuesta injustificada          | 3 apercibimientos | 15 días de Urgencias |
| 2     | Aceptar y no concurrir injustificadamente | 2 apercibimientos | Un mes de Urgencias  |

* Ambas sanciones afectan únicamente Urgencias.
* La cuenta y los demás módulos siguen disponibles.
* Una suscripción paga no evita la sanción.
* Cada apercibimiento cuenta durante 90 días desde el incumplimiento.
* Después deja de acumular y conserva su registro histórico.
* Al cumplir una suspensión se reinicia el contador del nivel que la originó.
* Nivel 1: máximo un apercibimiento por guardia de doce horas.

Motivos justificados aprobados: clima adverso, inundaciones o alertas climáticas; lesión o imprevisto durante el viaje; estar atendiendo otra urgencia que impida asumir un servicio nuevo. Los fallos técnicos no se atribuyen al profesional.

Documentá estas reglas sin activar sanciones.

## 7. Pendientes que deben conservarse explícitos

* Revisión jurídica de términos, privacidad, consentimientos y sanciones.
* Cancelaciones del cliente y devoluciones: la propuesta de devolución antes del viaje y el cargo durante el traslado no están cerrados.
* Desglose obligatorio o combinado de traslado y diagnóstico.
* Cómputo de “un mes”: calendario o cantidad fija de días.
* Cancelación o modificación de guardias.
* Reservas y servicios ya comprometidos cuando comienza una suspensión.
* Fin de guardia durante una secuencia de avisos.
* Justificación, revisión e impugnación de apercibimientos.
* Acceso, validación y conservación de evidencias de llegada.
* Efectos de una suspensión sobre la suscripción.
* Integración contractual, comunicaciones y pagos.

No resuelvas estos puntos mediante supuestos silenciosos.


## Validaciones de esta sesión

Comando Python (SQLite en memoria, usuarios sintéticos, sin Docker):

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:DATABASE_URL='sqlite:///:memory:'
.venv/Scripts/python.exe -m unittest tests.test_professional_urgencies_ux tests.test_emergency_shift_service tests.test_professional_workspace_ux tests.test_emergency_entry tests.test_loading_error_states -q
node --test tests/js/professional_notifications.test.js tests/js/auth_ux.test.js
```

65 tests descubiertos: 64 aprobados y 1 omitido (gate IANA existente sin datos
locales). Siete tests nuevos de este incremento. Node: 3 comprobaciones aprobadas
(archivo AUTH y dos tests de notificaciones). Logs ERROR intencionales de tests de
manejo de errores; no fallos. No se suman pruebas de sesiones previas. Sintaxis
Python AST, UTF-8 sin BOM/NUL/U+FFFD y diff-check correctos.

QA Chrome aislado en 54932: Solicitudes en 320,390,768,1024,1440, claro y oscuro,
sin overflow horizontal; campana Enter/Escape, cambio de tema y sección Guardias
con error recuperable comprobados. Capturas representativas válidas: escritorio
claro y móvil oscuro fuera del repo. La captura etiquetada escritorio oscuro
quedó desfasada durante el cambio de viewport: no se utiliza como evidencia.
Captura full-page falló por timeout; se usó viewport.
La sesión de navegador se desconectó durante el chequeo final de foco/no-JS:
no se acredita esa comprobación. Contenido y navegación son HTML/GET nativos,
sin nuevo JS. Reduced motion inspeccionado estáticamente, sin emulación real.
Pendiente: matriz completa de Guardias/Actividad, interacción de fecha con IANA
real, QA íntegro sin JS, lector de pantalla y testing independiente. No se declara
AA integral ni aprobación de Producto. Preview propio detenido al cierre.

## Inventario y conservación

Modificados sobre trabajo preexistente:
- app/routes/main_routes.py: solo ruta GET nueva.
- app/templates/professional_workspace_base.html: estado activo de Oportunidades en subruta.
- app/templates/professional_opportunities.html: subnavegación y anclas de fuentes reales.
- docs/HANDOFFS/ACTIVE_HANDOFF.md: entrada nueva, antecedentes preservados.

Nuevos:
- app/services/professional_urgencies_view_service.py
- app/templates/components/_professional_opportunity_nav.html
- app/templates/professional_urgencies.html
- app/static/css/professional-urgencies.css
- tests/test_professional_urgencies_ux.py
- docs/REQUISITOS/PROF_URGENCIAS_UX_001.md

Hashes previos de archivos de app registrados fuera del repo; solo tres archivos
preexistentes de app cambiaron, los enumerados arriba. Trabajo previo de INDEX
preservado SHA256 46400cbd6de53ddabc3f535fec46cc1d901f17a1ed2001c6c5e1916041acd7a0.
Estado final: 24 paths del trabajo acumulado más INDEX previo; staging vacío.
Sin commit, push, PR, merge ni fetch. No administración Docker ni bases compartidas.
Próximo paso: revisión visual de Cristian en 5050 y retest independiente antes
de autorizar integración. No crear reservas, contratos, comunicaciones, pagos ni
sanciones para completar el boceto. Sin sincronización remota en esta sesión.


## Solicitudes y calendario semanal A — 2026-10-25

Registro: 2026-10-25T15:10:43-03:00. Responsable: Codex local, laptop. Estado: READY_TO_RESUME.
Bocetos seleccionados por Cristian el 2026-10-25: bandeja de Solicitudes y calendario semanal A.
La selección de bocetos no es aprobación visual de esta implementación.

### Alcance y conexiones comprobadas

Ruta conservada: `/profesional/oportunidades/urgencias`, con `vista=solicitudes`, `guardias`
y `actividad`. Sin selector superior Presupuestos/Urgencias/Propuestas; shell, notificaciones,
permisos persistidos y pestañas internas con aria-current conservados. Mi actividad y condiciones
conserva destino y contenido; no se incorpora un detalle profesional no autorizado.

- Operativo: navegación privada, consulta semanal de fechas y bloques, selección provisoria local
  en controles nativos, resumen progresivo con JavaScript, aceptación inicialmente desmarcada.
- Reservas y consulta de guardias programadas/en curso: todavía no habilitadas. El planificador
  puro `emergency_shift_service.py` no persiste reservas. No hay modelo de guardia en `app/models`.
- Recepción profesional: todavía no habilitada. `EmergencyRequest.cliente_id` acredita propietario
  cliente; no existe vínculo de convocatoria/autorización profesional. No se consulta esa tabla
  desde esta vista, ni se usa rubro/zona para revelar solicitudes privadas.
- La bandeja respeta composición de panel principal y lateral, pero muestra disponibilidad pendiente
  en lugar de tarjetas ficticias o un vacío que sugiera una recepción operativa. Sin CTA Ver solicitud
  inventado. No se fabrican estados de guardia activa o programada.

Calendario lunes–domingo calculado; diurna 07:00–19:00 y nocturna 19:00–07:00 siguiente.
Zona IANA Buenos Aires, reloj de servidor y corte inclusivo T−2 minutos, sin redondeo; bloques fuera
de plazo deshabilitados. Fechas extremas que desbordan la semana se rechazan con 400.
Se conservan las reglas vigentes de REQ-004/ADR-002 de 2026-10-01; las duraciones libres y la
activación inmediata históricas no se implementan. No cancelación, recurrencia ni modificación.
La selección no usa sesión, localStorage, requests ni persistencia; jamás confirma reservas.
El botón de reserva siempre está deshabilitado. Cambiar selección reinicia aceptación con JS;
sin JS siguen operativos selección nativa y enlaces semanales, con aviso de resumen no automático.

Desktop: siete columnas con bloques diurnos/nocturnos y resumen lateral desde 1280 px.
Entre 768 y 1279 px el resumen pasa debajo; móvil muestra lista por día. Tokens existentes,
CSS del módulo, estados seleccionados distinguibles por checkbox y texto, foco y ambos temas.

### Inventario de este incremento

- `app/services/professional_urgencies_view_service.py`: semana, fechas, corte y límites.
- `app/templates/professional_urgencies.html`: bandeja pendiente, calendario y resumen.
- `app/static/css/professional-urgencies.css`: composición responsive encapsulada.
- `app/static/js/professional-shifts.js` (nuevo): resumen sin persistencia ni operaciones.
- `tests/test_professional_urgencies_ux.py`: expectativas y borde temporal semanal.
- `tests/js/professional_shifts.test.js` (nuevo): controlador productivo real.
- `docs/REQUISITOS/PROF_URGENCIAS_UX_001.md`, `docs/HANDOFFS/ACTIVE_HANDOFF.md`, `docs/CHANGELOG.md`.

### Verificaciones ejecutadas y límites

SQLite en memoria, datos sintéticos, sin Docker ni bases compartidas:

```text
.venv/Scripts/python.exe -m unittest tests.test_professional_urgencies_ux tests.test_emergency_shift_service tests.test_urgency_workflow tests.test_professional_workspace_ux_002 -q
node tests/js/professional_shifts.test.js
node --check app/static/js/professional-shifts.js
```

Python: 36 casos, **35 aprobados y uno omitido** por falta de IANA en esta laptop.
Incluye roles persistidos, privacidad, GET sin commit, POST 405, fechas inválidas, medianoche,
T−2 exacto y microsegundo posterior, contacto protegido y regresiones del espacio profesional.
Node: controlador real aprobado (selección múltiple, texto seguro, deselección, exclusión de
bloques deshabilitados, reinicio de aceptación y página sin calendario). Sintaxis Python/JS,
UTF-8 sin BOM/NUL/U+FFFD y diff check comprobados. No suite completa ni PostgreSQL.
La primera ejecución detectó un argumento incorrecto de MultiDict en el test nuevo y un mensaje
pendiente ausente en el fallback IANA; ambos corregidos antes del resultado final.

Chrome real: **40 combinaciones de página** = dos vistas × cinco anchos (320/390/768/1024/1440)
× claro/oscuro × JS activo/deshabilitado realmente. Capturas, sin overflow, selección nativa por
teclado, resumen con JS, aceptación desmarcada y reserva siempre deshabilitada. Cuatro chequeos
adicionales de texto largo, foco y prefers-reduced-motion emulado en 320/1440, ambos temas.
No se contabiliza la repetición de la matriz tras acortar la etiqueta Elegido como cobertura nueva.
Preview descartable usó explícitamente UTC−03:00 como fixture temporal: no prueba disponibilidad
IANA productiva. Sin IANA real la página muestra error recuperable, no un calendario inventado.
Los temas se fijaron desde el driver; no es retest del switch global. No auditoría AA integral,
móvil físico ni validación integral de consola/CSP heredada.

[Evidencias y capturas](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/urgencias-calendario/):
`baseline.json`, `tests.log`, `browser-results.json`, `long-focus.json`, capturas solicitudes/guardias
por ancho/tema/JS, scripts de preview y QA aislados, `integrity-final.json`.
Playwright no tenía Chromium bundled y el sandbox bloqueaba localhost; se usó Chrome instalado y
preview/driver autorizados fuera del sandbox. Sin instalaciones ni cambios de configuración productiva.

Identidad conservada: `feature/professional-workspace-ux`, HEAD
`2e552f2fdc57c152c97f0486050574696f6b250e`, staging vacío; 75 paths iniciales y 77 finales.
INDEX, Presupuestos y todos los archivos ajenos preservados por SHA-256. Sin modelos, migraciones,
dependencias ni Git mutable. Reservas, recepción autorizada y consulta personal requieren otro
incremento de dominio; este cambio no habilita difusión, bot, pagos ni contratación urgente.

INTERFACES IMPLEMENTADAS LOCALMENTE; PENDIENTES DE REVISIÓN VISUAL Y TESTING INDEPENDIENTE.


## Cierre técnico independiente — Solicitudes y Mis guardias

Registro documental: **2026-10-25T15:46:39-03:00**. Responsable: Codex local, laptop.
Dictamen independiente recibido: **2026-10-25T15:40:22-03:00**.
**VERIFICADO EN EL ALCANCE EVALUADO**. Ningún hallazgo P0–P3.

- Python: primera corrida con **35 aprobadas y una omitida por falta de IANA**.
  Ejecución posterior del caso omitido aprobada con **IANA real en otro runtime**.
  Total: **36 casos únicos satisfactorios entre ambos entornos**, no 36 ejecutados en el entorno original.
- Controlador JavaScript aprobado.
- Navegador: **40/40 combinaciones aprobadas**.
- Sin escrituras ni efectos operativos.

La ejecución alternativa resolvió la cobertura del caso IANA, pero **no modificó el entorno
Python del proyecto**. La limitación local de disponibilidad IANA y su fallback recuperable
siguen vigentes. Estos resultados pertenecen al dictamen independiente: no se realizaron
nuevas ejecuciones de pruebas en esta sesión ni se suman repeticiones como cobertura adicional.

[Evidencia independiente existente](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/prof-urgencias-independent-qa/):
`browser-results.json`, capturas y verificaciones de navegación semanal y movimiento reducido/textos largos.
La carpeta fue localizada y se conserva sin modificaciones.

Alcance cerrado técnicamente: interfaces informativas y selección provisional; **reservas
deshabilitadas**. No se declara recepción profesional, backend de reservas, PostgreSQL validado,
certificación AA ni habilitación productiva. Se conservan los antecedentes, la CSP heredada y
la limitación de móvil físico. La **aprobación visual de Cristian continúa pendiente**; seleccionar
los bocetos no equivale a aprobar visualmente su implementación. No integración ni despliegue.

Identidad inicial/final: rama `feature/professional-workspace-ux`, HEAD
`2e552f2fdc57c152c97f0486050574696f6b250e`, **77 paths pendientes y staging vacío**.
Actualización limitada a esta especificación, `docs/HANDOFFS/ACTIVE_HANDOFF.md` y `docs/CHANGELOG.md`.
Todos los restantes archivos, incluido INDEX, preservados por SHA-256. UTF-8 y `git diff --check`
verificados. Sin cambios productivos, nuevas pruebas, Docker, dependencias, bases ni operaciones
Git mutables. Próximo paso: revisión visual de Cristian dentro del alcance informativo implementado.


## Guardias persistentes — primera entrega operativa

Registro: **2026-10-26T20:26:49-03:00**. Responsable: Codex local, laptop. Autorización de Cristian del
**2026-10-26**: amplía expresamente el incremento visual a persistencia, migración y operaciones.
Los cierres independientes anteriores permanecen como antecedentes del alcance informativo;
no certifican esta entrega nueva. Revisión visual de Cristian y testing independiente pendientes.

### Recorrido y reglas implementadas

La factory ordinaria registra los modelos y el despachador. En una base migrada, el calendario
`/profesional/oportunidades/urgencias?vista=guardias` permite confirmar de 1 a 14 bloques mediante
`POST /profesional/guardias/reservar`, con CSRF, clave firmada ligada al actor y aceptación expresa.
El éxito se devuelve después del commit. El mismo recorrido funciona sin JavaScript; las
reservas no dependen de sesión, localStorage ni de mantener abierta la página. GET no escribe.

Se reutiliza el planificador aprobado: Buenos Aires IANA, diurna 07–19, nocturna 19–07 del día
siguiente, UTC persistido, reserva hasta T−2 minutos inclusive y vigencia [inicio, fin).
Estados derivados: selección provisional, programada, en curso, finalizada e invalidada.
El servidor deriva horarios y propietario; no acepta esos datos como autoridad del formulario.
No se permite cancelación o modificación manual ni recurrencia o duración libre.

Elegibilidad: cuenta activa PROFESIONAL, perfil completo y VERIFICADO, verificación de tipo
PROFESIONAL en estado `APROBADO` (nombre del enum actual), oficio y cobertura no vacíos, sin
caracteres de control y dentro de los límites actuales. PRO no concede habilitación.
No se amplía el proceso previo de verificación: la aprobación de una VerificationRequest por sí
sola no sustituye el requisito separado de estado VERIFICADO del perfil.

Se conservan selección válida y mensajes recuperables ante errores; la aceptación vuelve
sin marcar. Una clave inválida requiere recargar el formulario. La respuesta de éxito es HTML
200; reenviar o refrescar se protege mediante replay durable. Límites: 10/minuto y 30/día por
actor, utilizando el limiter existente; su backend en memoria no acredita límites distribuidos.

### Persistencia, concurrencia y efectos

Migración nueva `20261026_01`, descendiente del head real `20260917_03`. Crea solamente
`emergency_shifts` y `emergency_shift_reminders`, sin activar guardias para usuarios existentes.
La primera tabla tiene FK de profesional, unicidad profesional/día/tipo y constraints de tipo,
coherencia temporal y versión. La segunda tiene FK de guardia y unicidad guardia/tipo de aviso.

Se reutiliza `OperationCommand` con operación `EMERGENCY_SHIFT_RESERVE`, hash del contenido y
resultado original durable en AuditLog (versión 1). Autorización precede al replay. Misma clave
con otro contenido produce conflicto; misma intención no repite guardias, auditorías o avisos.
Lote, comando, auditoría y notificación interna de confirmación comparten una única transacción.
Un conflicto parcial o excepción revierte todo el lote. Los locks toman primero User y luego
Professional; reserva, escritores de habilitación y despachador comparten ese orden.
El despachador toma después guardia y recordatorio. Las constraints refuerzan la exclusión.

Suspensión, ban, cambio de rol, revocación de verificación profesional y actualización del
perfil por los servicios actuales invalidan bloques actuales/futuros cuyo fin aún no pasó,
aumentan versión, auditan y omiten recordatorios pendientes en la misma transacción del cambio.
Restaurar habilitación no resucita esas reservas. El escritor de perfil ya restablecía
PENDIENTE_VERIFICACION: se conserva esa regla y se invalidan sus guardias vigentes/futuras.
No se promete interceptar modificaciones SQL externas que eludan los servicios de la aplicación.

### IANA y recordatorios internos

`tzdata==2025.2` declarado en requirements e instalado en el entorno Python del proyecto.
IANA real comprobada allí y en un contenedor Python 3.12 slim descartable; Dockerfile existente
instala requirements. Esta entrega sí resuelve la dependencia local que el retest histórico
había cubierto mediante otro runtime. Sin offset fijo silencioso.

T−6 h y T−1 h se programan de forma persistente al reservar, excluyendo offsets ya pasados.
El despachador procesa hasta 100 pendientes por invocación. T−6 puede entregarse desde su
instante hasta T−1 exclusivo; T−1 hasta el inicio exclusivo. Fuera de ventana o sin elegibilidad,
marca SKIPPED. Aviso interno y estado SENT se confirman juntos, sin duplicación concurrente.
No hay proveedores externos ni nueva cola. La expiración de la guardia no requiere despachador.

**Operación pendiente:** configurar una invocación cada minuto en el entorno que se habilite.
Windows: tarea programada con directorio del repositorio, ejecutable de su venv, entorno y usuario
controlados. Linux/Docker: temporizador/cron del operador, ejecutando el mismo comando dentro del
servicio web ya migrado. No se instaló ningún scheduler ni se administró el Docker habitual.
Supervisar errores y pendientes; con más de 100 vencimientos por minuto, dimensionar la frecuencia
antes de habilitar volumen productivo. Comando manual probado en la base exclusiva:

```powershell
.venv/Scripts/python.exe -m flask --app 'app:create_app(initialize_schema=False)' dispatch-shift-reminders
```

### Actualización posterior de la plataforma (no ejecutada)

Con autorización del operador, respaldo y DATABASE_URL comprobada para el destino elegido,
instalar requirements en el runtime habitual y aplicar la migración. No reutilizar la URL
sintética de QA ni ejecutar estos pasos contra una base compartida sin autorización:

```powershell
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m alembic current
.venv/Scripts/python.exe -m alembic heads
.venv/Scripts/python.exe -m alembic upgrade 20261026_01
.venv/Scripts/python.exe -m alembic current
```

Head esperado posterior: `20261026_01`. Para Docker, reconstruir el runtime mediante el proceso
habitual autorizado para incorporar requirements; luego migrar y programar el comando anterior.
La reversión `downgrade 20260917_03` se probó únicamente en PostgreSQL descartable: elimina las
dos tablas nuevas y sus reservas/avisos, no borra comandos/auditorías existentes. No es un rollback
sin pérdida de datos ni debe aplicarse a la plataforma sin respaldo y decisión explícita.

### Validaciones de esta entrega

- Python focal SQLite: **61/61**, con IANA real del proyecto. Comando: `python -m unittest tests.test_emergency_reservations tests.test_emergency_shift_service tests.test_professional_urgencies_ux tests.test_urgency_workflow tests.test_professional_workspace_ux tests.test_security_controls -q`.
- Reejecución posterior tras validar fechas extremas: **23/23** en los dos módulos de reservas/planificador, incluidos en los 61; no cobertura adicional.
- PostgreSQL 16 real exclusivo: **5/5** (`tests.test_emergency_reservations_postgres`, habilitado mediante GUARDIAS_QA_DATABASE_URL). Sesiones independientes: misma clave concurrente, claves distintas con bloques coincidentes, despacho concurrente, suspensión concurrente, rollback y lote parcialmente conflictivo. Relectura con factory recreada.
- Alembic: upgrade completo desde base vacía; downgrade de esta revisión y upgrade nuevamente correctos. CLI real ejecutado, sin pendientes en ese instante.
- Node: controlador productivo de calendario aprobado y notificaciones **2/2**. Sin modificaciones del JavaScript productivo.
- Chrome: **20 recorridos** (320/390/768/1024/1440 × claro/oscuro × JavaScript habilitado/deshabilitado), con reserva real, relectura, teclado, foco y sin overflow; movimiento reducido emulado.
- Dos recorridos adicionales de error 400, selección conservada y reenvío correcto: 320 claro sin JavaScript y 1440 oscuro con JavaScript. Controles alcanzados desplazando la página, sin clics forzados.
- Cierre de sesión/reingreso y reinicio real del proceso sin reseed: guardias conservadas.
- Sintaxis Python, UTF-8 y diff check comprobados al cierre. No suite completa, certificación AA integral ni dispositivo físico. CSP heredada no auditada en este incremento.

Evidencia durable: [guardias-persistentes](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/guardias-persistentes/), con `tests-final.log`,
`postgres-final.log`, `browser-results.json`, `errors.json`, `restart-check.json`, capturas
`selected-*`/`persisted-*`, baseline e integridad final. Son ejecuciones locales nuevas;
no sustituyen el dictamen independiente histórico ni constituyen aprobación independiente.
PostgreSQL exclusivo `mandobra-guardias-qa-20261026`, puerto 55479, creado para esta tarea;
no se usaron trax_db, bases/volúmenes previos ni migraciones de la plataforma habitual.

### Inventario del incremento y límites

Modificados respecto de la línea base de esta sesión:

- `app/__init__.py`: registro ordinario de modelos y CLI.
- `app/routes/main_routes.py`: consulta y POST protegido del calendario.
- `app/services/professional_urgencies_view_service.py`: reservas y estados reales del actor.
- `app/services/professional_service.py`, `user_service.py`, `verification_service.py`: invalidación transaccional con los escritores vigentes.
- `app/templates/professional_urgencies.html`: formulario nativo, permisos y estados persistidos.
- `requirements.txt`: IANA reproducible.
- `tests/test_professional_urgencies_ux.py`: expectativas del alcance operativo.
- Esta especificación, REQ-004, ADR-002, ACTIVE_HANDOFF y CHANGELOG: continuidad y operación.

Nuevos: `app/models/emergency_shift.py`, `app/services/emergency_reservation_service.py`,
`migrations/versions/20261026_01_emergency_shifts.py`, `tests/test_emergency_reservations.py`
y `tests/test_emergency_reservations_postgres.py`. Total: **19 archivos**, 14 existentes y 5 nuevos.

Identidad conservada: `feature/professional-workspace-ux`,
`2e552f2fdc57c152c97f0486050574696f6b250e`; 77 paths iniciales, 88 finales, staging vacío.
INDEX, Presupuestos y trabajo ajeno preservados por SHA-256. Sin commit, push, PR o merge.

Solicitudes continúa como recepción pendiente. No distribución, recepción profesional,
asignación, bot, pagos, contratación urgente ni rediseño de detalle/actividad. Operación habitual
requiere aplicar migración y configurar despachador mediante autorización posterior.
No se declara todo Urgencias operativo, integración ni habilitación productiva.

**GUARDIAS PERSISTENTES IMPLEMENTADAS LOCALMENTE; PENDIENTES DE REVISIÓN VISUAL Y TESTING INDEPENDIENTE.**


## Cierre técnico independiente — guardias persistentes

Registro documental: **2026-10-26T20:57:14-03:00**. Responsable: Codex local, laptop.
Dictamen independiente del **2026-10-26T20:51:36-03:00**:
**GUARDIAS PERSISTENTES — VERIFICADO EN EL ALCANCE EVALUADO.**
Sin hallazgos P0–P3.

- Python: **61/61**.
- PostgreSQL: **5/5**, incluyendo migración y concurrencia.
- Controlador Node aprobado y notificaciones **2/2**.
- Navegador: **20/20 combinaciones**.
- Persistencia tras reinicio, atomicidad, idempotencia, invalidación y recordatorios verificados.
- Alembic: head **20261026_01**, padre **20260917_03**.

Resultados del dictamen independiente, registrados sin nuevas ejecuciones de pruebas ni
recreación de evidencias. No se suman a las ejecuciones locales anteriores como casos adicionales.
[Evidencia independiente existente](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/guardias-persistentes-independent-qa-20261026/):
`python-focal.log`, `postgres-gate.log`, logs Alembic, `browser-independent-results.json`,
`restart-independent.json` y capturas. Carpeta localizada y consultada en modo lectura.

Este cierre técnico sustituye la condición de testing independiente pendiente de la entrega
anterior dentro del alcance evaluado; conserva todos los antecedentes y no constituye aprobación
visual de la implementación. Continúan pendientes la instalación/programación del scheduler,
la recepción profesional, el recorrido completo de Urgencias y la revisión visual del usuario.
Se mantienen las limitaciones de accesibilidad: sin certificación AA integral y sin validación
en dispositivo móvil físico; la CSP heredada no queda certificada por este cierre.

Las migraciones verificadas corresponden al entorno aislado de QA. **No hay evidencia en este
cierre de migración de la base habitual** y no se afirma que se haya realizado. No se declara
habilitación productiva, integración ni despliegue; cualquier operación posterior requiere su
autorización y verificación específica.

Identidad inicial/final conservada: `feature/professional-workspace-ux`, HEAD
`2e552f2fdc57c152c97f0486050574696f6b250e`, **88 paths pendientes y staging vacío**.
Sesión limitada a esta especificación, ACTIVE_HANDOFF y CHANGELOG. Los demás archivos,
incluidos INDEX y Presupuestos, preservados por SHA-256. UTF-8 y `git diff --check` verificados.
Sin cambios productivos, nuevas pruebas, Docker, migraciones, dependencias, bases ni operaciones
Git mutables. Commit, push, PR y merge no ejecutados por estar fuera del alcance autorizado.


## Cuatro semanas de guardias y simplificación de pestañas

Registro: **2026-10-26T21:37:42-03:00**. Decisión de Producto: Cristian, 2026-10-26.
Estado: implementado localmente; pendiente de revisión visual y testing independiente.
Este incremento complementa el cierre técnico independiente de guardias persistentes del
2026-10-26T20:51:36-03:00; no reemplaza sus evidencias ni extiende su dictamen al código nuevo.

### Intervalo único y comportamiento

`reservation_window(now)` centraliza el intervalo por fecha local de inicio: lunes de la semana
actual en America/Argentina/Buenos_Aires inclusivo, lunes de cuatro semanas después exclusivo.
Calendario, navegación y nuevas confirmaciones usan ese intervalo. Cambia automáticamente con
el reloj del servidor al comenzar el lunes local (03:00 UTC con las reglas IANA actuales).
Ejemplo del 26/10/2026: semanas del 26/10, 02/11, 09/11 y 16/11; último inicio permitido 22/11.
La nocturna de ese domingo termina el lunes 23/11 a las 07:00. Los bloques vencidos de la semana
actual permanecen visibles y no seleccionables; se conserva T−2 minutos inclusive.

GET fuera del intervalo redirige 302 a la semana permitida más cercana mediante el endpoint
canónico, sin escrituras. Se conserva el rechazo 400 de fechas inválidas/repetidas y extremos
ISO rechazados por el contrato anterior. Anterior/Siguiente usan botones nativos disabled en
los extremos, sin enlaces ni foco alcanzable; no dependen de JavaScript.

POST valida el rango después de adquirir los locks y resolver un posible replay autorizado;
el mismo instante efectivo alimenta rango y planificador temporal. Lotes con cualquier bloque
fuera del intervalo devuelven validación 400 y rollback sin efectos parciales. Se recalcula el
contexto de presentación tras el resultado para formularios abiertos al cambiar de semana.
Un comando anterior válido devuelve su resultado durable sin aplicar retroactivamente la nueva
restricción. No se borran ni invalidan reservas previas por quedar fuera de la ventana. Sus
registros e historial persisten; el calendario solo muestra las cuatro semanas permitidas.

El bloque común «Tu presencia en la búsqueda manual», su descripción y ambos enlaces se retiró
del template. Solicitudes conserva «Tu guardia», su estado real y «Ver mis guardias»; recepción
pendiente, pestañas, navegación general y «Mi actividad y condiciones» conservados.
Solo CSS encapsulado para el control semanal deshabilitado; sin cambios globales.

### Inventario atribuible a esta sesión

- `app/services/emergency_shift_service.py`: intervalo compartido.
- `app/services/emergency_reservation_service.py`: comprobación transaccional posterior al replay.
- `app/services/professional_urgencies_view_service.py`: semanas acotadas, extremos y fecha canónica.
- `app/routes/main_routes.py`: redirección GET y contexto POST actualizado.
- `app/templates/professional_urgencies.html`: controles nativos, texto del alcance y retiro del bloque.
- `app/static/css/professional-urgencies.css`: presentación de extremos deshabilitados.
- `tests/test_emergency_reservation_window.py` (nuevo): seis regresiones del intervalo, HTTP y replay.
- `tests/test_emergency_reservations.py`, `tests/test_emergency_reservations_postgres.py`,
  `tests/test_professional_urgencies_ux.py`: relojes controlados, cobertura temporal conservada y
  regresión PostgreSQL adicional de lote fuera del intervalo/replay.
- `tests/test_urgency_workflow.py`: ausencia de enlace retirado, conservando la recepción pendiente.
- Esta especificación, REQ-004, ACTIVE_HANDOFF y CHANGELOG: decisión y trazabilidad.

Total **15 archivos: 14 existentes y uno nuevo**. Sin migraciones/dependencias nuevas.
Head Alembic declarado por los archivos conservado: `20261026_01`, padre `20260917_03`.

### Validación ejecutada

- Python focal **67/67**, sin omisiones: `python -m unittest tests.test_emergency_reservation_window tests.test_emergency_reservations tests.test_emergency_shift_service tests.test_professional_urgencies_ux tests.test_urgency_workflow tests.test_professional_workspace_ux tests.test_security_controls -q`.
- Tras retirar completamente el bloque común del template, repetición de **14/14** casos de ventana/interfaz ya incluidos; no sumar como cobertura nueva.
- PostgreSQL 16 descartable **6/6**: `python -m unittest tests.test_emergency_reservations_postgres -q`, con GUARDIAS_QA_DATABASE_URL exclusivo. Incluye lote fuera de ambos extremos sin persistencia parcial, replay con registros fuera del intervalo y regresiones concurrentes existentes. Migraciones existentes aplicadas solo a esta base vacía.
- Node: controlador productivo de calendario aprobado y notificaciones **2/2**; `node --test tests/js/professional_shifts.test.js tests/js/professional_notifications.test.js`.
- Chrome: **20 recorridos / 40 combinaciones de pestaña**, cinco anchos 320/390/768/1024/1440, claro/oscuro, JavaScript habilitado y realmente deshabilitado. Navegación ida/vuelta, extremos disabled, teclado/foco, confirmación y relectura de última nocturna; sin overflow. Movimiento reducido emulado.
- Temas aplicados por el driver y comprobados mediante carga completa/color computado; sin JavaScript, se aplica la clase temática desde la automatización, sin habilitar scripts de la aplicación. La primera ejecución del driver tenía una carrera con el controlador de tema; se corrigió y repitió la matriz. Solo la matriz final y sus capturas sustentan ambos temas.
- Primera ejecución Python: dos errores de construcción de MultiDict en las nuevas pruebas; corregidos y repetición completa 67/67. No se atribuyen a código preexistente.
- Sintaxis Python, UTF-8 sin BOM/NUL/U+FFFD y `git diff --check` verificados al cierre. Sin certificación AA integral, móvil físico ni ejecución de suite completa.

[Evidencia de esta sesión](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/guardias-cuatro-semanas/):
`baseline.json`, `python-final.log`, `template-final.log`, `postgres.log`, `migration.log`,
`browser-results.json`, capturas `solicitudes-*`, `primera-*`, `ultima-*` e integridad final.

Preview 54960 y PostgreSQL exclusivo `mandobra-window-qa-20261026`/55479 detenidos y retirado
el contenedor descartable al finalizar. Docker de revisión mandobra_stabilization conservado
funcionando con los mismos contenedores; su base habitual y la cuenta QA no fueron consultadas
ni modificadas en esta sesión. Sin reservas sobre ese entorno.

### Actualización manual de web (comandos entregados, no ejecutados)

Desde la raíz del repositorio, por Cristian, para reconstruir únicamente la imagen de web y
actualizar solamente ese servicio, sin ejecutar dependencias, seed ni migrate:

```powershell
docker compose --env-file .env.example -p mandobra_stabilization -f docker-compose.stabilization.yml build web
docker compose --env-file .env.example -p mandobra_stabilization -f docker-compose.stabilization.yml up -d --no-deps web
```

No requiere nueva migración. Ruta de revisión tras actualizar web:
`/profesional/oportunidades/urgencias?vista=guardias`; Solicitudes en el mismo endpoint sin vista.
No se ejecutaron estos comandos ni se interrumpió el Docker de revisión.

Identidad conservada: `feature/professional-workspace-ux`, HEAD
`2e552f2fdc57c152c97f0486050574696f6b250e`; 88 paths iniciales, 90 finales, staging vacío.
INDEX, Presupuestos y resto del trabajo ajeno preservados por SHA-256. Sin Git mutable.
Continúan pendientes revisión visual/QA independiente de este ajuste, scheduler, recepción
profesional y recorrido completo de Urgencias. No habilitación productiva ni integración.

**AJUSTES IMPLEMENTADOS LOCALMENTE; PENDIENTES DE REVISIÓN VISUAL Y TESTING INDEPENDIENTE.**


## Liberación de guardias — 2026-10-26T22:41:47-03:00

Decisión de Cristian: sustituye el pendiente anterior de liberación únicamente para
una guardia propia programada. Se admite cuando faltan **más de 12 horas**; a T−12
exacto queda bloqueada. No se habilitan cancelaciones de acuerdos con clientes.
La reserva conserva T−2 minutos inclusive. Antes de confirmar se advierte siempre
que un turno dentro de las últimas 12 horas ya no admite liberación.
La decisión posterior sustituye la respuesta previa sobre volver a reservar:
**volver a reservar un bloque liberado queda fuera de este incremento**.

Implementación local: POST protegido por rol persistido, elegibilidad, ownership,
CSRF y rate limit; clave firmada por actor/guardia/versión. Locks usuario → perfil →
guardia y reloj efectivo posterior al bloqueo. `OperationCommand` y auditoría
`EMERGENCY_SHIFT_RELEASE` hacen el replay idempotente. `invalidated_at` retira la
guardia de la disponibilidad; la auditoría ligada a versión distingue Liberada de
Invalidada por pérdida de habilitación. Conserva fila, aceptación original e historial;
recordatorios PENDING pasan a SKIPPED en la misma transacción. No modifica modelos,
migraciones, contratos ni el servicio de reserva existente. Un replay autorizado de
reserva devuelve su resultado histórico sin reactivar; una clave nueva no puede
reservar el bloque liberado. Sin escrituras durante GET.

Interfaz: botón primario naranja, gris/deshabilitado al vencimiento; explicación del
plazo en Buenos Aires. JavaScript sólo actualiza la presentación del vencimiento;
el servidor vuelve a autorizar incluso sin JavaScript. Formularios independientes,
sin anidación; confirmación original vinculada con atributos form.

Validación de esta entrega: 29/29 Python (release/reservas/ventana/interfaz),
9/9 PostgreSQL descartable (3 nuevas de liberación y 6 de reservas), controlador
Node de liberación y controlador de selección aprobados; sintaxis JS/Python correcta.
PostgreSQL comprueba reenvío simultáneo con un único efecto, rollback, ownership,
revalidación del reloj después de esperar locks y rechazo de nueva reserva liberada.
Chrome: 20 combinaciones, 320/390/768/1024/1440 px, claro/oscuro, con/sin JavaScript,
movimiento reducido emulado; botón habilitado/deshabilitado, foco, formularios y sin
overflow. Recorrido adicional de liberación nativa sin JS con CSRF aprobado.
No constituye certificación AA, testing independiente ni prueba de dispositivo físico.
Primer intento Python encontró un parser no instalado; se reemplazó por HTMLParser
estándar, sin dependencias. Los primeros intentos de navegador fallaron por aislamiento
de red; la ejecución final usó únicamente localhost con preview aislado.

Evidencia: [guardias-liberacion](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/guardias-liberacion/).
Sin nueva migración (continúa 20261026_01), sin tocar base habitual ni cuenta QA.
Recepción profesional, scheduler, revisión visual y retest independiente pendientes.
Estado: IMPLEMENTADO LOCALMENTE; PENDIENTE DE TESTING INDEPENDIENTE.


## Cierre técnico independiente de guardias y liberación — 2026-10-28T14:37:23-03:00

Dictamen independiente del **2026-10-28T14:29:40-03:00**:

**GUARDIAS, LIBERACIÓN Y AJUSTES ACUMULADOS — VERIFICADOS EN EL ALCANCE EVALUADO.**

- Sin defectos funcionales P0–P2.
- P3 heredado: tres templates sin salto final, fuera del incremento. Se conserva la
  observación; no se corrigen esos archivos en este cierre documental.
- Python **74/74**, PostgreSQL **9/9** y Node **4/4**.
- **40 combinaciones de navegador** y liberación adicional sin JavaScript.
- Liberación propia programada únicamente cuando faltan **más de 12 horas**;
  a las 12 horas exactas queda bloqueada en interfaz y servidor.
- Los bloques liberados no son reservables nuevamente en este incremento.
- Historial, atomicidad, idempotencia y recordatorios verificados.
- Sin migración adicional: continúa el head **20261026_01**. Este cierre no afirma
  una migración de la base habitual.

[Evidencia independiente existente](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/guardias-release-independent-qa-20261028/):
python-focal.log, postgres-gate.log, node-tests.log, browser-results.json,
browser.log, capturas e inventarios de integridad. No se recrearon evidencias ni se
repitieron pruebas. Los resultados anteriores permanecen como antecedentes y no
se suman como cobertura adicional. No se declara consola limpia ni certificación AA.

Pendientes: revisión visual de Cristian, scheduler periódico, recepción profesional
y recorrido completo de Urgencias. No habilitación productiva, integración ni despliegue.
La aprobación visual sigue pendiente; este dictamen cierra únicamente el alcance técnico evaluado.

Registro documental: Codex local, laptop. Rama `feature/professional-workspace-ux`,
HEAD `2e552f2fdc57c152c97f0486050574696f6b250e`, 95 paths pendientes y staging vacío.
Únicamente se actualizan `docs/REQUISITOS/PROF_URGENCIAS_UX_001.md`,
`docs/HANDOFFS/ACTIVE_HANDOFF.md` y `docs/CHANGELOG.md`, conservando antecedentes.
Control de cierre: UTF-8 y `git diff --check`; integridad SHA-256 del resto del
inventario, incluidos INDEX y Presupuestos. Sin cambios productivos, pruebas nuevas,
Docker, bases, migraciones ni operaciones Git mutables. Commit/push/PR/merge no
realizados: fuera de autorización; sincronización remota no comprobada.


## Configuración de urgencias con guardado real — 2026-10-28T23:38:49-03:00

Estado: IMPLEMENTADO LOCALMENTE; pendiente de revisión visual y testing independiente.
Cristian aprobó el boceto con mapa en el encargo actual. La aprobación del boceto no
constituye aprobación visual de esta implementación. Responsable: Codex local, laptop.
Base: `feature/professional-workspace-ux`, `2e552f2fdc57c152c97f0486050574696f6b250e`.
Preflight: origin esperado, 95 paths pendientes, staging vacío, head Alembic `20261026_01`.

### Comportamiento y decisiones

- Pantalla canónica GET/POST `/profesional/urgencias/configuracion`, en el shell privado.
  Accesos desde Mi perfil y Configuraciones de Solicitudes/Mis guardias. La antigua
  actividad conserva su ruta; no se cambia su contenido ni los acuerdos existentes.
- Composición del boceto: cobertura, mapa opcional/radio, visita y diagnóstico,
  condiciones y vista previa lateral; una columna móvil; tokens DS v2 en ambos temas.
  Provincia/localidad/barrio son campos nativos del dominio: no existe un catálogo
  geográfico que justifique simular los selectores del boceto.
- Cobertura única en `Professional`, normalizada por `coverage_service`; radio entero
  entre 1 y 200 km. Campos omitidos se conservan. Centro y consentimiento sólo cambian
  por acción explícita actualizar/eliminar; actualizar requiere aceptación expresa.
  El centro orientativo de Google no completa coordenadas al inicializar esta pantalla.
  Marcador arrastrable, círculo y radio sincronizado mediante controlador existente.
  Fallback por clave ausente, timeout y rechazo de API, también tras inicialización.
  Los campos nativos funcionan sin JavaScript. Centro público aproximado conservado.
- Tabla `emergency_configurations`, una fila por profesional: PACKAGE o SEPARATE,
  importes Numeric(12,2) ARS, descuento informado, aclaraciones y reparación/materiales
  aparte. NULL significa incompleto; cero requiere Sin cargo explícito. Se admiten
  decimales con punto/coma, hasta dos posiciones, sin separador de miles. Sólo se
  validan/persisten importes aplicables; no hay movimientos financieros ni tarifas horarias.
- GET no escribe. POST exige rol/estado persistido, propietario, CSRF y límite
  de 30 solicitudes/hora por usuario. Configurar no exige PRO ni concede verificación;
  las tarifas no son una condición adicional de elegibilidad de guardias.
- Formulario firmado ligado a actor, cobertura y versión de configuración. Replay
  mediante OperationCommand, con autorización previa. Guarda bajo locks User →
  Professional → configuración → guardias. Cambio real de cobertura revisa guardias
  no invalidadas con fin futuro; exige aceptación firmada de ids/versiones/valores.
  Una reserva nueva obliga a revisar el impacto nuevamente. Sin cambios efectivos o
  sólo tarifas no invalida. Cobertura, configuración, invalidaciones, recordatorios
  pendientes y auditoría se confirman en una transacción. Rollback íntegro.
- Se reutiliza `invalidate_locked`; liberación voluntaria T−12 sigue separada.
  No se borran historiales ni se reactivan turnos. Fecha de impacto en Buenos Aires,
  con UTC explícito si el runtime carece de IANA (sin fingir hora local).

### Persistencia y migración

Nueva revisión `20261028_01`, padre `20261026_01`. La factory normal registra modelo
 y blueprint. No se reescribieron migraciones previas. Migración desde base vacía hasta
head ejecutada con Alembic exclusivamente en PostgreSQL 16 descartable, sin create_all.
La base habitual NO fue migrada. Es necesario migrar antes de servir esta pantalla.

Procedimiento sugerido para Cristian, NO ejecutado sobre el entorno habitual:
verificar destino y respaldo primero; construir imagen, aplicar revisión y actualizar
sólo web. No ejecutar seed, no recrear PostgreSQL ni eliminar volúmenes.

```powershell
docker compose --env-file .env.example -f docker-compose.stabilization.yml -p mandobra_stabilization build web
docker compose --env-file .env.example -f docker-compose.stabilization.yml -p mandobra_stabilization run --rm --no-deps web python -m alembic current
docker compose --env-file .env.example -f docker-compose.stabilization.yml -p mandobra_stabilization run --rm --no-deps web python -m alembic upgrade 20261028_01
docker compose --env-file .env.example -f docker-compose.stabilization.yml -p mandobra_stabilization up -d --no-deps web
```

Revisión posterior: `http://127.0.0.1:5050/profesional/urgencias/configuracion`.
El compose vigente declara clave Google vacía: mostrará fallback hasta configurar una
clave autorizada mediante el mecanismo existente. No se incorporó una clave ni proveedor.

### Inventario atribuible al incremento

Compartidos modificados (se conserva el resto del trabajo previo):
- `app/__init__.py`: registro normal de modelo y blueprint.
- `app/static/js/professional-coverage-map.js`: centro explícito y fallback de API.
- `app/templates/completar_perfil_profesional.html`: acceso único.
- `app/templates/professional_urgencies.html`: destino de Configuraciones.
- `app/templates/components/_professional_navigation.html`: Mi perfil seleccionado.
- Este requisito, `docs/HANDOFFS/ACTIVE_HANDOFF.md` y `docs/CHANGELOG.md`.

Nuevos:
- `app/models/emergency_configuration.py`.
- `app/routes/emergency_configuration_routes.py`.
- `app/services/emergency_configuration_service.py`.
- `app/static/css/emergency-configuration.css`.
- `app/static/js/emergency-configuration.js`.
- `app/templates/emergency_configuration.html`.
- `migrations/versions/20261028_01_emergency_configuration.py`.
- `tests/test_emergency_configuration.py`.
- `tests/test_emergency_configuration_postgres.py`.
- `tests/js/emergency_configuration.test.js`.
- `tests/js/emergency_configuration_map.test.js`.

### Validaciones realmente ejecutadas

- Suite seleccionada SQLite: 104/104. Después se añadieron dos casos de radio/
  coordenadas y autorización previa al replay: focal final 8/8 (seis ya incluidos
  en los 104; **106 casos únicos**, no 112).
- PostgreSQL descartable: 5/5, migración real, comandos concurrentes, nueva reserva
  durante revisión, liberación concurrente, suspensión antes de replay, rollback y
  persistencia con nueva factory. Última revisión efectiva `20261028_01`.
- Node: 10/10 entre configuración, adaptador Google, navegación, notificaciones,
  reservas y liberación. El adaptador ejercita el controlador productivo; no equivale
  a validar Google Maps real.
- Chrome: 20 combinaciones (320/390/768/1024/1440, claro/oscuro, con/sin JS),
  error monetario repoblado y envío corregido por teclado; sin overflow una vez
  cargados estilos, foco visible. Movimiento reducido emulado realmente. Para oscuro
  sin JS, el harness aplica la clase del tema; no se atribuye al selector deshabilitado.
- Revisión de impacto con aceptación desmarcada, confirmación real y ambos accesos.
  Reinicio del proceso aislado y nuevo login normal conservan tarifas y cobertura.
- Sintaxis Python/JavaScript, UTF-8 sin BOM/NUL/U+FFFD y diff check al cierre.

Evidencias y scripts reproducibles, externos al repositorio:
[urgencias-configuracion](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/urgencias-configuracion/).
Incluye baseline/inventario, python-final.txt, postgres.txt, node.txt,
browser-results.json, restart.txt y capturas config-{light,dark}-{390,1440}.png.

Incidencias de ejecución: puerto 55479 reservado por Windows, recurso fallido retirado
 y reemplazado por puerto 15479; driver usado psycopg2 existente. La primera corrida
 de medios falló por permisos temporales del sandbox; repetición aislada fuera de él
 pasó. Adaptador de mapa completado y fallback corregido tras prueba fallida. La matriz
 repetitiva alcanzó el límite real 429: sólo el preview descartable deshabilitó su
 limiter en memoria para completar las combinaciones. Límite productivo intacto.
 No se presenta esa matriz como validación de rate limit. Espera de estilos requerida
 antes de medir geometría; envío nativo por teclado para la ejecución sin JS.

Límites: API Google real no verificada (sin clave); sin auditoría AA integral, móvil
 físico ni suite total. CSP heredada sin cambios. Recepción profesional, scheduler,
 contratación urgente y habilitación productiva pendientes; pagos/facturación fuera
 del alcance. Antecedentes y cierres independientes anteriores conservados.

Cierre de integridad: 19 archivos atribuibles (8 existentes, 11 nuevos), 107 paths
pendientes totales y staging vacío. Los 598 archivos previos restantes conservan SHA-256,
incluidos INDEX y Presupuestos. Rama/HEAD conservados. Sin commit/push/PR/merge.
Preview detenido y PostgreSQL exclusivo retirado; entorno habitual intacto.


## P2 — Vencimiento de revisión de impacto — 2026-10-30T08:21:08-03:00

Estado: P2 CORREGIDO LOCALMENTE; PENDIENTE DE RETEST INDEPENDIENTE.
Encargo focal sobre el hallazgo independiente del 2026-10-29. No sustituye ese dictamen.
Responsable: Codex local, laptop; rama `feature/professional-workspace-ux`, HEAD
`2e552f2fdc57c152c97f0486050574696f6b250e`. Preflight: origin esperado, 107 paths,
staging vacío, Alembic `20261028_01`. Se conserva el trabajo previo.

### Causa, reproducción y corrección

La revisión usaba URLSafeSerializer sin timestamp ni max_age. Antes de modificar el
servicio, dos regresiones nuevas reprodujeron guardados indebidos con antigüedades de
901 segundos y 306 días: ambas fallaron porque `saved` era True. La evidencia original
se conserva en before.txt. Después del cambio, las mismas dos pruebas pasan sin escrituras.
El reloj de firmas se controla en las pruebas; no se modificó la hora del sistema.
La reproducción de edad mantiene deliberadamente el impacto sintético sin cambios
para aislar la vigencia criptográfica de las reglas de calendario/reserva.

Sólo la firma de revisión pasa a URLSafeTimedSerializer, manteniendo el salt de la
operación y el payload ligado a actor, snapshot, contenido e ids/versiones de guardias.
El formulario original conserva su firma y la identidad durable de OperationCommand.
La validación usa obligatoriamente `max_age=900`, después de adquirir los locks de
actor/perfil/configuración/guardias afectadas y antes de una mutación nueva.

Precisión: timestamp entero del servidor, en segundos Unix (truncamiento de fracciones
por TimestampSigner). Edad entera de 0 a 900 inclusive válida; 901 rechazada.
Se rechazan timestamps futuros (edad negativa), alteraciones y formato anterior sin
vencimiento. Ninguna fecha enviada por el navegador determina la vigencia.

Una revisión vencida responde HTTP 409, sin configuración, cobertura, invalidaciones,
recordatorios, auditoría ni efectos de éxito nuevos, con el mensaje:

> La revisión venció. Revisá nuevamente las guardias afectadas antes de confirmar

Se recalcula el impacto, se entrega otro token y se conservan los campos escapados.
La aceptación se renderiza desmarcada mediante el template existente; el servidor
vuelve a exigirla. Una revisión inválida también pide revisión nueva (409).
Un snapshot cambiado mantiene su rechazo previo y requiere reabrir la configuración.
La comprobación del token presentado no se omite si el impacto quedó vacío: si se
liberó la última guardia, se revisa/acepta el conjunto vacío actualizado antes de guardar.
La regresión concurrente anterior se adaptó a esa confirmación explícita; sigue
comprobando que no se reactiva ni se invalida dos veces la guardia liberada.

Una operación ya completada sigue devolviendo su replay durable después de autorizar
al actor y comprobar comando/contenido, antes del control temporal de una mutación
nueva. La caducidad no genera duplicados ni bloquea la recuperación de ese resultado.

### Inventario focal y validación

Archivos productivos: `app/services/emergency_configuration_service.py` y
`app/routes/emergency_configuration_routes.py`. Pruebas:
`tests/test_emergency_configuration_expiry.py` (nuevo) y
`tests/test_emergency_configuration_postgres.py` (extendido).
Documentación: este requisito, ACTIVE_HANDOFF y CHANGELOG. No cambian templates,
CSS, JavaScript, modelos, migraciones ni dependencias. No se corrigen P3 heredados.

- Python: **41/41**, ejecutando configuración, nuevas pruebas temporales, reservas,
  liberación y ventana. Incluye límites 0/900/901, 306 días, formato anterior, firma
  manipulada, futuro, otro actor, snapshot/nuevas guardias, replay vencido, impacto
  vacío y recuperación HTTP sin escrituras con campos escapados.
- PostgreSQL descartable: **6/6**. Prueba nueva observa `wait_event_type = Lock` en
  pg_stat_activity mientras una transacción independiente mantiene el lock de la
  guardia. Avanza sólo el reloj de firma a 901, libera el lock y comprueba rechazo
  sin cambios. Conserva las cinco regresiones transaccionales anteriores.
- Navegador Chrome: **8/8 recorridos** (390/1440, claro/oscuro, con/sin JavaScript).
  Revisión, vencimiento 409, campos conservados, token renovado, aceptación desmarcada
  y guardado corregido (303 seguido de 200). Envío nativo mediante teclado, sin overflow.
  Oscuro sin JS se selecciona mediante clase CSS del harness, con scripts de página
  realmente deshabilitados. No se repitieron matrices ajenas al cambio.
- UTF-8 y sintaxis Python; `git diff --check`. No se ejecutó Node: no hay cambios JS.
  No es suite completa ni certificación AA; Google Maps real y móvil físico no reevaluados.

[Evidencia antes/después y capturas](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/urgencias-impact-expiry-p2-20261030/):
before.txt, after-reproduction.txt, python.txt, postgres-final.txt, browser-results.json,
expired-{light,dark}-{390,1440}-{js,nojs}.png, baseline.json e informe de integridad.
Incidencia de fixture corregida: el control global de TimestampSigner también afecta
las sesiones Flask; la sesión sintética se firma con el mismo reloj controlado para
no convertir la prueba HTTP en un rechazo de autenticación. Sin cambio productivo extra.

No hay migración nueva: continúa `20261028_01`. Sólo se aplicó la cadena existente en
PostgreSQL exclusivo descartable. No se migró ni administró el Docker/base habitual;
cuenta QA existente intacta. Persisten revisión visual de Cristian, retest independiente,
scheduler, recepción profesional y recorrido completo; no habilitación productiva.

Integridad final del P2: 7 archivos intervenidos (6 existentes y 1 prueba nueva),
108 paths pendientes totales, staging vacío, rama/HEAD conservados. Los otros 611
archivos del baseline mantienen SHA-256, incluidos INDEX, Presupuestos y todos los
templates/P3 heredados. UTF-8/sintaxis y git diff --check correctos. Preview detenido
y PostgreSQL descartable retirado; Docker habitual conserva sus contenedores.
Sin operaciones Git mutables, migración nueva ni modificación de cuenta QA habitual.

## Cierre técnico del P2 de Configuración de urgencias — 2026-10-30T09:06:28-03:00

Dictamen independiente del **2026-10-30T08:47:41-03:00**:
**P2 CERRADO — VERIFICADO EN EL ALCANCE EVALUADO.**

- Confirmación válida entre 0 y 900 segundos inclusive; rechazo desde 901 segundos.
  Se revalida después de adquirir los locks pertinentes, antes de una mutación nueva.
- Recuperación del formulario con campos conservados y escapados, nueva revisión y
  aceptación inicialmente desmarcada. Replay completado idempotente y atomicidad preservada.
- Resultados del retest independiente: Python **41/41**, PostgreSQL **6/6** y
  **ocho recorridos funcionales de navegador**. Son ejecuciones del dictamen citado;
  este cierre documental no repite pruebas ni suma resultados históricos.
- Evidencia durable existente: [config-impact-expiry-retest-20261030](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/config-impact-expiry-retest-20261030/).
  No se recrearon evidencias.

Se conservan los antecedentes de implementación, hallazgo y corrección. Continúan
pendientes Google Maps real, recepción profesional (no habilitada) y aprobación
visual de Cristian. Permanecen documentados los P3 heredados, la observación del
tema oscuro forzado sin JavaScript y los avisos CSP existentes. Este cierre no
declara habilitación productiva ni certificación AA.

Rama `feature/professional-workspace-ux`; HEAD
`2e552f2fdc57c152c97f0486050574696f6b250e`; 108 paths pendientes y staging vacío.
Alcance exclusivo: este requisito, `docs/HANDOFFS/ACTIVE_HANDOFF.md` y
`docs/CHANGELOG.md`. Los otros 615 archivos del inventario inicial se preservan por
SHA-256, incluidos INDEX y Presupuestos. Controles del cierre: UTF-8 y
`git diff --check`; sin cambios productivos, nuevas pruebas, migraciones, Docker
ni operaciones Git mutables.
