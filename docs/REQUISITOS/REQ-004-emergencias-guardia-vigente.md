---
id: REQ-004
titulo: UX-07A — Emergencias y guardia vigente
estado: APROBADO COMO ESPECIFICACIÓN
aprobacion_producto: APROBADO_PARA_ESPECIFICACION
fecha_aprobacion_producto: 2026-09-27T23:03:15-03:00
responsable_producto: Cristian Sánchez
implementacion: PENDIENTE
---

# REQ-004 — UX-07A: Emergencias y guardia vigente

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

## Aceptación de ADR-002 y continuidad — 2026-09-28

Fecha y hora: `2026-09-28T21:10:35-03:00` (America/Argentina/Buenos_Aires).
Responsable: agente documental (Codex), laptop.
Rama: `feature/ux-ui-foundation`.
HEAD base: `a7391a87db200e678ba4320e74c0075b365df649`.
Documento/decisión: ADR-002.
Motivo: registrar aceptación arquitectónica posterior al retest independiente final.
Decisión de Producto: Cristian Sánchez, `2026-09-28T20:59:57-03:00`.
Estado: ADR-002 APROBADO. Alcance siguiente: PREFLIGHT UX-07A.1.
Implementación UX-07A.1: NO AUTORIZADA. UX-07A.2: BLOQUEADO POR DEPENDENCIA.
Captura y persistencia de coordenadas exactas: BLOQUEADAS.
Esta entrada actualiza los estados vigentes; las entradas anteriores conservan su
valor histórico. No modifica la normativa aprobada ni declara trabajo técnico iniciado.

REQ-004: APROBADO COMO ESPECIFICACIÓN / IMPLEMENTACIÓN PENDIENTE.
[ADR-002](../ADR/ADR-002-emergencias-guardia-vigente.md) queda APROBADO tras
el retest independiente final del `2026-09-28T20:55:50-03:00`.
UX-07A.1 puede ingresar únicamente al preflight técnico, sin iniciar implementación,
migraciones ni testing funcional. UX-07A.2 depende de completar y aprobar UX-07A.1.
Las 27 filas CA-01–CA-27 permanecen intactas; no se declara el requisito implementado,
probado funcionalmente ni desplegado.

## P2 residuales: contrato aplicable — 2026-09-28

Fecha y hora: `2026-09-28T20:45:39-03:00` (America/Argentina/Buenos_Aires).
Responsable: agente de corrección documental (Codex), laptop.
Rama: `feature/ux-ui-foundation`.
HEAD base: `a7391a87db200e678ba4320e74c0075b365df649`.
Motivo: incorporar las decisiones aprobadas para cerrar los P2 residuales sobre
contrato territorial y confianza de IP/proxy.
Estado: CORREGIDO / PENDIENTE DE RETEST INDEPENDIENTE.
Autorización de Producto: Cristian Sánchez, `2026-09-28T20:42:54-03:00`.
Los dos P2 están corregidos documentalmente, no cerrados ni aprobados por este agente.
ADR-002: PROPUESTO / EN CORRECCIÓN; UX-07A.1: BLOQUEADO;
UX-07A.2: BLOQUEADO POR DEPENDENCIA. Implementación pendiente, sin autorización.
Esta entrada precisa exclusivamente esos dos contratos y prevalece sobre sus
formulaciones previas; conserva las demás decisiones, las 27 filas CA y el historial.

REQ-004 continúa APROBADO COMO ESPECIFICACIÓN, implementación PENDIENTE.
Definición normativa completa:
[ADR-002, P2 residuales](../ADR/ADR-002-emergencias-guardia-vigente.md#p2-residuales-territorio-e-ip-confiable--2026-09-28).

**P2-01 territorial.** Profesional: provincia desde coverage_province y localidad desde
coverage_city. Emergencia: ambos valores declarados separadamente por el cliente y
conservados en contexto autorizado. EmergencyRequest hoy solo tiene zona; el preflight
debe resolver mapeo/cambio mínimo antes de implementar, sin heurísticas sobre zona.
No se acreditaron IDs territoriales canónicos; solo si se verifican podrá proponerse
uso preferente, sin catálogo nuevo ni dependencia externa.

Regla única en ambos lados: texto válido/no vacío → NFC → trim y colapso de espacios
Unicode internos → casefold → NFC. Rechazar datos inseguros y controles no espaciales;
no quitar acentos, transliterar ni inferir aliases. Exigir igualdad exacta CONJUNTA de
provincia y localidad normalizadas. Homónimos necesitan provincia; ambigüedad restante,
dato incompleto/inválido o ausencia de correspondencia exacta excluyen conservadoramente.
Texto libre y substring/contains/fuzzy no acreditan cobertura. Sin inferencias entre
localidades, código postal inferido, geocodificación implícita, distancia vial, ETA
o coordenadas inventadas. Oficio es filtro independiente; PRO es neutral y el orden
posterior sigue estable por contrato, sin inventar distancia o prioridad.
Captura/persistencia exacta bloqueada hasta política de minimización, acceso y retención.

**P2-02 IP/proxy.** Por defecto usar peer inmediato, ignorando encabezados del cliente.
Solo interpretar X-Forwarded-For/X-Real-IP/Forwarded o equivalentes bajo proxy conocido,
peer original en allowlist, saltos exactos y configuración validada por entorno.
Verificar peer antes de reescritura; ProxyFix/equivalente por sí solo no acredita confianza.
Cadena excesiva/inconsistente no amplía confianza; configuración ausente/inválida falla
cerrada en modo proxy, sin fallback a encabezados. No confianza global ni dependencia nueva.
Clave principal autenticada: ID estable validado por servidor + operación; IP es señal
complementaria, nunca autorización, ownership o identidad idempotente. En anónimos,
reconocer NAT/red compartida/IPv6/rotación y respetar el mismo contrato de confianza.
El código actual combina usuario/IP y usa get_remote_address; no se afirma que ya cumpla.

Separar cuotas por superficie/operación; conservar límites provisionales previos y
replays contabilizados. 429 con política de reintento y Retry-After coherentes; mantener
misma clave ante respuesta interrumpida, sin convertir replay en segunda mutación.
memory:// no comparte contadores entre procesos/réplicas y se pierde al reiniciar;
no basta para producción distribuida. No Redis por esta corrección.
Preflight bloqueante antes de implementar/desplegar: actor/clave, operación, ventana,
cantidad, respuesta 429, reintento y proxies confiables por entorno definidos/aprobados.
IP minimizada en HTML, query strings y logs; no incluirla en resultado/payload durable
de dominio sin justificación aprobada, respetando privacidad y retención.

Casos territoriales previstos: igualdad normalizada, case/espacios, provincia igual y
localidad distinta, homónimos entre provincias, incompletos, ambiguos, substring,
Unicode, oficio incompatible y neutralidad PRO.
Casos IP previstos: directo, spoofing directo, proxy no confiable, saltos exactos
confiables, cadena excesiva, cambio de IP del usuario, NAT compartida, cuota por
operación, replay, 429/reintento y reinicio/multiproceso memory://.
Son escenarios complementarios de retest, no nuevos criterios ni pruebas ejecutadas.
Las 27 filas CA-01–CA-27 permanecen exactamente intactas.

## Corrección normativa para retest — 2026-09-28

Registro de corrección: `2026-09-28T20:15:29-03:00`.
Decisión de Producto: `2026-09-28T20:12:39-03:00`, Cristian Sánchez,
APROBADO PARA CORRECCIÓN DOCUMENTAL. Autor: agente documental local (Codex), laptop.
Rama: `feature/ux-ui-foundation`; HEAD base: `a7391a87db200e678ba4320e74c0075b365df649`.
Motivo: incorporar las recomendaciones arquitectónicas adoptadas sobre 2 hallazgos P1
y 4 hallazgos P2. Estado de la corrección: CORREGIDO / PENDIENTE DE RETEST.
ADR-002: PROPUESTO / EN CORRECCIÓN, no aceptado.
UX-07A.1: BLOQUEADO. UX-07A.2: BLOQUEADO POR DEPENDENCIA.
Implementación, migraciones y pruebas técnicas/funcionales: PENDIENTES, sin autorización.
Esta entrada expresa el contrato vigente para retest y prevalece sobre las alternativas
y próximos pasos de registros anteriores, que se conservan como historia.
La adopción de recomendaciones no acepta ADR-002 ni autoriza implementar UX-07A.1.

La aprobación documental de REQ-004 se conserva; estas aclaraciones adoptadas quedan
pendientes de retest independiente, sin aceptación de ADR-002 ni autorización técnica.
Contrato arquitectónico de referencia:
[corrección ADR-002](../ADR/ADR-002-emergencias-guardia-vigente.md#corrección-arquitectónica-adoptada--2026-09-28).

### Reglas adoptadas que sustituyen alternativas anteriores

> SUSTITUIDAS (2026-10-01, Cristian Sánchez): las reglas temporales de duración libre, 2/4/8 h, fila única y activar/renovar/desactivar de este antecedente. Rige la corrección focal superior; las demás reglas se conservan.

- P1-1: exigir perfil_completo, estado_perfil VERIFICADO y verificación APROBADA de
  tipo PROFESIONAL. Aprobar esa verificación produce la transición autorizada
  PENDIENTE_VERIFICACION → VERIFICADO y auditoría en una operación de aplicación.
  No reutilizar has_approved_verification() sin filtro explícito de tipo PROFESIONAL.
  No exigir verificación de CLIENTE por traslado de reglas de contratación.
- P1-2: invalidar por desactivación atómica, incremento de versión y auditoría en la
  transacción del cambio de elegibilidad. Incluye rechazo/revocación, suspensión,
  cambio de rol, pérdida de habilitación, oficio y cobertura. Todos los escritores
  usan servicios componibles sin commits internos. Restaurar datos nunca reactiva.
  Se descarta para este incremento la alternativa de revisión monotónica adicional.
- P2-1: OperationCommand identifica la intención; la fila mutable no es resultado
  histórico. Activar/renovar/desactivar y no-op conservan payload original mínimo,
  versionado e inmutable. Solo formato, operación, resultado/no-op, versiones previa
  y nueva, inicio/vencimiento e IDs técnicos mínimos. Puede referenciar AuditLog
  protegido durante la vida útil del replay; sin ubicación, teléfono o datos sensibles.
  Estado actual separado del histórico. Misma clave ante respuesta interrumpida,
  nueva clave para otra intención; clave criptográfica servidor ligada a actor/operación.
  Tras IntegrityError: rollback, nueva autorización, relectura y replay solo con comando
  confirmado compatible. No convertir otros errores de integridad en éxito.
- P2-2: renovar reemplaza desde ahora por 2/4/8 horas; puede acortar y requiere mostrar
  y confirmar nuevo vencimiento. No renovar vencida: nueva activación explícita.
  Reloj posterior a locks, versión esperada obligatoria y conflicto ante versión obsoleta.
  Replay no revive ventanas; desactivación repetida puede ser no-op sin nueva transición.
- P2-3: localidad y provincia normalizadas, comparación explícita y cobertura declarada.
  Homónimos requieren provincia u otro contexto inequívoco; datos ambiguos/incompletos
  se excluyen. Texto libre ayuda a buscar, no acredita cobertura. Ningún substring
  ilike("%zona%") acredita elegibilidad. Sin PostGIS; captura exacta bloqueada.
- P2-4: creación 10 POST/día provisional, incluidos replays; contacto 10/hora provisional.
  La clave vigente depende de usuario/IP y memory:// no es cuota global distribuida.
  Activar/renovar requieren cuota por actor más control IP; desactivar no comparte esa
  cuota. Cancelación y contacto tienen límites propios. HTTP 429; cifras nuevas y
  alcance obligatorios en preflight .1. No Redis ni garantía distribuida inventada.

### Contratos complementarios 6–15

Locks en orden: usuarios involucrados por ID → profesional → guardia → solicitud
cuando corresponda → comando idempotente existente cuando corresponda.
Profesional serializa primera activación sin fila de guardia; UNIQUE es defensa final.
La versión complementa locks. Refrescar datos, autorizar antes de replay y revalidar
bajo locks; PostgreSQL obligatorio para carreras de todos los escritores.

Solo CLIENTE activo propietario cancela ABIERTA → CANCELADA, tras bloquear solicitud.
Propia ya cancelada: no-op; otros estados: rechazo; no reabrir. Cancelación/contacto
comparten lock de solicitud; un contacto emitido no se revoca retroactivamente.
Contacto exige además consentimiento, guardia vigente y elegibilidad completa, reloj
posterior al lock y datos refrescados. Contacto y auditoría se confirman antes de entregar
destino; sin llamadas externas dentro de transacción ni promesa de disponibilidad futura.

Coordenadas exactas BLOQUEADAS hasta definir finalidad, campos, acceso, retención,
vencimiento lógico, purga verificable, backups y protección aplicable. Ubicación exacta
separada de zona aproximada. Contexto vencido no se utiliza; no declarar cifrado inexistente.
Mantener las prohibiciones de exposición por query, referrer, logs, HTML/JSON y auditoría.

> SUSTITUIDAS (2026-10-01, Cristian Sánchez): las reglas temporales de duración libre, 2/4/8 h, fila única y activar/renovar/desactivar de este antecedente. Rige la corrección focal superior; las demás reglas se conservan.

GET únicamente lectura; POST con CSRF para crear/cancelar/activar/renovar/desactivar/contactar.
Actor/propietario de sesión, allowlist, duración/clave/versión cuando correspondan.
400 validación, 409 conflicto, 429 límite; denegación sin revelar solicitudes ajenas.
POST exitoso a lectura autorizada; contacto con confirmación nativa previa a salida externa.
Soporte básico sin JS; replay no simula creación nueva. URLs nuevas no declaradas existentes.

Downgrade con pérdida requiere precondiciones, respaldo y autorización; conserva
AuditLog/OperationCommand. Re-upgrade y replay no recrean guardias históricas.
Diferenciar rollback de aplicación y downgrade de esquema.
Índices candidatos: UNIQUE profesional y vencimiento de activas/no desactivadas con
predicado estático, sin now() ni duplicar UNIQUE. Mapeo de asistencia primero; planes
con volumen representativo después. No se declara rendimiento probado.
Guardia es estado actual; OperationCommand resuelve idempotencia; AuditLog es evidencia
histórica. No event sourcing ni otra tabla de historial. Retención del resultado
idempotente separada del contexto privado, protegida mientras deba admitir replay.

### Aclaración de cobertura sin renumerar CA-01–CA-27

Las 27 filas de aceptación se conservan íntegramente. En su retest deberán incluir:
CA-02/03/08: tipo de verificación, transición de perfil, rol y restauración sin resurrección;
CA-04–10: versión obsoleta, no-op durable, orden de locks, reloj tras espera y rollback;
CA-11/13: localidad/provincia, homónimos, datos incompletos y exclusión sin substring;
CA-14/17: cancelación contra contacto y autorización bajo lock;
CA-15/16: captura bloqueada, retención y límites reales con respuesta 429;
CA-25/27: downgrade sin resurrección, historia preservada y estados bloqueados.
No son criterios nuevos ni evidencia de pruebas ejecutadas.

## Cierre de revisión documental UX-07A — 2026-09-28

Registro: `2026-09-28T19:42:16-03:00`. Dictamen: `2026-09-28T19:31:39-03:00`.
Responsable de Producto: Cristian Sánchez. Revisor: agente documental local.
Estado: APROBADO COMO ESPECIFICACIÓN. Hallazgos: P0: 0; P1: 0; P2: 0; P3: 0.
Implementación: PENDIENTE. Pruebas técnicas y funcionales: PENDIENTES.
ADR-002: PROPUESTO / PENDIENTE DE DECISIÓN ARQUITECTÓNICA; no aceptado ni implementado.
UX-07A.1 permanece pendiente de aprobación arquitectónica y autorización de implementación.
UX-07A.2 depende de UX-07A.1 implementado y verificado antes de afirmar disponibilidad.
Próximo paso: decidir ADR-002 y preparar el paquete UX-07A.1. Ninguna implementación iniciada.
Este cierre aprueba la especificación documental; no acredita implementación ni pruebas
funcionales, ni acepta las soluciones técnicas propuestas. Los 27 criterios se conservan.
Los registros fechados anteriores mantienen su estado histórico; este cierre expresa el vigente.

Registro documental: 2026-09-27T23:14:25-03:00.
Responsable de Producto: Cristian Sánchez. Redacción: Codex, laptop MANDOBRA.
Rama: `feature/ux-ui-foundation`. HEAD: `4489c5c208245368a2a9bfd1672a261cf3004c93`.
Motivo: formalizar el preflight UX-07A aprobado y las decisiones recibidas el
`2026-09-27T23:03:15-03:00` (APROBADO PARA ESPECIFICACIÓN).
Estado documental: BORRADOR PARA REVISIÓN; implementación: PENDIENTE.
Orden neutral aprobado: PRO no concede elegibilidad ni prioridad; verificación
obligatoria como filtro, nunca como privilegio adicional de orden.
Siguiente paso: revisión de esta especificación y autorización de UX-07A.1;
UX-07A.2 no podrá afirmar disponibilidad hasta verificar UX-07A.1.


## 1. Autoridad, problema y estado

El usuario necesita encontrar asistencia compatible y con guardia temporal real,
sin confundir descubrimiento y contacto con despacho o contratación. Las decisiones
explícitas de Producto que siguen están aprobadas para especificación. Las reglas
operativas detalladas marcadas como propuesta completan el contrato para revisión;
no se presentan como nuevas decisiones ya aprobadas ni autorizan implementación.

Convención verificada: REQ-001 a REQ-003 ocupados; REQ-004 disponible. ADR-002
complementa este requisito. Se conserva UX-07A como identificador de experiencia.

Fuentes: [Master Spec](MASTER_SPEC.md), [antecedente conceptual](BORRADOR_PLANES_REPUTACION_GUARDIAS_CONTRATACION.md),
[estándares](../ESTANDARES_DESARROLLO.md), [DS v2](../DESIGN_SYSTEM_V2.md),
[DS v1 conceptual](../design-system-v1.md), [guía documental](../GUIA_DOCUMENTACION.md),
[taxonomía](../trax-taxonomy-v1.md), [ADR-002](../ADR/ADR-002-emergencias-guardia-vigente.md).
Preflight aprobado: informe del chat local «PREFLIGHT_UX07A_EMERGENCIAS_GUARDIA_PENDIENTE_DE_REVISION»,
sobre HEAD 4489c5c. Este documento incorpora su diagnóstico sin inventar un archivo
previo ni atribuir pruebas ejecutadas a esta sesión.

### Línea base contrastada, todavía vigente en código

- Navbar → GET/POST `/emergencias/nueva` → GET `/emergencias/directorio`.
- Visitante consulta sin persistir; cualquier usuario activo puede persistir hoy,
  discrepancia con el rol CLIENTE requerido para el comportamiento objetivo.
- `EmergencyRequest` declara ABIERTA, ASIGNADA, EN_CAMINO, RESUELTA y CANCELADA;
  no persiste profesional asignado. Helpers sin integración no constituyen despacho.
- No hay guardia real. El directorio filtra cuenta activa y perfil completo,
  coincide por texto y ordena incluyendo PRO; «Disponible según perfil» es texto fijo.
- Creación y notificación tienen commits separados; falta comando idempotente.
- Coordenadas pueden pasar a query string; `solicitud` en URL no acredita ownership.
- WhatsApp centralizado comprueba dueño de emergencia solo cuando hay actor;
  debe impedirse la asociación anónima de solicitudes ajenas.
- El formulario no valida todos los límites en servidor. El título oscuro hereda
  un token inverso casi negro. Skeleton global existe y matching es síncrono.
- Taxonomía estática solo tiene Electricidad, Plomería y Refrigeración: las otras
  cuatro asistencias son ampliaciones objetivo, no datos ya implementados.

Referencias de código: [rutas](../../app/routes/operation_routes.py),
[creación](../../app/services/emergency_service.py), [modelo](../../app/models/emergency_request.py),
[consulta](../../app/services/professional_service.py), [presentación](../../app/services/operation_view_service.py),
[cobertura](../../app/services/geographic_matching_service.py),
[WhatsApp](../../app/services/whatsapp_contact_service.py).

## 2. Paquetes y exclusiones

> SUSTITUIDAS (2026-10-01, Cristian Sánchez): las reglas temporales de duración libre, 2/4/8 h, fila única y activar/renovar/desactivar de este antecedente. Rige la corrección focal superior; las demás reglas se conservan.

| Paquete | Entrega exigida | Gate |
| --- | --- | --- |
| UX-07A.1 | Catálogo, disponibilidad real, permisos, modelo/migración, UI profesional mínima de activar/renovar/desactivar, expiración, matching, privacidad, creación atómica/idempotente, contacto seguro | Focales y PostgreSQL real; revisión independiente |
| UX-07A.2 | WebP, carrusel, overlay, formulario, skeleton, listado, vacío, responsive y accesibilidad | UX-07A.1 implementado y verificado antes de afirmar guardia; revisión visual y regresiones |

La UI profesional mínima pertenece a .1 para que la guardia sea operable; .2 no
rediseña dashboards ni perfiles públicos completos. Se puede preparar presentación
antes, pero no habilitar afirmaciones de disponibilidad sin el gate .1.

Fuera de alcance: despacho automático, aceptación bilateral, asignación operativa,
EN_CAMINO ejecutable sin asignado, contrato EMERGENCY, ETA, rutas viales, pagos,
garantía, recurrencias, agenda semanal, turnos futuros, invitaciones automáticas,
WhatsApp Business API, polling, WebSockets, colas, cron obligatorio y prioridad PRO.
No se trasplantan estados SCHEDULED/PAUSED ni entidades de invitación/respuesta del
antecedente conceptual. Sus demás temas comerciales/contractuales siguen separados.

## 3. Catálogo de seis asistencias

Los nombres visibles están aprobados. IDs y colocación siguientes son la propuesta
estable de especificación; su adopción en código requiere el paquete .1.

| Nombre visible | ID estable propuesto | Ubicación industria → categoría → rubro | Legacy/sinónimos explícitos |
| --- | --- | --- | --- |
| Electricidad | electricidad | Construcción → Electricidad → Electricista (existentes) | electricidad, electricista, eléctrico/electrico, electricista matriculado |
| Plomería | plomeria | Construcción → Plomería → Plomero (existentes) | plomeria/plomería, plomero, sanitario |
| Cerrajería del hogar | cerrajeria-hogar | Hogar → Cerrajería → Cerrajero del hogar (nuevo) | cerrajería domiciliaria, cerrajero del hogar, cerraduras de vivienda |
| Cerrajería automotor | cerrajeria-automotor | Movilidad → Cerrajería automotor → Cerrajero automotor (nuevo) | cerrajería automotriz, cerrajero automotor, cerraduras de auto |
| Auxilio vehicular para automóvil | auxilio-vehicular-auto | Movilidad → Auxilio vehicular → Auxilio para automóvil (nuevo) | auxilio para auto, asistencia vehicular automóvil, cambio de rueda de auto |
| Auxilio móvil para motocicleta | auxilio-movil-moto | Movilidad → Auxilio vehicular → Auxilio para motocicleta (nuevo) | auxilio para moto, asistencia móvil motocicleta, gomería móvil para motos |

«Categoría visible de asistencia» es la opción operativa, no necesariamente un
TaxonomyCategory: tiene mapeo explícito a nodos. Rubro identifica oficio; especialidad
refina su capacidad; sinónimo es solo una entrada alternativa, no habilitación.
No cambiar slugs existentes ni inventar especialidades para completar un árbol.

Normalización objetivo: espacios, mayúsculas y diacríticos para resolver únicamente
aliases explícitos, manteniendo etiqueta original y significado. Nunca inferir
cerrajería del hogar desde «cerrajero» ambiguo, ni auto/moto desde «auxilio»,
«mecánico» o «gomería» sin contexto. Desconocido/ambiguo: error de campo controlado,
sin persistir ni buscar un rubro alternativo silenciosamente.

Compatibilidad: conservar datos legacy y resolver aliases conocidos mediante la
capa canónica; no hacer backfill masivo ni reasignar perfiles por texto parecido.
Perfiles con clasificación desconocida/ambigua no son elegibles para ese filtro
hasta confirmar su oficio. Un cambio de label no cambia el ID. SQL parametrizado;
`%`/`_` no se interpretan como comodines de una asistencia seleccionada.
No mapear ninguna asistencia nueva a Electricidad, Plomería o Refrigeración.

## 4. Actores y permisos

| Actor | Puede | No puede |
| --- | --- | --- |
| CLIENTE autenticado activo | Crear, consultar su solicitud, recibir candidatos, iniciar contacto autorizado y cancelar según reglas | Leer/modificar solicitud ajena, activar guardias, autoadjudicar |
| Visitante | Ver portada e iniciar autenticación segura | Persistir emergencia, asociar contacto a una emergencia ajena |
| PROFESIONAL activo elegible | Activar/renovar/desactivar su guardia, aparecer si pasa todos los filtros, recibir contactos existentes | Operar como cliente, modificar solicitudes, activar guardia ajena, autoadjudicarse |
| ADMINISTRADOR | Capacidades existentes de soporte/auditoría con permisos vigentes | No se agregan switches de guardia ajena ni adjudicaciones manuales |

Ruta y servicio validan actor activo desde servidor, no el rol enviado por formulario.
No introducir verificación adicional de CLIENTE sin una política vigente que la exija;
la verificación aprobada es obligatoria para el profesional. Ownership antes de replay.

Propuesta de cancelación: solo dueño CLIENTE activo, solicitud ABIERTA → CANCELADA;
misma cancelación repetida no duplica efectos. No reabrir. Estados históricos distintos
no se reinterpretan ni habilitan operaciones nuevas; se rechaza transición incompatible.
Detalle y resultados mediante identificador siempre autorizados. Nombre de nuevas
rutas/endpoints se fija al inspeccionar routing en implementación, no se afirma que existan.

Visitante puede autenticarse antes de completar el formulario operativo. Si se
conservan campos ante sesión caducada, aplicar el patrón seguro de Presupuestos:
lista permitida, límites, TTL breve, actor/navegación/pestaña, CSRF, login interno,
limpieza tras éxito/cancelación/expiración y revalidación. Nunca guardar borrador
con datos en URL, logs, archivos adjuntos, tokens o coordenadas exactas. No prometer
recuperación indefinida ni entre dispositivos; fallback sin JS debe seguir seguro.

## 5. Guardia temporal y casos límite

> SUSTITUIDAS (2026-10-01, Cristian Sánchez): las reglas temporales de duración libre, 2/4/8 h, fila única y activar/renovar/desactivar de este antecedente. Rige la corrección focal superior; las demás reglas se conservan.

Aprobado: desactivada por defecto, voluntaria, 2/4/8 horas, una única disponibilidad
vigente por profesional, renovación explícita, cancelación anticipada, timestamps
timezone-aware, auditoría e idempotencia/concurrencia.

Elegibilidad temporal: `activa AND inicio <= ahora AND ahora < vencimiento AND no cancelada`.
El vencimiento efectivo se deriva de consulta; una fila vencida nunca aparece aunque
su flag permanezca activo. No requiere cron ni escritura para expirar cada búsqueda.

### Reglas operativas propuestas para revisión

> SUSTITUIDAS (2026-10-01, Cristian Sánchez): las reglas temporales de duración libre, 2/4/8 h, fila única y activar/renovar/desactivar de este antecedente. Rige la corrección focal superior; las demás reglas se conservan.

| Situación | Resultado especificado |
| --- | --- |
| Activación inicial/inactiva/vencida | Con elegibilidad y versión actuales, inicio=ahora y fin=ahora+2/4/8 horas |
| Repetición misma clave y payload | Retorna resultado original sin extender horario ni duplicar auditoría |
| Misma clave con otro payload/actor | Conflicto/denegación; ninguna mutación |
| Nueva activación cuando ya hay guardia vigente | 409; ofrecer renovación explícita, no extender silenciosamente |
| Renovación antes del vencimiento | Inicio=ahora y fin=ahora+duración elegida; reemplaza ventana, no suma horas al fin previo; UI informa nuevo vencimiento incluso si acorta |
| Renovación que esperaba lock y ya venció | 409; nueva activación explícita con formulario actualizado |
| Dos renovaciones distintas concurrentes | Misma versión esperada: una gana; otra 409; nunca sumar ambas ni perder actualización |
| Desactivación | Inactiva/cancelada inmediatamente en transacción; versión nueva y auditoría |
| Desactivar una fila ya inactiva/vencida | No-op autorizado, resultado idempotente; no duplicar evento de desactivación |
| Replay de activación/renovación después de desactivar | No reactiva; muestra resultado original y estado actual claramente separados |
| Suspensión, pérdida de verificación o perfil no habilitado | Exclusión inmediata; invalidar ventana sin reactivación automática al recuperar elegibilidad |
| Cambio de oficio o cobertura | Invalidar ventana y exigir nueva activación explícita con contexto actualizado |
| Cambio de nombre/foto sin impacto en elegibilidad | No extiende ni cambia ventana; no confundirlo con cambio de oficio/cobertura |
| Instante igual a inicio | Elegible si cumple los demás filtros |
| Instante igual a vencimiento | No elegible |

UTC aware en persistencia/cálculos; presentación en America/Argentina/Buenos_Aires
con zona visible. Nunca reloj del navegador. Leer reloj efectivo del servidor/base
DESPUÉS de adquirir los locks y usar el mismo instante para transición/auditoría.
No usar `now()` de inicio de transacción si la espera puede cruzar el vencimiento.
Pruebas con reloj controlado y fronteras exactas; reloj operativo sincronizado.

La invalidación por cambios de elegibilidad debe integrarse atómicamente con los
comandos que los modifican, o mediante una revisión monotónica verificable que haga
inválida la ventana anterior. Un hash reversible de campos no basta: cambiar y volver
al valor anterior no debe revivir guardia. Detalle técnico sujeto al ADR y revisión.

## 6. Modelo mínimo y migración (objetivo, no código)

> SUSTITUIDAS (2026-10-01, Cristian Sánchez): las reglas temporales de duración libre, 2/4/8 h, fila única y activar/renovar/desactivar de este antecedente. Rige la corrección focal superior; las demás reglas se conservan.

Propuesta: una fila de disponibilidad actual por Professional, FK/UNIQUE profesional,
activa por defecto false, inicio/fin aware, cancelación opcional, última actualización,
versión positiva y referencia/revisión del contexto de elegibilidad. Historial de
operaciones en auditoría existente; no borrar historial al renovar la fila actual.
Una fila por profesional es una restricción más fuerte y simple que «una vigente».

Checks: fin > inicio para una ventana emitida; campos temporales coherentes al activar;
versión positiva. No intentar UNIQUE parcial basado en `ahora`, que cambia sin escribir.
Índices: UNIQUE/FK profesional; índice de consulta activa/vencimiento y de relación con
asistencia cuando se materialice su mapeo. Confirmar plan de consulta y evitar índices
redundantes. No introducir PostGIS ni nueva infraestructura por preferencia.

Alembic obligatorio: crear disponibilidad desactivada (ausencia de fila también equivale
a desactivada); jamás convertir perfiles activos/PRO en guardias. Inspeccionar head real
antes de asignar revision/down_revision. También evaluar la persistencia privada del
contexto de ubicación por emergencia; si exige columnas/tabla, incluirla explícitamente
en la misma propuesta de esquema antes de implementar. No fijar nombres innecesarios.

Downgrade estructural posible, pero elimina ventanas/contextos nuevos y puede perder
historial si se eliminara una tabla de auditoría nueva (no recomendada). Conservar
AuditLog/OperationCommand existentes; revisar referencias a resultados eliminados para
fallar de forma controlada. Rollback de despliegue no implica ejecutar downgrade ni
reactivar solicitudes/guardias. Requiere backup/plan explícito y no se ejecuta ahora.

## 7. Matching y orden neutral

Elegibilidad conjuntiva: cuenta ACTIVA + rol PROFESIONAL + verificación aprobada +
perfil habilitado + oficio compatible + cobertura compatible + guardia vigente.
Propuesta concreta para perfil habilitado: `perfil_completo` y estado VERIFICADO,
coherentes con la política existente de elegibilidad formal; utilizar evaluador común
sin trasladar requisitos ajenos de contratación. La política final debe quedar única.
PRO, popularidad, rating y presencia visual no otorgan elegibilidad.

Tras filtrar, orden lexicográfico: (1) exactitud con asistencia; (2) cobertura compatible;
(3) menor distancia aproximada si está disponible; (4) rating verificable como desempate;
(5) nombre normalizado e ID estable. No volver a premiar verificación obligatoria.
No consulta a plan PRO para elegir prioridad. Ausencia de rating no se inventa como
reseña cero; queda detrás de rating comparable solo en su nivel de desempate.

Con coordenadas válidas: Haversine <= radio declarado. Fuera de cobertura excluido,
no solo colocado al final. Si no hay coordenadas/radio suficientes, fallback a zona
pública declarada normalizada con coincidencia explícita; mostrar «cobertura declarada»,
no «comprobada». Propuesta: cobertura geométrica comprobada antes de textual declarada;
distancias desconocidas nunca se reemplazan por cero. Si no se puede establecer ninguna
compatibilidad, excluir del listado de guardia. La tokenización/aliases de localidades
requieren pruebas; no considerar una coincidencia arbitraria por substring como prueba.
No exigir geolocalización del dispositivo para usar el formulario.

El matching es síncrono: no polling/colas. Paginar después de filtros/orden, con totales
y navegación coherentes. DTO público mínimo: ID público, nombre, oficio, zona aproximada,
verificación, vencimiento, distancia aproximada permitida y acciones autorizadas.
Nunca pasar un ORM completo como contrato público.

## 8. Creación atómica, idempotencia y ciclo de solicitud

Reutilizar OperationCommand canónico y su resultado genérico; no otro ledger ni
infraestructura. Formulario con clave criptográfica servidor ligada a actor y operación,
formato/longitud validados. Autorizar antes de resolver replay, incluso con clave válida.
Payload canónico de campos permitidos y contexto privado; mismo payload/clave devuelve
mismo resultado, otro payload 409; claves nuevas permiten necesidades distintas.

Una transacción: autorización, comando, EmergencyRequest ABIERTA, notificación INTERNAL
al cliente, auditoría sin descripción/coordenadas sensibles y resultado del comando.
Un commit final; helpers sin commit; cualquier fallo revierte todos los hechos y deja
sesión utilizable. Doble clic/reenvío/concurrencia no duplica solicitud ni notificación.
CSRF y rate limiting siguen activos; JavaScript es apoyo UX, nunca idempotencia durable.
No hay asignación, invitación ni contrato al crear o al contactar.

Propuesta de límites: ID de asistencia permitido, barrio/localidad 1–120 caracteres y
descripción 1–600, tras trim. Prioridad técnica ALTA derivada por servidor: no aceptar
prioridad, owner, estado o IDs internos del formulario como autoridad. Rechazar valores
inválidos conservando campos permitidos y errores accesibles. No persistir primero para
luego descubrir un filtro inválido. Mantener 10 POST/día existentes hasta decisión nueva;
replay también cuenta como petición, sin duplicar efectos. Documentar respuesta 429.

## 9. Privacidad, ubicación y contacto

Resultados por ID/contexto opaco del servidor; un ID no es un permiso. Autenticación y
ownership obligatorios en detalle/resultados/cancelación/contacto asociado. Las rutas
públicas legacy no deben permitir recuperar una emergencia ajena ni simular confirmación.

Coordenadas exactas solo en contexto privado servidor, con consentimiento cuando se
obtengan del dispositivo. Nunca en query string, referrer, logs, HTML público, atributos
data, JSON público o auditoría de payload. Preferir barrio/localidad público y resolver
coordenadas en servidor; un centroide de localidad no es ubicación exacta del cliente
ni justifica precisión falsa. Datos exactos opcionales no bloquean fallback textual.
Definir retención mínima y purga del contexto privado antes de habilitar su captura;
no tomar la cookie firmada legible de Flask como depósito de coordenadas secretas.

WhatsApp continúa centralizado. Si llega emergency_id: requerir actor CLIENTE autenticado,
activo y dueño ANTES de asociar, incluso si el directorio era público. Revalidar guardia,
cuenta, rol, verificación, perfil, oficio, cobertura y solicitud ABIERTA inmediatamente
antes de registrar contacto y generar salida. Revalidación/versiones deben serializarse
con desactivación/cambios de contexto; si vence mientras se espera, rechazar y refrescar.
Una vez emitido contacto, no prometer reservar capacidad ni impedir expiración posterior.

Errores no deben revelar existencia/datos privados de solicitudes ajenas. Sin consentimiento
no se abre WhatsApp. `source_path` no guarda URL/referrer completo: solo ruta permitida,
sin parámetros privados. Evitar números en HTML listado; resolver teléfono/contacto en
acción autorizada, con consentimiento y validación equivalentes para llamada asociada.
La eventual URL tel/wa.me necesariamente entrega el destino al cliente autorizado;
no prometer anonimato técnico del número tras consentir. Sin JS: confirmación nativa
servidor y POST CSRF, no campo oculto que solo JavaScript pueda completar.

Textos obligatorios en resultado: «Guardia vigente hasta …» y «Confirmá disponibilidad
con el profesional». No «llega inmediatamente», «respuesta garantizada», «disponible 24/7»,
ETA inventado ni asignación confirmada. Cambió elegibilidad: explicar que ya no puede
iniciarse ese contacto desde Emergencias y permitir actualizar resultados.

## 10. UX-07A.2: experiencia visual

DS v2 canónico, v1 conceptual. Hero con seis fotografías, overlay rojo oscuro localizado,
título fijo «Buscá ayuda para una urgencia», texto sobre fotografía legible en ambos
temas y superficies neutras fuera del hero. Corregir token inverso que en oscuro se
vuelve negro; contrastar cada foto/transición, no solo el color de overlay aislado.

Carrusel derecha→izquierda, unos 6 s, transición 600–750 ms sin flashes; anterior/siguiente,
indicadores nombrados y pausa/reanudación. Pausa por foco, interacción, toque y pestaña
oculta; reanudación explícita tras pausa manual. Soporte táctil obligatorio, teclado completo;
no mover foco con autoplay ni anunciar cada cambio decorativo a lectores de pantalla.
Primera imagen src real/prioritaria, dimensiones reservadas, object-fit cover; carga
progresiva con fallback al fallar foto. Reduced motion: cero autoplay y animación;
manual inmediato disponible. Sin JS: primera fotografía visible y formulario funcional.

Reutilizar núcleo adecuado existente: Mercados tiene desplazamiento solicitado, Home
carga/controles, Explorar fundido. Extraer módulo configurable con adaptadores, no copiar
un carrusel entero ni cambiar globalmente otras superficies. Preservar contratos y
pruebas de Home/Explorar/Mercados; extracción exacta sujeta a inspección de implementación.

### Inventario aprobado de imágenes

Origen externo: `C:\Users\Cristhian\Downloads\MANDOBRA_IMG_EMERGENCIA`.
Destino previsto: `app/static/images/emergencias/hero/`.

| Original | Salida prevista | Asistencia |
| --- | --- | --- |
| 01.png | electricista-tablero.webp | Electricidad |
| 02.png | plomero-desague.webp | Plomería |
| 03.png | cerrajero-hogar.webp | Cerrajería del hogar |
| 04.png | cerrajero-automotor.webp | Cerrajería automotor |
| 05.png | auxilio-vehicular-auto.webp | Auxilio vehicular para automóvil |
| 06.png | auxilio-movil-moto.webp | Auxilio móvil para motocicleta |

Preflight: seis PNG RGB 1448×1086, 4:3, sin ICC declarado, decodificación correcta y
hashes distintos. No convertir en esta fase documental. Conservar PNG externos.
WebP principal 1448×1086; 960×720 solo si beneficio demostrado. Optimizar y validar cada
imagen, foco propio por breakpoint, sin recorte universal automático. Presupuesto objetivo
propuesto <=150 KB principal y <=100 KB variante; si no preserva calidad, registrar y
revisar, no ocultar degradación. No ampliar resolución ni asumir perfil ICC inexistente.
Fotografías decorativas alt vacío si texto HTML ya comunica asistencia; selección con
etiqueta nativa siempre nombrada. Manos, cerraduras, herramientas y ruedas no deben
perderse en recortes; móvil puede separar franja 4:3 y contenido para evitarlo.

### Formulario, skeleton y vacío

Tipo de asistencia + barrio/localidad + descripción breve + «Buscar ayuda ahora».
Seis radios nativos opcionalmente ilustrados, fieldset/legend, texto visible, selección
sin depender del color, foco y teclado; servidor revalida. Errores por campo y resumen
con foco, sin perder valores permitidos. No controles que el backend no utilice.

Reutilizar UX-04B: validación antes, demora 300 ms, a los 8 s mensaje prolongado,
sin porcentajes/cantidades inventadas, limpieza pageshow/bfcache/cancelación, reduced
motion y navegación nativa sin JS. Geometría de listado opcional, mismo controlador.
No bloquear validación, controles manuales ni errores amistosos. Conservar contratos
403/404/500/503 y errores de formulario específicos 400/409/429 sin secretos.

Vacío: «No encontramos profesionales con guardia vigente para este servicio y zona.»
Acciones: cambiar asistencia/zona, volver al formulario y directorio general con
advertencia de disponibilidad no verificada. Nunca rellenar con profesionales no elegibles.
Solo «Solicitud registrada» tras comprobar servidor/existencia/propiedad; no por query.

Aviso visible: «Primero, protegé a las personas.» MANDOBRA no reemplaza policía,
bomberos, emergencias médicas, defensa civil ni prestadores oficiales de gas/electricidad.
Ante incendio, fuga grave, riesgo eléctrico inmediato o peligro personal, contactar
primero servicios oficiales. No inventar números universales ni garantías de atención.

Responsive: 1440/1024/768/390/320 px, ambos temas, reflow real al 200 %, sin overflow
persistente, controles >=44×44, orden de lectura y foco visibles, contraste texto normal
>=4.5:1 y controles/texto grande >=3:1. No usar swipe obligatorio ni alto fijo que corte
texto. Validar todas las fotografías y todos los estados, no solo la primera pantalla.

## 11. Criterios verificables y matriz mínima

Todos los criterios están PENDIENTES de implementación y ejecución; no hay casillas
marcadas como aprobadas por Testing.

| ID | Dado / cuando / entonces | Prueba mínima |
| --- | --- | --- |
| CA-01 | Dado el catálogo, elegir cualquiera de seis IDs resuelve su nodo; alias ambiguo/desconocido falla sin mapear a otro oficio | Unitarias de normalización y rutas con legacy |
| CA-02 | Visitante/PRO/admin no persisten como CLIENTE; cliente inactivo tampoco; propietario activo opera solo lo propio | Rutas + servicios, roles/ownership/IDOR |
| CA-03 | Propietario elegible reserva bloques diurnos 07–19 o nocturnos 19–07 de 12 h, múltiples y consecutivos; T−2 min inclusivo; sin duplicados ni ingreso iniciado; horarios/owner inválidos se rechazan | Unitarias focales; integración y PostgreSQL pendientes |
| CA-04 | En inicio exacto es temporalmente elegible; en fin exacto no; nunca depende de cron | Reloj controlado y PG tras espera de lock |
| CA-05 | Reserva requiere aceptación expresa; confirmación inmediata; T−6 h y T−1 h solo futuros; fronteras exactas omiten avisos vencidos; reserva tardía no genera retroactivos | Unitarias focales; integración y PostgreSQL pendientes |
| CA-06 | Reservas concurrentes del mismo profesional/bloque no duplican; bloques distintos y consecutivos se permiten | Unitarias focales; integración y PostgreSQL pendientes |
| CA-07 | Replay de reserva no duplica bloques, aceptación, confirmación ni recordatorios; no cambia inicio/fin ni revive un bloque vencido o invalidado | Unitarias focales; integración y PostgreSQL pendientes |
| CA-08 | Suspensión/pérdida de verificación/oficio/cobertura invalida; restaurar datos no revive ventana | Integración de políticas + PG concurrencia |
| CA-09 | Misma clave/payload devuelve mismo resultado; otro actor/payload falla; claves diferentes permiten creaciones deliberadas | Ruta, servicio, doble clic/reenvío/replay |
| CA-10 | Fallo de notificación/auditoría revierte solicitud/comando/hechos; sesión reutilizable y retry único | Inyección de fallos + PostgreSQL rollback |
| CA-11 | Solo conjunción completa de filtros produce candidatos; fuera de cobertura/vencidos/ambiguos quedan excluidos | Matching unitario e integración |
| CA-12 | Cambiar plan PRO no altera elegibilidad ni orden; verificación no suma prioridad; empates son deterministas | Comparación de orden con mismo conjunto |
| CA-13 | Haversine se identifica aproximado; sin coordenadas solo fallback declarado compatible, no distancia ficticia | Unitarias coordenadas/radio/fallback |
| CA-14 | ID ajeno o anónimo nunca asocia contacto; guardia vencida entre listado y contacto se rechaza | Rutas, ownership, CSRF y PG temporal |
| CA-15 | No coordenadas exactas/domicilios/telefonía innecesaria en URL, referrer, HTML/JSON público ni logs | Inspección de respuestas, cabeceras y capturas de logs |
| CA-16 | CSRF inválido/XSS/campos extra/longitudes/enum fallan sin efectos y con salida escapada | Rutas negativas, seguridad y sesión |
| CA-17 | Login/errores no borran valores permitidos según contrato; cancelación solo dueño ABIERTA, no reabre | Integración ciclo + recuperación si incluida |
| CA-18 | Cada WebP decodifica, MIME/tamaño/dimensiones son correctos; originales intactos; recorte seguro en seis imágenes | Hashes, assets GET/HEAD e inspección visual individual |
| CA-19 | Carrusel 6 s y 600–750 ms, controles/indicadores/pausa/táctil/foco funcionan; foto fallida no deja hero vacío | Node y navegador real |
| CA-20 | Reduced motion no tiene autoplay; sin JS primera imagen/formulario/contacto nativo funcionan | Node + navegador sin JS/reduced motion |
| CA-21 | Formulario radios etiquetados selecciona con teclado; error enfocado no dispara navegación/skeleton | Navegador + rutas |
| CA-22 | Respuesta <300 ms no muestra skeleton; demora activa forma; a 8 s cambia mensaje; pageshow limpia | Node timers + navegación/bfcache real |
| CA-23 | Vacío no muestra guardias falsas y acciones resuelven; éxito requiere solicitud propia existente | Integración y visual |
| CA-24 | Los cinco anchos, dos temas y zoom 200 % no cortan contenido; controles 44×44, contraste/foco adecuados | getBoundingClientRect, teclado, contraste y axe complementario |
| CA-25 | Migración upgrade/downgrade y defaults no crean disponibilidad; índices/constraints se cumplen | Gate PostgreSQL exclusivo y revisión de pérdida de datos |
| CA-26 | Home/Explorar/Mercados, navbar, skeleton, errores, Presupuestos y WhatsApp conservan sus contratos | Regresiones focales y suite según Testing |
| CA-27 | Spec/ADR/índices/handoff distinguen aprobado/implementado y evidencias, sin claims falsos | Revisión documental y enlaces |

Gate PostgreSQL: base descartable exclusiva con nombre protegido y reset explícito;
no trax_db ni trax-postgres. Dos conexiones reales, barreras reproducibles, casos ganador
commit/rollback, payload diferente, unicidad, ventana vencida durante lock, invalidación
concurrente y ausencia de auditoría/notificación duplicada. SQLite solo para focales
permitidas; nunca sustituye prueba concurrente. Migración y pruebas se autorizan aparte.

## 12. Riesgos, secuencia y decisiones por revisar

Secuencia: revisar reglas propuestas → aprobar paquete .1 con esquema/retención/contexto
privado y contratos de endpoint → implementar y verificar PG/seguridad → habilitar .2 →
retest visual/funcional independiente. No autorización implícita de commit/deploy.

> SUSTITUIDAS (2026-10-01, Cristian Sánchez): las reglas temporales de duración libre, 2/4/8 h, fila única y activar/renovar/desactivar de este antecedente. Rige la corrección focal superior; las demás reglas se conservan.

Puntos de revisión explícitos: ventana de renovación desde ahora (puede acortar),
invalidación sin resurrección, definición de perfil habilitado, fallback textual de
localidades, retención del contexto exacto si se habilita, y flujo nativo de contacto
sin revelar teléfonos antes de autorizar. Ninguno habilita sustituciones silenciosas.
Si faltan políticas de ubicación exacta, usar barrio/localidad y no capturar coordenadas
privadas hasta definirlas. No bloquear el formulario por permisos de geolocalización.

## 13. Evidencia de implementación

PENDIENTE. Esta sesión solo redacta documentación: no código, assets, migraciones,
Docker ni base de datos. El preflight anterior aportó inspección de fuentes, imágenes y
navegador; no certificó zoom 200 % ni guardias inexistentes. Ninguna prueba de este
requisito se declara ejecutada. No se sustituye el retest independiente con este texto.


### Antecedentes de criterios temporales sustituidos

SUSTITUIDOS el 2026-10-01 por Cristian Sánchez; solo evidencia histórica:

> SUSTITUIDAS (2026-10-01, Cristian Sánchez): las reglas temporales de duración libre, 2/4/8 h, fila única y activar/renovar/desactivar de este antecedente. Rige la corrección focal superior; las demás reglas se conservan.

- Criterio anterior número 03: Guardia ausente/inactiva no aparece; propietario elegible activa 2/4/8 h; otras duraciones/owner se rechazan
- Criterio anterior número 05: Renovación reemplaza desde ahora; no suma al fin anterior; activación repetida distinta devuelve conflicto
- Criterio anterior número 06: Dos activaciones/renovaciones independientes no crean dos ventanas ni pierden updates
- Criterio anterior número 07: Desactivar y repetir/replay de activación no revive ni duplica auditoría
