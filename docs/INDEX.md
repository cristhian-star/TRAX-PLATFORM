# Centro documental de MANDOBRA

Esta carpeta es la fuente documental canonica del proyecto MANDOBRA y puede
abrirse directamente como una boveda de Obsidian.

## Como interpretar la informacion

La prioridad de las fuentes es:

1. Codigo, migraciones y pruebas ejecutables.
2. Requisitos aprobados y decisiones vigentes.
3. Documentacion operativa y tecnica validada.
4. Documentos de sprint e historial.
5. Ideas, borradores e investigacion aun no aprobada.

Si un documento contradice al codigo o a una migracion aplicada, no debe
corregirse silenciosamente: se registra la inconsistencia y se determina cual
de las dos partes debe cambiar.

## Navegacion principal

### Producto y alcance

- [Master Spec](REQUISITOS/MASTER_SPEC.md)
- [Roadmap](ROADMAP.md)
- [Backlog](BACKLOG.md)
- [Taxonomia del producto](trax-taxonomy-v1.md)
- [Requisitos](REQUISITOS/README.md)

### Estado documental

- [Auditoria documental del 2026-08-31](AUDITORIA_DOCUMENTAL_2026-08-31.md)

### Arquitectura y datos

- [Decisiones de arquitectura](DECISIONES_ARQUITECTURA.md)
- [ADR individuales](ADR/README.md)
- [Alembic](alembic.md)
- [PostgreSQL de desarrollo](postgres_dev.md)

### Desarrollo y calidad

- [Estandares de desarrollo](ESTANDARES_DESARROLLO.md)
- [QA local](QA_LOCAL.md)
- [Handoffs tecnicos](HANDOFFS/README.md)
- [Troubleshooting](TROUBLESHOOTING/README.md)
- [Runbooks](RUNBOOKS/README.md)

### Experiencia visual

- [Design System v2](DESIGN_SYSTEM_V2.md)
- [Design System v1](design-system-v1.md)

### Historia del proyecto

- [Changelog](CHANGELOG.md)
- [Documentacion de sprints](SPRINTS/)

### Reglas y plantillas

- [Guia de documentacion](GUIA_DOCUMENTACION.md)
- [Plantillas](PLANTILLAS/README.md)

## Separacion respecto del segundo cerebro

`docs/` contiene conocimiento especifico, vigente y verificable de MANDOBRA.
El segundo cerebro personal puede conservar ideas, aprendizaje e investigacion
transversal. Cuando una idea sea aprobada para MANDOBRA, debe formalizarse aqui
como requisito, decision, riesgo o tarea.

## Seguridad

No se almacenan contrasenas, tokens, claves privadas, archivos `.env`, datos
personales reales ni volcados de bases de datos en esta boveda.
