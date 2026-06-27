# TRAX Taxonomy v1

## Objetivo

Preparar una capa unica de clasificacion para que los modulos publicos y operativos de TRAX puedan converger sobre el mismo arbol:

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
