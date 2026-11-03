# URGENCIAS-UX-002 — Recorrido manual y contacto protegido

Registro: 2026-10-20T19:57:49-03:00. Responsable: Codex local, laptop.
Estado: READY_TO_RESUME. Implementado localmente; pendiente de revisión visual y testing independiente.
Rama: `feature/professional-workspace-ux`. HEAD: `2e552f2fdc57c152c97f0486050574696f6b250e`.
Origin confirmado: https://github.com/cristhian-star/TRAX-PLATFORM.git.

## Alcance y decisiones

Continúa la prioridad indicada el 2026-10-19 y el encargo de cierre de Presupuestos e inicio de Urgencias.
Se preservan MASTER_SPEC, REQ-004, ADR-002 y PROF_URGENCIAS_UX_001; una propuesta documental
no habilita operaciones aún ausentes del dominio. No hay modelos, migraciones, dependencias,
pagos, cobros, facturación, reservas, difusión ni bot nuevos.

El cierre independiente de Presupuestos está registrado separadamente en PRESUPUESTOS_UX_001,
HANDOFF y CHANGELOG. Sus 36 pruebas y evidencias son históricas del dictamen del
2026-10-20T14:09:02-03:00; no se repitieron para actualizar documentos.

## Inventario funcional comprobado

| Recorrido / fuente | Implementación y límites |
| --- | --- |
| `/urgencias/nueva`, `emergency_service`, validación existente | Búsqueda manual anónima sin crear solicitud; CLIENTE activo registra EmergencyRequest y notificación. Rol PROFESIONAL no crea solicitudes por este POST. Se preservan validación y errores del formulario. |
| `/urgencias/directorio`, `operation_view_service` | Perfiles reales según rubro/zona, cuenta activa y perfil completo según contrato vigente de búsqueda manual. No equivale a selección de guardia ni verificación reforzada. Total y paginación visibles. |
| Confirmación `solicitud` | Se comprueba usuario CLIENTE activo persistido y propiedad. Identificador inválido, ajeno o inexistente: 404; repetido: 400. GET no escribe. El aviso no afirma convocatoria ni asignación. |
| Contacto `/whatsapp/iniciar`, `whatsapp_contact_service` | POST existente con CSRF, consentimiento explícito y rate limit. Formulario nativo accesible sin JS. No se expone teléfono completo ni enlace tel en el directorio. Una solicitud sólo puede vincularla su propietario autenticado; se conserva contacto anónimo sin solicitud. Cuenta inactiva rechazada. Abrir WhatsApp no significa enviar un mensaje ni acordar un trabajo. |
| `/profesional/oportunidades/urgencias` | Shell privado, permisos y pestañas vigentes. Agrega acceso al perfil/contacto y al directorio explícitamente público. No expone solicitudes ajenas. |
| `/emergencias/...` | Compatibilidad 308 existente conservada, incluidos cuerpo POST, CSRF y parámetros. |
| Guardias, convocatoria, respuesta profesional y contrato urgente | Pendientes de implementación/definición; no hay ownership profesional en EmergencyRequest ni bandeja autorizada. El planificador puro existente no constituye una reserva. |

Disponibilidad: se muestra **Disponibilidad por confirmar**. Se elimina el uso de PRO como
prioridad del orden y la etiqueta que lo vinculaba a atención; una insignia PRO real no
acredita disponibilidad. No se fabrican profesionales, horarios activos ni tiempos de llegada.

## Interfaz y seguridad

Directorio con superficies/tokens DSv2 encapsulados, claro/oscuro, foco visible, contacto
expandible nativo, consentimiento y botón táctil; estado vacío y enlaces para ajustar búsqueda.
Se retira la promoción de límites WORK/PRO no sustentados para Urgencias. Se conserva aviso de
servicios oficiales ante riesgo y se explica la guardia futura.

Chrome detectó que `form-action 'self'` bloqueaba la redirección nativa de contacto después
 del POST. Se permite adicionalmente **https://wa.me** sólo en la respuesta del endpoint
`operations.directorio_emergencias`. Las demás páginas conservan `form-action 'self'`;
no se habilitan scripts inline ni otros destinos. Prueba verifica ambos encabezados.
Se conserva el endpoint canónico y no se introduce un mecanismo paralelo de contacto.

## Archivos de este incremento

Código/presentación (ocho):

- `app/__init__.py`: CSP del formulario limitada al directorio.
- `app/routes/operation_routes.py`: confirmación propia y metadatos de paginación; cambios previos de Presupuestos preservados.
- `app/services/operation_view_service.py`: disponibilidad honesta, sin número telefónico en view model del directorio ni prioridad por PRO.
- `app/services/whatsapp_contact_service.py`: propiedad obligatoria de la solicitud vinculada y cuenta activa.
- `app/templates/components/_emergency_professional_card.html`: consentimiento nativo y contacto protegido.
- `app/templates/directorio_emergencias.html`: confirmación, paginación y mensajes honestos.
- `app/templates/professional_urgencies.html`: accesos a perfil y directorio manual.
- `app/static/css/emergency-directory-v1.css`: presentación encapsulada de estos cambios.

Pruebas: `tests/test_urgency_workflow.py` (nuevo, seis métodos con subcasos) y
`tests/test_urgencias_e31.py` (expectativas compatibles con el shell profesional vigente).
Documentación: este archivo, `docs/HANDOFFS/ACTIVE_HANDOFF.md`, `docs/CHANGELOG.md` y
`docs/REQUISITOS/PRESUPUESTOS_UX_001.md` (únicamente cierre independiente).
Catorce archivos intervenidos en esta sesión; 67 paths pendientes al inicio y 74 al cierre.
INDEX y archivos ajenos conservados por hash. Rama, HEAD y staging conservados.

## Validación ejecutada

Entorno descartable con SQLite en memoria y datos sintéticos; no Docker ni bases compartidas.
Comandos con PYTHONDONTWRITEBYTECODE=1 y DATABASE_URL=sqlite:///:memory:.

```text
.venv/Scripts/python.exe -m unittest tests.test_urgency_workflow tests.test_emergency_entry tests.test_urgencias_e31 tests.test_professional_urgencies_ux tests.test_emergency_shift_service tests.test_whatsapp_contact_privacy_service -q
.venv/Scripts/python.exe -m unittest tests.test_security_controls -q
.venv/Scripts/python.exe -m unittest tests.test_urgency_workflow -q
```

Primera selección: 58 casos, 57 aprobados y uno omitido (IANA America/Argentina/Buenos_Aires
no disponible en esta laptop). Seguridad: 9/9 aprobados. Reejecución final de los seis nuevos
tras agregar cliente activo ajeno: 6/6; no se suma como cobertura nueva. Total único: 66
aprobados y una omisión, no suite completa. Incluye permisos, CSRF, contacto, ausencia de
creación por GET, propiedad, filtros, paginación, vacíos, entrada inválida y rutas antiguas.

La primera ejecución detectó tres subcasos E3.1 con expectativas de Home público para un
profesional. Se actualizaron a redirección canónica y enlace privado del shell vigente.
`main_routes.py`, templates del dashboard/perfil y servicio del workspace mantuvieron sus
hashes iniciales; no se modificó ese comportamiento para hacer pasar la prueba.

Chrome real automatizado: 14 combinaciones visuales (directorio 320/390/1440 × claro/oscuro;
cliente y profesional 390/1440 × claro/oscuro), sin overflow observado. Dos recorridos
anónimos de búsqueda/contacto, con JS y sin JS, POST 302; destino WhatsApp interceptado por QA,
sin contacto externo. Un recorrido adicional de humo profesional. Teclado Enter/Espacio,
expansión y consentimiento probados. Movimiento reducido emulado realmente en las seis
combinaciones del directorio. Temas de las capturas aplicados mediante clase CSS del driver;
no equivale a retest de persistencia global del selector.

Un primer intento de click automático sin JS agotó espera de estabilidad; se completó por
teclado nativo. Un intento de matriz con logins repetidos recibió 429; se corrigió el harness
reutilizando sesiones y reiniciando exclusivamente el preview descartable. No se alteraron
límites productivos. El bloqueo CSP de salida fue reproducido y corregido como se indica arriba.
No hubo pageerror en la matriz final. Persiste aviso de consola por script inline bloqueado
por CSP en base.html (archivo no modificado); no se declara consola limpia ni se relaja script-src.

## Evidencias y revisión

[Evidencia durable](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/evidencias-permanentes/URGENCIAS-UX-002/):
`baseline.json`, `integrity-final.json`, `tests.log`, `tests-final.log`, `security.log`,
`ownership-final.log`, `browser-results.json`, `browser-authenticated.json`, scripts del
preview/QA y capturas `directorio-*`, `client-*`, `pro-*`. Datos exclusivamente sintéticos.
AST Python, UTF-8 estricto sin BOM/NUL/U+FFFD y git diff --check comprobados al cierre.

Rutas de revisión en el entorno que administre Cristian: `/urgencias/nueva`,
`/urgencias/directorio` y `/profesional/oportunidades/urgencias`.
El preview local de QA no es un despliegue y se detuvo al terminar.

## Pendientes y límites

- Bandeja profesional, reservas y disponibilidad real, difusión, respuesta/selección, acuerdos,
  seguimiento, notificaciones de convocatoria y bot requieren su incremento aprobado.
- La creación manual actual no posee una clave durable de idempotencia; no se promete deduplicar
  envíos nuevos repetidos. No se modificaron operaciones contractuales ni se creó otro contrato.
- Matching actual por texto y cobertura declarada; no promete ubicación exacta, guardia o llegada.
- IANA del entorno, PostgreSQL, dispositivo móvil físico, auditoría AA integral y QA independiente pendientes.
- No se probaron WhatsApp real, envío de mensajes, pagos ni servicios externos.
- Sin Git mutable, commit, push, PR, merge ni integración; sin autorización para esos pasos.

IMPLEMENTADO LOCALMENTE; PENDIENTE DE REVISIÓN VISUAL Y TESTING INDEPENDIENTE.
