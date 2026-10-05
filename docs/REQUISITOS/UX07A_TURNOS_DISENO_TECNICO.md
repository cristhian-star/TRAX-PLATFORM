# Emergencias: turnos programados y aval por especialidad

## Corrección focal de Testing — 2026-10-01

Registro: 2026-10-01T20:07:29-03:00. Responsable técnico: agente MANDOBRA, laptop.
Responsable de Producto: Cristian Sánchez. Fecha de sustitución: 2026-10-01.
Fuente: retest 2026-10-01T20:00:59-03:00, RECHAZADO_REQUIERE_CORRECCIONES.
Estado: CORREGIDO DOCUMENTALMENTE / PENDIENTE DE RETEST FOCAL.

**Regla vigente: TURNOS FIJOS DE 12 HORAS CON MÚLTIPLES BLOQUES PROGRAMADOS.**

- GUARDIA_DIURNA: 07:00–19:00; GUARDIA_NOCTURNA: 19:00–07:00 del día siguiente.
- Múltiples bloques futuros, diurnos/nocturnos y consecutivos; nunca duplicar el mismo bloque.
- Reserva hasta T−2 minutos inclusive; después se rechaza. No incorporación al bloque iniciado.
- Confirmación inmediata con aceptación expresa; avisos T−6 h y T−1 h solo si aún son futuros.
  En T−6 h se omite ese aviso; en T−1 h se omiten ambos. No avisos retroactivos.
- Disponibilidad temporal derivada del bloque activo: starts_at <= ahora < ends_at;
  además se mantienen las condiciones de elegibilidad aprobadas. No requiere cron para expirar.
- Zona America/Argentina/Buenos_Aires, instantes UTC; 06:58:00/18:58:00 exactos se admiten,
  un microsegundo posterior se rechaza. Sin redondeos.
- Tarifas bajo autonomía profesional; no cálculo automático por horario.

**SUSTITUIDAS:** reglas de 2/4/8 horas, duración libre, activación/renovación desde ahora
y una única fila mutable por profesional. Los antecedentes inferiores que las describen
son históricos, no normativa activa; sus referencias a activar/renovar/desactivar no
autorizan tales operaciones en este incremento. Cancelar/modificar/abandonar turnos sigue
pendiente. Se conserva el resto de las decisiones de seguridad, matching, pagos,
sanciones, privacidad y soporte sin modificación. Las afirmaciones históricas de
«sin cambios normativos» describen sus sesiones originales, no esta sustitución.
Alcance actual: lógica pura y corrección focal, sin persistencia, migración ni interfaz.

Registro: 2026-10-01T19:39:41-03:00. Responsable: agente técnico documental, laptop.
Rama: feature/ux-ui-foundation. Base: a7391a87db200e678ba4320e74c0075b365df649.
Estado: lógica temporal implementada sin integración; persistencia PROPUESTA, no autorizada.

## Decisiones de Producto y precedencia

> SUSTITUIDAS (2026-10-01, Cristian Sánchez): las reglas temporales de duración libre, 2/4/8 h, fila única y activar/renovar/desactivar de este antecedente. Rige la corrección focal superior; las demás reglas se conservan.

Las decisiones explícitas del chat del 2026-10-01 sustituyen las duraciones 2/4/8 h,
la renovación desde ahora y la fila única mutable propuestas en
[ADR-002](../ADR/ADR-002-emergencias-guardia-vigente.md) y
[REQ-004](REQ-004-emergencias-guardia-vigente.md), incluido el contenido anterior de CA-03.
Corrección del 2026-10-01: ADR/REQ y criterios afectados ya alineados, con antecedentes
marcados SUSTITUIDOS. La persistencia continúa pendiente de autorización. La autorización vigente permite únicamente constantes, lógica pura,
validaciones y pruebas sin migración. No constituye aprobación del diseño de tablas.

Turnos locales 07–19 y 19–07; fecha del bloque = fecha local de inicio. Se permiten
varios bloques y consecutivos, no duplicados. Reserva hasta T−2 minutos inclusive.
Se exige aceptación expresa. Confirmación inmediata siempre; recordatorios solo si
booked_at es estrictamente anterior a T−6 h o T−1 h, respectivamente. Desde T−1 h
la confirmación es tardía. No hay recordatorios retroactivos ni ingreso una vez iniciado.
El aval es por profesional y especialidad; tags propuestos nunca habilitan matching.
No hay cobros, ETA garantizada, prioridad PRO, coordenadas exactas ni sanciones automáticas.

## Mapa y compatibilidad actual

| Componente | Evidencia y límite |
| --- | --- |
| Formulario | `app/routes/operation_routes.py:869`, `app/templates/nueva_emergencia.html:1`: POST con categoría/zona/descripción, CSRF; redirige al directorio. No se modifica en este incremento acotado. |
| Persistencia de solicitud | `app/models/emergency_request.py:6`, `app/services/emergency_service.py:12`: texto libre y commit propio; sin provincia/localidad separadas ni turnos. |
| Matching manual | `app/services/professional_service.py:43`: cuenta ACTIVO y perfil completo, ilike por servicio/especialidad/zona; no prueba aval ni guardia. No debe presentarse como nuevo matching aprobado. |
| Presentación/contacto | `app/services/operation_view_service.py:34,76`: muestra Prioridad PRO, ordena por PRO y usa coordenadas/distancia. Contradice las reglas nuevas; no habilitarlo como matching aprobado. Contacto manual existente, fuera del cambio. |
| Profesional | `app/models/professional.py:4`: especialidad singular textual, cobertura y credenciales declaradas; no son aval por especialidad. |
| Taxonomía | `app/services/taxonomy_service.py:1`: catálogo estático jerárquico con slugs y aliases. No se convierte completo a tablas. |
| Reloj | `app/services/pro_time.py:4`: utc_now aware y as_utc_naive para columnas legacy. |
| Notificación | `app/models/activity_notification.py:4`: INTERNAL, idempotency_key única, attempt_count y delivery_status. No due_at ni reserva FK. |
| Emisión | `app/services/notification_service.py`: crear_notificacion permite commit=False; no asigna automáticamente clave idempotente. Reutilizar modelo y transacción, no un segundo inbox. |
| Auditoría | `app/models/audit_log.py:6`: metadata_json y correlación; evidencia, no historial funcional ni cola. |
| Comandos | `app/models/operation_command.py:10`: actor/operación/clave únicos y payload_hash. Reutilizar para reservas. |

No se localizó un scheduler fiable en app/scripts/requirements. Alembic heads ejecutado
sin conectar a datos: único head 20260917_03. Un conteo AST inicial omitió asignaciones
anotadas; se descarta ese resultado frente al comando oficial.

## Código seguro entregado

`app/services/emergency_shift_service.py` produce planes inmutables UTC, sin guardar,
notificar, consultar DB ni autorizar profesionales. Reutiliza utc_now inyectable.
El plan contiene aceptación, versión de compromiso, recordatorios aplicables/omitidos,
cutoff y confirmación con fechas completas y zona explícita. No es una reserva confirmada.
El lote utiliza un solo instante y detecta duplicados internos; la DB deberá impedir
duplicados entre solicitudes y carreras. No se inventó un catálogo autorizado de Emergencias.

Precisión: starts_at/ends_at tienen segundos y microsegundos cero; cutoff exacto 06:58:00
o 18:58:00 local. 18:58:00.000000 se admite y 18:58:00.000001 se rechaza. No redondear
booked_at. PostgreSQL debe conservar microsegundos. El adaptador futuro tomará el reloj
del servidor después de adquirir locks; no confiará en timestamps del navegador.
La UI deberá mostrar ese instante exacto y deshabilitar el envío después del corte;
latencia de red no extiende el plazo. No hay UI nueva en esta entrega.

IANA: usar ZoneInfo(America/Argentina/Buenos_Aires); no fallback silencioso UTC−03.
La laptop carece de tzdata/IANA. Las pruebas usan una zona UTC−03 inyectada expresamente:
verifican aritmética, no certifican las reglas IANA. Antes de integrar, validar el runtime
Linux con tzdata del sistema o aprobar la dependencia Python tzdata para Windows.
No se instaló ninguna dependencia. Una zona ausente falla explícitamente.

## Persistencia propuesta, no creada

Todos los IDs nuevos: Integer PK; FKs RESTRICT para preservar evidencia. Nuevos instantes:
DateTime(timezone=True), PostgreSQL timestamptz, normalizados a UTC. Presentación IANA.
No convertir fechas legacy en este incremento. Campos obligatorios salvo indicación.

| Entidad propuesta | Campos, responsabilidad y restricciones |
| --- | --- |
| EmergencySpecialty | id; canonical_path String(300) UNIQUE con industria/categoría/rubro/especialidad; source_version String(80); label String(120). Puente al catálogo existente, no copia de toda la taxonomía. Slug de especialidad aislado no garantiza identidad. Solo filas revisadas se consideran operativas. |
| SpecialtyProposal | id; proposer_user_id FK users; proposed_label String(120); context Text; review_status String(30); reviewer_user_id FK users nullable; reviewed_at nullable; approved_specialty_id FK EmergencySpecialty nullable; created_at. Estados de revisión propuestos PENDIENTE_REVISION/APROBADO/RECHAZADO. Aprobación administrativa resuelve equivalencias, nunca inserta texto operativo automáticamente. |
| ProfessionalEmergencyEndorsement | id; professional_id FK professionals; specialty_id FK EmergencySpecialty; status String(30) CHECK PENDIENTE_REVISION/APROBADO/RECHAZADO/SUSPENDIDO; version Integer >=1; reviewer_user_id FK users nullable; reviewed_at nullable; jurisdiction String(160); review_reference String(160) nullable. UNIQUE(professional_id,specialty_id). Alcance territorial de aval requiere definición; no adjuntar DNI ni matrícula universal. |
| EmergencyShiftReservation | id; professional_id FK professionals; kind String(30) CHECK diurna/nocturna; starts_at, ends_at, cutoff_at, booked_at, accepted_at; commitment_version String(80); commitment_text Text; origin String(40) validado por servidor. UNIQUE(professional_id,starts_at); CHECK ends_at=starts_at+12h, cutoff_at=starts_at−2min, booked_at<=cutoff_at, accepted_at=booked_at. Horario local se valida en dominio. Sin estado de cancelación inventado. |
| EmergencyShiftSpecialty | reservation_id FK reserva y endorsement_id FK aval, PK compuesta. Vincula especialidades expresamente aprobadas. Servicio verifica mismo propietario; constraint trigger o diseño de FK compuesta a evaluar en PostgreSQL antes de aprobar migración. Revalidar aval al consultar/contactar: snapshot no perpetúa habilitación. |
| EmergencyShiftReminder | id; reservation_id FK; kind String(20) CHECK T_MINUS_6H/T_MINUS_1H; scheduled_at; status String(30) CHECK PENDING/OMITTED_LATE/DELIVERED/FAILED/EXPIRED; omitted_reason String(80) nullable; attempt_count Integer >=0; dispatched_at nullable; last_error_code String(80) nullable; notification_id FK activity_notifications nullable UNIQUE. UNIQUE(reservation_id,kind). Dos filas permiten auditar también los omitidos. |

Índices propuestos: reservas(professional_id,starts_at) ya cubierto por UNIQUE;
reservas(starts_at,ends_at) para consulta temporal a validar con EXPLAIN;
avales(specialty_id,status,professional_id); recordatorios(status,scheduled_at,id).
Nada de índices parciales dependientes de NOW. Bloques consecutivos comparten frontera
sin solaparse: starts_at <= now < ends_at. No exclusión por día que impida diurno+nocturno.
Datos actuales: cero backfill de avales o guardias basado en perfil completo/PRO/texto.
No inferir matrículas ni aprobar automáticamente. Necesita carga administrativa explícita.

## Atomicidad, idempotencia y auditoría propuestas

Autorización en servidor y CSRF en futuros endpoints. Lock usuario→profesional→avales
ordenados→reservas→comando existente; recapturar reloj. Reutilizar OperationCommand,
vinculando actor/operación/clave y hash canónico del lote, especialidades y compromiso.
Reservas, confirmaciones internas, dos registros de recordatorio y AuditLog se crean
en una transacción. Ningún helper con commit propio. Un lote inválido revierte completo.
Replay idéntico devuelve el resultado original sin crear eventos; diferente payload/actor
rechazado, con reautorización antes del replay. La representación del resultado del lote
debe diseñarse antes de migrar: OperationCommand solo apunta a una entidad (posible
BookingBatch con id/actor/created_at y FK batch_id en reserva). No guardar una lista
de IDs sin contrato en AuditLog para suplir una entidad funcional.

Confirmación interna con clave única derivada de reserva+CONFIRMATION+versión.
Recordatorio con clave reserva+kind+INTERNAL. Despacho: lock recordatorio y crear
ActivityNotification y marcar DELIVERED en la misma transacción; UNIQUE como defensa
final. Rollback y nueva consulta ante IntegrityError específico, nunca éxito genérico.
Fallo técnico deja pendiente/reintentable sin cancelar guardia ni sancionar. Registrar
error saneado, intento y timestamps; nunca datos privados en logs/query strings.
Historial funcional conserva cada intento en ReminderAttempt (id, reminder_id FK,
attempt_number, attempted_at, outcome, error_code nullable; UNIQUE reminder+number).
AuditLog conserva actor, operación y cambios administrativos; no sustituye esa entidad.

## Alternativas de ejecución, pendientes de elección

1. Comando Flask de despacho por lote invocado por programador del entorno: sencillo,
   durable en PostgreSQL; requiere aprobar operación, frecuencia y monitoreo.
2. Worker dedicado con polling de tabla: misma transacción y locks; requiere proceso
   y supervisión nuevos. No se crea ni se elige automáticamente.
3. Despachar al recibir peticiones: no garantiza avisos si no hay tráfico; no apto
   como mecanismo fiable de recordatorios, ni como promesa de puntualidad.

No hay envío externo. Definir tolerancia de retraso técnico y política de reintentos
antes de habilitar scheduler; no despachar retrospectivamente eventos vencidos.
No confundir determinismo del plan con idempotencia real de entrega (pendiente).

## Migración, pruebas y pendientes

Upgrade propuesto: partir del head vigente revalidado; crear entidades e índices
aditivos en orden catálogo/propuestas/aval/lote/reserva/vínculos/recordatorio/intentos.
No modificar ni borrar datos existentes, no sembrar aprobaciones. Desplegar primero
con funciones deshabilitadas y administración autorizada. Se requiere autorización
separada para crear/ejecutar la migración y definir lote/alcance territorial del aval.
Downgrade: deshabilitar escritores/despacho; respaldo y autorización explícita si hay
reservas/evidencia; no borrar auditoría ni OperationCommand. Rechazar downgrade con
datos sin estrategia aprobada; tablas vacías se eliminan en orden inverso. Re-upgrade
no debe resucitar guardias. Ninguna migración creada en esta sesión.

Ejecutadas: 9 pruebas unittest puras, 0 fallos. Incluyen fronteras 6h/1h/2min,
microsegundos, noche al día siguiente, cambio de año, UTC, lotes consecutivos,
duplicados internos, aceptación explícita y reloj naive rechazado.
Pendientes: IANA real; integridad/locks/rollback/carreras/replay PostgreSQL; duplicados
entre lotes; aval aprobado/pendiente/rechazado/suspendido; tag propuesto; matching
neutral por cobertura; fallo de envío sin sanción; no duplicación de confirmaciones;
CSRF/ownership; UI, accesibilidad y temas. No suite completa: entorno persistente no
preparado ni autorizado para esta sesión; pruebas puras no requieren DB.

Decisiones pendientes: cancelación/modificación/abandono, permisos y alcance territorial
de revisión, catálogo inicial operativo, mecanismo y tolerancia de despacho, política
de retención, campos del lote. Cobro de visita y devoluciones archivados para incremento
posterior jurídico/producto. No implementar esas decisiones por inferencia.

## Contrato público corregido y evidencia de retest focal

P2: ShiftValidationError (subclase ValueError) es la excepción pública uniforme para
validación de entradas. No se reutilizan errores de contratos/pagos, ajenos al dominio.
Colección principal: exclusivamente list o tuple de Python; bloques: list o tuple
de exactamente dos componentes. Fecha: date exacto (no datetime); kind: str exacto
y uno de los dos turnos. Se validan todos antes de normalizar a tuplas inmutables,
deduplicar o consultar reloj. No se consumen generadores ni iteradores arbitrarios.
Lote vacío, estructura/tipo/valor inválido o duplicado normalizado falla sin planes
parciales. Mensajes saneados, sin repr del payload. Clock inválido y falta de aceptación
también usan ShiftValidationError; falta de IANA es error ambiental explícito, no fallback.

P3: suite permanente 15 pruebas. Windows: 14 aprobadas, 1 omitida con
ZoneInfoNotFoundError explícito. Imagen oficial proyectomandobra-trax-web:latest
(8772cada809b), contenedor efímero sin red, filesystem de solo lectura: 15 aprobadas,
0 omitidas, IANA real incluida. Matriz de 19 entradas inválidas, normalización lista/tupla,
cinco fronteras diurnas, fin de mes/año y noche al día siguiente. No factory ni DB.
No se instaló tzdata. Es evidencia de ejecución, no aprobación independiente de Testing.
