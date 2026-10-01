---
id: ADR-002
titulo: Emergencias y guardia vigente
estado: APROBADO
fecha: 2026-09-27
---

# ADR-002 — Emergencias y guardia vigente

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

## Aceptación arquitectónica final — 2026-09-28

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

Retest independiente final: APROBADO, registrado el `2026-09-28T20:55:50-03:00`,
con dictamen `APROBAR_ADR002_CON_OBSERVACIONES_MENORES`.
Según ese retest comunicado por Producto, no quedan P0, P1 ni P2 pendientes.
Cristian Sánchez acepta formalmente ADR-002 y habilita exclusivamente el preflight
técnico de UX-07A.1. La implementación requiere una nueva autorización explícita.
REQ-004 conserva APROBADO COMO ESPECIFICACIÓN / IMPLEMENTACIÓN PENDIENTE.
La aprobación no equivale a validación funcional, ejecución PostgreSQL ni despliegue.
Se preservan todas las decisiones normativas y registros de PROPUESTO, EN CORRECCIÓN
y PENDIENTE DE RETEST como evidencia histórica.

### Observaciones menores

El retest registra un único P3 histórico no bloqueante: salto H1 a H3 en
ACTIVE_HANDOFF (línea aproximada 2496 en la evidencia del retest).
Queda fuera de alcance y se conserva sin corrección; no condiciona la aceptación.

## P2 residuales: territorio e IP confiable — 2026-09-28

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

### P2-01: contrato territorial determinista

Estado actual verificado: Professional.coverage_province representa provincia y
Professional.coverage_city localidad, ambos textos separados; la normalización de
formulario actual solo limpia texto y longitud.
[Modelo profesional](../../app/models/professional.py) y
[cobertura](../../app/services/coverage_service.py).
EmergencyRequest solo tiene zona como texto libre, sin campos separados de provincia
y localidad: [modelo de emergencia](../../app/models/emergency_request.py).
El matching actual usa ilike sobre zona/servicio; no cumple este contrato futuro:
[búsqueda](../../app/services/professional_service.py).
No se identificaron IDs territoriales canónicos confiables en esos modelos ni en
las migraciones inspeccionadas; no se afirma que exista un catálogo geográfico.

Fuentes futuras obligatorias:
- Profesional: provincia declarada desde coverage_province y localidad declarada desde
  coverage_city, validadas; no deducirlas de zona, coverage_location o coverage_notes.
- Emergencia: provincia y localidad declaradas separadamente por el cliente, dentro
  de campos permitidos y contexto autorizado de la solicitud. Hoy no existen ambos
  componentes estructurados: el preflight .1 debe resolver su mapeo o cambio mínimo
  de datos y su conservación antes de implementar matching. No partir zona con
  heurísticas ni permitir substring como transición.
- Si el preflight demuestra IDs canónicos confiables, podrá proponer su uso preferente
  mediante decisión explícita; no diseñar ahora catálogo nuevo ni dependencia externa.

Aplicar a ambos componentes y a ambos lados la misma función determinista:
1. Exigir valor de texto válido y no vacío; rechazar datos inválidos, ambiguos o que
   no puedan normalizarse con seguridad, sin coerción de objetos a texto.
2. Normalizar Unicode a NFC.
3. Eliminar espacios exteriores y reducir secuencias de espacios Unicode internos a
   un único espacio. Rechazar caracteres de control no espaciales o invisibles que
   impidan una interpretación segura; no eliminarlos silenciosamente.
4. Aplicar casefold y volver a NFC para obtener la clave de comparación.
5. No eliminar acentos, transliterar, expandir abreviaturas ni introducir aliases
   territoriales implícitos. Equivalencia Unicode canónica no es semejanza geográfica.

El match textual es compatible SOLO si provincia_normalizada_profesional ==
provincia_normalizada_emergencia Y localidad_normalizada_profesional ==
localidad_normalizada_emergencia. Ambos componentes son obligatorios.
Localidades homónimas requieren provincia; si aun con ambos datos existe ambigüedad,
excluir hasta resolución inequívoca en preflight. Nombres parecidos no son iguales.
Dato faltante, inválido, ambiguo, inseguro o sin correspondencia exacta excluye al
profesional para esa emergencia. Texto libre puede ayudar a buscar, no acredita cobertura.
Quedan prohibidos substring, contains, aproximación difusa, inferencias entre localidades,
código postal inferido, geocodificación implícita, distancia vial, ETA y coordenadas inventadas.
Oficio y territorio son filtros independientes: territorio coincidente no sustituye
el oficio compatible. PRO no participa. Tras filtrar, conservar el orden neutral
estable de REQ-004, incluido desempate por nombre/ID, sin distancia inventada.
No PostGIS ni catálogo geográfico nuevo. Captura/persistencia de coordenadas exactas
continúa BLOQUEADA hasta política aprobada de minimización, acceso y retención.

Casos mínimos previstos (sin ejecución ni modificación de CA-01–CA-27):
- Igualdad exacta tras normalizar ambos componentes.
- Diferencias solo de mayúsculas, espacios exteriores o internos repetidos.
- Misma provincia y distinta localidad: excluir.
- Localidad homónima en provincias diferentes: excluir.
- Provincia/localidad incompleta, inválida o ambigua: excluir.
- Coincidencia parcial/substring: excluir.
- Unicode compuesto/descompuesto equivalente: misma clave; nombres distintos,
  acentos no equivalentes y caracteres inseguros no producen coincidencia silenciosa.
- Oficio incompatible con territorio coincidente: excluir.
- Cambiar únicamente PRO no modifica elegibilidad ni orden.

### P2-02: confianza de IP y proxies para cuotas

Estado actual verificado: [security.py](../../app/utils/security.py) usa
get_remote_address() y la clave autenticada user_or_ip_rate_limit_key combina usuario
e IP; [Flask](../../app/__init__.py) inicializa Limiter con get_remote_address.
[Configuración](../../app/config/config.py) declara memory:// por defecto.
No se encontró ProxyFix ni validación de allowlist/saltos en la aplicación inspeccionada.
Esto no acredita la topología del despliegue ni una IP original confiable detrás de proxy.
El contrato siguiente es FUTURO; no se modifican configuración ni código.

Por defecto usar el peer inmediato observado por la aplicación. Nunca confiar
directamente en X-Forwarded-For, X-Real-IP, Forwarded u otro encabezado del cliente.
En modo directo ignorar esos encabezados, aunque parezcan válidos.
Solo interpretar encabezados en modo proxy explícito cuando el reverse proxy sea
conocido, el peer inmediato original pertenezca a una allowlist configurada y la
cantidad exacta de saltos confiables esté definida y validada por entorno.
La comprobación del peer se realiza ANTES de cualquier reescritura de REMOTE_ADDR.
No basta contar saltos ni usar confianza global en X-Forwarded-For.
El proxy confiable debe sanear la cadena entrante según el contrato configurado.
Cadenas con más saltos de los permitidos o inconsistentes no autorizan seleccionar
otra dirección: rechazar su interpretación; en modo proxy obligatorio, fallar cerrado.
Configuración ausente/inválida impide habilitar esa superficie en modo proxy, sin
fallback silencioso a encabezados. El modo directo válido sigue usando el peer.
Si se adopta ProxyFix o equivalente ya disponible, configurar el número exacto de
proxies y validar allowlist/topología además del middleware; ninguna dependencia nueva
por preferencia. Preflight debe fijar configuración y comportamiento cerrado por entorno.

En endpoints autenticados, clave principal de cuota = ID estable del actor autenticado,
validado por servidor, más operación protegida. IP solo como señal complementaria.
No usar IP como autorización, identidad idempotente, ownership ni sustituto del actor.
Cambiar IP no reinicia la cuota principal; usuarios distintos tras NAT tienen claves
principales distintas, aunque puedan compartir un control complementario.
Superficies anónimas usan IP solo bajo este contrato; reconocer NAT, redes compartidas,
IPv6 y rotación de direcciones. Separar cuotas por superficie/operación de riesgo.

Conservar provisionalmente 10 POST/día para creación, incluidos replays, y 10/hora
para contacto. Un 429 puede impedir ejecutar la petición, pero no altera la identidad
ni duplica efectos de OperationCommand: después de la espera se reintenta con la misma
clave/payload ante respuesta interrumpida; no rotar la clave para eludir el límite.
HTTP 429 con política de reintento y Retry-After coherentes con la ventana aplicable,
sin exponer datos sensibles. Conservar cuotas separadas y desactivación fuera de la
cuota de activar/renovar conforme a la decisión anterior.

memory:// es protección local: no comparte contadores entre procesos/réplicas y se
pierde al reiniciar. No es defensa suficiente para producción distribuida.
Antes de implementar o desplegar, el preflight debe definir y aprobar por operación:
actor/clave contabilizada, operación, ventana, cantidad, 429, política de reintento
y configuración de proxies confiables por entorno. Cifras nuevas pendientes mantienen
el gate BLOQUEADO. No introducir Redis ni prometer cuotas distribuidas inexistentes.

Minimizar IP: no incluirla innecesariamente en HTML/query strings ni logs no esenciales.
No agregarla al payload durable de dominio salvo justificación aprobada; preservar
política aplicable de privacidad/retención. Que AuditLog tenga ip_address no autoriza
su captura indiscriminada. IP nunca forma parte de la identidad de OperationCommand.

Casos mínimos previstos:
- Petición directa sin proxy; encabezados falsificados enviados directamente.
- Peer/proxy no confiable; configuración de proxy ausente o inválida.
- Proxy confiable con cantidad exacta de saltos y cadena saneada.
- Cadena con más saltos de los permitidos: rechazo según modo, sin confianza ampliada.
- Usuario autenticado que cambia IP; usuarios distintos detrás de una NAT.
- Límites separados por operación; replay antes/después de 429 sin segunda mutación.
- Respuesta 429 y reintento coherente, sin fuga de información.
- Reinicio y múltiples procesos con memory://: demostrar límites locales, no simular
  persistencia ni contador global. Ningún caso fue ejecutado en esta corrección.

### Gate residual

Retest documental y arquitectónico independiente final de ambos P2 obligatorio.
No aceptar ADR-002 ni autorizar UX-07A.1 en esta sesión. Los contratos anteriores
de habilitación, locks, temporalidad, atomicidad, resultados durables, cancelación,
contacto y downgrade permanecen sin reformulación.

## Corrección arquitectónica adoptada — 2026-09-28

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

### Modelo y temporalidad definitivos para retest

> SUSTITUIDAS (2026-10-01, Cristian Sánchez): las reglas temporales de duración libre, 2/4/8 h, fila única y activar/renovar/desactivar de este antecedente. Rige la corrección focal superior; las demás reglas se conservan.

Una fila mutable de guardia por profesional, PK propia, FK obligatoria y UNIQUE por
profesional. Ausencia de fila equivale a desactivada. El propietario se deriva de
Professional.user_id; un perfil sin propietario no puede activar guardia.
Mantener activa, starts_at, expires_at, deactivated_at, versión positiva y timestamps
de creación/actualización timezone-aware. Vencida es una condición calculada, no otro
estado persistido. No crear agenda ni historial de ventanas adicional.
La invalidación atómica definida abajo sustituye la alternativa de revisión monotónica
de elegibilidad; no agregar ese segundo mecanismo sin una necesidad adicional justificada.
Checks: fin posterior a inicio, coherencia temporal al activar y versión positiva.

> SUSTITUIDAS (2026-10-01, Cristian Sánchez): las reglas temporales de duración libre, 2/4/8 h, fila única y activar/renovar/desactivar de este antecedente. Rige la corrección focal superior; las demás reglas se conservan.

P2-2 — Renovar reemplaza la ventana: starts_at=ahora y expires_at=ahora+2/4/8 horas.
Puede acortar una ventana vigente; la interfaz debe mostrar y confirmar el nuevo
vencimiento. Leer el reloj efectivo después de adquirir locks; inicio inclusivo,
vencimiento exclusivo, UTC para cálculo/persistencia y zona local para presentación.
No renovar una guardia ya vencida, incluso si venció esperando: conflicto y nueva
activación explícita. Versión esperada obligatoria; versión obsoleta es conflicto.
Replay nunca revive una guardia vencida, cancelada o invalidada. Desactivar una guardia
ya desactivada puede ser no-op idempotente sin duplicar la transición.
La consulta no escribe expiraciones ni requiere cron.

### Habilitación e invalidación: P1-1 y P1-2

P1-1 — Elegibilidad conjunta: cuenta activa, rol PROFESIONAL, perfil_completo,
estado_perfil == VERIFICADO, verificación APROBADA de tipo PROFESIONAL, oficio,
cobertura y guardia compatibles/vigentes. PRO no habilita, filtra ni prioriza.
La aprobación de esa verificación debe efectuar la transición autorizada
PENDIENTE_VERIFICACION → VERIFICADO y su auditoría dentro de una única operación de
aplicación. No inferir habilitación por una aprobación histórica de otro tipo ni
quitar el requisito de perfil verificado. Las precondiciones incompatibles se rechazan.
has_approved_verification() no sirve para esta elegibilidad sin filtrar expresamente
tipo PROFESIONAL. No trasladar la verificación de CLIENTE de contratación a Emergencias.

P1-2 — Rechazo, revocación, suspensión, cambio de rol, pérdida de habilitación y
cambio/eliminación de oficio o cobertura invalidan mediante desactivación atómica de
la guardia vigente, aumento de versión y auditoría en la MISMA transacción del cambio.
Todos los escritores de usuario, verificación y perfil deben participar mediante
servicios componibles sin commits internos. Restaurar cuenta, rol, perfil u otros
datos nunca reactiva la guardia; exige activación explícita nueva.
Nombre/foto sin impacto en elegibilidad no cambia ni extiende la ventana.

Orden único de locks para todos los participantes, omitiendo solo filas no aplicables:

1. Usuarios involucrados, ordenados por ID.
2. Profesional.
3. Guardia.
4. Solicitud de emergencia, cuando corresponda.
5. Comando idempotente existente, cuando corresponda.

La fila de profesional serializa la primera activación cuando no existe guardia;
UNIQUE es defensa final. Locks serializan; versión optimista rechaza formularios
obsoletos. Refrescar los datos bajo lock: un objeto previamente cargado no prueba
revalidación. Cancelación, contacto y escritores de elegibilidad respetan este orden.
Autorizar antes de exponer replay y revalidar bajo locks antes de mutar.
PostgreSQL real es obligatorio para carreras; SQLite no sustituye ese gate.

### Comandos, auditoría e historial: P2-1

OperationCommand conserva identidad y resolución idempotente; guardia conserva el
estado actual; AuditLog conserva evidencia histórica. La auditoría no reconstruye
disponibilidad actual. No introducir event sourcing ni una tabla nueva de historial.
Clave emitida por servidor y vinculada criptográficamente a actor y operación,
payload canónico permitido, autorización antes del replay. Misma clave ante respuesta
interrumpida; nueva clave para nueva intención. Unicidad por actor/operación/clave no
sustituye el vínculo criptográfico ni ownership.

Activar, renovar, desactivar y los no-op necesitan resultado original durable.
La guardia mutable no puede ser el resultado histórico. Usar payload mínimo,
versionado e inmutable por contrato, limitado a:

- versión del formato;
- operación;
- resultado efectivo o no-op;
- versión anterior y nueva;
- inicio y vencimiento aplicables;
- identificadores técnicos mínimos.

Puede referenciar un evento AuditLog identificado mediante el resultado genérico de
OperationCommand, siempre que su retención y protección contra eliminación preserven
ese resultado durante toda la vida útil del replay. No incluir ubicación, teléfono ni
información sensible. Devolver el estado actual separado del resultado histórico.
Un no-op conserva resultado durable, pero no genera otra transición de desactivación.

Un commit final para mutación, comando, auditoría y notificación cuando corresponda.
Crear emergencia incluye EmergencyRequest ABIERTA y notificación INTERNAL al cliente.
Ningún helper participante confirma parcialmente. Cualquier fallo revierte todos los
hechos y permite recuperar la sesión SQLAlchemy.
Tras IntegrityError: rollback, nueva autorización, relectura y replay solo si existe
comando confirmado y compatible. Si no existe, no simular éxito; conservar error
controlado o propagar el fallo técnico correspondiente. Probar ganador que confirma
y ganador que revierte. No convertir cualquier error de integridad en replay.

### Territorio y matching: P2-3

La compatibilidad territorial exige localidad normalizada y provincia normalizada
con comparación explícita y cobertura declarada. Localidades homónimas necesitan
provincia u otro contexto inequívoco. Datos ambiguos o incompletos se excluyen del
resultado de guardia vigente; no completar ni mapear silenciosamente.
El texto libre puede ayudar a buscar, pero no acredita cobertura: ningún substring
equivalente a ilike("%zona%") es prueba de elegibilidad.
Mantener IDs de asistencia y aliases explícitos sin mapeos falsos, sin cambiar el
catálogo de seis asistencias. No PostGIS ni tablas de taxonomía nuevas.
Filtrar antes de ordenar/paginar; PRO no interviene. Distancia aproximada solo con
información válida y permitida, sin ETA ni distancia vial inventada. Fuera del radio
se excluye; lo textual se presenta como cobertura declarada, no comprobada.
La captura de geodatos exactos permanece bloqueada.

### Decisiones 6–15: contratos operativos y límites

**6. Cancelación ABIERTA.** Solo CLIENTE activo propietario; bloquear solicitud antes
de decidir ABIERTA → CANCELADA. Repetición propia ya cancelada: no-op sin duplicar
efectos; otros estados: rechazo, sin reapertura. Cancelación y contacto comparten
lock de solicitud. Un contacto ya emitido no puede revocarse retroactivamente.

**7. Ubicación/contexto.** Captura exacta BLOQUEADA hasta aprobar finalidad, campos,
acceso, retención, vencimiento lógico, purga verificable, backups y protección aplicable.
Zona aproximada y ubicación exacta son datos separados. Un contexto vencido no se usa
aunque la purga física esté pendiente. No declarar cifrado inexistente ni usar cookie
firmada como depósito secreto. Nunca coordenadas en query strings, referrers, logs,
HTML/JSON públicos o auditoría. source_path solo conserva una ruta permitida sin
parámetros privados. No inventar ahora plazo de retención ni habilitar captura.

**8. Contacto.** Exigir CLIENTE activo, ownership, solicitud ABIERTA, consentimiento,
guardia vigente y elegibilidad completa. Incluir solicitud en locks, refrescar datos
y leer reloj después de esperar. Registrar contacto y auditoría, confirmar antes de
entregar destino. Ninguna llamada externa dentro de la transacción. No reservar
capacidad ni prometer disponibilidad posterior. Mantener servicio WhatsApp centralizado
y autorización equivalente para llamada asociada; no divulgar teléfono en listados.

**9–10. OperationCommand, locks y versión.** Rigen los contratos anteriores; integrar
todos los escritores antes de habilitar el flujo, no solo las nuevas rutas.
La emisión del contacto no es aceptación, asignación ni contratación.

**11. Downgrade.** Pérdida de ventanas exige precondiciones, respaldo y autorización.
Nunca eliminar AuditLog/OperationCommand compartidos. Re-upgrade no reactiva ventanas;
replay posterior no recrea guardias históricas. Resultados retirados fallan controladamente.
Diferenciar rollback de aplicación de downgrade; no afirmar reversibilidad sin pérdida.

**12. Rate limiting — P2-4.** Creación conserva provisionalmente 10 POST/día y los
replays cuentan. Contacto conserva provisionalmente 10/hora. La clave actual combina
usuario e IP para autenticados; memory:// no ofrece cuota distribuida global.
No afirmar garantía independiente de IP o proceso ni protección productiva distribuida.
Activar y renovar requieren un límite separado por actor con control complementario
por IP. Desactivar no comparte su cuota. Cancelación y contacto tienen límites propios.
HTTP 429 para exceso. La cifra de operaciones nuevas y el alcance de cada cuota son
decisiones obligatorias del preflight UX-07A.1; sin resolverlas no se habilitan.
No incorporar Redis por este hallazgo.

**13. Endpoints mínimos (contratos, no URLs existentes).** GET solo lecturas;
detalle/resultados asociados siempre autorizados. POST con CSRF para crear, cancelar,
activar, renovar, desactivar y contactar. Actor/propietario derivados de sesión;
allowlist de campos, duración, clave y versión esperada cuando correspondan.
400 para validación, 409 para conflicto, 429 para límites; denegar sin revelar solicitudes
ajenas. POST exitoso redirige a lectura autorizada; para contacto externo, primero
confirmación nativa autorizada y luego salida al destino conforme al contrato de contacto.
Funcionamiento básico sin JavaScript. Replay nunca simula creación nueva.
Nombres concretos de rutas y contratos de respuesta se fijan en preflight antes de
implementar; no se afirma que existan endpoints nuevos.

**14. Índices PostgreSQL.** Candidatos: UNIQUE por profesional e índice de vencimiento
para filas activas/no desactivadas, con predicado estático. No now() en predicados ni
duplicar UNIQUE. Resolver mapeo de asistencia antes de indexarlo; validar planes con
volumen representativo en entorno autorizado. Rendimiento no probado.

**15. Auditoría/historial.** Rige la separación anterior. Proteger el resultado durable
referenciado contra modificación/eliminación durante replay; definir su vida útil y
retención antes de implementar. No confundir esa retención con la del contexto privado.

### Evidencia y retest pendientes

La revisión del código confirma dependencias todavía sin corregir:
[perfil](../../app/services/professional_service.py),
[verificación](../../app/services/verification_service.py),
[usuarios](../../app/services/user_service.py),
[comando](../../app/models/operation_command.py),
[auditoría](../../app/models/audit_log.py),
[contacto](../../app/services/whatsapp_contact_service.py),
[cuotas](../../app/utils/security.py) y [configuración](../../app/config/config.py).
No se declara que esos servicios ya cumplan este contrato.

Conservar CA-01–CA-27 de [REQ-004](../REQUISITOS/REQ-004-emergencias-guardia-vigente.md).
Ampliar escenarios previstos de habilitación, restauración sin resurrección, tipo de
verificación, orden de locks, cancelación/contacto, replay/no-op, rollback y sesión,
localidades homónimas/incompletas, límites por actor/IP/proceso y ausencia de geodatos.
Retest documental y arquitectónico independiente obligatorio antes de aceptar ADR-002.
UX-07A.1 sigue bloqueado; UX-07A.2 depende de .1 implementado y verificado.

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

Registro: `2026-09-27T23:14:25-03:00`. Responsable de Producto: Cristian Sánchez; redacción: Codex, laptop MANDOBRA.
Rama: `feature/ux-ui-foundation`. HEAD: `4489c5c208245368a2a9bfd1672a261cf3004c93`.
Motivo: formalizar el preflight UX-07A aprobado y la decisión de Producto de
`2026-09-27T23:03:15-03:00`, `APROBADO PARA ESPECIFICACIÓN`.
Estado: especificación para revisión; implementación PENDIENTE. El preflight es el
antecedente de inspección del chat, no evidencia de guardias implementadas.
Orden neutral: PRO no habilita ni prioriza Emergencias; verificación es filtro obligatorio,
no privilegio adicional de orden. Próximo paso: revisar REQ-004/ADR-002 y autorizar
UX-07A.1; UX-07A.2 depende de su verificación.

## Contexto y autoridad

[REQ-004](../REQUISITOS/REQ-004-emergencias-guardia-vigente.md) contiene las decisiones
aprobadas para especificación y las reglas operativas propuestas para revisión. Este ADR
no aprueba implementación ni convierte el antecedente conceptual de guardias en código.
El estado actual no dispone de disponibilidad temporal persistida; actividad de cuenta
y plan PRO no acreditan una guardia. El orden objetivo supera para Emergencias la
priorización PRO de antecedentes históricos, pero no modifica todavía el comportamiento.

## Decisión propuesta

> SUSTITUIDAS (2026-10-01, Cristian Sánchez): las reglas temporales de duración libre, 2/4/8 h, fila única y activar/renovar/desactivar de este antecedente. Rige la corrección focal superior; las demás reglas se conservan.

1. Mantener el monolito modular y servicios existentes. Una fila de disponibilidad actual
   por profesional, con FK única, es una restricción más fuerte que una única ventana
   vigente. Guardar inicio/vencimiento timezone-aware, indicador activo, cancelación,
   versión y revisión de elegibilidad; historial mediante AuditLog existente.
2. La consulta exige `activa AND inicio <= ahora AND ahora < vencimiento AND no cancelada`
   además de cuenta activa, rol PROFESIONAL, verificación aprobada, perfil habilitado,
   oficio y cobertura compatibles. Default sin guardia. Duraciones 2/4/8 horas.
3. Activar/renovar/desactivar requiere ownership, autorización en ruta y servicio y CSRF
   donde corresponda. Serializar por profesional y comprobar versión. La fila ausente
   requiere un punto de bloqueo estable (por ejemplo, profesional) y constraint UNIQUE;
   no basta SELECT FOR UPDATE sobre una fila inexistente. Definir orden consistente de
   locks entre guardia y cambios de elegibilidad, con pruebas de carreras y rollback.
4. Usar UTC para persistencia y reloj confiable de servidor/DB evaluado después de adquirir
   locks. El `now()` de inicio de transacción PostgreSQL puede quedar obsoleto tras esperar:
   no utilizarlo como prueba final de vigencia. Inicio inclusivo y vencimiento exclusivo.
   Mostrar fecha/hora local con zona, sin interpretar fechas naive como ventanas activas.
5. Reutilizar OperationCommand. Autorizar antes del replay; vincular clave a actor y
   operación y comparar payload canónico. Solicitud, comando, notificación interna y
   auditoría se confirman en una transacción. Ningún helper debe hacer commit intermedio.
   No incorporar una segunda infraestructura de comandos ni efectos externos dentro de
   esa transacción. El contacto WhatsApp continúa por su servicio centralizado.
6. Para comandos de guardia, conservar resultado original inmutable y correlación durable
   con auditoría existente: apuntar solamente a la fila mutable de disponibilidad no basta
   para reproducir el resultado. Revisar capacidades de OperationCommand/AuditLog durante
   implementación; no fijar nombres ni duplicar un ledger. Replay no ejecuta transiciones
   ni revive guardias desactivadas. Si se muestra estado actual, distinguirlo del resultado
   histórico. No incluir coordenadas, teléfonos ni descripción sensible en la auditoría.
7. Suspensión, pérdida de verificación, cambios de oficio/cobertura invalidan la ventana.
   Usar desactivación atómica o revisión monotónica de elegibilidad: comparar solo valores
   actuales no detectaría cambio y posterior restitución. Restaurar datos no reactiva.
   Las lecturas no renuevan guardias ni escriben eventos de expiración por cada consulta.
8. Filtrar antes de ordenar: asistencia exacta, cobertura, distancia aproximada válida,
   rating verificable solo como desempate posterior y nombre/ID estable. PRO nunca entra
   en el ranking. Haversine no representa ruta ni ETA. Excluir fuera de radio; fallback
   textual solo para cobertura declarada compatible, identificado y sin distancia ficticia.
9. Resultados privados por solicitud/contexto seguro de servidor, con ownership. DTO mínimo:
   cobertura y distancia aproximada permitida; no puntos exactos/domicilios ni teléfonos
   prematuros. No coordenadas en URLs, referrers, HTML público ni logs. No usar una cookie
   firmada como almacén secreto. Retención debe decidirse antes de capturar ubicación exacta.
10. Revalidar elegibilidad y ownership al contactar, sincronizado con desactivación y cambios
    de elegibilidad. No equivale a reserva o aceptación. Un emergency_id anónimo/ajeno se
    rechaza antes de asociar el contacto. Consentimiento, CSRF y límites existentes se
    conservan; fallback nativo debe funcionar sin divulgar teléfonos anticipadamente.

Renovación desde ahora reemplazando la ventana, cancelación de solicitud solo ABIERTA,
perfil completo como habilitación y fallback textual son propuestas expresas de REQ-004
para revisión. No constituyen decisiones de Producto adicionales ya aprobadas.

## Alternativas consideradas

- Booleano indefinido: descartado, no satisface vencimiento ni duración voluntaria.
- Constraint parcial dependiente de ahora: no representa una invariante temporal estable;
  se propone unicidad por profesional y elegibilidad calculada, no un índice basado en NOW.
- Múltiples ventanas/agenda recurrente: complejidad innecesaria fuera de alcance.
- Cron como fuente de vigencia: descartado; limpieza futura no determina elegibilidad.
- Redis, colas o un nuevo ledger: no necesarios; reutilizar PostgreSQL y servicios actuales.
- Orden comercial PRO: contrario a la decisión neutral aprobada.

## Consecuencias, migración y reversión

Se requiere Alembic en UX-07A.1, sin crear migración en esta sesión. Inspeccionar entonces
head real y esquema. Constraints de FK/unicidad, fin mayor que inicio y coherencia de
campos; índices por profesional y filtros de actividad/vencimiento según consulta real.
No activar guardias de datos existentes. Contexto geográfico privado puede requerir
persistencia adicional, pendiente de política y revisión del esquema.

Downgrade puede perder ventanas y contexto nuevos: documentar respaldo y pérdida antes
de ejecutarlo; preservar AuditLog/OperationCommand existentes y resolver referencias a
resultados retirados con error controlado, nunca borrando infraestructura compartida.
No afirmar reversibilidad sin pérdida. Cambios de elegibilidad compartidos requieren
regresión de sus consumidores; ninguna modificación transversal se autoriza aquí.

## Garantías y evidencia requerida

PostgreSQL real y descartable exclusivo como gate: dos conexiones, barreras, unicidad,
versión, autorización antes de replay, doble envío, conflicto de payload, ganador que
confirma/revierte, rollback de notificación/auditoría, expiración mientras espera lock,
invalidación y contacto concurrentes. SQLite solo en focales autorizadas; no reemplaza
concurrencia PostgreSQL. No usar trax_db ni alterar trax-postgres.

Seguridad: CSRF, XSS, IDOR, mass assignment, privacidad de logs/referrer/respuestas y
rechazo de asociación anónima. UX-07A.2 queda subordinado a esas garantías y reutiliza
Design System v2, skeleton UX-04B y errores amigables. Matriz CA-01–CA-27 en REQ-004.
Evidencia ejecutada de implementación: PENDIENTE; esta sesión solo documentación.

## Sustitución y referencias

No sustituye ADR-001 ni los contratos de Presupuestos, pagos o contratación. Complementa
[decisiones](../DECISIONES_ARQUITECTURA.md) y [Master Spec](../REQUISITOS/MASTER_SPEC.md).
Una revisión futura debe registrar aceptación o sustitución de este ADR sin borrar su
historia; aprobación de especificación no equivale a aprobación de ejecución.
