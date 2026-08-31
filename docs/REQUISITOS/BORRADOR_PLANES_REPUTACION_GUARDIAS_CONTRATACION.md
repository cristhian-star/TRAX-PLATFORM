---
id: DISCOVERY-PLANES-GUARDIAS-CONTRATACION
titulo: Propuesta de planes, reputacion, guardias y contratacion
estado: APROBADO_PARA_ESPECIFICACION
fecha: 2026-08-31
ultima_revision: 2026-08-31
---

# Propuesta de planes, reputacion, guardias y contratacion

## Proposito

La direccion conceptual fue aprobada por producto el 2026-08-31 para avanzar a
especificaciones independientes. Esta aprobacion no autoriza todavia cambios de
codigo, migraciones, precios ni promesas comerciales.

Quedaron aprobados como principios:

- separar plan comercial, verificacion y reputacion;
- mantener `FREE`, `PRO` y `ENTERPRISE` como catalogo correcto;
- retirar puntos legacy de permisos y elegibilidad futura;
- no vender reputacion ni mezclar promocion paga con ranking organico;
- modelar la guardia como disponibilidad temporal y voluntaria;
- no confundir contacto, invitacion o disponibilidad con asignacion;
- exigir consentimiento bilateral antes de crear un contrato de emergencia;
- revisar cancelaciones, correcciones y snapshots antes de integrar Emergencias.

Permanecen pendientes los beneficios exactos, precios, duraciones, plazos,
politicas de cancelacion y criterios detallados de aceptacion.

Los cuatro problemas relacionados son:

1. alinear la UI con los planes correctos `FREE`, `PRO`, `ENTERPRISE`;
2. separar plan comercial, verificacion y reputacion;
3. modelar disponibilidad de guardia sin confundirla con una contratacion;
4. permitir que una emergencia aceptada ingrese al contrato canonico con
   consentimiento bilateral y trazabilidad.

## 1. Diagnostico de puntos legacy y PRO

### Comportamiento actual

- `get_user_reputation_score()` suma `ReputationEvent.puntos`.
- La ruta de upgrade permite PRO con `score >= 100` o una verificacion
  aprobada.
- Las reviews contractuales nuevas crean un evento neutral con rating de 1 a 5
  en `event_value` y exigen `puntos = NULL`.
- Las defensas de base bloquean puntos en eventos contractuales nuevos.
- Los puntos antiguos se conservan exclusivamente como datos legacy.

### Consecuencia

Un profesional historico puede conservar 100 puntos y acceder a PRO. Un
profesional nuevo puede completar muchos contratos y recibir reviews validas,
pero continuar con cero puntos porque el sistema nuevo no genera puntos. La
regla de upgrade queda desigual, dificil de explicar y sin camino canonico para
usuarios nuevos.

Tambien se mezclan conceptos distintos:

- `VERIFICADO`: identidad o credenciales comprobadas.
- `REPUTACION`: evidencia neutral de trabajos y reviews.
- `PRO` o `ENTERPRISE`: derecho de uso de funciones comerciales.

Ninguno debe implicar automaticamente a los otros.

## 2. Propuesta recomendada para Free, Pro y Enterprise

### Principio

El plan determina funcionalidades y limites. La verificacion determina
confianza de identidad. La reputacion describe desempeño verificable. Son tres
ejes independientes.

### FREE

Base abierta para participar en el marketplace:

- perfil profesional;
- busqueda y descubrimiento;
- portfolio basico;
- presupuestos con limite mensual;
- propuestas y contratos basicos;
- reputacion y verificacion visibles;
- posibilidad de declarar guardia si cumple las condiciones de seguridad.

El limite actual de nueve ofertas mensuales puede conservarse provisionalmente,
pero debe validarse con uso real antes de presentarlo como definitivo.

### PRO

Herramientas para un profesional individual con mayor actividad:

- eliminacion o ampliacion de limites operativos;
- portfolio avanzado;
- analitica de actividad propia;
- agenda y disponibilidad avanzada cuando existan;
- automatizaciones y plantillas;
- historial y exportes ampliados.

PRO no debe comprar una mejor reputacion. Si en el futuro existe promocion
paga, debe aparecer separada y etiquetada como patrocinada, nunca mezclada con
el ranking organico.

### ENTERPRISE

Capacidades para empresas o equipos, no simplemente un PRO mas caro:

- organizacion con multiples miembros y roles;
- sucursales, zonas y categorias administradas;
- cuadrillas o profesionales asignables;
- calendario compartido y rotacion de guardias;
- bandeja operativa comun;
- auditoria, reportes y exportes de equipo;
- politicas y permisos centralizados.

Enterprise probablemente requiera en el futuro entidades `Organization`,
`OrganizationMember` y asignaciones de profesionales. El enum actual por
usuario no demuestra que esas capacidades ya esten implementadas.

### Activacion recomendada antes de pagos

Mientras no exista facturacion, el acceso puede provenir de:

- concesion administrativa;
- prueba con vencimiento;
- programa piloto documentado;
- migracion legacy explicitamente marcada.

La verificacion puede ser requisito previo para determinadas funciones, pero no
debe activar automaticamente un plan pago.

### Cambios conceptuales necesarios

- Retirar puntos y verificacion de la decision automatica de upgrade.
- Conservar puntos legacy solo para auditoria o migracion, no para permisos.
- Sustituir `get_user_reputation_score()` en permisos por un servicio de
  entitlement de plan.
- Registrar fuente, inicio, vencimiento y actor que concedio el plan.
- Impedir multiples suscripciones activas incompatibles para un mismo titular.
- Diferenciar claramente badges `VERIFICADO`, `PRO` y metricas de reputacion.

## 3. Ranking y confianza

El orden organico recomendado es explicable y dependiente del contexto.

### Busqueda general

1. coincidencia de categoria y cobertura;
2. disponibilidad pertinente;
3. verificacion requerida para la tarea;
4. reputacion neutral;
5. distancia y tiempo estimado;
6. nombre u otro desempate estable.

El plan no debe superar a verificacion o reputacion. El codigo actual prioriza
PRO antes que verificacion y rating cuando existe contexto geografico; esa regla
debe revisarse.

### Emergencias

1. guardia activa y confirmada recientemente;
2. categoria y habilitacion apropiadas;
3. cobertura y ETA estimada;
4. capacidad disponible;
5. verificacion;
6. confiabilidad especifica de guardias;
7. reputacion contractual general.

FREE, PRO y ENTERPRISE no deben alterar el orden de seguridad de una emergencia.

## 4. Concepto propuesto de Guardia

Una guardia es una declaracion voluntaria y temporal de disponibilidad. No es
una aceptacion de trabajo, una garantia de llegada ni un contrato.

### Dos modos complementarios

#### Guardia inmediata

Un switch `Estoy de guardia ahora` activa una ventana finita. Debe vencer
automaticamente para evitar profesionales que aparezcan disponibles por
olvido.

#### Guardia programada

El profesional define ventanas futuras para noches, fines de semana o feriados.
Las recurrencias complejas pueden quedar para una segunda fase.

### Datos minimos de una guardia

- profesional;
- inicio, fin y zona horaria;
- categorias o especialidades cubiertas;
- zona o radio aplicable;
- tiempo estimado de respuesta;
- capacidad simultanea;
- modalidad de precio o recargo informado;
- estado y ultima confirmacion de disponibilidad;
- origen manual, programado o de organizacion.

### Estados sugeridos

- `SCHEDULED`;
- `ACTIVE`;
- `PAUSED`;
- `EXPIRED`;
- `CANCELLED`.

No se recomienda un switch indefinido. Como referencia de producto, Taskrabbit
separa disponibilidad habitual y same-day, permite configurar horario, zona y
categorias, y apaga la disponibilidad same-day diariamente. El patron util para
MANDOBRA es la disponibilidad explicita, contextual y con vencimiento, no copiar
su modelo completo.

## 5. Flujo de Emergencias propuesto

### Limite de seguridad

MANDOBRA debe aclarar que no reemplaza policia, bomberos, emergencias medicas ni
servicios publicos ante riesgo vital, incendio, fuga de gas u otra situacion
peligrosa. El producto conecta servicios profesionales urgentes dentro de su
alcance.

### Flujo MVP recomendado

1. El cliente describe categoria, problema, zona y ventana de llegada deseada.
2. La ubicacion exacta permanece privada hasta una etapa autorizada.
3. El sistema filtra guardias activas por categoria, cobertura y habilitacion.
4. Se envian invitaciones limitadas y con vencimiento a candidatos compatibles.
5. Cada profesional responde `DISPONIBLE`, `NO_DISPONIBLE` o deja vencer la
   invitacion.
6. Una respuesta disponible incluye ETA y terminos economicos suficientes.
7. El cliente selecciona una respuesta; el MVP no autoasigna al primero.
8. La seleccion crea un acuerdo trazable o inicia una negociacion si faltan
   terminos.
9. WhatsApp se habilita despues de una respuesta autorizada o seleccion, no a
   cualquier profesional del directorio.
10. La ejecucion y cierre continúan en el contrato canonico.

### Entidades sugeridas

#### `GuardAvailability`

Representa la oferta temporal de disponibilidad del profesional.

#### `EmergencyRequest`

Representa la necesidad urgente del cliente. No contiene por si sola una
asignacion.

Estados propuestos:

- `DRAFT`;
- `PUBLISHED`;
- `MATCHING`;
- `RESPONSES_RECEIVED`;
- `SELECTED`;
- `EXPIRED`;
- `CANCELLED`.

#### `EmergencyInvitation`

Registra a que profesional se ofrecio evaluar la solicitud, con vencimiento y
resultado. Evita broadcasts no auditables.

#### `EmergencyResponse`

Registra disponibilidad real, ETA, precio o modalidad, observaciones y plazo de
validez. Una respuesta no seleccionada no es un contrato.

### Metricas especificas futuras

- tasa de respuesta durante guardia;
- ETA prometida versus llegada declarada;
- cancelaciones despues de aceptar;
- expiraciones por falta de respuesta;
- trabajos de guardia confirmados.

Estas metricas deben mostrarse de forma explicable. No deben convertirse de
manera automatica en puntos opacos.

## 6. Integracion con el contrato canonico

### Separacion de etapas

- Guardia: disponibilidad potencial.
- Emergencia: necesidad y matching.
- Respuesta: oferta concreta del profesional.
- Seleccion: consentimiento del cliente.
- Contrato: acuerdo bilateral y ejecucion.

### Opcion recomendada

Cuando una respuesta contiene alcance, ETA y terminos suficientes, la respuesta
del profesional funciona como oferta y la seleccion del cliente como
aceptacion. El sistema puede crear atomicamente un contrato de origen
`EMERGENCY` en estado `ACEPTADA`, siempre que conserve evidencia de ambos
consentimientos.

Esto requiere una operacion cerrada nueva, por ejemplo
`CREATE_ACCEPTED_CONTRACT_FROM_EMERGENCY_RESPONSE`, con:

- idempotencia;
- snapshot inmutable de terminos;
- vinculo unico a la respuesta seleccionada;
- evento de creacion y aceptacion derivados;
- auditoria y notificaciones en la misma transaccion;
- constraints de identidad y ownership;
- proteccion de concurrencia ante dos selecciones simultaneas.

Si los terminos no estan completos, debe crearse una negociacion o contrato
`CREADA` pendiente de aceptacion. No se debe marcar la emergencia como asignada
solo porque hubo un contacto por WhatsApp.

### Campos contractuales que una emergencia necesita preservar

- categoria y descripcion acordada;
- ubicacion privada o referencia autorizada;
- ETA o ventana de llegada;
- precio, rango o mecanismo de determinacion;
- recargo informado, si existe;
- materiales o visita incluidos;
- limites de responsabilidad y advertencias;
- origen y version de la respuesta aceptada.

La urgencia puede ser un atributo contractual (`STANDARD`, `URGENT`,
`EMERGENCY`) sin crear una maquina de estados paralela para la ejecucion.

## 7. Mejoras generales del contrato

### Cancelacion

La cancelacion actual es unilateral del cliente y esta marcada en codigo como
compatibilidad legacy. Conviene conservar `CANCELADA` como terminal, pero
registrar en eventos:

- quien inicio la cancelacion;
- motivo;
- momento contractual;
- respuesta de la contraparte;
- responsabilidad `UNDETERMINED`, `CLIENT`, `PROFESSIONAL`, `MUTUAL` o `SYSTEM`;
- efectos posteriores cuando exista politica comercial.

### Correcciones

`CORRECCION_SOLICITADA` existe en la maquina de estados, pero falta un flujo de
interfaz y operacion completo. Debe definirse antes de prometer al cliente una
etapa formal de correccion.

### Expiraciones

Una invitacion o respuesta de emergencia vencida debe expirar antes del
contrato. No debe registrarse como contrato cancelado.

### Evidencia

Cada origen contractual debe conservar un snapshot de los terminos aceptados,
no depender de campos mutables del presupuesto, propuesta o emergencia.

## 8. Consideraciones legales y de lenguaje

No se recomienda que MANDOBRA calcule automaticamente un recargo legal fijo por
noche o feriado sin definir antes la relacion juridica y obtener revision
profesional. La normativa laboral argentina regula jornada nocturna y recargos
en relaciones de empleo; una plataforma de profesionales independientes no debe
presentar esos porcentajes como universales sin analisis aplicable.

Para el MVP, el profesional puede declarar tarifa o recargo y el cliente debe
verlo antes de aceptar. MANDOBRA registra el acuerdo, pero no certifica por si
sola que el precio cumpla todas las obligaciones legales o sectoriales.

## 9. Orden de trabajo recomendado

### Fase 0 - Alineacion documental y visual

- Reemplazar `Plus` por `Enterprise` en la pantalla de Planes.
- No inventar beneficios Enterprise que aun no existen.
- Separar badges de plan, verificacion y reputacion.

### Fase 1 - Desacoplar PRO de puntos legacy

- Aprobar beneficios y fuentes de entitlement.
- Retirar el score legacy de permisos.
- Definir migracion segura de accesos existentes.
- Revisar ranking organico y promociones pagas.

### Fase 2 - Pulir contrato comun

- Diseñar cancelacion bilateral y responsabilidad.
- Exponer correcciones con reglas claras.
- Definir snapshots por origen contractual.

### Fase 3 - Guardias

- Disponibilidad inmediata con vencimiento.
- Ventanas programadas simples.
- Filtros por categoria y cobertura.
- Sin autoasignacion ni promesa de llegada.

### Fase 4 - Matching de emergencias

- Invitaciones y respuestas con vencimiento.
- ETA y terminos visibles.
- Seleccion explicita del cliente.
- Privacidad y limites de seguridad.

### Fase 5 - Contrato de origen EMERGENCY

- Creacion atomica desde respuesta seleccionada.
- Concurrencia, idempotencia y auditoria PostgreSQL.
- Ejecucion mediante el contrato canonico.

### Fase 6 - Enterprise operativo

- Organizaciones, equipos y rotacion de guardias.
- Bandeja comun, permisos y reportes.

## 10. Decisiones que requieren aprobacion de producto

1. Beneficios concretos de Free, Pro y Enterprise.
2. Forma de activar PRO antes de incorporar pagos.
3. Si existira promocion paga separada del ranking organico.
4. Duracion predeterminada de una guardia inmediata.
5. Si el profesional fija tarifa, rango o recargo de guardia.
6. Tiempo limite para responder una invitacion urgente.
7. Si el cliente siempre selecciona o si alguna fase futura permite despacho
   automatico.
8. Datos exactos que se revelan antes y despues de la seleccion.
9. Politica de cancelacion, responsabilidad y no-show.
10. Rubros que requieren verificacion o credencial obligatoria para guardias.

## Referencias externas consultadas

- [Taskrabbit: same-day depende de disponibilidad local](https://support.taskrabbit.com/hc/en-us/articles/46260409256859-Can-I-Book-a-Same-Day-Task)
- [Taskrabbit: disponibilidad, zona y categorias para same-day](https://www.taskrabbit.com/blog/how-to-manage-your-schedule/)
- [Uber Driver: pasar online y aceptar solicitudes limitadas](https://www.uber.com/us/en/drive/driver-app/)
- [Ley de Contrato de Trabajo actualizada](https://www.argentina.gob.ar/normativa/nacional/ley-20744-25552/actualizacion)
