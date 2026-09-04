# Acceso QA local

El panel QA es una ayuda exclusiva para `development` y `testing`. Alembic crea
la estructura de la base, pero no crea usuarios demo: el seed debe ejecutarse de
forma explicita sobre una base local o temporal.

## Preparacion segura

Configurar una base descartable y estas variables:

```text
APP_ENV=development
ENABLE_DEV_QA_PANEL=true
TRAX_DEMO_PASSWORD=una-clave-local-segura
DATABASE_URL=sqlite:///ruta/a/una-base-temporal.db
```

Luego ejecutar, en este orden:

```text
alembic upgrade head
python scripts/dev_seed_professionals.py
```

El seed es reiniciable: actualiza las cuentas demo y restablece su contrasena a
`TRAX_DEMO_PASSWORD`. Si no se define esa variable, la clave local por defecto es
`TraxDemo2026!`.

Cuentas principales:

- Cliente: `cliente.demo@trax.local`.
- Profesional: `electricidad.pro@demo.trax.local`.

Desde 2026-09-04T09:56:46-03:00, el seed deja exactamente a
`electricidad.pro@demo.trax.local` con entitlement PRO valido, usando una fila
demo `SUBSCRIPTION` con vencimiento UTC. `plomeria.work@demo.trax.local` y
`refrigeracion.pro@demo.trax.local` quedan funcionalmente FREE. Reejecutar el
seed reutiliza la fuente valida y neutraliza solo suscripciones PRO activas de
las cuentas demo; no incorpora excepciones al evaluador productivo.

La vigencia de 365 dias es exclusivamente un dato sintetico para QA. No define
precio, periodicidad ni regla comercial. Mientras esa fuente permanezca activa
y futura, reejecutar el seed conserva exactamente su `expires_at`; una fuente
vencida se renueva reutilizando la misma fila.

Se puede usar el login normal en `/login`. Como alternativa, `/dev/qa` ofrece
acceso rapido y enlaces canonicos a perfiles. Los perfiles publicos se identifican
por `Professional.id`, que no necesariamente coincide con `User.id` en bases
migradas o historicas.

## Produccion y Render

En produccion el blueprint QA no se registra aunque
`ENABLE_DEV_QA_PANEL=true`. El seed tambien se bloquea sin excepciones cuando el
entorno es `production` o `prod`. En Render debe mantenerse `APP_ENV=production`
y no debe configurarse el panel QA.

La negociacion formal sigue siendo opcional. Visitantes y cuentas no habilitadas
conservan el perfil publico y el contacto por WhatsApp; el acceso formal requiere
un cliente activo con verificacion aprobada y un profesional activo, verificado y
habilitado.
