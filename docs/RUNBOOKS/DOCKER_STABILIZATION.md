# Docker descartable para estabilización local

Registro operativo: 2026-09-18T10:43:12-03:00; laptop; Codex.
Rama: `fix/platform-runtime-stabilization`; base: `a698961`.

Este procedimiento usa exclusivamente `mandobra_stabilization` y
`docker-compose.stabilization.yml`. No administra `docker-compose.yml`,
`trax-postgres`, `trax_db` ni sus volúmenes.

## Arquitectura y aislamiento

- Python 3.12, dependencias de `requirements.txt` y ejecución como `appuser`.
- PostgreSQL 16 con base `mandobra_stabilization_db`, sin puerto publicado.
- Red interna y volúmenes `postgres_data`, `instance` y `uploads` propios del proyecto.
- Web tiene además una red `http` propia para publicar 5050 en Docker Desktop;
  PostgreSQL, migrate y seed solo acceden a la red interna. La red HTTP no es
  una barrera de salida: los servicios externos se deshabilitan por configuración.
- `migrate` ejecuta `python -m alembic upgrade head` después del healthcheck DB.
- `web` espera DB saludable y migración terminada con exit code 0.
- `/healthz` responde 200 únicamente si la conexión permite verificar el head
  Alembic vigente; 503 genérico si la base no está disponible o está desactualizada.
- Web en `http://127.0.0.1:5050/`; no exposición a la LAN.
- Configuración development explícita, CSRF habilitado, sin `create_all`.
- Sin bind del repositorio ni interpolación de variables privadas. El comando
  usa `.env.example` para impedir la carga automática del `.env` real de Compose;
  la imagen excluye `.env` y variantes privadas. `PYTHON_DOTENV_DISABLED=1` impide
  cargar dotenv en Python. Las credenciales incluidas son exclusivamente sintéticas.
- Media local escribible por usuario no root; Maps/Cloudinary sin claves.
- Checkout, webhook, conciliación y efectos financieros permanecen deshabilitados.
- `seed` tiene perfil `tools`: nunca se ejecuta durante el arranque normal.

## Prerrequisitos y arranque

Docker Desktop operativo y puerto 5050 libre. Desde la raíz del repositorio en
PowerShell, definir los argumentos y conservarlos en todos los comandos:

```powershell
$stabilizationArgs = @('--env-file', '.env.example', '-p', 'mandobra_stabilization', '-f', 'docker-compose.stabilization.yml')
docker inspect trax-postgres --format '{{.Id}} {{.State.Status}} {{.State.Health.Status}}'
docker ps -a --filter label=com.docker.compose.project=mandobra_stabilization
docker volume ls --filter label=com.docker.compose.project=mandobra_stabilization
docker network ls --filter label=com.docker.compose.project=mandobra_stabilization
docker compose @stabilizationArgs config
docker compose @stabilizationArgs build --no-cache --pull web
docker compose @stabilizationArgs up -d --no-build --wait --wait-timeout 120
docker compose @stabilizationArgs ps --all
docker compose @stabilizationArgs logs migrate web
```

Si hay recursos previos del proyecto, detenerse e identificar su origen antes
de declarar una validación desde base vacía. Registrar el ID y salud iniciales
de `trax-postgres`; verificarlos nuevamente al finalizar.

La migración vigente es `20260917_03`, descendiente de `20260917_02`.
Un error de migración impide arrancar web; inspeccionar `logs migrate`.
No usar `stamp` para evitar errores, `create_all`, resets ni downgrades.

## Seed explícito y validación

Solo después de que web esté saludable:

```powershell
docker compose @stabilizationArgs --profile tools run --rm --no-deps seed
docker compose @stabilizationArgs --profile tools run --rm --no-deps seed
docker compose @stabilizationArgs exec -T web python -m pip check
```

El seed actual crea un cliente y tres profesionales con verificación demo;
Electricidad tiene una suscripción PRO sintética. No activa Mercado Pago ni
define política comercial. La segunda ejecución conserva identidades, cantidad
de registros y vencimiento vigente, aunque restablece contraseñas demo.
Login: `cliente.demo@trax.local` o `electricidad.pro@demo.trax.local`;
contraseña exclusivamente local: `stabilization-demo-only`.

Verificar `/healthz`, `/`, `/login`, `/register`, `/explorar`, `/planes`, `/dev/qa`
y perfiles demo. No confundir smoke público con validación funcional completa.
Contratación, cuentas admin y escenarios financieros requieren fixtures separados.

Para comprobar persistencia, registrar cantidades/IDs y vencimientos tras seed,
escribir un archivo de prueba en uploads/instance como `appuser` y ejecutar:

```powershell
docker compose @stabilizationArgs restart postgres web
```

Esperar nuevamente ambos healthchecks y confirmar mismos datos, archivo y head.
`restart` conserva contenedores y volúmenes, y no ejecuta el seed ni `migrate`.
Una nueva ejecución de `up` puede volver a ejecutar el trabajo terminado:
`upgrade head` sin revisiones pendientes no vuelve a aplicar DDL.

## Teardown exclusivamente descartable

Comprobar primero que los recursos tienen la etiqueta de este proyecto; nunca
omitir `-p` o `-f`, usar `down` genérico ni `docker system prune`:

```powershell
docker compose @stabilizationArgs down --volumes
docker ps -a --filter label=com.docker.compose.project=mandobra_stabilization
docker volume ls --filter label=com.docker.compose.project=mandobra_stabilization
docker network ls --filter label=com.docker.compose.project=mandobra_stabilization
docker inspect trax-postgres --format '{{.Id}} {{.State.Status}} {{.State.Health.Status}}'
```

Las tres listas del proyecto deben quedar vacías y `trax-postgres` conservar su
ID y estado saludable. La imagen local construida y la caché de build se conservan
para reconstrucción; no son servicios activos ni datos del entorno descartable.

## Límites

Flask sirve desarrollo local; no es un despliegue productivo. Las imágenes base
usan tags y las dependencias transitivas no tienen lock completo: esta validación
acredita arranque funcional repetible, no reconstrucción binaria idéntica.
Sin credenciales reales, pruebas live, pagos, conciliación externa ni producción.
