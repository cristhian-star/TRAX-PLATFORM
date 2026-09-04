# BACKLOG MANDOBRA

## PRO y Facturacion - requisitos aprobados, implementacion pendiente

- Completar [REQ-001 - Activacion y vigencia de MANDOBRA PRO](REQUISITOS/REQ-001-activacion-y-vigencia-pro.md):
  el nucleo calculado, la eliminacion de puntos legacy y las fuentes temporales
  reconocidas quedaron implementados parcialmente; faltan onboarding PSP,
  prueba de 30 dias, extension de 60
  dias por operacion con comision efectiva, suscripcion pagada y transiciones
  seguras a `FREE`.
- Resolver antes de implementar REQ-001: porcentaje de comision; precio y
  periodicidad; beneficios y limites completos; renovacion, cancelacion, mora,
  contracargos, periodo de gracia; migracion de accesos existentes; proveedor
  PSP y modelo futuro de `ENTERPRISE`.
- Implementar [REQ-002 - Facturacion MANDOBRA PRO MVP](REQUISITOS/REQ-002-facturacion-pro-mvp.md)
  como modulo opcional para PRO vigente, limitado inicialmente a persona
  humana, monotributo activo y Factura C, con borrador asistido, vista previa,
  confirmacion humana, CAE, auditoria e idempotencia.
- Resolver antes de implementar REQ-002: integracion directa o proveedor;
  custodia y rotacion de certificados; validacion fiscal; datos del receptor;
  almacenamiento, entrega y retencion; limites; correcciones, anulaciones y
  notas de credito; contingencia ARCA; IA, costos y revisiones legal, fiscal,
  contable y de seguridad.
- Crear los ADR necesarios cuando se decidan PSP, integracion fiscal, custodia
  de secretos, modelo de datos, idempotencia externa y proveedor de IA. Ninguna
  de esas decisiones esta aprobada todavia.

## Alta prioridad

- Alinear la UI publica con el catalogo aprobado `FREE`, `PRO`, `ENTERPRISE` en
  una fase de implementacion autorizada; `Plus` permanece como contradiccion
  visible y no pertenece al catalogo aprobado.
- Definir el alcance objetivo de Emergencias: solicitud y descubrimiento,
  asignacion operativa o integracion con el contrato canonico de origen
  `EMERGENCY`.
- Diseñar en una fase futura `hiring_mode = MULTIPLE`; Sprint 7 conserva exclusivamente `SINGLE`.
- Diseñar en una fase futura cancelaciones consensuadas y correcciones ampliadas sin alterar el cierre exitoso `CONFIRMADA`.
- Definir, mediante decisión de producto futura, si MANDOBRA necesita badges plata/oro o una proyección propietaria; no forman parte de la reputación neutral.
- Diseñar hitos, evidencias, disputas y modificaciones de contrato sin implementar pagos todavia.
- Sustituir almacenamiento en memoria de Flask-Limiter por Redis u otro backend compartido.
- Definir WSGI productivo para despliegues fuera del servidor Flask de desarrollo.
- Revisar politicas legales con profesional: terminos, privacidad, cookies y consentimientos.
- Configurar Cloudflare/WAF o equivalente antes de exposicion publica.
- Implementar checklist productivo en staging con secretos reales, HTTPS, backups, monitoreo y prueba de restauracion.
- Implementar recuperacion de contraseña con tokens seguros y expiracion.
- Implementar verificacion de email antes de activar flujos sensibles.
- Incorporar pruebas especificas para Emergencias, suscripciones/PRO,
  mutaciones del centro de notificaciones y operaciones administrativas que
  hoy no tienen cobertura directa equivalente al Contracting Core.

## Media prioridad

- Implementar oferta profesional como segundo tipo de publicacion de propuestas.
- Migrar navbar completo a Design System v2 en un sprint especifico sin cambiar rutas ni comportamiento.
- Migrar Home, Resultados y Perfil Profesional completo a Design System v2 con validacion visual dedicada.
- Migrar Dashboards, Presupuestos, Propuestas, Emergencias, Admin y tablas a componentes `.trax-*` por fases.
- Reducir `styles.css` legacy despues de cubrir visualmente las pantallas migradas.
- Unificar breakpoints dispersos bajo tokens `--trax-ds-breakpoint-*`.
- Eliminar CSS muerto cuando exista mapa de cobertura por pantalla.
- Revisar uso del servidor Flask de desarrollo dentro de Docker y separar perfil local de perfil productivo.
- Reemplazar usos legacy de `Query.get()` por `db.session.get()`.
- Reemplazar `datetime.utcnow()` deprecated por timestamps timezone-aware.
- Auditar la lectura administrativa de comentarios originales con un evento de acceso si el volumen y la política de privacidad lo requieren.
- Evaluar una outbox transaccional cuando se habilite el primer canal externo; `INTERNAL` permanece sin dispatcher.
- Definir politica de retencion y limpieza de `OperationCommand` sin perder capacidad de auditoria.
- Agregar `source` explicito al modelo de consentimientos si producto requiere trazabilidad separada del contexto tecnico.
- Incorporar escaneo automatizado de dependencias y secretos en CI.
- Evaluar Redis futuro para rate limiting, cache o colas cuando el volumen lo justifique.
- Restringir la clave de Google Maps por origen autorizado, API permitida y cuotas.
- Validar Google Maps con una API key real restringida en staging.
- Confirmar apertura de WhatsApp en Chrome escritorio y dispositivo movil fisico antes de produccion.
- Validar Cloudinary con credenciales reales de staging, URLs seguras, thumbnails, reemplazo, eliminacion y rollback.
- Incorporar escaneo antivirus o analisis externo de imagenes antes de produccion publica.
- Implementar limpieza asincronica de imagenes huerfanas en storage.
- Evaluar `PortfolioItem` futuro si el portfolio necesita agrupar trabajos con multiples imagenes y narrativa propia.
- Evaluar soporte de videos solo si producto define moderacion, storage y costos.
- Evaluar moderacion automatica de imagenes cuando exista politica aprobada y proveedor definido.
- Evaluar el actor o flujo `EMPRESA` solo durante la futura definicion de
  `ENTERPRISE`; REQ-001 no autoriza crearlo.
- Implementar geocoding de ubicaciones base.
- Evolucionar matching geografico hacia PostGIS o indices espaciales cuando escale el volumen.
- Implementar rutas, tiempos de viaje o distancia real por calle solo si producto lo requiere.
- Incorporar poligonos avanzados y zonas personalizadas multiples.
- Evaluar estilos avanzados de Google Maps si MANDOBRA define un mapa de marca propio.
- Crear listado dedicado de emergencias del cliente para reemplazar enlaces operativos provisorios.
- Crear vista consolidada de solicitudes del cliente que incluya presupuestos, emergencias y propuestas.
- Implementar Agenda.
- Implementar canal Email para notificaciones transaccionales.
- Integrar WhatsApp Business API cuando exista definicion de producto y proveedor.
- Implementar webhooks de WhatsApp Business Cloud API solo si se aprueba el alcance de eventos externos.
- Validar apertura directa por username si WhatsApp publica una URL estable para esa capacidad.
- Evaluar grupos automaticos de WhatsApp solo con una API oficial y consentimiento explicito.
- Evaluar Push notifications cuando exista estrategia mobile/browser.
- Evaluar polling moderado o WebSockets solo cuando el producto requiera tiempo real.
- Planificar la migracion gradual de identificadores internos `TRAX` sin
  romper taxonomia, tokens CSS, rutas, datos persistidos ni compatibilidad
  historica.

## Baja prioridad

- Incorporar Mercados.
- Incorporar funcionalidades de IA.
# Deuda tecnica posterior al nucleo PRO

Timestamp: 2026-09-04T10:29:16-03:00

- Revisar en un incremento separado la atomicidad de las acciones
  administrativas legacy que todavia combinan servicios con commits propios.
  La revocacion PRO ya fue corregida; este registro no autoriza refactorizar las
  demas acciones dentro del alcance actual.
