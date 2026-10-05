# MANDOBRA Taxonomy v1

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

## UX-07A — Estado arquitectónico aprobado — 2026-09-28

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

[ADR-002](ADR/ADR-002-emergencias-guardia-vigente.md) APROBADO tras el retest
independiente final APROBADO del `2026-09-28T20:55:50-03:00`.
[REQ-004](REQUISITOS/REQ-004-emergencias-guardia-vigente.md) conserva
APROBADO COMO ESPECIFICACIÓN / IMPLEMENTACIÓN PENDIENTE.
Emergencia y guardia vigente mantienen sus significados, identificadores, asistencias
y reglas de matching aprobados. No se agregan categorías ni se cambian equivalencias.
Solo se habilita el preflight de UX-07A.1; UX-07A.2 continúa bloqueado hasta completar
y aprobar UX-07A.1. Esta alineación de estados no implementa el catálogo ni disponibilidad.

## UX-07A — Comparación territorial exacta — 2026-09-28

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

Contrato normativo: [ADR-002](ADR/ADR-002-emergencias-guardia-vigente.md#p2-residuales-territorio-e-ip-confiable--2026-09-28) y
[REQ-004](REQUISITOS/REQ-004-emergencias-guardia-vigente.md#p2-residuales-contrato-aplicable--2026-09-28).
No cambia ningún ID de asistencia ni alias de oficio. Compatibilidad de oficio y
territorio independientes. Match territorial exige provincia Y localidad exactas tras
la normalización normativa común; la referencia previa a otro contexto no permite
omitir provincia o localidad. Excluir dato ambiguo/incompleto o coincidencia parcial.
Profesional: coverage_province/coverage_city; emergencia: mapeo estructurado pendiente
del preflight, pues zona libre no basta. No catálogo geográfico nuevo ni IDs canónicos
supuestos. PRO neutral; no geocodificación ni coordenadas exactas habilitadas.
Las pruebas territoriales se especifican en ADR-002/REQ-004, sin cambiar CA-01–CA-27.

## Corrección territorial UX-07A — 2026-09-28

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

La [corrección de REQ-004](REQUISITOS/REQ-004-emergencias-guardia-vigente.md#corrección-normativa-para-retest--2026-09-28)
y [ADR-002](ADR/ADR-002-emergencias-guardia-vigente.md#corrección-arquitectónica-adoptada--2026-09-28)
mantienen los seis IDs y aliases de asistencia. No cambian el catálogo estático ni
convierten términos de búsqueda en permisos.
P2-3 queda precisado: localidad normalizada y provincia normalizada, comparación
explícita con cobertura declarada, sin completar ni mapear silenciosamente. Homónimos
requieren provincia u otro contexto inequívoco. Datos ambiguos o incompletos se
excluyen del resultado de guardia vigente. Texto libre puede orientar búsqueda,
pero ilike("%zona%") o cualquier substring no acredita elegibilidad territorial.
Sin PostGIS, tablas nuevas de taxonomía ni autorización de coordenadas exactas.
Pruebas previstas: localidad/provincia compatibles e incompatibles, homónimos,
acentos/case/espacios, ausencia de contexto, datos incompletos y rechazo de substring.
Todo permanece documental: ninguna prueba ejecutada ni taxonomía de código modificada.

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

## Objetivo

Preparar una capa unica de clasificacion para que los modulos publicos y operativos de MANDOBRA puedan converger sobre el mismo arbol:

```text
Industria
  Categoria
    Rubro
      Especialidad
```

La implementacion v1 es deliberadamente no invasiva: no reemplaza buscadores existentes, no cambia pantallas y no modifica modelos principales.

## Decision tecnica

En esta etapa la taxonomia vive en `app/services/taxonomy_service.py` como estructura estatica versionada en codigo.

Motivos:

- Evita una migracion prematura mientras el producto todavia valida nombres y jerarquias.
- Mantiene compatibilidad con campos actuales como `servicio`, `categoria`, `rubro`, `especialidad` y `zona`.
- Permite que Explorar, Presupuestos, Emergencias, Propuestas, Mercados y Dashboard adopten helpers comunes en futuros sprints.

## Helpers disponibles

- `obtener_industrias()`
- `obtener_categorias(industria=None)`
- `obtener_rubros(industria=None, categoria=None)`
- `obtener_especialidades(industria=None, categoria=None, rubro=None)`
- `buscar_por_taxonomia(...)`
- `resolver_termino_legacy(...)`

## Compatibilidad legacy

La funcion `resolver_termino_legacy()` permite mapear entradas actuales como:

- `servicio`
- `categoria`
- `rubro`
- `especialidad`

a nodos de la taxonomia sin exigir cambios visuales ni de base de datos.

## Migracion futura sugerida

Cuando la taxonomia sea estable, puede migrarse a tablas:

- `industries`
- `taxonomy_categories`
- `rubros`
- `specialties`

con claves foraneas jerarquicas y slugs unicos. En v1 no se crean tablas porque no aportan valor inmediato y podrian rigidizar una nomenclatura que todavia puede cambiar.

## UX-07A — Extensión propuesta del catálogo de asistencias

Registro: `2026-09-27T23:14:25-03:00`. Responsable de Producto: Cristian Sánchez; redacción: Codex, laptop MANDOBRA.
Rama: `feature/ux-ui-foundation`. HEAD: `4489c5c208245368a2a9bfd1672a261cf3004c93`.
Motivo: formalizar el preflight UX-07A aprobado y la decisión de Producto de
`2026-09-27T23:03:15-03:00`, `APROBADO PARA ESPECIFICACIÓN`.
Estado: especificación para revisión; implementación PENDIENTE. El preflight es el
antecedente de inspección del chat, no evidencia de guardias implementadas.
Orden neutral: PRO no habilita ni prioriza Emergencias; verificación es filtro obligatorio,
no privilegio adicional de orden. Próximo paso: revisar REQ-004/ADR-002 y autorizar
UX-07A.1; UX-07A.2 depende de su verificación.


Las seis categorías visibles aprobadas son asistencias de Emergencias, no seis nuevas
categorías estructurales obligatorias. Tabla completa de IDs, legacy, sinónimos y reglas:
[REQ-004, catálogo](REQUISITOS/REQ-004-emergencias-guardia-vigente.md).

| Asistencia visible | ID propuesto | Ubicación estructural propuesta |
| --- | --- | --- |
| Electricidad | electricidad | Construcción / Electricidad / Electricista |
| Plomería | plomeria | Construcción / Plomería / Plomero |
| Cerrajería del hogar | cerrajeria-hogar | Hogar / Cerrajería / Cerrajero del hogar |
| Cerrajería automotor | cerrajeria-automotor | Movilidad / Cerrajería automotor / Cerrajero automotor |
| Auxilio vehicular para automóvil | auxilio-vehicular-auto | Movilidad / Auxilio vehicular / Auxilio para automóvil |
| Auxilio móvil para motocicleta | auxilio-movil-moto | Movilidad / Auxilio vehicular / Auxilio para motocicleta |

Electricidad/Plomería conservan compatibilidad conocida; los otros nodos son propuestas
nuevas, no valores ya desplegados. Sinónimo es término de búsqueda, no especialidad ni
permiso de disponibilidad. Cerrajero/auxilio genérico no resuelve hogar/automotor/moto.
Desconocidos o ambiguos generan validación sin persistir ni mapear a otro oficio.
No backfill automático, tablas de taxonomía ni cambios al servicio estático en esta sesión.
La futura incorporación debe preservar consumidores y datos existentes mediante pruebas.
