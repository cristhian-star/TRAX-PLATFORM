# Anexo PROF-UX-004 — Ampliación comercial de Cobros

Timestamp: 2026-10-18T15:28:27-03:00. Responsable: Codex, laptop.
Estado: BORRADOR / PROPUESTO; NO aprobado, NO implementado. No autoriza migraciones.
Rama: feature/professional-workspace-ux; HEAD: 2e552f2fdc57c152c97f0486050574696f6b250e.
Motivo: separar el objetivo posterior de la conexión interna de total contractual.

## Estructura actual y objetivo

Hoy PaymentObligation tiene unicidad por ContractRequest; PaymentOrderReservation tiene
unicidad por obligación. La reserva durable representa una llamada idempotente: no puede
convertirse en otra porción de deuda ni regenerarse después de incertidumbre.
Objetivo propuesto: varias obligaciones (anticipo, parcial, saldo) para un mismo trabajo,
y trabajo externo real sin ContractRequest ficticio. `contracting_mode=EXTERNAL` expresa
modalidad contractual/pago fuera de plataforma; NO origen comercial del trabajo.

## Opciones incrementales

1. Varias obligaciones internas vinculadas al contrato existente: menor cambio de sujeto,
   pero exige nueva identidad de obligación y unicidades por contrato/secuencia/tipo según
   decisión. Mantener una reserva de creación por obligación inicialmente; recovery no es
   una nueva obligación. Externos seguirían pendientes.
2. Introducir caso comercial de cobro con vínculo opcional a contrato y origen explícito:
   admite externos sin contaminar contratación/reputación. Requiere definir contraparte,
   consentimiento, total, estado, titularidad y política de datos externos. Mayor alcance.
3. Separar deuda de intentos múltiples: sólo después de decidir renovación/cancelación y
   conciliación autoritativa. Nunca usar un nuevo intento para esquivar UNCERTAIN.

Secuencia sugerida, no aprobada: obligaciones internas múltiples → sujeto externo → relación
fiscal opcional → activación remota con gates. No se elimina estructuralmente ninguna opción.

## Invariantes y decisiones económicas pendientes

- Actor activo, ownership de sujeto/obligación/cuenta, autorización revalidada, CSRF y datos
  mínimos. Moneda/precisión exactas, no floats.
- Total acordado es la fuente de deuda autorizada; total solicitado suma obligaciones que
  comprometen saldo según estado; total acreditado procede sólo de evidencia autoritativa;
  total devuelto/revertido tiene identidad y correlación propias. No equiparar esos totales.
- Proponer un ledger o proyección derivada de hechos idempotentes para saldos; decidir si
  devolución reabre deuda y cómo representar descuentos/cambios de alcance con consentimiento.
- Prevenir sobrecobro mediante reserva de exposición bajo lock y constraints en una base real:
  obligaciones activas y montos inciertos consumen exposición hasta resolución, no se liberan
  por timeout de navegador. La fórmula exacta y política de excedentes requieren aprobación.
- Precio interno deriva de acuerdo vigente; externos necesitan fuente del importe y revisión
  explícita de contraparte/alcance. No aceptar precio arbitrario como pago autorizado.
- Cada obligación mantiene referencia/clave durable. Replays y notificaciones duplicadas no
  alteran saldos dos veces. Incertidumbre conserva identidad y bloquea; recuperación consulta
  la misma operación y tiene auditoría propia.
- Anticipo cobrado no finaliza trabajo. Parcial no acredita cumplimiento. Orden no es pago.
  No activar reputación contractual para casos externos ni cambiar reglas PRO/comisiones.
  No fijar tarifas, porcentajes ni fórmulas comerciales en este anexo.

## Migración y compatibilidad propuestas

Diseñar migración Alembic posterior con backfill uno-a-uno de obligaciones actuales, referencia
estable y discriminador de total legacy. Mantener reservas/órdenes/links originales, auditoría
y claves. Reemplazar unicidades sólo con invariantes equivalentes aprobadas; evitar que dos
workers comprometan el mismo saldo. Validar rollback, datos históricos incoherentes y consultas
paginadas. Gates PostgreSQL de locks, concurrencia, transacciones y recuperación obligatorios.
No se genera SQL ni migración aquí. Compatibilidad de endpoints 4D y permisos debe conservarse,
o versionarse explícitamente sin convertir un contrato legacy en caso externo.

## Relación con facturas futuras

Factura/autorización ARCA, deuda, pago y finalización son eventos distintos. Proponer relación
explícita opcional entre comprobantes y obligaciones/asignaciones, con cardinalidad y ajuste
por notas de crédito aún por decidir. Evitar sumar importe fiscal y financiero como dos deudas.
Pago parcial puede imputarse sin afirmar emisión; emisión no confirma pago. QR fiscal y QR de
Checkout distintos. Comprobantes de suscripción MANDOBRA quedan en dominio separado.

## Documentos y aprobaciones necesarias

- Actualizar REQ-003: sujeto, múltiples obligaciones, fuentes de importe, identidad de intentos,
  saldo/sobrecobro, expiración/renovación y recovery.
- Actualizar Master Spec tras aprobación: origen comercial y fronteras cobro/contrato/fiscal.
- Nuevo ADR de sujeto comercial, ledger/exposición, unicidades, migración y compatibilidad.
- Coordinar REQ-002 para cardinalidad fiscal; REQ-001 sólo si decisiones aprobadas cambian
  reglas PRO, sin asumir modificaciones. Privacidad/legal para contraparte externa.
- Decidir quién acuerda total y cambios; aceptación del anticipo/parcial; cancelación y
  devoluciones; límites de exposición; fuente de crédito; identidad y privacidad de clientes
  externos; permisos; requisitos de conciliación; estrategia de migración y gates.

No modifica Master Spec, ADR o requisitos aprobados. La propuesta debe revisarse por Producto,
Arquitectura, Seguridad y fiscal/legal según corresponda antes de un encargo ejecutable.
