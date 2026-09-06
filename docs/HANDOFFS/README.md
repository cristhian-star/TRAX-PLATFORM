# Handoffs tecnicos

Fecha: 2026-09-02
Estado: IMPLEMENTADO
Alcance: continuidad segura de trabajo entre sesiones, agentes y dispositivos.

## Objetivo

Un handoff conserva el estado operativo necesario para retomar trabajo de
MANDOBRA sin depender de la memoria de una sesion, agente o dispositivo. Se usa
cuando una sesion termina sin completar su objetivo o cuando el trabajo debe
continuar en otro entorno.

No reemplaza un requisito, ADR, runbook, troubleshooting, documento de sprint
ni historial Git. Debe enlazar esos documentos cuando resulten relevantes.

## Registro activo

El punto de entrada canonico es [ACTIVE_HANDOFF.md](ACTIVE_HANDOFF.md). Solo debe
describir un traspaso vigente. Para iniciarlo, copiar la
[plantilla de handoff](../PLANTILLAS/HANDOFF_TEMPLATE.md) sobre ese archivo y
completar todos los campos aplicables.

Estados permitidos:

- `ACTIVE`: el trabajo continua y todavia no esta listo para otra persona.
- `BLOCKED`: existe un impedimento concreto que no puede resolverse en la sesion.
- `READY_TO_RESUME`: otra sesion, agente o dispositivo puede continuar.
- `COMPLETED`: el objetivo termino y fue validado o integrado segun corresponda.
- `SUPERSEDED`: otro handoff identificado expresamente reemplaza este registro.

## Reglas obligatorias

1. Registrar un timestamp ISO 8601 con offset de Argentina, por ejemplo
   `2026-09-02T14:49:28-03:00`.
2. Registrar hechos verificados. Toda inferencia imprescindible debe marcarse
   como `INFERIDO` y nunca presentarse como hecho.
3. No incluir contrasenas, tokens, secretos, datos personales, contenido privado
   ni URLs con credenciales.
4. Indicar exactamente que tests y validaciones se ejecutaron, su resultado y
   cuales no se ejecutaron.
5. Registrar rama, ultimo commit y estado de cambios sin commit.
6. Indicar expresamente si la rama fue subida a GitHub. Si no se verifico o no
   fue subida, advertirlo sin asumir sincronizacion.
7. Enumerar rutas concretas de archivos modificados, sin copiar diffs extensos.
8. Enlazar migraciones, troubleshooting y decisiones relacionadas.
9. Incluir riesgos, bloqueantes, el proximo paso y acciones prohibidas.
10. No reescribir documentos historicos para acomodar el estado de una sesion.

## Cierre y archivo

Cuando el trabajo termine, actualizar el estado a `COMPLETED` y registrar la
evidencia final. Si conviene conservar el traspaso como historial, copiarlo con
nombre `AAAA-MM-DDTHH-mm-ss-03-00_descripcion-breve.md` dentro de este directorio
y dejar `ACTIVE_HANDOFF.md` nuevamente en estado `COMPLETED`, indicando que no
hay un handoff activo.

Un handoff reemplazado debe marcarse `SUPERSEDED` e identificar el archivo que
lo sustituye. No eliminar registros que sean evidencia de una decision, riesgo
o recuperacion relevante.
