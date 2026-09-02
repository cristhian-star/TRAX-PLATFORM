# Handoff tecnico: titulo breve

Timestamp: AAAA-MM-DDTHH:MM:SS-03:00
Estado: ACTIVE | BLOCKED | READY_TO_RESUME | COMPLETED | SUPERSEDED
Alcance: componente, objetivo o sesion cubierta por este handoff

## Identificacion

- Dispositivo/origen: DESCONOCIDO | notebook | laptop | PC de escritorio | otro
- Agente o sesion de origen: DESCONOCIDO | identificador no sensible
- Rama actual: rama verificada
- Ultimo commit: hash corto y asunto verificados
- Cambios sin commit: SI | NO; detalle breve
- Rama subida a GitHub: SI, verificado | NO, no subida | NO VERIFICADO
- Destino previsto: dispositivo, agente o sesion; usar `DESCONOCIDO` si aplica

## Objetivo de la sesion

Describir el resultado concreto buscado.

## Trabajo completado

- Hechos terminados y verificados.

## Trabajo parcialmente completado

- Trabajo iniciado, estado exacto y limite alcanzado.
- Si no aplica: `Ninguno`.

## Pendientes

- Acciones necesarias que aun no se realizaron.
- Si no aplica: `Ninguno`.

## Bloqueantes

- Impedimento, evidencia y condicion necesaria para desbloquear.
- Si no aplica: `Ninguno`.

## Archivos modificados

- `ruta/al/archivo`: cambio realizado y estado con/sin commit.
- Si no aplica: `Ninguno`.

## Migraciones relacionadas

- Revision, archivo, direccion ejecutada y base utilizada.
- Si no aplica: `Ninguna`.

## Tests y validaciones ejecutados

Registrar el comando exacto y no incluir secretos:

- `comando`: EJECUTADO; resultado exacto.

## Tests y validaciones no ejecutados

- `comando o suite`: NO EJECUTADO; motivo.
- Si se ejecuto todo lo requerido: `Ninguno`.

## Resultados de tests

- Aprobados: cantidad o suites verificadas.
- Fallidos: cantidad, test y error resumido.
- Omitidos: cantidad y motivo.
- Resultado general: PASS | FAIL | PARCIAL | NO EJECUTADO.

## Errores conocidos

- Sintoma, alcance y evidencia disponible.
- Si no aplica: `Ninguno`.

## Troubleshooting relacionado

- [Documento](../TROUBLESHOOTING/archivo.md): relacion con el trabajo.
- Si no aplica: `Ninguno`.

## Decisiones tomadas

- Decision verificada y motivo. Enlazar ADR o decision permanente cuando exista.
- Marcar expresamente cualquier dato `INFERIDO`.
- Si no aplica: `Ninguna`.

## Documentacion actualizada

- `ruta/al/documento`: contenido actualizado.
- Si no aplica: `Ninguna`.

## Riesgos

- Riesgo, impacto y mitigacion pendiente.
- Si no aplica: `Ninguno identificado`.

## Proximo paso recomendado

Una unica accion concreta y verificable para continuar.

## Instrucciones para retomar

1. Verificar `git status`, rama y ultimo commit antes de actuar.
2. Confirmar que los cambios sin commit enumerados siguen presentes.
3. Revisar archivos, migraciones, tests y documentos enlazados.
4. Ejecutar solo las acciones pendientes autorizadas.
5. Actualizar este handoff con nueva evidencia antes de transferir nuevamente.

## Acciones que NO deben realizarse

- No descartar, sobrescribir ni mezclar cambios sin verificar su propiedad.
- No ejecutar migraciones destructivas contra bases compartidas.
- No usar secretos o datos personales copiados desde este documento.
- Agregar prohibiciones especificas del trabajo actual.

## Criterio de cierre

Indicar que evidencia permite marcar el handoff como `COMPLETED` y si requiere
commit, push, PR, merge, validacion en `develop` o integracion posterior.
