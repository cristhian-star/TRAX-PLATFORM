---
titulo: Esquema PostgreSQL DEV desalineado con Alembic
estado: RESUELTO
fecha: 2026-10-04
componente: PostgreSQL y Alembic
entorno: local
---

# Esquema PostgreSQL DEV desalineado con Alembic

## Resumen

La base DEV informaba la revisión Alembic `20260726_07`, pero el esquema no
contenía las tablas de negocio esperadas. Solo estaba presente
`alembic_version`, junto con funciones residuales de intentos anteriores. Luego
de confirmar expresamente que la base no contenía datos que preservar, se
reconstruyó exclusivamente su esquema `public` y se aplicó la cadena completa
hasta `20260917_03`.

Este procedimiento fue una recuperación excepcional de una base vacía. No es
un mecanismo válido para reparar una base con datos.

## Síntomas observados

- `alembic_version` indicaba `20260726_07`, aunque faltaban tablas esperadas
  como `proposal_requests` y `subscriptions`.
- Los intentos de continuar desde esa marca no podían reconstruir de forma
  confiable los objetos ausentes.
- Persistían funciones creadas durante intentos anteriores, sin las tablas de
  negocio correspondientes.
- El portal de propuestas no podía considerarse operativo sobre ese esquema.

## Contexto y entorno

- Timestamp de registro: `2026-10-04T15:04:39-03:00`.
- Sistema operativo: Windows, entorno local de desarrollo.
- Rama observada al documentar: `feature/ux-ui-foundation`.
- Base afectada: base PostgreSQL DEV `trax_db`.
- Revisión declarada antes de recuperar: `20260726_07`.
- Revisión validada al finalizar: `20260917_03` (`head`).

## Investigación

Se compararon la revisión declarada, el inventario real de tablas y los objetos
residuales. La marca de Alembic no describía el esquema físico existente: la
presencia aislada de `alembic_version` no demostraba que las revisiones previas
hubieran creado sus tablas.

Los intentos de avanzar la cadena sobre esa estructura incompleta no resolvían
la causa, porque Alembic consideraba aplicadas revisiones cuyos objetos no
existían. Antes de cualquier reconstrucción se confirmó que no había filas ni
tablas de negocio que debieran conservarse.

## Causa raíz

Existía una desalineación entre el estado físico del esquema y la revisión
registrada en `alembic_version`. El origen histórico exacto de esa marca
inconsistente no quedó demostrado; no debe atribuirse a una migración concreta
sin evidencia adicional.

## Solución aplicada

Con autorización y después de verificar que no había datos que preservar:

1. se limitó la recuperación a la base DEV afectada;
2. se reconstruyó exclusivamente su esquema `public`;
3. se ejecutó la cadena Alembic completa desde un esquema vacío;
4. se verificó el head `20260917_03`;
5. se confirmó la existencia de `proposal_requests` y `subscriptions`;
6. se confirmó `GET /propuestas` con respuesta `200`.

No se copiaron datos desde SQLite ni se utilizó `stamp` para aparentar un
estado no aplicado físicamente.

## Validación

- [x] El esquema terminó en `20260917_03` (`head`).
- [x] `proposal_requests` quedó presente.
- [x] `subscriptions` quedó presente.
- [x] `GET /propuestas` respondió `200`.
- [x] Se confirmó previamente que no existían datos de negocio que preservar.
- [ ] No se repitió este procedimiento durante el Testing independiente P1.

## Prevención

- Comparar `alembic_version` con un inventario mínimo de tablas críticas antes
  de asumir que una base está correctamente migrada.
- No usar `alembic stamp` para corregir una divergencia física.
- Ejecutar migraciones destructivas solamente sobre bases descartables o con
  respaldo, autorización y plan de recuperación verificados.
- Detener el proceso si existen datos, tablas de negocio o dudas sobre el
  alcance del entorno.
- Mantener gates que validen head único y ancestros requeridos en bases
  temporales aisladas.

## Advertencia de seguridad de datos

No aplicar `DROP SCHEMA`, `DROP DATABASE`, truncados, downgrade o reconstrucción
sobre una base con datos sin respaldo comprobado y autorización explícita. La
ausencia de datos fue una precondición indispensable de esta recuperación.

## Archivos y documentos relacionados

- [QA local](../QA_LOCAL.md)
- [Propuestas P1](../REQUISITOS/PROPUESTAS_P1.md)
- [Handoff activo](../HANDOFFS/ACTIVE_HANDOFF.md)

## Palabras clave

`PostgreSQL`, `Alembic`, `alembic_version`, `schema drift`, `DEV`, `recuperación`
