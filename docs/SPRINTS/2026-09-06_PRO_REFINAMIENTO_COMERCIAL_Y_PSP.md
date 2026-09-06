# PRO - Refinamiento comercial, PSP y plan de tres sprints

Timestamp: 2026-09-06T19:22:08-03:00  
Estado: SPRINT_1_DOCUMENTAL_EN_VALIDACION  
Responsable de producto: Cristian Sánchez  
Agente: 01 - Documentation Engineer  
Rama: `docs/pro-commercial-psp-refinement`  
Commit base observado: `1548935`

## Alcance y continuidad historica

Esta secuencia no reinicia la numeracion historica ni modifica el cierre de
Sprint 7. “Sprint 1”, “Sprint 2” y “Sprint 3” son etiquetas del ciclo PRO
comercial iniciado el 2026-09-06.

La PRO Entitlement Foundation esta integrada mediante PR #5 y merge `1548935`.
El resultado post-merge informado es `APROBADO_POST_MERGE`: 294 tests, 289
aprobados, 0 fallos y 5 omisiones justificadas; Alembic `20260904_01`, sin
P0/P1 y con `trax_db` preservada. Esta evidencia no acredita PSP, creditos,
pagos, suscripciones recurrentes ni facturacion.

## Sprint 1 - Especificacion y viabilidad

Objetivo: consolidar cobros, creditos, PRO y facturacion; preparar los
expedientes juridico/contable y PSP; delimitar evaluacion fiscal.

Entregables documentales:

- REQ-001 conciliado con creditos, periodos y transiciones aprobadas.
- REQ-002 separado de cobro y actualizado para todos los periodos PRO.
- Master Spec, Roadmap, Backlog, Changelog, indices y handoff consistentes.
- [Consultas Mercado Pago](../CONSULTAS/MERCADO_PAGO_v0_1.md), todas pendientes
  y no enviadas.
- [Base de revision juridica](../LEGAL/BASE_REVISION_JURIDICA_v0_2.md), sin
  valor de dictamen.
- Evaluacion fiscal delimitada; implementacion fiscal en incremento separado.

Cierre documental: diff revisado, enlaces validos y pendientes con responsable.
La viabilidad externa puede continuar pendiente y bloquear solo incrementos
dependientes. Este documento no autoriza implementacion.

## Sprint 2 - Cobros transaccionales y creditos

Estado: PENDIENTE_DE_REFINAMIENTO_Y_AUTORIZACION.

Objetivo propuesto: un cobro trazable vinculado al nucleo contractual o enlace
independiente admitido; checkout/QR; comision efectiva; lotes de creditos;
reserva, consumo, vencimiento y renovacion transaccional sin duplicados.

Dependencias principales: decisiones economicas y juridicas, MP-08 a MP-10 y
MP-12 a MP-16, ADR de integracion/eventos/ledger y autorizacion de desarrollo.
El origen `EXTERNAL` del Contracting Core se conserva; pagos integrados son una
capacidad futura, sin renombrar enums ni crear migraciones en Sprint 1.

## Sprint 3 - Suscripcion y transicion de modalidades

Estado: PENDIENTE_DE_REFINAMIENTO_Y_AUTORIZACION.

Objetivo propuesto: suscripcion de 30 dias, creditos como pago total/parcial,
inicio diferido, renovacion manual/automatica, exencion, gracia y retorno
transaccional, con consentimiento e idempotencia.

Dependencias principales: MP-01 a MP-11 y MP-14 a MP-16, politicas de baja,
reversas y reintentos, pruebas juridicas del consentimiento y ADR aprobados.

## Facturacion

Sprint 1 evalua alcance, riesgos, integracion directa/proveedor y evidencia
fiscal. No se agrega ARCA ni IA a Sprint 3. La implementacion de Facturacion
PRO MVP debe estimarse como incremento propio despues de la evaluacion de
REQ-002, seguridad, legal, fiscal y contabilidad.

## Handoff previsto a Agente 02

El Agente 02 debe producir una propuesta revisable, no codigo:

1. mapa de capacidades y brechas;
2. evaluacion separada de marketplace y suscripcion contra MP-01 a MP-16;
3. comparacion con evidencia oficial de ARCA directo y proveedores;
4. slicing de sprints 2 y 3, criterios, dependencias y riesgos;
5. estrategia de pruebas para idempotencia, concurrencia, fechas, reservas y
   reversas, con PostgreSQL donde corresponda;
6. estimaciones de trabajo separadas de esperas externas;
7. recomendacion y decisiones que requieren aprobacion antes de codigo.

No debe contactar proveedores o abogados ni implementar integraciones sin una
autorizacion posterior y expresa.
