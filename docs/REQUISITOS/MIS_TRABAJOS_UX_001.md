# MIS-TRABAJOS-UX-001 — Registro privado de trabajos

Registro: 2026-10-30T15:48:41-03:00. Responsable: agente implementador local, laptop.
Estado: implementado localmente; pendiente de revisión visual y testing independiente.
Bocetos de listado, formulario y detalle aprobados por Cristian como referencia; no equivalen a aprobación de esta implementación.
Rama `feature/professional-workspace-ux`; HEAD base `2e552f2fdc57c152c97f0486050574696f6b250e`.

## Alcance y separación de contratos

Herramienta opcional para profesionales activos, sin exigir PRO, contrato ni cupo.
El registro pertenece al usuario profesional persistido. No modifica contratos, reputación,
precios, pagos ni facturación. No publica notas ni crea clientes a partir de texto libre.
Decisión: [ADR-004](../ADR/ADR-004-registro-privado-trabajos.md).

- `/profesional/trabajos`: listado privado, filtros GET y paginación de diez registros.
- `/profesional/trabajos/contratados`: conserva el listado contractual anterior, permisos,
  filtros y destinos. Acceso secundario explícito desde Mis trabajos.
- `/profesional/trabajos/registros/nuevo`: GET/POST crear.
- `/profesional/trabajos/registros/<id>`: detalle del propietario.
- `/profesional/trabajos/registros/<id>/editar`: GET/POST editar.

El destino anterior sigue siendo accesible como entrada de Mis trabajos; sus contratos
se consultan mediante el acceso secundario. No hay redirecciones genéricas de POST.
Anonimato, CLIENTE, cuenta inactiva e IDs ajenos no conceden acceso privado.

## Datos, validación y presentación

| Campo | Contrato |
| --- | --- |
| title | Obligatorio, 160 caracteres |
| work_date | Fecha calendario válida; hoy en Buenos Aires al abrir creación |
| client_name | Referencia libre opcional, 160 |
| contact | Texto libre opcional, 254 |
| location | Texto libre opcional, 300 |
| notes | Obligatorio, 10000, texto plano con párrafos conservados |

Límites centralizados en el servicio y reutilizados en el formulario. Normalización
`strip`, sin truncamiento; validación directa y HTTP. Error 400 conserva campos escapados;
conflicto 409 conserva el intento y exige revisar la versión vigente. CSRF y límite
POST de 60/hora. Éxito al crear vuelve al listado sin filtros; al editar vuelve al detalle.
Cancelar no escribe. Datos del formulario nunca van en query strings.

Filtros combinables: `q` (título/notas), `client`, `from`/`to` inclusivos,
`follow` vacío/with/without, `page`. Longitud máxima de filtro 160, parámetros repetidos
rechazados, página 1–100000. Orden fecha descendente e ID descendente. Fuera del contenido
existente se muestra vacío; filtros inválidos responden 400. Volver desde detalle conserva
filtros/página mediante contexto firmado vinculado al actor; no admite destinos externos.

Shell y logos existentes, CSS `.wr`, tarjetas compactas con acento naranja, temas del DSv2.
Detalle en dos columnas de escritorio y una en tablet/móvil. Formulario único crear/editar.
Seguimiento opcional con checkbox nativo; campos visibles e instrucciones, también sin JS.
Esta elección reemplaza el switch decorativo del boceto para evitar otro controlador.
No se añaden scripts ni dependencias. Estado vacío diferencia ausencia de registros y filtros.
La navegación profesional compartida reconoce las rutas hijas; CLIENTE no usa este shell.

## Seguimiento y destinatarios

Un seguimiento vigente por registro, inicialmente desactivado; motivo obligatorio hasta
300 y fecha tentativa al activarlo. Dos avisos independientes inicialmente desmarcados.
Anticipación 0/1/7 días (inicial 1); hora HH:MM (inicial 09:00), IANA
`America/Argentina/Buenos_Aires`. Sin ventana de cuatro semanas.
Fecha nueva/reprogramada >= hoy local; aviso nuevo estrictamente futuro.
Editar notas de un seguimiento pasado no lo rearma ni vuelve a validar su fecha como nueva.
Desactivar/reprogramar/desvincular cancela pendientes anteriores; emitidos se conservan.

El campo Cliente sigue siendo libre. Acción secundaria «Vincular cliente de MANDOBRA»
lista solamente contrapartes CLIENTE activas de contratos del profesional. «Revisar
vinculación» es un POST de consulta, sin guardar, que conserva el formulario y habilita
el checkbox del destinatario comprobado. No hay buscador global ni asociación por email.
Servicio y despachador revalidan contrato propio, profesional persistido y destinatario.
Aviso CLIENTE: profesional, motivo y fecha; sin notas, contacto, ubicación privada ni enlace
al registro. Cliente no obtiene permiso de lectura. Se reutiliza `crear_notificacion`;
no existe un selector de preferencias para este tipo de aviso interno en el modelo vigente.
Las preferencias de contacto WhatsApp no se reutilizan para simular una suscripción interna.

## Persistencia, transacciones y despachador

Nuevas tablas: `work_records`, `work_followups`, `work_reminders`. Versiones de registro
para edición optimista y de seguimiento para invalidar programación anterior.
Reutiliza `OperationCommand` (`PRIVATE_WORK_SAVE`) y `AuditLog` sin nuevas tablas comunes.
Clave UUID y hash del contenido; misma clave/contenido devuelve resultado original,
contenido diferente produce 409. Autorización precede al replay. Escritura y auditoría,
cancelación/programación y resultado idempotente se confirman atómicamente.

Orden de locks: propietario → registro → contrato → recordatorio. Escrituras y despacho
comparten el lock de propietario; dos procesos no envían el mismo pendiente dos veces.
Cada despacho reconsulta versión, activadores, cuenta, relación y reloj después de locks.
Notificación interna y estado SENT se confirman en la misma transacción; fallo revierte
ambos. PENDING no se presenta como enviado. Estados históricos: SENT/CANCELLED/SKIPPED.

Instantes UTC sin zona conforme a `pro_time`, conversión con IANA para mostrar/calcular.
Recuperación: un pendiente atrasado puede emitirse una vez hasta el final de su fecha
local tentativa, inclusive; desde el día siguiente queda SKIPPED. Un batch fallido conserva
pendientes para el próximo intento; el ejecutor no registra notas/contactos/tokens.
No depende del navegador. Límite por pasada 100; el siguiente intervalo procesa el resto.

## Migración y operación posterior (NO ejecutadas sobre entorno habitual)

Migración `20261030_01`, padre real `20261028_01`. Cadena única.
Downgrade elimina registros privados, seguimientos e historial de programación nuevos;
no elimina usuarios/contratos ni notificaciones internas ya emitidas. Sus enlaces privados
pueden quedar sin destino después del downgrade. Respaldar antes de cualquier reversión.

Procedimiento manual posterior a revisión, backup e identificación de base/entorno:

```powershell
$compose = @('--env-file', '.env.example', '-p', 'mandobra_stabilization', '-f', 'docker-compose.stabilization.yml')
docker compose @compose build web
docker compose @compose run --rm --no-deps migrate python -m alembic current
docker compose @compose run --rm --no-deps migrate python -m alembic upgrade 20261030_01
docker compose @compose up -d --no-deps web
# Ejecutor en primer plano, en una terminal dedicada; detener con Ctrl+C.
docker compose @compose exec web python scripts/run_work_reminders.py --interval 60
# Comprobación manual de una pasada, sin bucle:
docker compose @compose exec web python scripts/run_work_reminders.py --once
```

Antes del upgrade comprobar que la revisión efectiva corresponde a la cadena prevista.
No ejecutar seeds, recreate de PostgreSQL, reset de datos ni compose down. El ejecutor en
primer plano requiere permanecer activo; no se instaló servicio de arranque automático.
Alternativa en entorno Python ya configurado: `python scripts/run_work_reminders.py --interval 60`.
CLI equivalente de una pasada: `flask dispatch-work-reminders` con la factory del proyecto.
No se declara automatización operativa en el Docker habitual ni migración de su base.

## Validación local y evidencia

Evidencia externa: [mis-trabajos-20261030](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/mis-trabajos-20261030/).

- **46/46 pruebas Python únicas**: 13 del módulo y 33 regresiones del workspace/propuestas.
  Comando: `.venv/Scripts/python.exe -B -m unittest -q tests.test_work_records tests.test_professional_workspace_ux tests.test_professional_workspace_ux_002 tests.test_professional_proposals`.
- **6/6 PostgreSQL**, separados: doble creación/conflicto, edición concurrente, dos
  despachadores, espera real de lock comprobada mediante `pg_stat_activity`, rollback y
  recuperación con nueva factory/conexión, downgrade/upgrade conservando datos previos.
  Se migró desde vacío y se volvió desde `20261028_01` con usuarios existentes.
  Comando: `.venv/Scripts/python.exe -B -m unittest -v tests.postgresql_work_records`.
  Variables: `TRAX_POSTGRES_TEST_URL` apuntando exclusivamente a PostgreSQL descartable
  en `127.0.0.1:55482/work_records_qa`, `TRAX_POSTGRES_TEST_ALLOW_RESET=1` y DATABASE_URL igual.
  El gate rechaza otra identidad y trunca únicamente esta base sintética autorizada.
- Ejecutable real en dos procesos: **1 emitido, 0 al repetir** (`executor.log`), sin navegador.
- **30 combinaciones visuales**: listado/alta/detalle × 320/390/768/1024/1440 × claro/oscuro,
  sin overflow; movimiento reducido emulado realmente.
- **4 recorridos funcionales**: 390/1440 × JS/sin JS: vinculación, error, conservación,
  corrección, guardado y edición; teclado Enter. Tema predeterminado real sin JS.
- **2 revisiones focales** adicionales, 320 claro/oscuro: texto de más de 5000 caracteres,
  vacío por filtro, foco de 3px y botón Guardar de 46px. Colores finales medidos del botón:
  claro `#ffffff` sobre `#d3440e`; oscuro `#0b1220` sobre `#ff8a4c`.
- AST Python, UTF-8 estricto sin BOM/NUL/U+FFFD en archivos intervenidos y `git diff --check`.
- Sin Node: no se incorporó controlador JavaScript. No suite completa ni certificación AA.

No sumar repeticiones como casos nuevos. Hubo ajustes de fixtures (contrato requería servicio),
dos expectativas antiguas trasladadas al destino contractual preservando sus comprobaciones,
y selectores de automatización corregidos (details, espera de navegación y títulos sintéticos
repetidos). Ejecuciones finales en `tests-final.log`, `postgres-final.log`, `browser-results.json`.
La primera preparación CLI no halló un aviso después del truncado del gate; se creó uno nuevo
sintético y se comprobó 1/0. No se atribuyeron estos fallos a producción ni al trabajo anterior.

## Inventario del incremento

Modificados sobre baseline:
- `app/__init__.py`: registro de modelos, blueprint y CLI.
- `app/routes/main_routes.py`: entrada privada y acceso secundario contractual.
- `app/templates/professional_jobs.html`: identificación del listado contractual y retorno.
- `app/templates/components/_professional_navigation.html`: selección de rutas hijas.
- `tests/test_professional_workspace_ux.py`: expectativas del acceso contractual conservado.
- `docs/HANDOFFS/ACTIVE_HANDOFF.md`, `docs/CHANGELOG.md`: trazabilidad.

Nuevos:
- `app/models/work_record.py`, `app/services/work_record_service.py`, `app/routes/work_record_routes.py`.
- `app/templates/work_record_list.html`, `app/templates/work_record_form.html`, `app/templates/work_record_detail.html`.
- `app/static/css/work-records.css`, `scripts/run_work_reminders.py`.
- `migrations/versions/20261030_01_work_records.py`.
- `tests/test_work_records.py`, `tests/postgresql_work_records.py`.
- Este requisito y `docs/ADR/ADR-004-registro-privado-trabajos.md`.

## Integridad y pendientes

Baseline: 628 archivos, 127 paths pendientes, staging vacío. Incremento: 20 archivos
(7 existentes y 13 nuevos). Final esperado: 140 paths pendientes. Los otros 621 archivos
se conservan por SHA-256, incluidos INDEX y Presupuestos/Urgencias/Propuestas.
Rama y HEAD intactos; sin add/commit/push/PR/merge. Evidencias fuera del repositorio.
Recursos nuevos exclusivos: PostgreSQL `mandobra-work-records-qa-20261030` sin volúmenes
y preview en 54968; retirados al terminar y puertos comprobados.

Pendientes: revisión visual de Cristian, testing independiente, accesibilidad integral,
dispositivo móvil físico, operación de migración autorizada y instalación/supervisión
periódica del ejecutor. Persistencia se probó reiniciando factory y conexiones, no apagando
el host PostgreSQL. No se administró Docker habitual, scheduler ni cuenta QA existente.
Sin adjuntos, exportación, eliminación, recurrencia, plantillas, IA o canales externos.
Los antecedentes y cierres de otros módulos continúan vigentes.
