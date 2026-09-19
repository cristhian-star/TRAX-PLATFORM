# Simulación end-to-end local y descartable

Estado técnico local: aprobado por Testing el `2026-09-19T11:22:22-03:00`.
Commit técnico: `6ce047a`. Alcance exclusivo QA/Compose descartable; producción,
cobros y efectos financieros reales permanecen deshabilitados. La aprobación
acredita una orden, una evidencia conciliada, una comisión ficticia y un crédito
PRO sin llamadas externas ni hallazgos P0–P3 pendientes.

Evidencia final: focales 7/7 locales y 7/7 en imagen; regresiones 174/174;
PostgreSQL 12/12 y 35/35; suite completa 715 ejecutadas, 709 aprobadas,
6 omitidas, 0 fallos y 0 errores. Las referencias posteriores a pruebas aún
pendientes describen el estado histórico anterior a esta aprobación.

Registro: 2026-09-19T10:55:09-03:00. Rama `feature/end-to-end-demo-scenarios`,
base `34dcb6c`. Esta simulación no recibe ni envía dinero y no usa Mercado Pago.

## Aislamiento y arranque

Usar exclusivamente `mandobra_stabilization`. Antes de actuar, inspeccionar
sus contenedores, redes y volúmenes. Si ya existen, identificar su dueño y
estado; no reiniciarlos ni eliminarlos por suposición. Nunca conectar a
`trax_db` ni administrar `trax-postgres`.

```powershell
$demo = @('--env-file', '.env.example', '-p', 'mandobra_stabilization', '-f', 'docker-compose.stabilization.yml', '-f', 'docker-compose.e2e.yml')
docker ps -a --filter label=com.docker.compose.project=mandobra_stabilization
docker volume ls --filter label=com.docker.compose.project=mandobra_stabilization
docker network ls --filter label=com.docker.compose.project=mandobra_stabilization
docker compose @demo config
docker compose @demo build web
docker compose @demo up -d --no-build --wait --wait-timeout 120
docker compose @demo --profile tools run --rm --no-deps e2e_seed
```

El seed se ejecuta únicamente por el comando explícito. Repetirlo conserva un
solo contrato, los IDs y los datos sintéticos. La base interna debe llegar a
`20260917_03`; PostgreSQL no publica 5432. Abrir
`http://127.0.0.1:5050/dev/qa` para ver los usuarios y la contraseña ficticia.
El panel `/dev/e2e/` está disponible solo con `E2E_DEMO_ENABLED`,
`ENABLE_DEV_QA_PANEL`, entorno development/testing, nombre del proyecto,
origen y nombre de DB esperados, y dentro del contenedor. El Compose base
mantiene los flags financieros y de Mercado Pago deshabilitados.

## Recorrido visible

1. En `/dev/qa`, iniciar como cliente demo; abrir el panel de progreso y el
   contrato directo con Punto Agua.
2. Cambiar a Punto Agua en `/dev/qa`; aceptar, iniciar y completar el contrato
   desde el detalle normal. Volver como cliente y confirmar la finalización.
3. Volver a Punto Agua; crear la orden simulada. Repetir el POST o refrescar:
   persiste la misma orden. Abrir enlace y QR: ambos representan exactamente
   `http://127.0.0.1:5050/dev/e2e/checkout/sim-...`.
4. Cambiar al cliente y abrir ese checkout local. El POST con CSRF simula pago
   aprobado. El evento entra por inbox/trabajo 4E, consulta un adaptador local
   sin HTTP y guarda evidencia. El tiempo acreditado usa una atestación
   exclusivamente simulada; el comportamiento productivo de 4E sigue siendo
   `UNKNOWN` cuando no hay prueba confiable de puntualidad.
5. Cambiar a Punto Agua y aplicar 4F. Política **ficticia**
   `simulated-pro-100-v1`: precio mensual PRO ARS 100, comisión neta simulada
   ARS 100, un crédito/30 días. No es precio ni fórmula comercial aprobados.
   Repetir el POST no crea otro crédito.

Las rutas `/dev/e2e`, sus adaptadores y enlaces no están registrados fuera
de este entorno. No hay OAuth, webhook HTTP, secretos PSP ni red externa en
la simulación. No confundir un `sim-` con un pago real. Checkout y QR rechazan
órdenes vencidas y requieren el actor propietario.

## Reinicio

Si se confirma que **todos** los recursos etiquetados pertenecen al proyecto
descartable de esta ejecución y no hay trabajo ajeno en curso, recrear solo
sus volúmenes con `docker compose @demo down --volumes` y repetir arranque y
seed. Confirmar luego ausencia de recursos del proyecto al terminar. No existe
borrado selectivo por usuario/email; nunca usar `down` sin `-p` y ambos `-f`,
`docker system prune`, ni borrar volúmenes de otros proyectos.

Esta guía no acredita pagos reales, suite completa, validación PostgreSQL de
Testing ni preparación productiva.
