# Guia de documentacion de MANDOBRA

## Objetivo

Mantener un contexto tecnico y funcional que permita reconstruir por que existe
cada comportamiento importante, como validarlo y como modificarlo sin repetir
investigaciones ya resueltas.

## Que debe documentarse

- Requisitos funcionales y criterios de aceptacion aprobados.
- Decisiones de producto, arquitectura, seguridad y datos.
- Errores cuya causa no fue evidente o cuya investigacion fue costosa.
- Operaciones delicadas, recuperaciones y procedimientos repetibles.
- Riesgos conocidos, restricciones y deuda tecnica relevante.
- Resultados de validaciones que sostengan una afirmacion importante.

No se documentan como verdad vigente ideas sin aprobar, resultados no
verificados ni supuestos presentados como hechos.

## Estados recomendados

- `BORRADOR`: todavia puede cambiar y no autoriza implementacion.
- `APROBADO`: define comportamiento esperado y alcance.
- `IMPLEMENTADO`: existe evidencia en codigo y pruebas.
- `OBSOLETO`: se conserva por historia, pero ya no gobierna el sistema.
- `REEMPLAZADO`: apunta expresamente al documento que lo sustituye.

## Reglas de mantenimiento

1. Todo documento nuevo indica fecha, estado y alcance.
2. Los criterios de aceptacion deben ser observables o verificables.
3. Las decisiones importantes explican contexto, alternativas y consecuencias.
4. Una solucion de debugging registra causa raiz y validacion, no solo el
   comando que parecio resolverla.
5. Los documentos historicos no se reescriben para simular que siempre fueron
   correctos; se agrega una correccion o se los marca como obsoletos.
6. Una discrepancia entre documentacion y codigo se registra antes de decidir
   cual debe modificarse.
7. Nunca se copian secretos ni datos personales reales en ejemplos, capturas o
   salidas de comandos.

## Cuando crear un registro de troubleshooting

Debe crearse cuando se cumpla al menos una de estas condiciones:

- La causa del error no fue evidente.
- Se probaron varias soluciones antes de encontrar la correcta.
- El problema puede repetirse en otro equipo o entorno.
- Existe riesgo de perdida de datos, seguridad o indisponibilidad.
- La solucion depende de una version, migracion, proveedor o configuracion.
- Una respuesta superficial podria ocultar el problema real.

Usar la plantilla [Error resuelto](PLANTILLAS/ERROR_RESUELTO.md).

## Cuando crear un ADR

Usar un ADR individual cuando una decision afecte varios modulos, cambie una
garantia de datos o seguridad, introduzca una dependencia relevante o resulte
costosa de revertir. Las decisiones menores pueden continuar en
`DECISIONES_ARQUITECTURA.md`.

Usar la plantilla [Decision de arquitectura](PLANTILLAS/DECISION_ARQUITECTURA.md).

## Convenciones de nombres

- Requisitos: `REQ-NNN-nombre-breve.md`.
- ADR: `ADR-NNN-nombre-breve.md`.
- Troubleshooting: `AAAA-MM-DD-descripcion-breve.md`.
- Runbooks: `operacion-descripcion-breve.md`.
- Sprints: conservar `AAAA-MM-DD_Nombre_del_Sprint.md` por compatibilidad con
  la politica historica del proyecto.
