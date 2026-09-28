---
id: ADR-002
titulo: Emergencias y guardia vigente
estado: PROPUESTO
fecha: 2026-09-27
---

# ADR-002 — Emergencias y guardia vigente

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
