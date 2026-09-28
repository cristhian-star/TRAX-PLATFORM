# MANDOBRA Taxonomy v1

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
