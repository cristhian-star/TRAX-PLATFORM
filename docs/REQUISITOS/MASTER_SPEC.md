---
id: MANDOBRA-MASTER-SPEC
titulo: Especificacion maestra de MANDOBRA
estado: LINEA_BASE_VERIFICADA
version: 0.1
fecha: 2026-08-31
ultima_revision: 2026-08-31
revision_codigo: d07d95
---

# MANDOBRA Master Spec

## Proposito

MANDOBRA conecta clientes con profesionales y organiza el descubrimiento,
solicitud, oferta, negociacion, contratacion, finalizacion y reputacion de
trabajos. La plataforma aporta estructura, trazabilidad y controles de
privacidad; no procesa pagos en su alcance actual.

Este documento describe la linea base observada en el codigo. No convierte
prototipos visuales ni campos reservados en funcionalidades aprobadas.

## Jerarquia de verdad

1. Codigo, migraciones y pruebas ejecutables.
2. Este Master Spec y requisitos aprobados.
3. Decisiones de arquitectura vigentes.
4. Runbooks y documentacion tecnica validada.
5. Roadmap y backlog.
6. Changelog y documentos de sprint como historia.

Una discrepancia debe registrarse y resolverse; no se asume automaticamente que
el documento o el codigo es correcto.

## Actores

### Visitante

- Puede ver inicio, explorar rubros, buscar profesionales y consultar perfiles
  publicos.
- Puede ver las pantallas informativas de Mercados y Planes.
- Debe autenticarse para iniciar operaciones privadas.

### Cliente

- Registra solicitudes de presupuesto, emergencias y propuestas.
- Evalua ofertas y postulaciones que le pertenecen.
- Puede iniciar negociaciones formales cuando cumple la politica de
  verificacion.
- Gestiona sus contratos y confirma la finalizacion.
- Puede publicar una review despues de un contrato confirmado.

### Profesional

- Completa un perfil profesional y su cobertura.
- Gestiona identidad visual y portfolio.
- Envia ofertas y postulaciones dentro de los limites aplicables.
- Participa en negociaciones elegibles.
- Acepta, inicia y declara completados los contratos asignados.

### SUPER_ADMIN

- Gestiona estados y roles de usuarios.
- Revisa verificaciones, reportes, contenido y media.
- Modera la parte publica de reviews sin alterar el comentario original.
- Puede activar o quitar PRO mediante herramientas administrativas existentes.

## Limites del sistema

- `contracting_mode = EXTERNAL`: el precio puede registrarse, pero el pago se
  acuerda y ejecuta fuera de MANDOBRA.
- No hay pagos, custodia, facturacion, garantias ni disputas financieras.
- WhatsApp se usa como salida controlada; MANDOBRA no lee ni almacena la
  conversacion.
- Las notificaciones actuales son internas.
- Google Maps es opcional y debe tener fallback cuando no hay clave valida.
- La ubicacion publica profesional es aproximada; no se debe exponer el punto
  exacto.
- Mercados usa datos mock y no debe presentarse como informacion real.
- Planes y precios publicos son informativos hasta una decision comercial.

## Capacidades funcionales actuales

### 1. Cuenta, autenticacion y consentimiento

- Registro y login usan CSRF y rate limiting.
- Roles admitidos: `CLIENTE`, `PROFESIONAL`, `SUPER_ADMIN`.
- Estados de cuenta: `ACTIVO`, `SUSPENDIDO`, `BANEADO`.
- El registro conserva aceptacion versionada de terminos y privacidad en la
  misma transaccion.
- Los usuarios inactivos no pueden iniciar sesion.
- Los redirects `next` deben ser internos.
- No hay recuperacion de contrasena ni login social.

### 2. Perfil, verificacion e identidad profesional

- El perfil profesional se crea o completa despues del registro de usuario.
- Estados de perfil: `INCOMPLETO`, `PENDIENTE_VERIFICACION`, `OBSERVADO`,
  `VERIFICADO`, `RECHAZADO`.
- Se registran especialidad, experiencia, credenciales, enlaces y cobertura.
- `ProfessionalMedia` administra avatar, portada y galeria.
- Las imagenes se validan, reprocesan y limpian de EXIF/GPS.
- La publicacion puede ser automatica o quedar sujeta a moderacion segun
  configuracion.
- Storage local es para desarrollo; Cloudinary es configurable para entornos
  externos.

### 3. Descubrimiento, taxonomia y cobertura

- Visitantes y usuarios pueden explorar categorias y buscar profesionales.
- La taxonomia actual conserva el identificador interno
  `trax-taxonomy-v1` por compatibilidad.
- La cobertura usa coordenadas, radio y consentimiento.
- El matching puede calcular distancia, priorizar cobertura y ofrecer fallback
  textual.
- Google Maps no debe activarse con placeholders ni exponer coordenadas exactas
  en vistas publicas.

### 4. Presupuestos

- El cliente crea una solicitud con categoria, titulo, descripcion, zona,
  urgencia y fecha estimada.
- Estados declarados: `BORRADOR`, `PUBLICADA`, `ABIERTO`, `COTIZANDO`,
  `ADJUDICADA`, `CANCELADA`, `CERRADA`.
- Un profesional con perfil completo puede enviar una oferta por solicitud.
- La oferta registra monto o rango, visita, plazo y condiciones.
- Una adjudicacion valida crea un contrato canonico de origen `BUDGET` de forma
  idempotente.
- Usuarios no PRO tienen un limite mensual de ofertas; PRO no tiene limite en
  el servicio actual.

### 5. Propuestas

- El cliente publica una propuesta con taxonomia, descripcion, ubicacion,
  modalidad, presupuesto y fechas.
- El unico modo soportado es `hiring_mode = SINGLE`.
- Profesionales pueden postularse con mensaje, experiencia, disponibilidad y
  pretension economica.
- Aceptar una postulacion crea un contrato `PROPOSAL`, cierra la propuesta y
  descarta postulaciones activas restantes.
- `MULTIPLE` no esta implementado.

### 6. Emergencias

- El cliente puede crear una emergencia.
- Se puede consultar un directorio de profesionales con contexto de cobertura.
- Estados declarados: `ABIERTA`, `ASIGNADA`, `EN_CAMINO`, `RESUELTA`,
  `CANCELADA`.
- El modelo actual no persiste profesional asignado.
- No existe flujo productivo completo de asignacion ni contrato de origen
  `EMERGENCY`.
- Hasta una decision posterior, Emergencias debe describirse como solicitud y
  descubrimiento, no como despacho contractual completo.

### 7. Contacto por WhatsApp

- Toda apertura pasa por `POST /whatsapp/iniciar`.
- El backend valida operacion, ownership, consentimiento, CSRF y rate limit.
- Se crea `WhatsAppContactSession` con identificador enmascarado.
- No se exponen telefonos completos en HTML, DOM o logs.
- La conversacion y sus archivos quedan fuera del sistema.

### 8. Negociacion formal directa

- Solo un cliente activo y verificado puede iniciar una negociacion con un
  profesional activo, verificado y habilitado.
- Se prohibe negociar consigo mismo.
- Estados: `OPEN`, `AGREED`, `CANCELLED`, `REJECTED`, `CONTRACTED`.
- Los terminos tienen versiones inmutables y hash canonico.
- Ambas partes deben aceptar la misma version vigente.
- Proponer nuevos terminos invalida aceptaciones anteriores.
- Una negociacion acordada puede finalizar en un unico contrato directo.
- Las operaciones sensibles usan idempotencia, version esperada, auditoria y
  correlacion.

### 9. Contratacion canonica

- Origenes declarados: `DIRECT`, `BUDGET`, `PROPOSAL`, `EMERGENCY`.
- Origenes productivos completos hoy: `DIRECT`, `BUDGET`, `PROPOSAL`.
- Modalidad unica: `EXTERNAL`.
- Flujo exitoso principal:

  `CREADA -> ACEPTADA -> EN_PROGRESO -> COMPLETADA -> CONFIRMADA`

- Desde `COMPLETADA`, el cliente puede confirmar o solicitar correccion.
- `CORRECCION_SOLICITADA` puede volver a progreso o completada.
- Terminales: `CONFIRMADA`, `RECHAZADA`, `CANCELADA`.
- `CERRADA` es un estado legacy, no un terminal nuevo.
- Las transiciones sensibles exigen actor autorizado, version esperada,
  idempotency key, lock cuando el motor lo soporta y una transaccion unica para
  efectos correlacionados.

### 10. Reviews y reputacion neutral

- Solo el cliente propietario activo puede reseñar un contrato exactamente
  `CONFIRMADA`.
- Existe como maximo una review por contrato.
- Rating admitido: 1 a 5.
- Review, evento reputacional neutral, auditoria, notificacion y comando se
  confirman atomicamente.
- El comentario original se conserva; el perfil publico usa exclusivamente
  `comment_public`.
- Moderar el comentario y excluir el rating son decisiones separadas.
- Las metricas publicas se derivan de reviews verificadas elegibles y contratos
  confirmados.
- No existe un score propietario nuevo.
- Datos legacy ambiguos permanecen no verificados y no se vinculan por
  heuristica.

### 11. Actividad y notificaciones

- El sistema genera notificaciones internas para eventos operativos.
- Los usuarios pueden listar, marcar una o marcar todas como leidas.
- Canales externos, outbox y tiempo real no estan implementados.

### 12. Administracion, seguridad y moderacion

- Las rutas administrativas requieren rol y estado adecuados.
- Se administran usuarios, rubros, verificaciones, reportes, reviews y media.
- Errores publicos evitan exponer detalles internos.
- Se aplican headers de seguridad, CSP, limites de request y rate limiting.
- La lectura del comentario original de una review esta restringida, aunque no
  genera todavia un evento por cada visualizacion.

### 13. Suscripciones, PRO y Planes

- El catalogo correcto confirmado es `FREE`, `PRO`, `ENTERPRISE`.
- El modelo de datos ya admite esos tres valores.
- La UI publica muestra todavia `Free`, `Plus`, `Pro`; `Plus` es una referencia
  desactualizada que debe reemplazarse por `Enterprise`.
- El upgrade actual puede habilitarse por verificacion o por puntos legacy.
- Un administrador puede activar o quitar PRO.
- No hay cobro ni renovacion comercial real.
- Esta area es provisional y requiere un requisito aprobado antes de evolucionar.

### 14. Mercados

- `/mercados` presenta indicadores y rangos mock.
- No consume APIs ni calcula estadisticas sobre datos reales.
- No debe usarse para decisiones economicas ni anunciarse como modulo
  implementado.

## Modelo tecnico

- Backend: Python, Flask y SQLAlchemy.
- Esquema: Alembic, head `20260726_07` al 2026-08-31.
- Base principal de desarrollo integrado: PostgreSQL mediante Docker Compose.
- SQLite: tests y desarrollo local expresamente controlado.
- Frontend: templates Jinja, CSS y JavaScript sin SPA.
- Design System v2: tokens `--trax-ds-*` y componentes `.trax-*` conservados
  como contrato tecnico durante la transicion de marca.

## Garantias no negociables

- No crear el esquema de entornos reales solo con `db.create_all()`.
- No eludir Alembic cuando una garantia depende de triggers o constraints.
- No cambiar estados contractuales mediante un estado destino libre.
- No duplicar contratos derivados, comandos o reviews por reintentos.
- No exponer secretos, telefonos completos, coordenadas exactas ni comentarios
  originales en superficies publicas.
- No presentar pagos externos como pagos procesados por MANDOBRA.
- No usar datos mock de Mercados como informacion real.
- No convertir puntos legacy en la reputacion contractual canonica.

## Requisitos no funcionales

### Seguridad

- CSRF en operaciones mutables.
- Rate limits adecuados por superficie y actor.
- Autorizacion por rol, ownership y estado de cuenta.
- Secretos fuera de Git.
- Errores sanitizados y logs sin payloads sensibles.

### Integridad

- Transacciones atomicas para operaciones correlacionadas.
- Idempotencia con conflicto cuando una misma key cambia de payload.
- Locks y constraints PostgreSQL para invariantes concurrentes.
- Historial de dominio y auditoria con responsabilidades separadas.

### Privacidad

- Minimizacion de datos publicos.
- Consentimiento antes de contacto externo y uso de ubicacion.
- Media reprocesada sin metadatos de localizacion.
- Moderacion sin destruir evidencia original.

### Accesibilidad y UX

- Labels, foco y feedback visibles.
- Componentes nuevos basados en Design System v2.
- Fallbacks para mapas, dialogs y proveedores externos.
- Validacion visual antes de migraciones masivas de pantallas.

## Validacion minima por cambio

- Pruebas unitarias y de integracion relevantes.
- `python -m unittest discover tests`.
- `python -m compileall app scripts tests`.
- `git diff --check`.
- Migracion upgrade/downgrade cuando se modifica esquema.
- Gate PostgreSQL real para locks, triggers, concurrencia o constraints
  dependientes del motor.
- Actualizacion de requisito, decision, changelog y documento de sprint segun
  el alcance.

## Fuera de alcance actual

- Pagos y facturacion.
- Custodia, garantias y disputas financieras.
- Contratacion multiple.
- Despacho contractual completo de emergencias.
- Mercados con datos reales.
- WhatsApp Business API.
- Email, push y tiempo real.
- Agenda.
- Inteligencia artificial productiva.
- Despliegue productivo aprobado.

## Decisiones pendientes prioritarias

1. Beneficios, limites y activacion de Free/Pro/Enterprise.
2. Sustituto neutral para la elegibilidad PRO basada en puntos legacy.
3. Alcance final de Emergencias y su relacion con contratos.
4. Politica de produccion, operacion y cumplimiento legal.
5. Estrategia gradual para nombres internos TRAX sin romper compatibilidad.

## Documentos relacionados

- [Auditoria documental del 2026-08-31](../AUDITORIA_DOCUMENTAL_2026-08-31.md)
- [Decisiones de arquitectura](../DECISIONES_ARQUITECTURA.md)
- [Roadmap](../ROADMAP.md)
- [Backlog](../BACKLOG.md)
- [Estandares de desarrollo](../ESTANDARES_DESARROLLO.md)
- [Cierre de Sprint 7](../SPRINTS/2026-08-04_SPRINT_7_CLOSURE.md)
