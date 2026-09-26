# Identidad MANDOBRA aprobada: navbar compartido de toda la plataforma

Estado: COMPLETED
Timestamp: 2026-09-26T14:13:29-03:00
Origen: laptop DESKTOP-5K3IE76, Codex Desktop.
Rama: `feature/ux-ui-foundation`; HEAD: `ffbb967275bc80460f88df0594f8f5e710f8b526`.
Origin: `https://github.com/cristhian-star/TRAX-PLATFORM.git`.
Autorizacion: el usuario aprobo la colocacion del logo para toda la plataforma tras revisar el canario. Este registro sustituye su restriccion al home y su aprobacion pendiente; el registro anterior se conserva como historia.

## Resultado y alcance
Los dos PNG normalizados aprobados son ahora la identidad por defecto del navbar compartido en `base.html`, tanto para visitantes como para usuarios autenticados. Sin duplicar navbar, nuevas dependencias, JS, rutas, cambios de permisos ni autenticacion. Footer, favicon, manifest, assets legacy y originales del workbench preservados. Sin migraciones.
Se retiro el opt-in canario y su CSS del home; ambos archivos vuelven al contenido de HEAD. El CSS compartido mantiene contain, dimensiones reservadas 1696x720, enlace accesible MANDOBRA inicio e imagenes decorativas. Claro/oscuro seleccionados por las clases de tema existentes. Hashes de ambos PNG iguales a los registrados en el canario.
Cajas: 200x56 escritorio, 160x56 entre 821 y 1080 px, 144-180x44 movil. En cuentas autenticadas se usa el menu colapsable existente hasta 1180 px para evitar superposicion con controles de cuenta. Corregido el contraste del boton de menu oscuro con tokens existentes; sus dos trazos quedan visibles.

## Archivos y estado Git
Cambios efectivos respecto de HEAD: `app/templates/base.html`, `app/static/css/visitor-navbar-v1.css`, este handoff y tres nuevos archivos: ambos wordmarks y [tests/test_platform_brand.py](../../tests/test_platform_brand.py). El test canario sin commit fue sustituido por el test global.
`git status --short` tambien enumera `app/templates/home.html` y `app/static/css/home-v1.css`, pero `git diff` confirma cero diferencias de contenido en ambos (working copy CRLF / index LF). Total observado: ocho paths, seis con cambios efectivos. Staging vacio. Trabajo previo del canario incorporado, sin cambios ajenos detectados.
Sin commit, push, PR, merge ni despliegue de produccion. HEAD no cambio. No hubo merge porque la aprobacion de colocacion no autoriza operaciones de integracion Git. Los cambios solo estan locales; el push de esta implementacion esta PENDIENTE.

## Validacion ejecutada
- 83/83 unittest PASS en la ejecucion final (7,843 s), incluidos 11 tests de identidad global. Modulos: tests.test_platform_brand, tests.test_home_hero_carousel, tests.test_navbar_markets_ux03a, tests.test_design_system_v2, tests.test_corporate_footer, tests.test_auth_ux_redesign_v1, tests.test_markets_ux03 y tests.test_explore_rubros_ux02.
- Contenedor descartable `docker run --rm --network none`, DATABASE_URL=sqlite:///:memory:, sin volumenes ni acceso a trax_db. Verificados GET/HEAD PNG, hashes, RGBA, alfa identico, seis paginas publicas, home y dashboards CLIENTE/PROFESIONAL/SUPER_ADMIN y notificaciones, accesibilidad del enlace y contrato de temas.
- `compileall -q app tests/test_platform_brand.py`: PASS. `git diff --check`: PASS. Advertencias heredadas SQLAlchemy Query.get y datetime.utcnow; log ERROR esperado del escenario negativo de Explorar, sin fallos de pruebas.
- Chrome: dashboard de cliente demo a 1440, 1024, 768, 390 y 320 CSS px en ambos temas. Diez casos sin overflow horizontal, recorte ni halos visibles; PNG correcto cargado y contain. Altura 84,8 px escritorio / 76 px movil. Menu de cuenta abierto a 1024 sin superposicion; dos trazos visibles, contraste oscuro corregido.
- Pagina publica /mercados revisada a 1024 claro y 1440 oscuro con logo nuevo y navegacion sin superposicion. Sesion demo cerrada y viewport temporal restablecido al terminar. Captura local fuera del repositorio: `C:/Users/Cristhian/.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/mandobra-identidad-global.png`.
- No ejecutados: suite completa, gates PostgreSQL, nueva ejecucion de tests JS (sin cambios JS), migraciones ni seed. Revision visual autenticada acotada a CLIENTE; PROFESIONAL/SUPER_ADMIN cubiertos por pruebas HTTP, no por navegador. No equivale a QA exhaustivo de toda ruta.

## Entorno, riesgos y continuidad
Reconstruido y recreado solo web con docker-compose.stabilization.yml. Web y PostgreSQL descartable existentes healthy al cierre, disponibles en http://127.0.0.1:5050/ y /mercados. Sin tocar volumenes ni trax_db. No hubo errores tecnicos bloqueantes; persiste la limitacion raster de detalle fino del maletin en tamanos pequenos. No se vectorizo ni transformo el master aprobado.
Documentacion actualizada: este handoff. Sin nuevo troubleshooting: ajustes CSS localizados, sin incidente de plataforma.
Proximo paso recomendado: revision del diff y autorizacion explicita para commit/push y posterior integracion a develop. Para retomar: ejecutar git status, git branch --show-current y git log -1 --oneline; verificar HEAD ffbb967, staging vacio y alcance aqui registrado; revisar el navbar en ambos temas. No reset/clean, no borrar originales o assets legacy, no migrar ni operar sobre trax_db. No hay implementacion parcial pendiente; quedan integracion Git y eventual QA independiente.

---

# Canario de identidad MANDOBRA: solo navbar del home publico (historico, sustituido)

Estado: READY_TO_RESUME
Timestamp: 2026-09-26T14:01:21-03:00
Origen: laptop DESKTOP-5K3IE76 (chassis 10), Codex Desktop.
Rama: `feature/ux-ui-foundation`.
HEAD: `ffbb967275bc80460f88df0594f8f5e710f8b526`.
Origin: `https://github.com/cristhian-star/TRAX-PLATFORM.git`.
Precheck: working tree limpio, staging vacio; `git ls-remote` confirmo la rama remota en el mismo SHA.
Los registros anteriores describen sesiones previas: sus cambios UX-03 ya estan guardados en HEAD; no representan cambios pendientes de esta sesion.

## Objetivo y resultado
Integrar los dos wordmarks normalizados exclusivamente en el navbar del home publico para aprobacion visual. Implementacion y verificacion focal COMPLETADAS; aprobacion visual del usuario y ampliacion global PENDIENTES.
`home.html` activa `home_brand_canary = true`; `base.html` usa ese contexto con default false. No se compara URL para seleccionar la marca, no se duplico navbar ni se cambiaron rutas, permisos o autenticacion. Home autenticado, dashboards y demas templates conservan el default legacy. Footer, favicon, manifest y assets anteriores intactos.

## Archivos y hashes
Copiados sin transformar desde `C:/Users/Cristhian/Downloads/MANDOBRA_BRAND_WORKBENCH/`:
- [Wordmark claro](../../app/static/img/branding/mandobra/mandobra-wordmark-light.png): SHA-256 `4d5e5b8738979d373ab5021f0ba89f15bd98d2ccd831fff47097025a6dfacb9e`.
- [Wordmark oscuro](../../app/static/img/branding/mandobra/mandobra-wordmark-dark.png): SHA-256 `ca6933542a281720f24d5fc3e9c1be2a4c6f9ce21458a14da81f601694cf2f0f`.
Ambos PNG RGBA 1696x720; origen y copia identicos; cero diferencias de alfa, IoU 100%. Texto MANDOBRA y maletin presentes; sin eslogan ni Casa. Masters del workbench intactos.
Codigo modificado: `app/templates/base.html`, `app/templates/home.html`, `app/static/css/home-v1.css`.
Nuevo en ese momento: `tests/test_home_brand_canary.py` (sustituido posteriormente por [tests/test_platform_brand.py](../../tests/test_platform_brand.py)).
Documentacion actualizada: exclusivamente este handoff.
Total: siete paths locales (cuatro modificados y tres nuevos), sin staging.

## Comportamiento y revision visual
CSS acotado a `.brand--home-canary` en home-v1.css; contain, dimensiones intrinsecas, sin recorte, fondo ni transformacion. Dos imagenes decorativas alt vacio/aria-hidden y enlace MANDOBRA inicio. El bootstrap de tema existente se ejecuta en head, antes del body; las clases theme-light/theme-dark seleccionan por CSS. No se incorporaron JS ni recursos externos.
Caja 200x56 en escritorio; 160x56 entre 821 y 1080 px; 144-180x44 en movil. A 1024 px se redujo solo el espacio horizontal reservado: el dibujo sigue limitado por altura, sin reducirse. Esto evita el solapamiento heredado Planes/selector de tema en home; /mercados conserva el comportamiento anterior.
Chrome: matriz de 1440, 1024, 768, 390 y 320 CSS px en ambos temas, diez casos revisados. Un solo navbar, PNG correcto y cargado, contain, sin overflow horizontal ni superposicion del wordmark con menu. Altura conservada: aproximadamente 84,8 px escritorio y 76 px movil. Cambiar tema conserva la caja, sin salto visible; persistencia al recargar verificada. Sin recorte ni halo visible. Wordmark viable hasta 320 px; no fue necesario fallback al simbolo compacto. Los detalles finos del maletin pierden nitidez al reducirse; aprobacion visual humana pendiente.
Comparacion /mercados: conserva ambos wordmarks anteriores y simbolo compacto movil. /login tambien observado con marca anterior.
Limitacion preexistente: menu hamburguesa movil en tema oscuro tiene lineas blancas sobre boton blanco; confirmado en /mercados a 320 px. No alterado por alcance. Solapamiento legacy a 1024 en /mercados tampoco modificado.
El visor integrado tuvo inconsistencias de escala/captura; la matriz final se verifico en Chrome con innerWidth exacto. Consola Chrome: errores de una extension ajena a la aplicacion; sin errores de aplicacion observados. Recursos de marca locales; no confundir scripts inyectados por extensiones con recursos introducidos por este cambio.

## Validaciones ejecutadas
- Python unittest: 54/54 PASS (9 focales de identidad + 45 regresiones): tests.test_home_brand_canary, tests.test_home_hero_carousel, tests.test_navbar_markets_ux03a, tests.test_design_system_v2, tests.test_corporate_footer, tests.test_auth_ux_redesign_v1.
- Ejecutadas en `docker run --rm --network none`, imagen mandobra_stabilization-app:local, DATABASE_URL=sqlite:///:memory:, sin volumenes. Sin acceso a trax_db ni a PostgreSQL para los tests.
- Focales cubren recursos GET/HEAD 200 image/png, hashes, RGBA, dimensiones, alfa, accesibilidad, contain, contrato CSS de temas, opt-in unico, ausencia de texto/eslogan en marca, default base incluso en ruta / y aislamiento de seis paginas publicas mas home autenticado. Unico template opt-in confirma aislamiento de dashboards/operativas; no se navegaron exhaustivamente todas las rutas autenticadas.
- Node: 2/2 archivos de regresion PASS, tests/js/home_hero_carousel.test.js y tests/js/home_faq.test.js.
- compileall app y test focal: PASS en contenedor descartable. UTF-8, enlaces locales afectados, hashes de copias y git diff --check: verificados al cierre.
- Advertencias historicas SQLAlchemy Query.get y datetime.utcnow; sin fallos. ResourceWarnings introducidos por respuestas de test se resolvieron cerrandolas; ejecucion final limpia de esas advertencias.
- No ejecutados: suite completa, gates PostgreSQL, migraciones, seed, retest independiente. No se declara aprobacion global.

## Docker y Git
Solo `docker compose -f docker-compose.stabilization.yml build web` y `up -d --no-deps web`. PostgreSQL y volumenes descartables existentes preservados; no se ejecuto migrate ni seed. Web y PostgreSQL se dejan encendidos para aprobacion; salud comprobada al cierre.
URLs: http://127.0.0.1:5050/ (canario) y http://127.0.0.1:5050/mercados (comparacion legacy).
Sin commit, push, PR, merge ni deploy. Remoto sigue en ffbb967; los siete paths del canario solo existen localmente. NO hubo merge porque falta aprobacion visual y autorizacion de integracion.

## Retomar y rollback
1. Ejecutar git status, git branch --show-current y git log -1 --oneline; confirmar HEAD ffbb967 y exactamente los siete paths del canario.
2. Abrir ambas URLs y revisar temas/escritorio/movil. Mantener el Compose encendido hasta aprobacion.
3. Con aprobacion, preparar retest/integracion o ampliacion en un alcance nuevo; no hacer staging/commit/push/merge sin autorizacion explicita.
Rollback funcional sencillo: retirar el opt-in de home.html devuelve ese navbar al bloque legacy. No eliminar assets anteriores ni masters. No tocar footer, favicon, autenticacion, DB o paginas fuera de alcance.
Riesgos pendientes: decision visual sobre tamano/detalles raster y contraste del menu global preexistente. Ningun bloqueante tecnico del canario observado.

---

# Refinamiento UX-03: grilla 2×2 para demanda por rubro

Estado: READY_TO_RESUME
Timestamp: 2026-09-25T23:43:16-03:00
Origen: laptop; agente: Codex. Rama: `feature/ux-ui-foundation`; HEAD base y
último commit: `24bcb9412e182d5190ca4ceaf75de577b66f0a18`; origin
`https://github.com/cristhian-star/TRAX-PLATFORM.git`.
Objetivo: reorganizar exclusivamente las cuatro tarjetas de gráficos de
`Demanda relativa por rubro` en dos filas de dos, con mayor presencia visual.

La grilla presenta dos columnas desde 48 rem, por lo que escritorio y tablet
muestran exactamente dos tarjetas por fila. Cada tarjeta aumenta su separación,
padding y altura mínima para aprovechar el ancho disponible sin alterar los
gráficos, rubros, textos, datos demostrativos ni accesibilidad. Por debajo de
48 rem conserva una columna para evitar compresión en móvil.

Inspección visual comprobada en 1440, 1024 y 768 CSS px: cuatro tarjetas en dos
filas de dos, anchos y alturas alineados y sin overflow horizontal. En 390 y
320 CSS px: cuatro filas de una tarjeta, sin recortes ni superposiciones. Tema
claro y oscuro conservan contraste; la consola del navegador no presenta
errores ni advertencias. La página queda abierta en
`http://127.0.0.1:5050/mercados` y el Compose exclusivo
`mandobra_stabilization` permanece encendido y saludable para revisión visual.

Validación ejecutada: focales mercados/navbar 19/19; `compileall` y
`git diff --check`, aprobados. La suite completa y PostgreSQL no se ejecutaron
por alcance. Archivos afectados por este ajuste:
`app/static/css/markets-v2.css`, `tests/test_markets_ux03.py` y este handoff.
No hubo migraciones, cambios de backend, rutas, permisos, autenticación ni
base de datos.

Git conserva los once paths locales autorizados de UX-03, staging vacío y HEAD
sin cambios. No hubo commit, push, PR, merge ni deploy porque resta la
aprobación visual y el retest independiente. Próximo paso: revisar la nueva
distribución 2×2 en la página abierta y, con aprobación expresa, preparar el
paquete de Testing sin modificar el contenido de los gráficos.

---

# Refinamiento UX-03: gráficos de demanda por rubro

Estado: READY_TO_RESUME
Timestamp: 2026-09-25T23:35:49-03:00
Origen: laptop; agente: Codex. Rama: `feature/ux-ui-foundation`; HEAD base y
último commit: `24bcb9412e182d5190ca4ceaf75de577b66f0a18`; origin
`https://github.com/cristhian-star/TRAX-PLATFORM.git`.
Objetivo: reemplazar exclusivamente las barras de `Demanda relativa por rubro`
por gráficos de línea demostrativos, preservando el resto de UX-03.

Electricidad, Refrigeración, Plomería y Herrería conservan su identidad y ahora
se presentan en cuatro tarjetas. Cada una contiene icono decorativo local, SVG
semántico fluido, línea y puntos con el naranja corporativo, área tenue, seis
períodos estáticos, etiqueta visible `Tendencia demostrativa`, cierre con flecha
y texto explicativo. La sección declara que las series existen para mostrar la
interfaz y no representan operaciones ni mediciones reales. No se atribuyeron
fechas, fuentes o actividad real.

Cada SVG tiene título y descripción accesibles específicos del rubro. Los seis
valores también se exponen en una lista HTML visualmente oculta y el cierre se
explica en texto, por lo que la lectura no depende del color o de interpretar la
línea. Se eliminaron los cuatro elementos `progress`. No se incorporaron canvas,
Chart.js, dependencias, CDN, APIs, rastreadores, animaciones ni JavaScript nuevo.

La grilla usa cuatro columnas a partir de 64 rem, dos desde 48 rem y una en
móvil. Las tarjetas mantienen ancho y altura alineados. Inspección visual en
1440, 1024, 768, 390 y 320 CSS px: sin overflow, recortes o superposiciones;
tema claro y oscuro aprobados localmente. En oscuro la línea conserva 3 px y el
naranja corporativo `rgb(255, 138, 76)`. La estructura accesible expone cuatro
gráficos, cuatro resúmenes y veinticuatro valores. Consola sin errores.

Validación ejecutada: focales mercados/navbar 19/19; selección relacionada de
autenticación, Design System V2, footer, Home UX-01, Explorar UX-02, navbar,
mercados y controles de búsqueda/seguridad 81/81. `compileall` y la sintaxis del
JavaScript preexistente del carrusel: aprobados. La suite completa no se ejecutó
por alcance y queda para Testing independiente.

Archivos afectados por este refinamiento:
`app/services/market_view_service.py`, `app/templates/mercados.html`,
`app/static/css/markets-v2.css`, `tests/test_markets_ux03.py` y este handoff.
`docs/BACKLOG.md` no requirió una nueva modificación. Sin migraciones, cambios
de backend, base de datos, rutas, permisos o autenticación. El Compose exclusivo
`mandobra_stabilization` queda encendido y saludable, con la página disponible
en `http://127.0.0.1:5050/mercados` para aprobación visual.

Git conserva los once paths locales autorizados de UX-03, staging vacío y HEAD
sin cambios. No hubo commit, push, PR, merge ni deploy porque falta aprobación
visual y retest independiente. Próximo paso: revisar la claridad de los cuatro
gráficos en la página abierta; no sustituir las series demostrativas por datos
reales sin la metodología y fuentes futuras ya registradas.

---

# Refinamiento visual UX-03: hero e importes desplegables

Estado: READY_TO_RESUME
Timestamp: 2026-09-22T23:02:36-03:00
Origen: laptop; agente: Codex. Rama: `feature/ux-ui-foundation`; HEAD base y
último commit: `24bcb9412e182d5190ca4ceaf75de577b66f0a18`; origin
`https://github.com/cristhian-star/TRAX-PLATFORM.git`.
Objetivo: aplicar la revisión visual del usuario al hero y los rangos de
`/mercados`, preservando navbar, tendencias y secciones inferiores de UX-03.

Se retiraron el rótulo `Referencia pública de precios` y el cuadro `Datos
demostrativos`. El hero conserva el tono verde con una capa más translúcida
sobre cuatro pares de imágenes locales ya aprobadas. Cada escena muestra dos
oficios en mitades iguales y cambia de derecha a izquierda cada 3 segundos. La
primera pareja funciona sin JavaScript; las restantes cargan progresivamente.
El control `Pausar imágenes`/`Reanudar imágenes`, la pausa durante interacción,
la visibilidad de la página y `prefers-reduced-motion` evitan movimiento no
controlado. No se agregaron assets, servicios externos ni dependencias.

Los cuatro indicadores existentes ocupan ahora el panel derecho del hero en
una grilla 2×2 y mantienen la indicación `Valores simulados`. Debajo comienza
directamente `Rangos orientativos por servicio`. Los rubros Electricidad,
Refrigeración y climatización, Plomería, Gas domiciliario, Construcción en seco,
y Revestimientos y terminaciones usan desplegables semánticos. Cada uno contiene
cinco trabajos frecuentes con unidad de referencia. Los treinta importes son
marcadores explícitos `$0 – $0`, rotulados `Rango estimativo pendiente`; la
introducción aclara que no son cotizaciones ni datos reales. No se inventaron
precios, demanda adicional ni estadísticas.

Validación ejecutada: focales UX-03/UX-03A 18/18; selección relacionada de
autenticación, Design System V2, footer, Home UX-01, Explorar UX-02, navbar,
mercados y controles de búsqueda/seguridad 80/80. Sintaxis de
`markets-carousel.js` aprobada. En Docker se verificó el avance automático,
pausa manual y `aria-pressed`, los seis desplegables, treinta filas y enlaces de
búsqueda; consola sin errores. Revisión visual en 1440, 1024, 768, 390 y 320 CSS
px, temas claro/oscuro, dos imágenes visibles, indicadores, controles de 44 px
y ausencia de overflow horizontal: aprobada localmente. La suite completa no se
ejecutó porque queda reservada para el retest independiente.

Archivo adicional de este refinamiento: nuevo
`app/static/js/markets-carousel.js`; se ajustaron
`app/services/market_view_service.py`, `app/templates/mercados.html`,
`app/static/css/markets-v2.css`, `tests/test_markets_ux03.py` y este handoff.
Sin migraciones, cambios de datos o backend productivo. El Compose descartable
permanece saludable en `http://127.0.0.1:5050/mercados` y la pestaña queda
abierta para aprobación visual. Git conserva todos los cambios UX-03 sin commit
y staging vacío. No hubo push, PR, merge ni deploy porque el refinamiento aún
requiere aprobación visual y retest independiente. Próximo paso: revisar hero,
cambio de imágenes y desplegables; no completar los importes hasta definir una
fuente y metodología de precios aprobadas.

---

# UX-03: navbar y rediseño público de Precios de mercado

Estado: READY_TO_RESUME
Timestamp: 2026-09-22T22:38:56-03:00
Origen: laptop; agente: Codex. Rama: `feature/ux-ui-foundation`; HEAD base y
último commit: `24bcb9412e182d5190ca4ceaf75de577b66f0a18`; origin
`https://github.com/cristhian-star/TRAX-PLATFORM.git`.
Objetivo: completar UX-03 sobre la base local UX-03A, preservando el navbar
público aprobado y rediseñando únicamente la página pública `/mercados`.

El navbar mantiene una sola estructura para escritorio y móvil, en el orden
`Inicio`, `Explorar rubros`, `Precios de mercado`, `Operaciones`, `Ecosistema`,
`Planes`, igual para visitantes, clientes y profesionales. `/mercados` continúa
siendo público, conserva `aria-current="page"` y no incorpora `Mi panel` ni
modifica dashboards privados, autenticación, permisos o rutas de negocio.

La página nueva presenta un hero de referencia pública, aviso visible de datos
demostrativos, cuatro indicadores y cuatro rangos preexistentes, tendencias
simuladas con `progress`, factores de interpretación, metodología desplegable y
acciones hacia `/explorar`, `/buscar` y `/presupuestos/nuevo`. Los datos de
presentación quedaron centralizados en `market_view_service.py`; son ficticios,
estables y escapados por Jinja. No se agregaron estadísticas, controles falsos,
CDN, dependencias, JavaScript, analítica ni persistencia. Los iconos son SVG
inline decorativos y accesibles. `markets-v2.css` usa tokens del Design System
V2, objetivos táctiles de 44 px y reflow sin estructura duplicada.

Validación local ejecutada: focales UX-03/UX-03A 16/16; selección relacionada
de autenticación, Design System V2, footer, Home UX-01, Explorar UX-02, navbar,
mercados y controles de búsqueda/seguridad 78/78. `compileall`, UTF-8 estricto
de diez archivos, enlaces de búsqueda y acciones, smoke HTTP 200 para `/` y
`/mercados`, consola sin errores y `git diff --check`: aprobados. No se modificó
JavaScript y no correspondió una validación nueva de sintaxis. La suite completa
no se ejecutó porque queda reservada para el retest independiente.

Inspección visual en `mandobra_stabilization`: imagen web reconstruida, servicio
saludable y disponible en `http://127.0.0.1:5050/` y
`http://127.0.0.1:5050/mercados`. Se verificaron 1440, 1024, 768, 390 y 320 CSS
px, temas claro y oscuro, navegación móvil, foco visible por teclado, lectura de
metodología, acciones de 44 px y ausencia de overflow horizontal o recorte. Las
dos páginas quedan abiertas para aprobación visual. El PostgreSQL descartable
permanece saludable. `trax-postgres` conservó el ID
`8d989fb2a948be425fb43d3992dc25fcaeae8f79dcb054b48c9d55cd89e18154` y su
estado previo `exited/unhealthy`; no fue iniciado, conectado ni modificado.

Archivos del trabajo local: `app/templates/base.html`,
`app/static/css/visitor-navbar-v1.css`, `tests/test_navbar_markets_ux03a.py`,
`app/routes/main_routes.py`, nuevo `app/services/market_view_service.py`,
`app/templates/mercados.html`, nuevo `app/static/css/markets-v2.css`, nuevo
`tests/test_markets_ux03.py`, `docs/BACKLOG.md` y este handoff. Sin migraciones,
cambios de esquema, datos o servicios externos. El backlog registra como futuro
la fuente real, metodología versionada, umbrales de muestra, privacidad,
retención y revisión administrativa; nada de eso se implementó aquí.

Git queda con estos diez paths sin commit y staging vacío. No hubo push, PR,
merge ni deploy porque falta la aprobación visual expresa y el retest
independiente. Riesgo pendiente: los valores siguen siendo demostrativos y no
deben presentarse como mediciones reales. Próximo paso: revisar visualmente las
dos pestañas abiertas; con aprobación, entregar el paquete al agente de Testing.
No incorporar dashboards privados, datos reales, migraciones ni analítica en
este incremento.

---

# UX-03A: reordenamiento del navbar público

Estado: READY_TO_RESUME
Timestamp: 2026-09-22T22:00:52-03:00
Origen: laptop; agente: Codex. Rama: `feature/ux-ui-foundation`; HEAD base y
último commit: `24bcb9412e182d5190ca4ceaf75de577b66f0a18`; origin
`https://github.com/cristhian-star/TRAX-PLATFORM.git`.
Objetivo: reubicar el acceso público existente de mercados y presentarlo como
`Precios de mercado`, sin rediseñar su página ni modificar los portales privados.

El navbar compartido conserva una sola estructura para escritorio y móvil. Su
orden público queda `Inicio`, `Explorar rubros`, `Precios de mercado`,
`Operaciones`, `Ecosistema`, `Planes`, tanto para visitantes como para sesiones
cliente o profesional. `Precios de mercado` reutiliza `/mercados`, permanece
público y es el único enlace con esa etiqueta. Los enlaces directos principales
incorporan `aria-current="page"`; el activo usa tokens del tema y mantiene el
foco visible existente. No se agregó `Mi panel` ni se cambiaron menú de cuenta,
sesión, roles, autenticación, rutas, lógica o JavaScript.

`Precios de mercado` es el tablero público y demostrativo de precios: conserva
íntegramente sus datos mock. Los dashboards privados de cliente y profesional
son conceptos distintos y no fueron modificados. `Mi panel` se incorporará en
un incremento posterior dentro de la navegación lateral izquierda de cada
portal autenticado, no en el navbar superior.

Validación local ejecutada: focales UX-03A 7/7; regresiones relacionadas de
autenticación, Design System V2, footer, Home UX-01 y Explorar UX-02 53/53.
`compileall`, UTF-8 estricto de los archivos técnicos, enlace `/mercados` y
`git diff --check`: aprobados. No se modificó JavaScript, por lo que no aplicó
una nueva validación de sintaxis JS. Suite completa no ejecutada por alcance.

Inspección visual en el Compose exclusivo `mandobra_stabilization`: web
reconstruida y saludable en `http://127.0.0.1:5050/`. A 1440 px y 390 px se
confirmaron orden, un solo enlace, activo correcto en `/mercados`, temas claro
y oscuro, menú móvil expandible y ausencia de overflow horizontal. La página
queda disponible para aprobación visual. PostgreSQL descartable sigue saludable;
`trax-postgres` conservó el ID `8d989fb2a948be425fb43d3992dc25fcaeae8f79dcb054b48c9d55cd89e18154`
y su estado previo `exited/unhealthy`; no fue iniciado, conectado ni modificado.

Archivos del incremento: `app/templates/base.html`,
`app/static/css/visitor-navbar-v1.css`, nuevo
`tests/test_navbar_markets_ux03a.py` y este handoff. Sin migraciones, cambios de
datos, servicios externos ni bases reales. Git queda con estos cuatro cambios
sin commit y staging vacío. Push, PR, merge y deploy no realizados por alcance
y porque falta la aprobación visual expresa del usuario. Próximo paso: revisar
Home y `/mercados` en escritorio y móvil; después de la aprobación corresponde
el retest independiente, sin iniciar todavía el rediseño de mercados o de los
dashboards privados.

---

# Corrección UX-02: contrato de tarjetas y aislamiento de logging

Estado: READY_TO_RESUME
Timestamp: 2026-09-22T02:54:54-03:00
Origen: laptop; agente: Codex. Rama: `feature/ux-ui-foundation`; HEAD base y
último commit: `f005b3ed2cef6d68d4f0de6b6303c622d88d69eb`; origin
`https://github.com/cristhian-star/TRAX-PLATFORM.git`.
Objetivo: resolver los hallazgos P2/P3 de Testing sin alterar el diseño visual
UX-02 aprobado ni debilitar la prueba de protección de secretos.

P2 resuelto. El usuario aprobó visualmente la tarjeta compacta formada por
imagen, título, etiquetas y acción `Explorar profesionales`; no lleva párrafo
descriptivo. La prueba focal ahora expresa ese contrato mediante la estructura
de las veinte tarjetas y los campos de `ExploreTrade`, en vez de depender solo
de que una frase concreta no aparezca. `description` no tenía consumidores ni
una utilidad documentada, por lo que se retiró del objeto de presentación y de
las veinte entradas. HTML, CSS, alineación, imágenes, títulos, etiquetas,
acciones, enlaces, términos de búsqueda y taxonomía permanecen intactos.

P3 resuelto localmente. La reproducción determinista demostró que
`logging.config.fileConfig("alembic.ini")`, usado por el entorno Alembic,
deshabilita por defecto el logger existente `app`; antes estaba
`disabled=False` y después `disabled=True`. Por eso el nodo aislado pasaba y
podía fallar tras pruebas de migración. La captura de seguridad ahora conserva
el nivel, handlers, filtros, `propagate`, `disabled` y el umbral global de
logging; habilita y limpia filtros solo durante `assertLogs`, y restaura todo en
`finally`. Una regresión contamina deliberadamente cada estado y acredita su
restauración. La prueba sigue exigiendo el mensaje público, presencia real del
log y ausencia de token, clave, teléfono y payload sensible. No se modificó
producción ni `migrations/env.py`.

Validación ejecutada: focales UX-02 15/15; nodo de seguridad aislado 1/1;
módulo `test_security_compliance_phase3` 9/9; reproducción mínima
`fileConfig -> seguridad` 2/2 y `seguridad -> fileConfig -> seguridad` 3/3;
selección con parche de `logging.Logger._log` y estados contaminados 3/3;
regresiones frontend relacionadas 38/38. `compileall`, UTF-8, enlaces relativos
y `git diff --check`: aprobados. La
suite completa no se ejecutó porque queda reservada para retest independiente.

Archivos ajustados por esta corrección:
`app/services/explore_catalog_service.py`,
`tests/test_explore_rubros_ux02.py`,
`tests/test_security_compliance_phase3.py` y este handoff. Los ocho cambios
locales UX-02 preexistentes fueron preservados; `tests/test_security_compliance_phase3.py`
es el único path adicional. Sin migraciones ni cambios de datos. Staging vacío;
sin commit, push, PR, merge ni deploy porque P2/P3 quedan pendientes de retest
independiente. Próximo paso: ejecutar el paquete de Testing sin incorporar
descripciones ni modificar la presentación aprobada.

---

# Refinamiento visual UX-02: alineación interna de tarjetas

Estado: READY_TO_RESUME
Timestamp: 2026-09-21T21:37:07-03:00
Origen: laptop; agente: Codex. Rama: `feature/ux-ui-foundation`; HEAD base y
último commit: `f005b3ed2cef6d68d4f0de6b6303c622d88d69eb`; origin
`https://github.com/cristhian-star/TRAX-PLATFORM.git`.
Objetivo: alinear títulos, etiquetas, acciones y bordes de las tarjetas de
`/explorar` sin alterar contenido, imágenes, enlaces ni búsquedas de UX-02.

La grilla exterior estira las tarjetas de cada fila. Cada tarjeta usa dos filas
internas, imagen y cuerpo, con `height: 100%`; el cuerpo usa áreas CSS Grid
compartidas para título, etiquetas y acción. El título conserva espacio mínimo
para dos líneas, las etiquetas ocupan una zona flexible sin recorte y la acción
queda al fondo. No se agregaron alturas rígidas de tarjeta, posiciones
absolutas, selectores individuales, rellenos invisibles, estilos inline ni
JavaScript. El template solo añadió la clase común `rubro-card__title`.

Medición con `getBoundingClientRect()` en 1440, 1280, 1024, 768, 390 y 320 px:
cuatro/dos/una columnas según breakpoint y diferencia máxima de `0 px` dentro
de cada fila para altura y borde inferior de tarjetas, inicio de títulos, inicio
de etiquetas y extremos superior/inferior de botones. No hubo overflow
horizontal, superposición ni recorte de títulos, etiquetas o acciones. Se
revisaron los temas claro y oscuro y el foco por teclado sobre `Explorar
profesionales`; el contorno y anillo de foco permanecen visibles. El reflow
equivalente a 200% se cubrió a 768 CSS px sobre el ancho de escritorio de 1536;
el bridge automatizado no expuso un control nativo del zoom cromado, por lo que
esa comprobación exacta queda incluida en la aprobación visual manual.

Validación local: 15/15 focales UX-02 y 38/38 regresiones de home, footer,
Design System y autenticación. `compileall`, UTF-8 y `git diff --check`
aprobados. Suite completa no ejecutada por alcance. Compose exclusivo
`mandobra_stabilization`: web reconstruida y saludable en
`http://127.0.0.1:5050/explorar`; localhost queda disponible para revisión.
`trax-postgres`, `trax_db`, imágenes, rutas, servicios, modelos y migraciones no
fueron tocados.

Archivos ajustados en este refinamiento:
`app/static/css/explore-rubros-v1.css`,
`app/templates/explorar_rubros.html`,
`tests/test_explore_rubros_ux02.py` y este handoff. Se preservaron los ocho
cambios locales UX-02 existentes. Staging vacío; sin commit, push, PR, merge ni
deploy porque el refinamiento espera aprobación visual del usuario y Testing
final. Próximo paso: revisar localhost, incluido zoom manual al 200%; si se
aprueba, entregar el paquete UX-02 completo a Testing sin integrar todavía.

---

# Refinamiento visual UX-02: tarjetas compactas y acciones destacadas

Estado: READY_TO_RESUME
Timestamp: 2026-09-21T21:15:23-03:00
Origen: laptop; agente: Codex. Rama: `feature/ux-ui-foundation`; HEAD base y
último commit: `f005b3ed2cef6d68d4f0de6b6303c622d88d69eb`; origin
`https://github.com/cristhian-star/TRAX-PLATFORM.git`.
Objetivo: simplificar las tarjetas de `/explorar` tras la revisión visual del
usuario, conservando títulos, etiquetas, imágenes, búsqueda y estructura UX-02.

Se retiraron de la vista los párrafos descriptivos de los veinte rubros. Las
descripciones permanecen en el catálogo de presentación como datos internos,
pero el template muestra únicamente título, etiquetas y acción. Las etiquetas
ahora usan los tokens semánticos `primary`, `primary-soft` y `primary-border`
del Design System, con contraste diferenciado en temas claro y oscuro. En
Calderas y calefacción se ajustó la etiqueta a `Pisos radiantes`, junto con
`Calderas` y `Controles de presión`. La acción por tarjeta pasó al estilo
primario naranja y al texto `Explorar profesionales`; su destino GET y los
términos de búsqueda no cambiaron.

Validación local: 14/14 focales UX-02 y 38/38 regresiones de home, footer,
Design System y autenticación; `compileall` aprobado. Inspección en el Compose
exclusivo `mandobra_stabilization`: 1536 px y 390 px, temas claro/oscuro, una
columna móvil, cero descripciones y cero overflow horizontal. Colores
computados: etiquetas claras `rgb(185, 56, 10)` sobre `rgb(255, 244, 237)` y
oscuras `rgb(255, 138, 76)` sobre fondo semitransparente del token; CTA claro
`rgb(211, 68, 14)` con texto blanco y CTA oscuro `rgb(255, 138, 76)` con texto
oscuro. Web reconstruida y saludable en `http://127.0.0.1:5050/explorar` para
revisión. `trax-postgres` y `trax_db` no fueron tocados.

Archivos ajustados en este refinamiento:
`app/templates/explorar_rubros.html`,
`app/static/css/explore-rubros-v1.css`,
`app/services/explore_catalog_service.py`,
`tests/test_explore_rubros_ux02.py` y este handoff. Se preservó el resto del
trabajo UX-02 local. Staging vacío; sin commit, push, PR, merge ni deploy porque
el conjunto continúa pendiente de revisión visual y Testing final. Próximo
paso: revisar el catálogo abierto en localhost y, si se aprueba, entregar el
paquete completo UX-02 a Testing sin modificar taxonomía ni lógica de búsqueda.

---

# UX-02: catálogo visual de Explorar rubros

Estado: READY_TO_RESUME
Timestamp: 2026-09-21T20:35:06-03:00
Origen: laptop; agente: Codex. Rama: `feature/ux-ui-foundation`; HEAD base y
último commit: `f005b3ed2cef6d68d4f0de6b6303c622d88d69eb`; origin
`https://github.com/cristhian-star/TRAX-PLATFORM.git`.
Objetivo: rediseñar `/explorar` como catálogo visual accesible de veinte rubros,
sin modificar la taxonomía canónica, los WebP versionados ni lógica de negocio.

Se incorporó un catálogo de presentación centralizado e inmutable con cinco
categorías editoriales y veinte tarjetas. Cada entrada declara identificador,
título, descripción, hasta tres ejemplos, WebP, alt ilustrativo y término de
búsqueda. La pantalla usa un único `h1`, `h2` por categoría, `h3` por tarjeta,
anclas nativas, buscador GET por servicio/zona, acción por rubro y acción general.
No se agregó JavaScript. Las imágenes mantienen 1200 x 900, lazy loading,
decodificación asíncrona y `object-fit: cover`.

Correspondencias aprobadas: Electricidad domiciliaria -> `Electricista`,
Plomería -> `Plomero` y Aire acondicionado ->
`Técnico en Aire Acondicionado`. Los otros diecisiete rubros no tienen una
equivalencia canónica exacta aprobada y envían su título editorial completo;
pueden producir una búsqueda vacía antes que una coincidencia incorrecta.
`resultados.html` conserva y muestra de forma escapada cualquier servicio que no
pertenezca al selector cerrado. El catálogo vacío muestra un estado propio y un
error inesperado conserva la respuesta genérica 500; ninguno se presenta como
falta de profesionales.

Responsive verificado en Docker a 1440, 1280, 768, 390 y 320 px: cuadrículas de
4/4/2/1/1 columnas, buscador apilado bajo 48rem, categorías con wrap, targets de
44 px y cero overflow horizontal. Se revisaron los veinte encuadres, navegación,
foco por teclado, estado de búsqueda vacío y temas claro/oscuro. Durante la
revisión se corrigió el contraste del título del hero en tema oscuro usando el
blanco estable del Design System. El navbar compartido conserva una atenuación
visual preexistente en el menú móvil oscuro; no fue modificado por estar fuera de
alcance.

Validación local: 13/13 focales UX-02; 38/38 regresiones de home, navbar, footer,
Design System y autenticación; 17/17 regresiones relacionadas de búsqueda y
seguridad. `compileall` focal, 31 enlaces internos/fragmentos, assets locales,
UTF-8 estricto y ausencia de mojibake nuevo, y `git diff --check`: aprobados.
Permanece una secuencia histórica de mojibake en una recomendación de reseñas de
`main_routes.py`, fuera del diff y del alcance; no se amplió. Suite completa y
Testing final no ejecutados por instrucción.

Compose exclusivo `mandobra_stabilization`: web reconstruida y saludable en
`http://127.0.0.1:5050/explorar`, con la pestaña abierta en tema claro para
aprobación visual. PostgreSQL descartable permaneció saludable; `trax-postgres`
conservó ID `8d989fb2a948`, detenido, y no se accedió a `trax_db`. No hubo
migraciones ni cambios de datos.

Archivos modificados: `app/routes/main_routes.py`,
`app/templates/explorar_rubros.html`, `app/templates/resultados.html`,
`app/static/css/explore-rubros-v1.css`, `docs/BACKLOG.md` y este handoff.
Archivos nuevos: `app/services/explore_catalog_service.py` y
`tests/test_explore_rubros_ux02.py`. Los veinte WebP y UX-01 permanecen intactos.
Staging vacío; sin commit, push, PR, merge ni deploy porque falta aprobación
visual del usuario y Testing final. Próximo paso: revisar `/explorar` en
localhost; si la presentación se aprueba, entregar el paquete a Testing sin
integrar ni modificar taxonomía, modelos o imágenes.

---

# Refinamiento footer corporativo UX-01: estructura demostrativa

Estado: READY_TO_RESUME
Timestamp: 2026-09-20T16:31:28-03:00
Origen: laptop; agente: Codex. Rama: `feature/ux-ui-foundation`; HEAD base `a65fe78e9a5a9f3a248a56383f5538d166c75ddd`; origin `https://github.com/cristhian-star/TRAX-PLATFORM.git`.
Objetivo: completar el footer azul compartido, distinguiendo destinos funcionales de contenido futuro, sin modificar secciones anteriores del home ni lógica de negocio.

`base.html` conserva un único footer global con identidad MANDOBRA, cobertura Capital Federal y AMBA, columnas Explorar/Para profesionales/Ayuda/Legal, tres SVG inline decorativos de Instagram, Facebook y LinkedIn sin enlaces ni red, y barra inferior 2026. Enlaces reales: `/buscar`, `/presupuestos/nuevo`, `/emergencias/nueva`, `/register`, `/propuestas`, `/planes` y anclas del home visitante `#featured-title`, `#faq-title`, `#trust-title`. Las anclas no se enlazan con sesión iniciada porque `/` muestra otro template; aparecen como texto inactivo. Herramientas, Cómo funciona, Contacto y todos los documentos legales son texto no interactivo con leyendas de preparación. No se afirman términos vigentes ni perfiles oficiales. Backlog registra titularidad/seguridad de cuentas, documentos, políticas, revisión legal/fiscal y habilitación gradual de rutas.

Validación local: 38/38 pruebas focales/footer/home y regresiones frontend; pruebas JS de FAQ y carrusel aprobadas. Sintaxis JS, `compileall`, UTF-8, enlaces válidos/fragmentos y `git diff --check` aprobados. Inspección preliminar del Compose descartable a 1440, 768, 390 y 320 px: cinco columnas (marca + cuatro) en escritorio, dos en tablet, una en móvil, sin overflow horizontal; contraste, iconos, foco y contenido pendiente distinguible, barra inferior. Footer también renderizado en login, registro y planes. Suite completa, PostgreSQL y retest independiente no ejecutados por alcance. Aprobación visual del usuario pendiente.

Archivos intervenidos en esta sesión: `app/templates/base.html`, `app/static/css/styles.css`, nuevo `tests/test_corporate_footer.py`, ajuste de expectativa en `tests/test_home_hero_carousel.py`, `docs/BACKLOG.md` y este handoff. Los refinamientos UX-01 previos permanecen íntegros. Web del proyecto exclusivo `mandobra_stabilization` disponible en `http://127.0.0.1:5050/`; no se tocó `trax_db`, base ni migraciones. Staging vacío; no hubo commit, push, PR, merge ni deploy porque está pendiente la revisión visual. Próximo paso: aprobación visual del usuario y luego retest final independiente. Conservar el entorno encendido hasta su inspección.

---

# Cuarto refinamiento visual UX-01: confianza, ayuda y cierre del home

Estado: READY_TO_RESUME
Timestamp: 2026-09-20T16:08:46-03:00
Origen: laptop; agente: Codex. Rama: `feature/ux-ui-foundation`; HEAD base `a65fe78e9a5a9f3a248a56383f5538d166c75ddd`; origin `https://github.com/cristhian-star/TRAX-PLATFORM.git`.
Objetivo: completar el home tras los seis oficios, con confianza compacta, FAQ local y llamado para ambos actores, conservando hero, carrusel, MIME, búsqueda y footer global.

Se sustituyó la confianza anterior por los tres mensajes aprobados y se añadió un FAQ de seis `details`/`summary`, con filtro independiente que normaliza acentos y mayúsculas, estado vacío y anuncio accesible. Sin JavaScript permanecen las seis respuestas; el filtro no envía ni conserva consultas. El llamado final reutiliza `main.buscar` (`/buscar`) y `auth.register` (`/register`), ambos GET 200. Registro permite elegir rol profesional, pero no preselecciona el rol mediante un enlace aprobado; no se alteró autenticación. Footer global único sin cambios. Backlog registra el futuro asistente documentado y soporte humano, sin implementarlos. Persiste el desajuste previo del selector de Pintura descrito en el registro anterior.

Validación local: 33/33 focales/regresiones frontend, pruebas JS de FAQ y carrusel, sintaxis JS, `compileall`, UTF-8, enlaces, y `git diff --check` aprobados. Inspección preliminar en `mandobra_stabilization` a 1440, 768, 390 y 320 px: tres elementos de confianza en escritorio/tablet y apilados en móvil, llamado doble en escritorio/tablet y apilado en móvil, FAQ expansible, filtro y estado vacío, footer único, sin overflow horizontal. Enlaces navegados hasta búsqueda y registro. Aprobación visual del usuario y retest final independiente pendientes; suite completa y PostgreSQL no ejecutados por alcance.

Archivos intervenidos en esta sesión: `app/templates/home.html`, `app/static/css/home-v1.css`, nuevo `app/static/js/home-faq.js`, `tests/test_home_hero_carousel.py`, nuevo `tests/js/home_faq.test.js`, `docs/BACKLOG.md` y este handoff. Se conservaron los cambios UX-01 anteriores, ocho WebP, carrusel, MIME y demás lógica. Web del Compose descartable reconstruida y recreada, disponible en `http://127.0.0.1:5050/`, sin tocar `trax_db` ni migraciones. Git: staging vacío, sin commit, push, PR, merge ni deploy porque continúa la revisión visual; próximo paso: aprobación visual del usuario, decisión posterior sobre catálogo Pintura y retest final independiente. No integrar antes de esa revisión.

---

# Tercer refinamiento visual UX-01: oficios destacados

Estado: READY_TO_RESUME
Timestamp: 2026-09-20T15:46:12-03:00
Origen: laptop; agente: Codex.
Rama: `feature/ux-ui-foundation`; HEAD base preservado: `a65fe78e9a5a9f3a248a56383f5538d166c75ddd`; origin `https://github.com/cristhian-star/TRAX-PLATFORM.git`.
Objetivo: reemplazar exclusivamente la sección de tres tarjetas numeradas por seis oficios editoriales, preservando hero, carrusel, mensajes, MIME y buscador.

Nueva sección "Oficios destacados" con seis enlaces semánticos e imágenes WebP existentes, lazy, 16:9 y alt vacío; cuadrícula de 3 columnas en escritorio, 2 en tablet y 1 en móvil. Mapeo visible → `servicio` GET: Electricidad → Electricidad; Plomería → Plomeria; Refrigeración y climatización → Refrigeracion A/C; Cableado estructurado → Electricidad; Instalación de calderas → Gas domiciliario; Pintura → Pintura. Las tres primeras equivalencias y las dos familias amplias reutilizan opciones existentes. `Pintura` es un valor real de `Professional.servicio` aceptado por `/buscar` y mostrado en el encabezado de resultados, pero no está en el selector cerrado de resultados: éste muestra "Todos los servicios" aunque el filtro Pintura esté activo. No se alteró el buscador ni se inventó una equivalencia. Si se requiere selección visible en ese control, hace falta autorizar un incremento de catálogo fuera del alcance actual.

Las tarjetas son selección editorial, no ranking respaldado por métricas. `docs/BACKLOG.md` registra diseño futuro de eventos anónimos, territorio CABA/AMBA, oferta/demanda, resultados vacíos, conversión, ventana y muestra, protección de manipulación, fallback editorial y privacidad/retención. No se implementó analítica ni persistencia.

Validación local: 30/30 pruebas focales y frontend relacionadas; temporizadores JS, `compileall`, sintaxis JS, UTF-8, enlaces y `git diff --check` aprobados. Vista preliminar Docker a 1440, 768, 390 y 320 px: imágenes encuadradas, tres/dos/una columnas, foco/enlaces accesibles y sin overflow horizontal. El enlace Pintura respondió 200 y evidenció el desajuste del selector descrito. Suite completa, PostgreSQL y retest independiente no ejecutados por alcance. Aprobación visual definitiva pendiente del usuario.

El Compose descartable `mandobra_stabilization` se reconstruyó solo para web y permanece disponible en `http://127.0.0.1:5050/`; no se tocó `trax_db`, volúmenes ni migraciones. Archivos intervenidos en esta sesión: `app/templates/home.html`, `app/static/css/home-v1.css`, `tests/test_home_hero_carousel.py`, `docs/BACKLOG.md` y este handoff. Los ocho WebP, el JS del carrusel y la corrección MIME no se modificaron. Git: 16 archivos con cambios locales, staging vacío, sin commit, push, PR, merge ni deploy. Próximo paso: inspección visual del usuario y decisión sobre Pintura en el selector; luego retest final independiente. No integrar ni desmontar el entorno antes de esa revisión.

---

# Segundo refinamiento visual UX-01: altura y mensajes dinámicos

Estado: READY_TO_RESUME
Timestamp: 2026-09-20T15:17:41-03:00
Origen: laptop; agente: Codex.
Objetivo: ampliar el hero aprobado y rotar tres pares de título/subtítulo sin mover buscador, flechas ni otros contenidos.
Rama: `feature/ux-ui-foundation`; HEAD base preservado: `a65fe78e9a5a9f3a248a56383f5538d166c75ddd`; origin `https://github.com/cristhian-star/TRAX-PLATFORM.git`.

Se preservaron íntegros los 14 cambios UX-01/MIME/refinamiento previo. El hero crece 80 px efectivos en escritorio (496,24 → 576,24 px a 1440) y 48 px en móvil (1087,20 → 1135,20 px a 390), con padding repartido arriba y abajo, sin altura rígida. Tres mensajes exactos rotan cada 10.000 ms con fundido de 180 ms; el primero queda en HTML sin JavaScript. Tres copias invisibles y excluidas de accesibilidad reservan el alto máximo del bloque, por lo que el buscador no salta. Las ocho imágenes continúan cada 5.000 ms; navegación manual cambia solo la imagen. Temporizadores separados se cancelan/reprograman ante hover, tacto, foco, pestaña oculta o movimiento reducido. En reduced motion no hay autoplay ni transiciones. No se recuperaron los elementos visibles retirados en el refinamiento anterior.

Validación: focales/regresiones frontend `tests.test_home_hero_carousel`, `tests.test_design_system_v2` y `tests.test_auth_ux_redesign_v1`: 28/28; nueva prueba de temporizadores con Node: aprobada. `compileall`, sintaxis JS, UTF-8 y `git diff --check`: aprobados. Inspección preliminar en Docker a 1440, 390 y 320 px: composición legible, flechas centradas, buscador completo, sin overflow horizontal ni errores de consola; la rotación hasta el tercer mensaje mantuvo altura y posición. GET/HEAD WebP y MIME de CSS/JS/PNG siguen cubiertos por la regresión focal. Suite completa, PostgreSQL y retest final no ejecutados por alcance.

Entorno descartable `mandobra_stabilization`: se reconstruyó y recreó solo web, disponible en `http://127.0.0.1:5050/` para revisión del usuario. Se deja encendido; no se accedió a `trax_db`, no se hicieron migraciones ni seed. Archivos intervenidos en esta sesión: `app/templates/home.html`, `app/static/css/home-v1.css`, `app/static/js/home-hero-carousel.js`, `tests/test_home_hero_carousel.py`, `docs/HANDOFFS/ACTIVE_HANDOFF.md`; nuevo `tests/js/home_hero_carousel.test.js`. Los ocho WebP y la corrección MIME de `app/__init__.py` permanecen sin cambios de esta sesión. Git: 15 archivos con cambios locales, staging vacío, sin commit, push, PR o merge porque falta aprobación visual. Sin bloqueantes técnicos conocidos; riesgo pendiente: valoración visual final del usuario. Próximo paso: el usuario revisa `5050` en escritorio y móvil; solo después corresponde retest independiente. No integrar ni desmontar el entorno antes de esa revisión.

---

# Refinamiento visual UX-01 pendiente de aprobación del usuario

Estado: READY_TO_RESUME
Timestamp: 2026-09-20T14:33:37-03:00
Origen: laptop; agente: Codex.
Objetivo: simplificar el hero visitante y mejorar la visibilidad de las ocho escenas sin iniciar todavía el retest final independiente.
Rama: `feature/ux-ui-foundation`; HEAD/base preservado: `a65fe78e9a5a9f3a248a56383f5538d166c75ddd`.
Origin: `https://github.com/cristhian-star/TRAX-PLATFORM.git`; staging vacío; 14 cambios locales UX-01/MIME/refinamiento, sin cambios adicionales.

Se retiraron del hero la ceja, los tres beneficios, la nota de imágenes, el botón de pausa y el contador visible. Permanecen el título, párrafo y buscador. El overlay azul oscuro se redujo moderadamente; los ocho WebP originales y la corrección MIME se conservaron intactos. Las flechas laterales son cheurones sin caja, con área de 44×44 px y nombres accesibles. El carrusel conserva fundido, avance automático de 5000 ms y navegación manual; reinicia un único temporizador después de cada cambio, pausa durante hover, tacto, foco o pestaña oculta y desactiva autoplay/transiciones con movimiento reducido. La primera imagen permanece como fallback sin JavaScript; el anuncio de cambios manuales no es visible.

Validación ejecutada: focal `tests.test_home_hero_carousel` y regresiones frontend `tests.test_design_system_v2`, `tests.test_auth_ux_redesign_v1`: **27/27**; `compileall`, `node --check`, UTF-8 y `git diff --check`: código 0. GET y HEAD reales desde el contenedor: ocho WebP `image/webp`, CSS `text/css`, JS `text/javascript` y PNG `image/png`, todos 200. Inspección de navegador: hero de escritorio, flechas funcionales, vista móvil sin overflow horizontal ni solapamiento horizontal con el buscador, consola sin errores. La suite completa y el retest final independiente **no se ejecutaron**, conforme al alcance solicitado. No se conocen bloqueantes técnicos; contraste y composición definitivos requieren aprobación visual del usuario.

Entorno de revisión: `docker compose -p mandobra_stabilization -f docker-compose.stabilization.yml build web`, seguido de `up -d --no-deps --force-recreate web`. Web y PostgreSQL descartable del proyecto permanecen saludables; web disponible solo en `http://127.0.0.1:5050/`. No se inició ni conectó `trax_db`; `trax-postgres` conservó ID `8d989fb2a948` y estado `Exited (0)`. No se ejecutó seed ni se eliminó el entorno, para permitir inspección del usuario.

Archivos editados en esta sesión: `app/templates/home.html`, `app/static/css/home-v1.css`, `app/static/js/home-hero-carousel.js`, `tests/test_home_hero_carousel.py` y este handoff. `app/__init__.py` y los ocho WebP preexistentes quedaron sin alteraciones de esta sesión. No hubo staging, commit, push, PR, merge ni deploy porque falta la aprobación visual. Próximo paso: usuario revisa en escritorio y móvil las ocho escenas, la legibilidad, las flechas, el buscador y el ritmo del carrusel; tras su aprobación, realizar retest independiente final. Para retomar: verificar rama, HEAD, staging y 14 cambios; consultar este registro; no integrar ni desmontar el Compose antes de la inspección del usuario.

---

# Corrección focal P2 UX-01: MIME WebP portable

Estado: READY_TO_RESUME
Timestamp: 2026-09-20T13:34:59-03:00
Origen: laptop; agente: Codex.
Rama: `feature/ux-ui-foundation`; HEAD base conservado: `a65fe78e9a5a9f3a248a56383f5538d166c75ddd`.
Hallazgo P2: la respuesta estática de los ocho `.webp` podía depender de la tabla MIME del host Windows y no anunciar `image/webp` de forma portable.
Corrección: `create_app` registra explícitamente `.webp` como `image/webp` antes de construir Flask. La regresión HTTP consulta GET y HEAD de los ocho assets y comprueba `Content-Type`; también protege los tipos CSS, JavaScript y PNG. No se alteraron imágenes, carrusel, buscador, caché, rutas ni backend financiero.
Validación focal y regresiones frontend relacionadas: 27/27; `compileall`, UTF-8 y `git diff --check` aprobados. Suite completa y PostgreSQL no ejecutados por alcance. No se conocen nuevos errores. Testing independiente debe revalidar el P2.
Git: solo los 13 cambios UX-01 anteriores más `app/__init__.py` modificado; staging vacío, sin commit ni push. No hubo PR ni merge porque la corrección está pendiente de retest. Próximo paso: retest HTTP independiente y revisión de UX-01; no integrar ni desplegar antes de aprobación.

---

# Handoff vigente: UX-01 carrusel visual del home

Estado: READY_TO_RESUME
Timestamp: 2026-09-19T13:22:54-03:00
Origen: laptop; agente: Codex.
Objetivo: incorporar ocho escenas aprobadas como fondo del hero visitante, sin alterar textos, buscador, rutas ni lógica de negocio.
Rama: `feature/ux-ui-foundation`; HEAD base conservado: `a65fe78e9a5a9f3a248a56383f5538d166c75ddd`.
Origin: `https://github.com/cristhian-star/TRAX-PLATFORM.git`.

Se convirtieron los ocho PNG aprobados de Downloads a WebP locales 1600×900, entre 53 y 98 KB cada uno; los originales no ingresaron al repositorio. El template muestra la primera imagen aun sin JavaScript. El carrusel carga las siguientes progresivamente, mantiene un overlay oscuro, ofrece controles anterior/siguiente y pausa, se detiene durante interacción y con movimiento reducido, y usa encuadre móvil. Las escenas se identifican como ilustrativas. No hay servicios externos, migraciones ni cambios financieros.

Validación local: 26/26 pruebas focales y regresiones frontend relacionadas; `compileall`, sintaxis JS y `git diff --check` aprobados. Revisión visual en contenedor descartable separado, servido en `127.0.0.1:5051`: escritorio y móvil legibles, buscador intacto, control manual funcional. El contenedor temporal se detuvo; no se modificó `mandobra_stabilization` ni `trax_db`. Suite completa y migraciones no ejecutadas por alcance. No hay errores conocidos; Testing independiente queda pendiente.

Archivos modificados: `app/templates/home.html`, `app/static/css/home-v1.css`, `docs/HANDOFFS/ACTIVE_HANDOFF.md`. Nuevos: `app/static/js/home-hero-carousel.js`, `tests/test_home_hero_carousel.py` y ocho WebP en `app/static/images/home/hero/`.
Git: cambios locales sin staging, commit ni push; no hubo PR ni merge porque UX-01 está pendiente de revisión. Riesgo restante: confirmar calidad y contraste en la matriz final de navegadores/dispositivos. Próximo paso: Testing visual/accesibilidad independiente, luego revisión para commit técnico. No hacer merge ni despliegue antes de esa revisión.

---

# Handoff vigente: demo E2E local aprobada por Testing

Estado: COMPLETED
Fecha de aprobación final: 2026-09-19T11:22:22-03:00.
Rama: `feature/end-to-end-demo-scenarios`.
Commit técnico: `6ce047a`.
Alcance: implementación técnica local exclusiva de QA en el Compose descartable
`mandobra_stabilization`; producción, cobros y efectos financieros reales siguen
deshabilitados.

Testing acreditó el recorrido completo cliente → contrato confirmado → Punto
Agua → una orden simulada → checkout y QR locales → pago aprobado simulado →
conciliación 4E → una comisión ficticia → un crédito PRO 4F. Se verificó una
única orden, evidencia, comisión ficticia y concesión, incluso ante replay, y
ausencia de llamadas externas. No quedaron hallazgos P0–P3 pendientes.

Evidencia final de Testing: focales **7/7** locales y **7/7** en imagen;
regresiones **174/174**; PostgreSQL **12/12** y **35/35**; suite completa
**715 ejecutadas, 709 aprobadas, 6 omitidas, 0 fallos y 0 errores**.
Los seis casos omitidos corresponden al resultado reportado por Testing; no se
reinterpreta su causa en este cierre. Esta aprobación no habilita producción.

El registro siguiente conserva íntegramente la implementación y las
validaciones previas, con sus timestamps originales.

---

# Handoff vigente: simulación end-to-end local 4A–4F

Estado: READY_TO_RESUME
Timestamp: 2026-09-19T11:00:18-03:00
Origen: laptop; agente: Codex.
Rama: `feature/end-to-end-demo-scenarios`.
HEAD/base conservado: `34dcb6c1821aded1f7836ab0d6fdf655095ef98b`.
Origin: `https://github.com/cristhian-star/TRAX-PLATFORM.git`.
Objetivo: recorrido visible cliente → contrato CONFIRMADA → Punto Agua → orden,
checkout y QR locales → pago simulado → conciliación 4E → crédito 4F.
Estado técnico: implementado y validado localmente; pendiente de revisión y
Testing independiente. No producción ni cobro real.

## Implementación y decisiones

`docker-compose.e2e.yml` es un opt-in para el proyecto descartable
`mandobra_stabilization`. Web registra `/dev/e2e` exclusivamente en contenedor,
entorno development/testing, QA habilitado, E2E_DEMO_ENABLED=True, proyecto,
base y origen local exactos. El Compose base mantiene todos los flags financieros
y Mercado Pago False. El seed E2E se ejecuta explícitamente con perfil tools,
crea/reproduce un solo contrato sintético y no se ejecuta en startup.

Se usa un adaptador SimulatedMercadoPago sin HTTP, OAuth ni secretos, con
`provider=mercadopago`, `live_mode=False` e IDs `sim-`. La política de URL local
se inyecta solo en el servicio QA; la allowlist productiva 4D queda intacta.
Enlace y QR codifican exactamente la misma URL local. Client/professional
mantienen sesión, CSRF, roles y ownership. Pago simulado entra por inbox y
trabajo durable 4E, no por webhook HTTP. Un evaluador temporal simulado e
inyectado permite `BEFORE_LOCAL_EXPIRY` solo para IDs `sim-`; el comportamiento
4E ordinario sigue `UNKNOWN` sin prueba temporal. 4F recibe política y prueba
de comisión explícitamente ficticias (`simulated-pro-100-v1`, umbral ARS 100,
comisión neta ARS 100); replay no duplica órdenes ni créditos. Nada representa
comisión comercial real ni pago productivo.

Enlaces visibles desde panel cliente, profesional y `/dev/qa`; contrato usa sus
transiciones normales. CSS usa Design System V2, diseño móvil, etiquetas de
simulación y foco visible. Reinicio únicamente mediante recreación acotada de
volúmenes del proyecto, documentada en el runbook; sin borrado selectivo.

## Validación y Git

- Focales nuevas: 7/7 locales y 7/7 dentro de imagen Docker aislada sin red.
- Focales + regresiones relacionadas: 193 casos cargados, comando final exit 0.
  Incluye contratos, PSP neutral, 4B–4F, rutas, seguridad y configuración.
- `docker compose config` combinado con perfil tools: aprobado; DB sin puerto,
  seed opt-in y flags base False.
- Build de imagen desde cero; migración interna hasta `20260917_03`;
  PostgreSQL y web saludables; seed explícito dos veces reprodujo contrato #1.
- Smoke HTTP host 5050: `/healthz` y `/dev/qa` 200; cambio de sesión, contrato
  CREADA → ACEPTADA → EN_PROGRESO → COMPLETADA → CONFIRMADA; orden, enlace y QR
  PNG, checkout local, pago simulado, 4E DONE y 4F ACCRUED.
- En la base exclusiva se verificaron exactamente un contrato, una orden, un
  evento, un trabajo DONE, una evidencia, una comisión efectiva ficticia y un
  crédito concedido. No se ejecutó suite completa ni gate PostgreSQL de Testing.
- Compileall y `git diff --check` aprobados. Staging vacío, sin commit/push/PR,
  merge o deploy. Cambios sin commit; no migraciones nuevas.
- Teardown con `down --volumes` únicamente del proyecto descartable; inventarios
  posteriores de sus contenedores, redes y volúmenes vacíos.

`trax-postgres` mantuvo ID `8d989fb2a948be425fb43d3992dc25fcaeae8f79dcb054b48c9d55cd89e18154`,
pero estaba `exited starting` al inspeccionarlo antes y después del smoke. No se
lo detuvo, inició, modificó ni se conectó a `trax_db`. Su condición requiere
diagnóstico independiente; no atribuirla a esta simulación.

Archivos de código: `app/__init__.py`, `app/config/config.py`,
`app/routes/e2e_demo_routes.py`, `app/services/simulated_mercadopago_demo.py`,
`app/services/psp_payment_order_contract.py`,
`app/services/payment_order_application_service.py`,
`app/services/payment_order_delivery_service.py`,
`app/services/payment_order_reconciliation_service.py`,
`app/templates/cliente_dashboard.html`, `app/templates/profesional_dashboard.html`,
`app/templates/dev_qa_panel.html`, tres templates E2E, CSS E2E,
`docker-compose.e2e.yml`, `scripts/dev_seed_e2e.py`, `tests/test_e2e_demo.py`.
Documentación: este handoff y `docs/RUNBOOKS/E2E_DEMO_LOCAL.md`.

Próximo paso: revisión independiente del alcance/aislamiento y Testing final,
incluido PostgreSQL adversarial y suite completa. No incorporar endpoints QA ni
valores ficticios a producción. Para retomar seguir el runbook con `-p` y ambos
Compose, verificar identidad de recursos antes de borrar los volúmenes del
proyecto y nunca tocar `trax_db`.

---

# Corrección focal Docker P2: exclusión de Obsidian

Estado: READY_TO_RESUME
Timestamp: 2026-09-18T11:04:43-03:00
Responsable: Codex; dispositivo: laptop.
Rama: `fix/platform-runtime-stabilization`.
HEAD conservado: `a6989619c553a96713baa6f35572fe48f7181110`.
Estado: corrección local validada, pendiente de retest independiente.

Hallazgo P2: el contexto Docker incluía `docs/.obsidian/` y su configuración
local (`app.json`, `appearance.json`, `core-plugins.json`, `graph.json`,
`workspace.json`). La imagen no debe incorporar estos artefactos del editor.
Corrección: `.dockerignore` excluye `.obsidian/` y `**/.obsidian/`, en la raíz y
cualquier profundidad, sin excluir documentación Markdown.

Regresiones en `tests/test_runtime_health.py`: reglas de exclusión y comprobación
real del árbol `/app` dentro de la imagen, incluidos los cinco JSON y conservación
de README/handoff Markdown. Activación explícita con `DOCKER_IMAGE_CHECK_ROOT=/app`.
Comando de regresión independiente, sin red, mounts ni conexión DB:

```powershell
docker run --rm --network none --label com.docker.compose.project=mandobra_stabilization --env DOCKER_IMAGE_CHECK_ROOT=/app --env PYTHON_DOTENV_DISABLED=1 --entrypoint python mandobra_stabilization-app:local -B -m unittest -v tests.test_runtime_health.DockerContextTest
```

Validaciones: build `--no-cache web` aprobado; Compose config aprobado;
focales/relacionadas 45 pruebas, 44 aprobadas y una omitida localmente porque exige
la imagen. Esa regresión se ejecutó dentro de la imagen: DockerContextTest 2/2
aprobadas. Ausencia completa de `.obsidian` y sus cinco JSON confirmada.
Compileall focal y `git diff --check` aprobados. Sin suite completa.

Solo tres archivos reciben esta corrección: `.dockerignore`,
`tests/test_runtime_health.py` y este handoff. Se conservan los diez cambios
existentes y todos los registros anteriores. Rama/HEAD sin cambios, staging
vacío; sin commit, push, PR o merge. No se levantó Compose ni PostgreSQL;
no se tocó `trax-postgres` ni se conectó a `trax_db`. Contenedor de regresión
eliminado por `--rm`; inventarios posteriores del proyecto sin contenedores,
volúmenes ni redes. Imagen/caché local conservadas para el retest.
Próximo paso: retest independiente del hallazgo P2 y revisión del incremento.

---

# Handoff vigente: base Docker descartable validada

Estado: READY_TO_RESUME
Timestamp: 2026-09-18T10:43:12-03:00
Responsable: Codex; dispositivo: laptop.
Rama: `fix/platform-runtime-stabilization`.
HEAD/base conservada: `a6989619c553a96713baa6f35572fe48f7181110`.
Origin verificado: `https://github.com/cristhian-star/TRAX-PLATFORM.git`.
Objetivo: construir y validar un entorno Docker aislado para diagnóstico local.
Estado final: implementación local validada, pendiente de revisión; no producción.

## Implementación y decisiones

Compose independiente `docker-compose.stabilization.yml`, proyecto exclusivo
`mandobra_stabilization`: PostgreSQL 16 interno sin publicar 5432, migración
one-shot `alembic upgrade head`, web condicionada a DB saludable y migración
exit 0. Healthcheck HTTP `/healthz` verifica conexión y head actual con respuesta
genérica. Web disponible en `http://127.0.0.1:5050/` durante el diagnóstico.
Red DB interna, red HTTP propia y tres volúmenes propios; sin nombres globales,
binds del repositorio ni carga del `.env` real. Configuración development
sintética explícita, CSRF habilitado, sin `create_all`. Uploads/instance escribibles
por `appuser` no root (UID 100). Mercado Pago, conciliación y efectos False;
Maps/Cloudinary sin claves. Seed explícito bajo perfil `tools`, nunca automático.

Docker Desktop no publicó el puerto con web solo en una red interna. Se añadió
una red HTTP exclusiva para web; PostgreSQL/migrate/seed permanecen en la interna.
Esta red permite salida de web: los flags y la ausencia de credenciales mantienen
las integraciones externas deshabilitadas. No se hicieron llamadas a Mercado Pago.

## Evidencia ejecutada

- Build desde cero: `build --no-cache --pull web`, aprobado.
- Compose config (también perfil tools), aislamiento y dependencias, aprobados.
- Arranque final desde base vacía, DB/web saludables; migrate exit 0 hasta
  `20260917_03`. Una segunda creación vacía confirmó ausencia de seed automático.
- Pruebas focales y relacionadas: **43/43** (runtime health, configuración,
  controles de seguridad y fundamento PRO entitlement).
- Seed explícito dos veces: primera 4 usuarios, 3 profesionales, 1 suscripción
  sintética y 4 verificaciones; segunda cero nuevos registros. IDs/cantidades y
  vencimiento PRO se conservaron. El seed restablece las contraseñas demo.
- Restart exclusivo de postgres/web: mismos datos y archivos de prueba en
  instance/uploads; migrate conservó ID/FinishedAt, sin ejecutar nuevamente.
- Smoke HTTP host 5050: 200 en `/healthz`, `/`, `/login`, `/register`, `/explorar`,
  `/planes`, `/dev/qa` y `/profesional/1`, `/profesional/2`, `/profesional/3`.
- `pip check`: sin dependencias rotas; compileall focal y diff check aprobados.
- Teardown exclusivo `down --volumes` del proyecto: ausencia posterior de sus
  contenedores, tres volúmenes y dos redes confirmada.
- `trax-postgres` conservó ID
  `8d989fb2a948be425fb43d3992dc25fcaeae8f79dcb054b48c9d55cd89e18154`
  y estado `running healthy`. Solo se inspeccionó metadata; no conexión a `trax_db`.

## Alcance, Git y pendientes

Archivos afectados: `.dockerignore`, `Dockerfile`, `README.md`,
`app/__init__.py`, `app/routes/health_routes.py`, `docker-compose.stabilization.yml`,
`tests/test_runtime_health.py`, `docs/alembic.md`,
`docs/RUNBOOKS/DOCKER_STABILIZATION.md` y este handoff.
Sin migraciones nuevas; head vigente `20260917_03`. Compose persistente original,
requirements y migraciones no modificados. Staging vacío; cambios sin commit.
Sin commit, push, PR, merge o deploy: no autorizados en este encargo.
La imagen local y caché de build quedan disponibles; no hay servicios descartables.

No se ejecutó suite completa: reservada para Testing final. Esta validación no
acredita flujos autenticados completos, contratos, fixtures admin, QA visual,
accesibilidad ni servicios externos. Flask es servidor de desarrollo; imágenes
con tags y transitivas sin lock no garantizan reconstrucción binaria idéntica.
Próximo paso: revisión/Testing independiente y diagnóstico de páginas/flujo con
fixtures explícitos. No inferir disponibilidad de cobros ni producción.

Para retomar seguir [el runbook](../RUNBOOKS/DOCKER_STABILIZATION.md), siempre con
`--env-file .env.example -p mandobra_stabilization -f docker-compose.stabilization.yml`.
No administrar `trax-postgres`, conectar a `trax_db`, usar stamp, prune o down
genérico, borrar volúmenes ajenos, ni hacer Git mutable sin autorización.

---

# Registro anterior conservado íntegramente

# Handoff vigente: cierre técnico local 4F aprobado

Estado: COMPLETED

Timestamp de registro documental: 2026-09-18T09:50:28-03:00
Estado técnico local: APROBADO
Implementación productiva: PENDIENTE
Rama: `feature/payment-effects-pro-commission`.
Commit técnico: `83581b3`.
Registro documental: Codex; dispositivo: laptop.
Evidencia final de Testing suministrada para este cierre, sin repetir su ejecución.

4F implementa el motor interno durable de créditos y comisión comercial separado
de evidencia PSP, contabilidad y facturación. Solo evidencia 4E correlacionada,
acreditada, completa en ARS y sin contradicciones permite evaluar efectos.
La política económica inyectada es versionada, explícita y obligatoria: precio
mensual/umbral y moneda sin valores predeterminados. Comisión neta efectiva
acumulada equivalente al precio mensual PRO genera 1 crédito; su consumo concede
30 días PRO. No se reintroduce la regla histórica de 60 días.

Acumulación y remanente Decimal exactos, consumo FIFO y lotes que vencen
individualmente a los 40 días, sin rejuvenecer saldos anteriores. Idempotencia
por evidencia e identidad financiera, locks y auditoría atómica protegen la
aplicación durable. El reloj efectivo se obtiene después de todos los locks:
se revalidan vencimiento y elegibilidad de lotes; un lote vencido durante la
espera no se consume ni concede PRO. Concesión y auditoría comparten ese instante.

Sin política o evidencia confiable de comisión neta efectiva: `PENDING_POLICY`,
sin crédito ni extensión; no se presume comisión cero ni se infiere comisión
neta de `marketplace_fee`. Suscripción paga no genera comisión transaccional.
Pagos tardíos, temporalidad incierta, reembolsos, reversos y contracargos quedan
`PENDING_REVIEW`, sin compensación ni revocación automática de efectos anteriores.
La temporalidad UNKNOWN de 4E no se convierte automáticamente en pago puntual.

`PAYMENT_EFFECTS_ENABLED=False` y `TRANSACTIONAL_COMMISSION_ENABLED=False`.
Migración `20260917_03`, descendiente de `20260917_02`.
No habilita disponibilidad productiva, cobros reales, contabilidad ni facturación.

### Evidencia final y cierre de hallazgos

- Testing aprobado: focales **66/66** y regresiones **363/363**.
- PostgreSQL **42/42** más **3/3** reproducciones adversariales.
- Suite completa: **694 aprobadas** y **5 omisiones históricas**.
- Ambos P2 corregidos y sin hallazgos pendientes: tiempo efectivo tras locks y
  claves generadas compatibles con el validador vigente. Tokens internos iniciados
  con `_` y `-` generan claves válidas; dos POST secuenciales conservan la misma
  clave estable, sin debilitar validación ni duplicar efectos.
- La historia de ambos hallazgos, sus correcciones y validaciones previas se conserva.

Este cierre acredita únicamente implementación técnica local 4F y su retest.
Supera la pendencia técnica de 4F en los registros anteriores, que se conservan
como historia de su fecha. REQ-001 y REQ-003 permanecen APROBADO/PENDIENTE para
la implementación productiva; el Sprint 2 productivo continúa abierto.

### Gate futuro obligatorio de producción

La activación productiva permanece bloqueada hasta acreditar y aprobar:

- Constitución/CUIT y asesoramiento fiscal.
- Cuenta bancaria empresarial.
- Cuenta empresarial Mercado Pago, aplicación y OAuth completo, incluida
  custodia y renovación de credenciales por profesional.
- Precio mensual, moneda y política comercial explícita y versionada.
- Fórmula/tasa real de comisión, evidencia confiable de comisión neta efectiva
  y tratamiento fiscal; no existen tasas o importes predeterminados aprobados.
- Dominios HTTPS, URLs públicas y secretos con custodia adecuada.
- Pruebas staging/live, monitoreo, soporte y respuesta a incidentes.
- Aprobación legal, privacidad y términos.

También siguen pendientes la integración operativa autorizada, retornos,
tratamiento productivo de pagos tardíos y reversos, resolución de revisiones,
contabilidad y facturación. El cierre local no satisface estos gates ni autoriza
activar flags o emplear credenciales reales.

Los registros previos se conservan íntegramente a continuación.

---

# Registro anterior preservado íntegramente

# Handoff vigente: implementación autorizada 4F

Estado: READY_TO_RESUME
## Decisión vigente 4F: créditos y política económica obligatoria

Timestamp: 2026-09-17T21:41:40-03:00
Estado: APROBADO
Implementación: PENDIENTE
Responsable: Cristian Sánchez; registro: Codex, laptop.
Rama: `feature/payment-effects-pro-commission`; base: `d3998e15418f1029273fa8887e9199d23dc4e3fb`.

- 1 crédito se obtiene al acumular comisión neta efectiva equivalente al precio
  mensual PRO vigente; 1 crédito concede 30 días PRO. El excedente se conserva.
- Consumo FIFO y vencimiento individual de lotes a 40 días; nuevos aportes no
  rejuvenecen saldos anteriores. No se reintroduce la regla histórica de 60 días.
- Precio/umbral y moneda pertenecen a una política versionada, explícita y
  obligatoria. No existe valor predeterminado.
- Sin política o sin evidencia confiable de comisión efectiva: PENDING_POLICY,
  sin crédito ni extensión. Un pago aprobado no prueba por sí solo una comisión.
- Suscripción paga no genera comisión transaccional. Pagos tardíos, temporalidad
  incierta, reembolsos y contracargos quedan PENDING_REVIEW; no hay compensación
  ni revocación automática de efectos previos.
- Flags deshabilitados hasta definir valores comerciales y habilitar producción.
- Esta decisión supera únicamente la fórmula pendiente de registros anteriores;
  los valores comerciales, cambios de precio, reversas y activación real siguen
  pendientes. Se preservan historia, trial/gracia y períodos de 30 días.

## Corrección focal posterior 4F: dos hallazgos P2

Timestamp: 2026-09-18T08:51:52-03:00
Estado: READY_TO_RESUME
Responsable: Codex, laptop.
Rama: `feature/payment-effects-pro-commission`.
HEAD: `d3998e15418f1029273fa8887e9199d23dc4e3fb`.
Origen: hallazgos P2 comunicados por Testing y corrección autorizada por Cristian Sánchez.

### Hallazgos preservados y corrección

1. P2 — tiempo efectivo anterior a locks: el consumo podía seleccionar un lote
   vigente y, tras esperar el lock de orden, consumirlo con un reloj anterior a
   su vencimiento real. Se adquieren locks de política, todos los lotes candidatos,
   órdenes financiadoras, fuentes PRO y elegibilidad antes de volver a obtener
   el reloj. Se excluyen los lotes vencidos usando ese instante posterior a locks;
   se revalidan política, fuente activa, elegibilidad y evidencia antes del consumo.
   Concesión, suscripción, auditoría de consumo y decisión/auditoría de acumulación
   usan el mismo tiempo posterior a locks. Un lote vencido no pierde saldo ni
   genera asignaciones o PRO. No cambian fórmula, FIFO ni períodos aprobados.
2. P2 — incompatibilidad preexistente de claves de formularios: token_urlsafe
   podía comenzar con `_` o `-`, rechazados por el validador contractual vigente.
   El generador común añade `op-` al token completo y verifica el resultado con
   ese mismo validador. Se conserva entropía; no se debilita la validación.
   Negociaciones, contratación, comandos y reviews usan el generador compatible.
   POST conserva la clave recibida; no se regenera durante replay.

### Regresiones y límites de evidencia

Tres regresiones nuevas 4F coordinan worker y reloj mediante Events, sin sleeps:
se pausa el write fence real de orden después de seleccionar lotes, se avanza
el reloj y se libera el worker. Reproducen de forma determinista el orden de
espera PostgreSQL en SQLite descartable; no sustituyen el retest PostgreSQL.
Cubren consumo explícito al vencimiento exacto, consumo válido con timestamps
posteriores y acumulación nueva con un lote previo que vence durante la espera.
Dos regresiones HTTP fuerzan tokens iniciados con `_` y `-`: GET entrega una
clave válida y dos POST secuenciales conservan esa clave, con una sola review,
claim, evento y auditoría. Se impide explícitamente regenerarla durante POST.

Validación final:
- Focales 4F: 44/44; rutas de reviews: 13/13; corrida conjunta 57/57.
- Regresiones relacionadas ampliadas: 368/368 en 31 módulos.
- Compileall y AST de los cuatro Python afectados: aprobados.
- UTF-8, enlaces, conservación del historial y git diff --check: aprobados.
- Focales incluyen migración SQLite y DDL PostgreSQL offline, sin conexión.
- Suite completa y PostgreSQL final no repetidos: corresponden al retest independiente.
- Primer ensayo de fixtures detectó dos errores de preparación: una suscripción
  paga excluía legítimamente la comisión. Se corrigió el fixture a una fuente
  transaccional activa; la corrida final no tiene fallos ni errores.

Archivos afectados por esta corrección:
- app/services/payment_effect_service.py
- app/routes/operation_routes.py
- tests/test_payment_effect_credits.py
- tests/test_sprint7_contract_review_routes_ui_moderation.py
- docs/HANDOFFS/ACTIVE_HANDOFF.md

Se preservan los 13 cambios recuperados; los dos archivos de rutas/pruebas
incorporados por la corrección de claves llevan el total a 15 cambios locales.
Rama y HEAD preservados, staging vacío; sin commit, push, PR, merge ni deploy.
No hubo merge: no autorizado y corresponde retest independiente de ambos P2.
Flags PAYMENT_EFFECTS_ENABLED y TRANSACTIONAL_COMMISSION_ENABLED siguen False;
no hay credenciales, llamadas reales ni activación productiva. Migración 03
sin cambios. Los pendientes comerciales y productivos anteriores se mantienen.
Próximo paso: retest independiente de Testing, incluida reproducción PostgreSQL
sobre base descartable; no utilizar trax_db ni habilitar efectos en producción.
Estado final: CORRECCION_P2_4F_PENDIENTE_DE_RETEST.

## Reanudación y cierre de validación local 4F

Timestamp: 2026-09-18T08:19:36-03:00
Estado: READY_TO_RESUME
Responsable: Codex, laptop.
Rama: `feature/payment-effects-pro-commission`.
HEAD: `d3998e15418f1029273fa8887e9199d23dc4e3fb`.

Se recuperaron íntegramente los 13 cambios existentes: motor de créditos,
modelos, migración, integración de locks, flags, documentación y pruebas.
La implementación funcional ya estaba completa; no se reinició ni sobrescribió.
Se completó la validación de cierre interrumpida: el historial del handoff es
idéntico al de HEAD normalizando únicamente finales LF/CRLF. El fallo anterior
era una comparación binaria entre finales de línea diferentes, sin pérdida
de registros históricos. Esta entrada conserva íntegramente el cierre anterior.

Validaciones repetidas sobre el estado local actual:
- Focales 4F: 41/41, sin fallos ni errores.
- Regresiones relacionadas: 324/324 en 27 módulos, sin fallos ni errores.
- Compileall focal, AST, UTF-8, mojibake, enlaces relativos y whitespace: aprobados.
- Alembic: head único `20260917_03`, descendiente de `20260917_02`.
- Migración SQLite descartable y DDL PostgreSQL offline: aprobados por focales.
- Git diff --check: aprobado.
- Suite completa y PostgreSQL real no ejecutados; reservados para Testing final.

La fórmula aprobada conserva Decimal exacto, remanente FIFO, vencimiento de
lotes a 40 días y concesiones de 30 días por crédito. Política y constancia de
comisión efectiva son obligatorias y confiables, sin valores predeterminados.
Pagos tardíos, temporalidad incierta y reversos quedan a revisión, sin revocación
ni compensación automática. Ambos flags permanecen False. No hay activación
productiva ni llamadas reales. Continúan los pendientes comerciales y fuentes
confiables detallados en el cierre anterior; UNKNOWN de 4E no se transforma.

Único archivo editado durante esta reanudación: este handoff, para registrar
validaciones y continuidad. Los otros doce cambios recuperados se preservaron.
Estado Git: 13 archivos modificados/nuevos, staging vacío y HEAD preservado.
Sin commit, push, PR, merge ni deploy; no hubo merge por falta de autorización
y porque corresponde primero revisión y Testing independiente.
Próximo paso: paquete de Testing final, con suite completa y PostgreSQL
estrictamente descartable; no utilizar trax_db ni habilitar flags productivos.
Estado final: IMPLEMENTACION_4F_PENDIENTE_DE_REVISION.

## Cierre técnico local de implementación 4F

Timestamp: 2026-09-17T22:06:54-03:00
Estado: READY_TO_RESUME
Implementación interna validada; pendiente de revisión y Testing independiente.
HEAD: `d3998e15418f1029273fa8887e9199d23dc4e3fb`.
Origin verificado: `https://github.com/cristhian-star/TRAX-PLATFORM.git`.

### Motor y límites

`PaymentEffectService` se compone explícitamente con `CreditPolicy` obligatoria,
versionada, precio Decimal positivo y moneda ARS coherente con 4E; sin defaults,
FX ni porcentaje de comisión inventado. `EffectiveCommission` es una constancia
confiable inyectada, vinculada a evidencia/hash, orden, profesional, entorno,
identidad de liquidación y fechas separadas de pago y comisión efectiva.
No inferir comisión neta efectiva de marketplace_fee o de pago aprobado.
Los proveedores se invocan fuera de transacción local y el contexto se revalida.
Sin política/proveedor/constancia confiable: PENDING_POLICY sin crédito ni PRO.

Ocho modelos separados: política, decisión por evidencia, comisión comercial,
claim de identidad financiera, lotes, concesiones, asignaciones FIFO y auditoría.
Idempotencia por evidencia, orden y liquidación; la identidad PSP del pago no
puede financiar dos órdenes. Un snapshot distinto no reacredita una comisión.
Acumulación y remanente Decimal exactos: cada lote guarda el numerador monetario
contra un umbral inmutable; no se redondean fracciones de crédito. SQLite usa
texto decimal exacto; PostgreSQL Numeric(64,2). Se conserva excedente y la fecha
individual de acreditación/vencimiento a 40 días, incluso después de pasar a FREE.

Conversión consume FIFO un umbral completo (1 crédito) y concede 30 días PRO
TRANSACTIONAL con asignaciones trazables, una sola vez por período. Períodos
activos, trial/gracia representados por la fuente existente, no se interrumpen.
El excedente queda disponible para el siguiente vencimiento; no se consumen
varios períodos futuros automáticamente. Suscripción paga al instante del pago
no genera comisión transaccional. Una fuente futura financiada que se solaparía
con la concesión bloquea conversión para revisión. Mezcla/redefinición de política
no tiene conversión económica aprobada: queda pendiente de revisión.

Locks de usuario, verificación, órdenes y lotes protegen efectos y consumo.
La cuarentena 4E toma el lock común de orden, conservando Work → Order; no cambia
HTTP, firma, backoff ni duración de lease. Se revalida el lease después de una
espera y se revierte íntegramente una finalización que exceda su permiso.
Concesión, remanente, decisión y auditoría se confirman en una transacción.
Fallo/commit fallido revierte todo; excepciones públicas neutrales, sin secretos,
__context__ ni __cause__. Review durable no se borra mediante replay.

Temporalidad UNKNOWN o pago tardío, cuarentena, evidencia contradictoria,
reembolso parcial/total o contracargo impiden efectos y/o generan revisión.
No se cancelan suscripciones, compensan créditos ni modifican comisión efectiva
histórica automáticamente. Contabilidad/facturación están separadas y ausentes.
`PAYMENT_EFFECTS_ENABLED=False` y `TRANSACTIONAL_COMMISSION_ENABLED=False`.
Sin endpoints, OAuth completo, credenciales o consultas reales, ni producción.

### Migración y validación

Migración/head único `20260917_03`, descendiente de `20260917_02`.
Upgrade–downgrade–upgrade sobre SQLite descartable conserva datos anteriores.
Downgrade de ledger poblado se rechaza: necesita plan separado de preservación
para no dejar derechos PRO sin trazabilidad; no se revocan automáticamente.
DDL PostgreSQL compilado offline solamente, sin conexión ni gate PostgreSQL real.

- Focales finales 4F: **41/41** en dos módulos.
- Regresiones relacionadas: **324/324** en 27 módulos PRO, 4A–4E, PSP,
  persistencia, migraciones, seguridad y configuración.
- Después de integrar el lock común y fencing, revalidación final conjunta:
  **138/138** (41 focales 4F + 97 relacionadas 4E/head).
- Compileall focal, AST/UTF-8, enlaces, Alembic heads y git diff --check: aprobados.
- Suite completa y PostgreSQL real no ejecutados: reservados para Testing final.
- No se usaron bases persistentes ni trax_db; transportes y precios ficticios.

### Documentación, Git y continuidad

Decisión registrada primero en REQ-001, decisiones arquitectónicas y este handoff.
Reglas vigentes 9/12 y pendientes económicos realineados; textos sustituidos
conservados explícitamente como historia. No se reintroducen los 60 días.
REQ-001 sigue APROBADO/IMPLEMENTACION_PARCIAL; implementación productiva pendiente.
Registros 4E y anteriores permanecen íntegros.

Archivos modificados/nuevos:
- app/models/payment_effect.py
- app/services/payment_effect_service.py
- migrations/versions/20260917_03_payment_effect_credits.py
- tests/test_payment_effect_credits.py
- tests/test_payment_effect_migration.py
- app/__init__.py
- app/config/config.py
- app/services/payment_order_reconciliation_service.py
- docs/DECISIONES_ARQUITECTURA.md
- docs/HANDOFFS/ACTIVE_HANDOFF.md
- docs/REQUISITOS/REQ-001-activacion-y-vigencia-pro.md
- tests/test_payment_order_application_migration.py
- tests/test_payment_order_reconciliation_migration.py

Rama y HEAD preservados; 13 cambios sin staging ni commit. Sin push/PR/merge/deploy.
No hubo merge: no autorizado y falta revisión y Testing independiente.
Pendientes: revisión, suite completa/gate PostgreSQL descartable independiente,
valores comerciales aprobados de política, fuente de comisión neta efectiva y
certificación confiable de temporalidad. 4E actual conserva UNKNOWN normalmente;
el motor no lo transforma en pago puntual. También quedan separados OAuth real,
trial/onboarding, aplicación operativa del consumo al vencimiento, consentimiento,
resolución manual de revisiones, reversas comerciales, contabilidad y facturación.
Flags deben seguir False hasta decisiones comerciales y activación autorizada.

Para retomar, verificar esta rama/HEAD y los 13 cambios; no usar trax_db ni
credenciales reales. Focales:
`.venv/Scripts/python.exe -B -m unittest tests.test_payment_effect_credits tests.test_payment_effect_migration`.
Siguiente paso: revisión y paquete de Testing final con PostgreSQL descartable;
no integrar ni habilitar cobros productivos a partir de esta validación local.
Estado final: IMPLEMENTACION_4F_PENDIENTE_DE_REVISION.

---

# Registro anterior preservado íntegramente

# Handoff vigente: cierre técnico local 4E aprobado

Estado: COMPLETED
Timestamp de registro documental: 2026-09-17T21:24:48-03:00
Estado técnico local: APROBADO
Implementación productiva: PENDIENTE
Rama: `feature/mercadopago-payment-reconciliation`.
Commit técnico: `8dc0e12`.
Registro documental: Codex; dispositivo: laptop.
Evidencia final de Testing suministrada para este cierre.

4E implementa recepción y conciliación verificada de evidencia durable de
Orders, sin efectos PRO, contables o comerciales. POST
`/api/webhooks/mercadopago` acepta únicamente el tópico `order`; HMAC-SHA256
con comparación constante conserva `data.id` case-sensitive. Inbox y trabajo
durables, deduplicación, cuarentena e intentos son independientes de los
estados informados por el webhook. La confirmación HTTP 200 ocurre únicamente
después del commit durable; firma inválida responde 401 sin persistencia.

La validación criptográfica está separada de la temporal: firma válida con
timestamp en milisegundos fuera de la ventana inclusiva ±10 minutos queda en
cuarentena durable `TIMESTAMP_OUTSIDE_WINDOW`, sin trabajo ejecutable ni consulta
PSP. Colisiones preservan la primera recepción y quedan en cuarentena.
`LEASE_DURATION_SECONDS = 60` y `STALE_LEASE_RECOVERY_SECONDS = 120` separan
vencimiento del permiso de despacho/finalización y recuperación del trabajo
abandonado. Entre 60 y 119 segundos no hay consulta; desde 120 segundos puede
recuperarse con otro token. Fencing impide finalizar con lease vencido;
ocho intentos programados como máximo, sin retries del transporte HTTP.

Consulta `GET /v1/orders/{id}` fuera de una transacción local abierta, con
credencial OAuth por profesional suministrada por un proveedor confiable
inyectado, vinculada a profesional, cuenta PSP y entorno; sin fallback global.
El onboarding, la custodia y la renovación OAuth permanecen pendientes.
Se correlacionan orden externa, PaymentOrder, obligación, contrato y reserva;
solo una respuesta autoritativa validada permite registrar evidencia normalizada
de pagos, reembolsos y reversos, incluidos contracargos y pagos tardíos.
El vencimiento contractual local sigue siendo la autoridad de entrega del
checkout; registrar un pago tardío no habilita automáticamente efecto alguno.

Suma Decimal exacta de reembolsos por pago asociado y por orden, deduplicada por
identidad externa. El snapshot remoto y la evidencia acumulada durable deben
respetar ambos límites. La validación acumulada se serializa bajo lock de
PaymentOrder y fence SQLite: contradicciones quedan en cuarentena sin insertar
nueva evidencia financiera válida; se conserva la evidencia histórica válida.

Migración `20260917_02`, descendiente de `20260917_01`, incorpora trabajo,
intentos, evidencia y cuarentena durables. Feature flags
`MERCADOPAGO_ORDER_WEBHOOK_ENABLED=False` y
`MERCADOPAGO_ORDER_RECONCILIATION_ENABLED=False` permanecen deshabilitados por
defecto. No se declaran credenciales reales, cobros productivos ni conciliación
financiera con efectos habilitados.

Evidencia final acreditada de Testing:

- Focales 4E: **96/96**.
- Regresiones relacionadas: **197/197**.
- PostgreSQL: **37/37**.
- Suite completa: **653 ejecutadas, 648 aprobadas y 5 omisiones históricas**.
- Migraciones SQLite/PostgreSQL, `compileall`, Alembic y `git diff --check`:
  aprobados; head `20260917_02`.
- Sin hallazgos P0–P3 pendientes.

Los hallazgos P1/P2 y su corrección de `2026-09-17T21:04:23-03:00`, junto con
la implementación de `2026-09-17T20:42:27-03:00`, se conservan en el
[historial del handoff](#registro-anterior-preservado-íntegramente). Los resultados de aquella corrección
(207/207 regresiones) son históricos; este cierre acredita los **197/197**
del paquete final suministrado, sin reemplazar la evidencia anterior.

Se cierra únicamente 4E técnico local y su retest: supera esos pendientes en
registros anteriores, conservados íntegramente. REQ-003 continúa
`estado: APROBADO` e `implementacion: PENDIENTE`; no se cierra Sprint 2 productivo.
Pendientes reales: OAuth completo y custodia/renovación, fórmula de comisión,
retornos, credenciales y prueba real, validación/activación productiva de la
recepción y consulta PSP. Los efectos PRO, comerciales y contables de evidencia
conciliada, pagos tardíos y reversos corresponden a 4F; producción permanece
pendiente. La recepción y evidencia local de webhook/Orders ya están
implementadas en 4E; no confundirlas con su activación productiva.

Próximo paso: diseñar y autorizar 4F por separado; no habilitar efectos o flags
productivos basándose únicamente en este cierre técnico local.
Commit técnico acreditado: `8dc0e12`; la implementación terminó en su rama.

---

# Registro anterior preservado íntegramente

# Handoff vigente: corrección focal 4E P1/P2

Timestamp: 2026-09-17T21:04:23-03:00
Estado: READY_TO_RESUME
Agente: Codex; dispositivo: laptop.
Rama: `feature/mercadopago-payment-reconciliation`.
HEAD preservado: `8b975b2472a594a8ca07f7e9cc1ef01f31376446`.
Origin: `https://github.com/cristhian-star/TRAX-PLATFORM.git`.
Objetivo: corregir exclusivamente los tres hallazgos P1/P2 de Testing comunicados
por el usuario; el registro de implementación anterior se conserva íntegro abajo.

## Hallazgos y corrección posterior

1. El rechazo temporal anterior impedía la cuarentena durable. Ahora HMAC y
ventana temporal se validan por separado. Firma inválida: 401 sin persistencia.
Firma válida fuera de ±10 minutos inclusivos: inbox y cuarentena durable
`TIMESTAMP_OUTSIDE_WINDOW`, trabajo QUARANTINED sin intentos ejecutables ni PSP.
200 exclusivamente después del commit. Rollback devuelve 500 genérico.
Se preservan data.id case-sensitive, deduplicación y colisiones.

2. El lease anterior confundía duración y recuperación. Constantes explícitas:
`LEASE_DURATION_SECONDS = 60`; `STALE_LEASE_RECOVERY_SECONDS = 120`.
El propietario pierde permiso de despacho y finalización al vencer 60 segundos;
la recuperación comienza a los 120 segundos desde el claim. Entre ambos límites
no se consulta. El trabajo conserva el estado PROCESSING no ejecutable durante
la espera; luego otro token recupera el trabajo o termina EXHAUSTED al octavo
intento. Se revalida el reloj después de adquirir locks antes de finalizar.
Regresiones de 59, 61, 119 y 120 segundos y respuesta recibida con lease vencido.

3. Faltaba el límite de reembolso por pago. Se suma Decimal exacto por identidad
externa deduplicada y por pago asociado; nunca puede superar el importe de ese
pago ni el límite global de la orden. Identidades contradictorias se rechazan.
El snapshot remoto valida el invariante; la finalización vuelve a validar todos
los snapshots durables y el candidato bajo lock de PaymentOrder y fence SQLite.
Una contradicción remota queda INVALID_RESPONSE; una contradicción acumulada
queda REFUND_CONTRADICTION. No se inserta evidencia del evento contradictorio;
la evidencia válida histórica permanece intacta. Pruebas concurrentes y rollback
acreditan atomicidad local, sin mensajes o excepciones públicas con secretos.

## Validación ejecutada y alcance

Focales 4E: 96/96 aprobadas en cinco módulos.
Regresiones relacionadas: 207/207 aprobadas en veinte módulos.
La primera corrida focal encontró un error de montaje en la nueva prueba de
concurrencia; se corrigió el fixture y la corrida final pasó sin errores.
Compileall, AST/UTF-8 y git diff --check: verificación de cierre de esta sesión.
No se ejecutaron suite completa ni PostgreSQL: corresponden a retest independiente.
Pruebas con transporte y credenciales ficticios, sin llamadas reales ni trax_db.
Ambos flags permanecen False; sin efectos PRO, comerciales, contables o producción.
No se altera migración, backoff, máximo de ocho intentos o alcance funcional.

Archivos afectados por esta corrección:
- app/services/mercadopago_webhook_signature.py
- app/services/mercadopago_webhook_notification.py
- app/routes/mercadopago_webhook_routes.py
- app/services/payment_order_reconciliation_service.py
- app/services/mercadopago_order_query_adapter.py
- tests/test_mercadopago_webhook_routes.py
- tests/test_mercadopago_order_reconciliation.py
- docs/HANDOFFS/ACTIVE_HANDOFF.md

Git: se preservan los 19 cambios existentes, rama y HEAD; staging vacío.
Sin commit, push, PR, merge o deploy por alcance autorizado. No hubo merge.
Pendiente: retest independiente de los hallazgos P1/P2 y gates finales.
Retomar en esta rama/base sin alterar cambios; ejecutar gates solo con autorización.
Estado final: CORRECCION_4E_PENDIENTE_DE_RETEST.

---

# Registro anterior preservado íntegramente

# Handoff vigente: implementación técnica local 4E

Timestamp: 2026-09-17T20:42:27-03:00
Estado: READY_TO_RESUME
Agente: Codex; dispositivo: laptop.
Objetivo: recepción durable y evidencia verificada de Orders, sin efectos comerciales.
Rama: `feature/mercadopago-payment-reconciliation`.
Base/último commit: `8b975b2472a594a8ca07f7e9cc1ef01f31376446`.
Origin verificado: `https://github.com/cristhian-star/TRAX-PLATFORM.git`.
Precheck: rama/base correctas; árbol y staging inicialmente limpios.
Estado final: implementación focal validada, pendiente de revisión y Testing independiente.
Git: 19 archivos nuevos/modificados sin staging ni commit; HEAD preservado.
Sin push, PR, merge o deploy: no autorizados y falta el gate independiente de Testing.
El merge PR #19 de 4D permanece acreditado por el commit base; no hubo merge de 4E.

## Implementación y decisiones aplicadas

POST `/api/webhooks/mercadopago`, exento de CSRF y sin autenticación por sesión:
requiere flag explícito y secreto de firma. Solo tópico exacto `order`, versión `v1`
e identificador Orders seguro. HMAC-SHA256 con comparación constante, `data.id`
case-sensitive, timestamp en milisegundos y ventana inclusiva ±10 minutos.
Request ID único/acotado; headers ambiguos, JSON duplicado, UTF-8 inválido,
constantes no estándar y recursos incoherentes se rechazan. Lectura limitada a
64 KiB, incluso sin Content-Length. No confiar en action/estado del webhook.
La confirmación 200 se entrega exclusivamente después de commit de inbox/trabajo
o cuarentena. Duplicados no recrean trabajo ni resetean intentos. Colisiones
conservan el primer evento, deduplican la cuarentena e invalidan trabajo/lease;
no se responde 409 a una colisión que ya quedó durablemente registrada.
Errores públicos genéricos: 400 entrada, 401 firma/ventana, 413 tamaño,
503 deshabilitado/secreto ausente y 500 fallo de persistencia con rollback.

Inbox existente reutilizado; UPSERT SQLite dirigido únicamente a la identidad
esperada conserva rollback exterior y valores neutrales UTC conscientes.
PostgreSQL conserva recuperación de la constraint de identidad esperada mediante
savepoint. La creación de trabajo/cuarentena/evidencia usa UPSERT con targets
explícitos, sin ocultar violaciones ajenas. Nuevos modelos separados de trabajo,
intentos, evidencia y cuarentena; no reutilizar PaymentAttempt para Orders.

Procesador interno de composición explícita con proveedor confiable inyectado.
Claim y registro de despacho se confirman antes de resolver OAuth/consultar.
Lease de 120 segundos, token único y fencing en despacho/finalización; despacho
atómico único por intento. Crashes quedan durables; leases vencidos permiten
recuperación con otro intento y contabilizan el anterior como LEASE_LOST.
Un crash en el octavo intento termina EXHAUSTED al vencer el lease.
`process_due(limit=100)` ejecuta un pase acotado sin bucle de retry; su invocador
programa pases posteriores, sin scheduler externo ni proceso automático nuevo.
Máximo ocho intentos por trabajo. Para fallos recuperables, demoras entre intentos:
15 min, 15 min, 5 h 30 min, 42 h, 48 h, 96 h, 96 h, desde la finalización anterior.
Cada intento hace como máximo una consulta, con cero retries del transporte.
Recursos aún no correlacionables o credenciales indisponibles quedan programados;
respuestas inválidas y cambios del contexto local quedan en cuarentena.

GET `https://api.mercadopago.com/v1/orders/{id}` con Bearer del profesional
vinculado por `ProfessionalOrderQueryCredential`: profesional, cuenta PSP,
entorno y ARS. Sin token global ni fallback. El receptor de la respuesta debe
coincidir con account_id confiable; identidad/referencia, importe Decimal exacto,
moneda, tipo/modo y contexto PaymentOrder → obligación → contrato/reserva también
se verifican. La respuesta Orders no exige un live_mode inexistente: el entorno
proviene del contexto y credencial confiables; si la respuesta lo incluye, se
valida estrictamente. Se conservan TLS verificado, no redirects, límite de 1 MiB,
JSON estricto y timeout de 10 s, configurable hasta 30 s. La sesión ORM se cierra
por completo antes de resolver la credencial y consultar. Nueva transacción
local corta revalida el contexto y el lease antes de guardar evidencia.

Evidencia deduplicada por orden/hash de snapshot normalizado, inmutable en el
flujo: IDs/estados de pagos, reembolsos parciales/totales y contracargos vinculados,
importes y fechas remotas. Payer, tokens, medios de pago y metadata no se guardan.
Observaciones antiguas se conservan como hechos y no sobreescriben aprobaciones
ni reversos: no hay proyección financiera mutable ni terminalidad que omita
consultas posteriores. Estados/detalles desconocidos se ponen en cuarentena.
El estado de vigencia de PaymentOrder, reserva, obligación, contrato y PRO no
se modifica por reconciliación. No aplicar comisión contable, facturación ni
ningún efecto de 4F.

Vencimiento local de 72 h continúa como autoridad contractual. Evidencia de
órdenes vencidas se admite sin entregar/reabrir checkout ni suponer pago a tiempo.
observed_at, remote_updated_at y vencimiento se conservan por separado. Si la
creación remota misma es posterior al vencimiento local, timing registra
AFTER_LOCAL_EXPIRY; en los demás casos registra UNKNOWN: last_updated_date no
se interpreta como fecha de aprobación/pago. Esto permite representar evidencia
posterior e incertidumbre temporal sin inventar la fecha efectiva de pago.
Los efectos y clasificación funcional final de pagos tardíos pertenecen a 4F.

Excepciones de OAuth, validación, transporte, JSON/parser y persistencia pública
se neutralizan capturando solamente sentinels/clasificaciones. La excepción
pública se lanza fuera del except, sin __context__, __cause__, argumentos
originales, tokens en repr ni logs de contenido sensible.

Flags `MERCADOPAGO_ORDER_WEBHOOK_ENABLED=False` y
`MERCADOPAGO_ORDER_RECONCILIATION_ENABLED=False` por defecto. 4C/4D conservan
sus flags deshabilitados. Habilitar flags no suministra OAuth ni compone un
procesador; requiere `build_order_reconciliation_processor(...)` explícito.
Sin credenciales reales, llamadas reales o disponibilidad productiva.

## Archivos y validación ejecutada

- Modelos: `app/models/payment_order_reconciliation.py`.
- Adaptador/procesador: `app/services/mercadopago_order_query_adapter.py`,
  `app/services/payment_order_reconciliation_service.py`.
- Cableado/configuración: `app/__init__.py`, `app/config/config.py`.
- Recepción: `app/routes/mercadopago_webhook_routes.py`,
  `app/services/mercadopago_webhook_signature.py`,
  `app/services/mercadopago_webhook_notification.py`, `app/services/psp_event_inbox.py`.
- Migración: `migrations/versions/20260917_02_payment_order_reconciliation.py`,
  descendiente de `20260917_01`, head único comprobado por test de migración.
- Focales nuevas: `tests/test_mercadopago_order_reconciliation.py`,
  `tests/test_payment_order_reconciliation_migration.py`.
- Focales actualizadas: `tests/test_mercadopago_webhook_signature.py`,
  `tests/test_mercadopago_webhook_notification.py`,
  `tests/test_mercadopago_webhook_routes.py`.
- Regresión del head: `tests/test_payment_order_application_migration.py`.
- Gates PostgreSQL preparados, no ejecutados:
  `tests/postgresql_payment_order_reconciliation_e2e.py`,
  `tests/postgresql_mercadopago_webhook_ingress_e2e.py`.
- Única documentación actualizada: este handoff; registros anteriores preservados.

Focales finales: **86/86**, en cinco módulos Orders/reconciliación, firma,
notificación, rutas y migración. Último endurecimiento del tópico exacto:
**19/19** rutas; protección pública de dispatch **2/2**. Regresiones relacionadas finales: **207/207**, en veinte módulos
4A–4D, inbox/conciliación anterior, consulta legacy, persistencia/orquestación,
migraciones relacionadas, seguridad y configuración. SQLite exclusivamente
descartable; pruebas de upgrade/downgrade/upgrade y preservación histórica.
compileall focal, UTF-8 y git diff --check aprobados; revisión de código/diff.
Advertencias históricas datetime.utcnow/Query.get, sin fallos finales.
Primeros focales detectaron fixtures de ventana antigua y aserciones globales
sobre sesiones de otros workers; corregidos manteniendo la comprobación de que
el caller HTTP no tiene sesión abierta. Primera regresión detectó pérdida de
tzinfo al recuperar UPSERT SQLite; corregida y revalidada sin modificar primera
recepción ni romper rollback.

## Pendientes, riesgos y continuidad

Testing independiente: suite completa y PostgreSQL final, incluidos concurrencia,
commit HTTP, rollback, leases y fencing bajo PostgreSQL real descartable.
No se ejecutaron Docker, PostgreSQL, suite completa, migraciones en bases
persistentes, credenciales reales ni consultas PSP reales. `trax_db` intacta.
El gate nuevo solo admite `trax_order_reconciliation_test` con sufijo seguro y
`TRAX_POSTGRES_TEST_ALLOW_RESET=1`; rechaza trax_db antes de conectar.
OAuth real/onboarding/custodia/renovación, fórmula comercial, credenciales/prueba
real y activación siguen pendientes. Programación operativa del invocador de
process_due y tratamiento comercial/contable de tardíos/reversos no se habilitan.
Sin efectos PRO/contables ni producción; REQ-003 continúa APROBADO/PENDIENTE.

Para retomar, verificar rama/base y estos 19 cambios, sin staging. Focales:
`.venv/Scripts/python.exe -B -m unittest tests.test_mercadopago_order_reconciliation tests.test_mercadopago_webhook_signature tests.test_mercadopago_webhook_notification tests.test_mercadopago_webhook_routes tests.test_payment_order_reconciliation_migration`.
PostgreSQL se reserva a Testing con autorización/base descartable explícita;
no usar trax_db, credenciales reales ni activar flags productivos. No integrar
hasta revisión y gate independiente. No hubo commit/push/merge de este incremento.

Fuentes oficiales consultadas:
- [GET Orders](https://www.mercadopago.com.ar/developers/es/reference/online-payments/checkout-pro/get-order/get).
- [Estados Orders](https://www.mercadopago.com.ar/developers/es/docs/checkout-pro-orders/payment-management/status/order-status?scope=prod).
- [Contracargos Orders](https://www.mercadopago.com.ar/developers/es/docs/checkout-pro-orders/chargebacks/notifications?scope=prod).
- [Firma case-sensitive, corrección oficial](https://github.com/mercadopago/sdk-python/pull/118).

---

# Registro anterior preservado íntegramente

# Handoff vigente: cierre técnico local 4D

Timestamp: 2026-09-17T16:14:10-03:00
Estado: COMPLETED
Objetivo: cierre técnico 4D aprobado por Testing, sin activación productiva.

## Cierre técnico local 4D aprobado por Testing

Timestamp de aprobación de Testing: 2026-09-17T16:14:10-03:00
Estado: APROBADO
Implementación productiva: PENDIENTE
Rama: `feature/checkout-pro-payment-order-delivery`.
Commit técnico: `763eee3`.
Agente verificador: `03 - Testing - Test Executor`.
Registro documental: Codex; dispositivo: laptop.
Implementación técnica: `2026-09-17T16:06:04-03:00`.

Alcance acreditado: POST `/contratacion/<int:id>/orden-de-cobro` de creación/replay
con sesión, actor desde `session["user_id"]`, CSRF y ownership contractual/perfil
del profesional activo; solo contratos CONFIRMADA. Importe y clave durable
proceden de 4B, sin overrides del navegador. Éxito/replay responde 303.
GET de esa ruta y GET `/contratacion/<int:id>/orden-de-cobro/qr.png` requieren
autorización y solo leen: no crean órdenes ni llaman al PSP ni resuelven OAuth/comisión.

Checkout y QR PNG están limitados al profesional propietario, reserva exitosa,
orden activa/coherente y vencimiento contractual vigente. `segno==1.6.6` genera
localmente el PNG en memoria, desde exactamente la misma checkout_url HTTPS
validada del enlace. Endpoint QR separado y autenticado; sin servicios externos,
JavaScript remoto, SVG safe, data URI ni archivos persistentes. Componentes
Design System V2, enlace alternativo, texto accesible y formato Decimal exacto.
Abrir el enlace o escanear el QR no acredita pago.

Órdenes vencidas, canceladas, bloqueadas, inciertas o no disponibles no entregan
checkout ni QR. Vencimiento revalidado al finalizar render/generación; autoridad
contractual local, sin afirmar igualdad con vencimiento remoto. Clave durable,
replay, cero retries y bloqueo 4B preservados; sin renovación ni recuperación
automáticas. Headers privados `Cache-Control: no-store, private`,
`Referrer-Policy: no-referrer` y nosniff cubren errores y redirects.
Errores públicos genéricos sin datos sensibles. Feature flags
`CHECKOUT_PRO_DELIVERY_ENABLED=False` y `MercadoPagoOrderConfiguration.enabled=False`
por defecto, composición explícita con proveedores confiables inyectados.

Evidencia final acreditada de `03 - Testing - Test Executor`:

- Focales 4D: **26/26**; focales 4B–4C: **52/52**.
- Regresiones relacionadas: **119/119**.
- PostgreSQL: **6/6**, más **3/3 reproducciones HTTP**.
- Suite: **594 ejecutadas, 589 aprobadas, 5 omisiones históricas y 0 fallos**.
- `compileall`, Alembic head `20260917_01`, UTF-8, enlaces, whitespace y
  `git diff --check`: aprobados. Sin migración nueva en 4D.

Se cierra únicamente el incremento técnico 4D: deshabilitado por defecto,
sin habilitar cobros productivos. REQ-003 conserva `estado: APROBADO` e
`implementacion: PENDIENTE`. Continúan pendientes OAuth real y custodia/renovación,
fórmula de comisión, retornos, webhooks, conciliación, tratamiento de pagos
tardíos, efectos PRO/contables, credenciales reales y validación/activación en
entornos de staging y producción. El cierre supera endpoint/presentación 4D y
Testing final pendientes en registros anteriores, preservados íntegramente.

---

# Registros históricos preservados

# Handoff vigente: implementación técnica local 4D

Timestamp: 2026-09-17T16:06:04-03:00
Estado: READY_TO_RESUME
Agente: Codex; dispositivo: laptop.
Rama: `feature/checkout-pro-payment-order-delivery`.
Base/último commit: `db9644764fe58572f28bbc431a2956b8bbaa862d`.
Origin verificado: `https://github.com/cristhian-star/TRAX-PLATFORM.git`.
La base confirma el merge del PR #18 del adaptador 4C; su commit técnico
`b859e6a` y evidencia de Testing permanecen en el registro histórico siguiente.
Objetivo: frontera HTTP por sesión y presentación privada de checkout/QR,
limitadas al profesional propietario, reutilizando 4A–4C.
Resultado: implementación focal validada, pendiente de revisión y Testing final.
REQ-003 sigue APROBADO con implementación productiva PENDIENTE.

## Implementación y decisiones

POST `/contratacion/<int:id>/orden-de-cobro`: actor exclusivamente desde
`session["user_id"]`, usuario activo/rol PROFESIONAL y CSRF global. Importe,
identidad profesional y clave PSP no se obtienen del formulario. Autoriza
ownership contractual/perfil y estado CONFIRMADA; delega claim/creación/replay
al servicio 4B. Libera la sesión ORM del request antes de la llamada externa.
Éxito/replay responde 303 a presentación GET, sin URL PSP en el redirect.

GET de esa ruta y GET `/contratacion/<int:id>/orden-de-cobro/qr.png`:
solo lectura autorizada; sin PSP ni resolución OAuth/comisión. Exigen reserva
SUCCEEDED, orden ACTIVE, coherencia con obligación/comando y vencimiento
contractual vigente. Revalidan URL HTTPS segura/host exacto
`www.mercadopago.com.ar`. La presentación comprueba vencimiento después de
renderizar; el QR lo comprueba después de generar. Rechazan vencidas/canceladas,
bloqueadas e inciertas; no generan sucesoras ni recuperaciones.

La misma checkout_url validada se muestra como enlace autoescapado y se pasa
exactamente al encoder QR. `segno==1.6.6` fijado en requirements.txt, PNG local
sobre BytesIO, negro/blanco, borde de cuatro módulos. Endpoint separado,
autenticado; sin servicios externos, JS remoto nuevo, SVG safe, data URI ni
archivos persistentes. Componentes Design System V2, enlace alternativo,
texto accesible y advertencia de que apertura/escaneo no acredita pago.
Importe mostrado mediante formato Decimal exacto, sin conversión a float.

`CHECKOUT_PRO_DELIVERY_ENABLED=False` por defecto; 4C conserva
`MercadoPagoOrderConfiguration.enabled=False`. Habilitar el flag por sí solo
no configura un receptor ni permite llamar al PSP: falta composición explícita.
`build_checkout_delivery_service(...)` admite únicamente proveedores confiables
inyectados; se registra explícitamente en
`app.extensions["payment_order_delivery_service"]`. Sin defaults OAuth/comisión
ni fallback global. Tests usan configuración explícita y transporte falso.

Errores públicos fijos: 400 entrada/CSRF, 403 autorización, 409 conflicto o
bloqueo/ incertidumbre, 410 no vigente, 503 no disponible y 500 inesperado;
anónimos/inactivos siguen el redirect al login existente. No se renderizan ni
registran argumentos/excepciones sensibles. Todos los endpoints de delivery,
incluidos redirects y errores CSRF, reciben `Cache-Control: no-store, private`,
`Referrer-Policy: no-referrer` y nosniff. Sin ETag/304 de QR; cada GET revalida.
Se conservan cero retries, la clave y el bloqueo durable de 4B.

## Archivos y validación

Cambios técnicos: `app/__init__.py`, `app/config/config.py`,
`app/routes/payment_order_delivery_routes.py`,
`app/services/payment_order_delivery_service.py`,
`app/templates/contract_detail.html`, `app/templates/payment_order_checkout.html`,
`requirements.txt`, `tests/test_payment_order_delivery.py`; este handoff actualizado.
Sin migración, modelos modificados ni ampliación de 4B/4C.

Focales 4D: 26/26 aprobadas; focales relacionadas 4B/4C: 52/52 aprobadas.
La ejecución conjunta inicial finalizada tuvo 77/77 (25 4D + 52 relacionadas);
la posterior focal 4D de 26/26 incluye la nueva regresión de escape HTML/URL.
Regresiones relacionadas: 180/180, en quince módulos PSP/pagos, seguridad,
configuración, contratación y reviews. SQLite desechable; ningún cobro real.
compileall focal y git diff --check aprobados; UTF-8/whitespace revisados.
Advertencias legacy SQLAlchemy/datetime existentes; no fallos de validación.
Un fallo inicial de fixtures CSRF al cambiar sesión se resolvió limpiando el
cache de Flask-WTF del app context sostenido por el test; CSRF productivo intacto.
Suite completa y PostgreSQL reservados a Testing final, no ejecutados.
Docker, migraciones, credenciales reales y llamadas PSP reales no ejecutados.

Pendientes reales: revisión independiente/Testing final; OAuth completo y
custodia/renovación; fórmula de comisión; retornos, webhook/conciliación;
tratamiento productivo de pagos tardíos; credenciales/prueba real y producción.
No se implementan efectos PRO, contabilidad, facturación ni activación productiva.
El vencimiento local rige la entrega; no coincide necesariamente con el remoto
ni puede revocar una URL ya copiada. Pagos tardíos requieren tratamiento futuro.

Estado Git: nueve archivos con cambios locales, sin commit, staging vacío.
Push/PR/merge/deploy no realizados: no autorizados en esta implementación.
No hubo merge durante este incremento; el PR #18 pertenece a la base anterior.
Próximo paso: revisión del diff y Testing final sobre esta rama/base; conservar
claims/claves y flags deshabilitados. No activar producción ni ejecutar llamadas
reales. Para retomar, leer este handoff y los módulos/pruebas de delivery y 4B/4C.

---

# Registros anteriores preservados

# Handoff vigente: cierre técnico local 4C

Timestamp: 2026-09-17T15:07:04-03:00
Estado: COMPLETED
Objetivo: cierre documental del incremento técnico interno aprobado por Testing.

## Cierre técnico local 4C aprobado por Testing

Timestamp de aprobación final: 2026-09-17T15:07:04-03:00
Estado: APROBADO
Implementación productiva: PENDIENTE
Rama: `feature/mercadopago-payment-order-create-adapter`.
Commit técnico: `b859e6a`.
Agente verificador: `03 - Testing - Test Executor`.
Registro documental: Codex; dispositivo: laptop.

Trazabilidad preservada:

- Implementación: `2026-09-17T12:58:58-03:00`.
- Hallazgo P2 de Testing: `2026-09-17T14:57:30-03:00`.
- Corrección P2: `2026-09-17T15:02:03-03:00`.
- Aprobación final: `2026-09-17T15:07:04-03:00`.

Alcance acreditado por Testing: adaptador Orders API interno, deshabilitado
por defecto. Credencial OAuth por profesional suministrada por un proveedor confiable inyectado. El onboarding, la custodia y la renovación OAuth permanecen pendientes.
Configuración válida y comisión
obtenida de política confiable antes del claim, enviada como `marketplace_fee`.
Sin defaults de comisión ni
fallback a token global de MANDOBRA. POST `/v1/orders`, importe ARS decimal
exacto, `X-Idempotency-Key` durable sin truncar/regenerar y `expiration_time=PT72H`.
Respuesta 201 validada: persistencia de `id` y `checkout_url` HTTPS con host
permitido `www.mercadopago.com.ar`. Cero retries y bloqueo durable tras error
o incertidumbre; ninguna llamada adicional automática.

Doble vencimiento: `expires_at = created_at + 72 horas` conserva la autoridad
contractual local; `PT72H` cuenta desde la creación remota. No se afirma que
coincidan. Se rechaza entregar o reutilizar el checkout local vencido.
Los pagos tardíos requieren conciliación/revisión y no generan automáticamente
efectos PRO, contractuales, contables ni de comisión local.

P2 corregido y revalidado: la excepción sensible retenida en `__context__`
se elimina lanzando el error neutral después de salir del `except`, sin
conservar la excepción original ni copiar sus argumentos. Secretos neutralizados,
incluidos `__context__` y `__cause__`; sin hallazgos P0–P3 pendientes.

Evidencia final acreditada de `03 - Testing - Test Executor`:

- Focales: **52/52**.
- Regresiones: **119/119**.
- PostgreSQL: **12/12**.
- Suite: **568 ejecutadas, 563 aprobadas, 5 omisiones históricas,
  0 fallos y 0 errores**.
- `compileall`, Alembic head único `20260917_01`, whitespace y
  `git diff --check`: aprobados. 4C no agrega migraciones.

REQ-003 conserva `APROBADO` con implementación productiva `PENDIENTE`.
Se cierra únicamente el incremento técnico interno; no se declaran producción
ni cobros disponibles. Pendientes: OAuth completo y custodia/renovación;
fórmula de comisión; endpoint/UI 4D; retornos, webhook y conciliación;
tratamiento productivo de pagos tardíos; credenciales y prueba real;
activación en producción. La recuperación de incertidumbre sigue
separada y deberá reutilizar la misma clave durable.

Este cierre supera los pendientes históricos de implementación del adaptador
y retest P2, preservando registros, timestamps y evidencia de etapas anteriores.


---

# Registros históricos preservados

# Handoff vigente: corrección focal P2 de Testing 4C

Timestamp: 2026-09-17T15:02:03-03:00
Estado: READY_TO_RESUME
Agente: Codex; dispositivo: laptop.
Rama: `feature/mercadopago-payment-order-create-adapter`.
Base: `fc5eb0c77f1101ada270a2a30d29a8acc795b9dd`.

Hallazgo P2 preservado: las excepciones neutrales lanzadas dentro de
`except`, aun con `from None`, conservaban la excepción sensible en
`__context__`. La supresión visual del traceback no eliminaba esa referencia.
El registro original de implementación y sus resultados se conserva debajo;
su afirmación de ausencia de fallos corresponde a esa validación anterior.

Corrección posterior en
[adaptador](../../app/services/mercadopago_order_creation_adapter.py): los fallos
de OAuth, comisión, validación del token, transporte y respuesta/URL capturan
únicamente una bandera no sensible. La excepción pública genérica se lanza
después de salir completamente del `except`, sin guardar la excepción original
ni copiar sus argumentos. Tipos/mensajes públicos y bloqueo durable 4B se
mantienen; idempotencia, cero retries y doble vencimiento permanecen intactos.

Se agregaron seis regresiones en
[pruebas del adaptador](../../tests/test_mercadopago_order_creation_adapter.py),
con marcadores sensibles por ruta: `__context__ is None`, `__cause__ is None`,
ausencia del marcador en `repr`, argumentos, mensaje y traceback públicos,
tipo/mensaje exactos y conteo de llamadas sin llamadas adicionales.

Validación posterior: 52/52 focales 4C/4B (25 adaptador/transporte,
11 integración y 16 servicio) y 148/148 regresiones relacionadas aprobadas.
`compileall -q app tests` y `git diff --check`: aprobados.
Suite completa y PostgreSQL no ejecutados: corresponden a revalidación
independiente. Sin migraciones ni ampliación funcional.

Resultado: corrección P2 pendiente de retest independiente. La activación
productiva sigue bloqueada por los pendientes técnicos del registro anterior.
Próximo paso: revalidar el hallazgo y el paquete 4C desde esta rama/base,
conservando los ocho cambios existentes. No habilitar flujos públicos.

---

# Registro original preservado: adaptador interno Orders API - incremento 4C

Timestamp: 2026-09-17T12:58:58-03:00
Estado: READY_TO_RESUME
Agente: Codex - implementación local; dispositivo: laptop.
Rama: `feature/mercadopago-payment-order-create-adapter`.
Base: `fc5eb0c77f1101ada270a2a30d29a8acc795b9dd`.
Objetivo: implementar únicamente creación interna Orders API con proveedores
confiables inyectados, conservando reserva/claim y persistencia de 4B/4A.
Resultado: implementación técnica preparada y validada focalmente,
pendiente de revisión y Testing final; producto no activado.

## Diseño y alcance implementado

[Adaptador y composición interna](../../app/services/mercadopago_order_creation_adapter.py):
configuración inmutable deshabilitada por defecto, OAuth explícito por
profesional receptor/ambiente/ARS y política confiable de comisión sin defaults.
Preparación resuelta una sola vez antes de escrituras de obligación/reserva y
claim. Token y payload quedan en un objeto de llamada inmutable, nunca en ORM.
No se implementa onboarding, refresh ni custodia OAuth.

[Servicio 4B](../../app/services/payment_order_application_service.py):
prepara el adaptador antes del claim, confirma el claim y cierra la sesión
antes de exactamente un POST. Mantiene replay y bloqueo durable después de
error, incertidumbre, caída o fallo de persistencia. No cambia claves ni
reintenta. Una recuperación futura debe reutilizar clave y payload compatible;
la conservación durable de comisión/contexto receptor para recuperación tendrá
diseño propio, sin presumir que basta recalcular una política cambiante.

POST a `https://api.mercadopago.com/v1/orders`, OAuth del receptor y clave
durable sin truncar/regenerar. Importes como strings decimales exactos;
ARS validado en contexto OAuth y respuesta. `marketplace_fee` explícito
(incluido cero únicamente si lo devuelve la política). `expiration_time=PT72H`.
Sin payer, DNI, teléfono, domicilio, metadata ni texto contractual; concepto
genérico generado por 4B. Respuesta 201 con ID/URL y eco monetario/referencia
validado, host exacto `www.mercadopago.com.ar` y URL HTTPS segura.
TLS verificado, redirects prohibidos, JSON estricto, respuesta acotada a 1 MiB,
timeout configurable 10 s (máximo 30 s), cero retries.
Timeout/red/409/423/429/5xx: incertidumbre; 401/403: autenticación;
resto 4xx: rechazo; éxito ilegible o incoherente: resultado inválido.
4B conserva el bloqueo para todos los fallos posteriores al claim.

Entrega y replay rechazados al vencer localmente, inclusive si el tiempo
vence durante la respuesta o después de leer el replay. ID/URL externos
válidos se conservan aunque la finalización ocurra al vencer; nunca se entregan
por el servicio en ese caso. No se afirma igualdad con la expiración remota.

## Evidencia y pendientes

Pruebas focales: 46/46 aprobadas (19 adaptador/transporte, 11 integración HTTP
falso con SQLite desechable, 16 servicio 4B). Regresiones relacionadas: 148/148
aprobadas en once módulos PSP/pagos. `compileall -q app tests` y
`git diff --check`: aprobados. Controles documentales UTF-8 y enlaces: aprobados.
Una expectativa inicial de auditoría de finalización tardía se corrigió:
4A registra tanto creación como expiración; se validó estado EXPIRED.
Sin fallos pendientes ni troubleshooting técnico nuevo.
Suite completa reservada a Testing final. PostgreSQL, Docker, migraciones,
llamadas reales y validación operativa marketplace: no ejecutados.
Sin nuevas dependencias declaradas ni migraciones; entorno local de pruebas
preparado con las dependencias existentes de requirements.txt.

Pendientes técnicos: revisión independiente/Testing final; OAuth completo y
configuración real; tasa/fórmula/base/redondeo de comisión aprobados; endpoint,
UI/QR y retornos (4D); recuperación y conciliación/revisión de pagos tardíos.
No hay efectos PRO, contractuales, contables ni de comisión local implementados.
La deducción externa marketplace y su tratamiento tardío requieren validación
y conciliación antes de producción; no se promete control de efectos remotos.
La activación productiva sigue bloqueada por la política completa de doble
vencimiento y estos pendientes. Este incremento no habilita flujos públicos.

Próximo paso: revisión de código y paquete de Testing final.
Para retomar: verificar rama/base y revisar adaptador, servicio 4B,
`tests/test_mercadopago_order_creation_adapter.py`,
`tests/test_mercadopago_order_application.py` y pruebas 4B.
Preservar claim/clave; no habilitar producción ni asumir conciliación de tardíos.
Los registros siguientes permanecen históricos; sus afirmaciones de
“4C no implementado” quedan superadas solo por este alcance técnico interno.

---

# Registro anterior preservado


# Handoff vigente: realineación documental previa de 4C

## 2026-09-17 - Política aprobada de doble vencimiento 4C

Timestamp: 2026-09-17T12:51:16-03:00
Estado: APROBADO
Implementación: PENDIENTE
Responsable: Cristian Sánchez; dispositivo: laptop; agente: Codex.
Rama: `feature/mercadopago-payment-order-create-adapter`; base: `fc5eb0c`.

MANDOBRA conserva `expires_at = created_at + 72 horas` como autoridad
contractual exacta. Mercado Pago recibe `expiration_time = PT72H`, contado
desde la creación remota. No se afirma igualdad entre ambos vencimientos.
Después del vencimiento local no se debe entregar ni reutilizar el checkout.
Un eventual pago tardío no genera automáticamente efectos PRO, contractuales,
contables ni de comisión: queda pendiente de conciliación/revisión.
La activación productiva permanece bloqueada hasta implementar esa política
completa; 4C sigue limitado al adaptador interno deshabilitado por defecto.
Esta decisión supera el bloqueo de diseño por igualdad de vencimientos,
preservando los registros anteriores y sin crear migraciones.

Fuente de semántica remota:
[Vigencia de Orders](https://www.mercadopago.com.ar/developers/es/docs/checkout-pro-orders/additional-settings/define-order-validity).



Timestamp: 2026-09-17T12:14:36-03:00
Estado: READY_TO_RESUME
Responsable de decisión: Cristian Sánchez
Agente: Codex - documentación local; dispositivo/origen: laptop.
Objetivo: realinear documentación a Orders API, OAuth por profesional y marketplace.
Rama: `feature/mercadopago-payment-order-create-adapter`.
HEAD/último commit: `ad9ce5964f09919990b30cbf31df4efcfb709b0e`.
Origin fetch/push: `https://github.com/cristhian-star/TRAX-PLATFORM.git`.
PR #17 ya fue fusionado en `develop` mediante `ad9ce59`, verificado en el
commit local y `develop` local.
El cierre 4B siguiente permanece histórico; sus pendientes de PR/merge quedan
superados por esta constatación, sin alterar su evidencia de Testing.

## Decisiones vigentes

Checkout Pro moderno: `POST /v1/orders`; Preferences descartada para la nueva
integración, con menciones históricas preservadas. `X-Idempotency-Key`
obligatorio con la clave durable 4B; sin reintentos automáticos.
La política queda aprobada; una recuperación futura, todavía no implementada, deberá reutilizar la misma clave durable.
Se conserva el bloqueo durable. Persistir `id` como `external_order_id` y
`checkout_url`. OAuth del profesional receptor; comisión MANDOBRA marketplace
mediante `marketplace_fee`. Ningún token global MANDOBRA como receptor productivo.
4C solo adaptador/cableado internos, apagado sin OAuth/configuración válida.
OAuth completo, endpoint/UI 4D, retornos, recuperación y conciliación separados.
Sin migración por esta decisión documental.
Tasa/fórmula no aprobada: REQ-001 RESTRICCIONES y PREGUNTAS ABIERTAS; no inventar
porcentaje/importe. Bloquea producción, no adaptador interno deshabilitado.
Fuentes y límites oficiales:
[REQ-003](../REQUISITOS/REQ-003-creacion-de-ordenes-de-cobro-checkout-pro.md#realineación-vigente-4c-orders-api-y-marketplace).

## Trabajo y estado de cierre

Completado: realineación en REQ-003 y decisiones arquitectónicas; actualización
normativa focal de REQ-001/Master Spec y de este handoff.
Trabajo parcialmente completado: ninguno de implementación; 4C no implementado.

Migraciones: ninguna creada/ejecutada; no requerida por esta decisión.
Validaciones documentales: UTF-8 estricto, enlaces locales/anchors añadidos,
diff completo y `git diff --check`. Resultado de cierre: aprobados.
Tests, Docker, migraciones, compileall y llamadas API: NO ejecutados.
Pendientes: revisión documental; diseño de contrato Orders y autorización
de implementación 4C; OAuth/configuración, fórmula de comisión y validación
operativa para producción; endpoint/UI 4D, retornos y conciliación separados.
Bloqueantes productivos: OAuth receptor, configuración válida y comisión
aprobada; no bloquean adaptador interno deshabilitado.
Riesgos: reutilizar payload Preferences, cambiar clave ante 409, inventar
comisión o usar token global. Mantener las reglas funcionales de REQ-001.
Errores conocidos/troubleshooting: ningún error técnico nuevo; sin nuevo runbook.
Estado final: documentación preparada, pendiente de revisión; sin activación productiva.

Próximo paso: revisión de la realineación antes de preparar implementación.
Para retomar: verificar rama/base/origin; leer este handoff,
REQ-003 y la decisión 4C; diseñar vigencia/pagador/receptor/comisión y errores.
No regenerar claves, liberar bloqueo 4B, introducir tokens, habilitar producción
ni modificar código sin alcance autorizado.

---

# Registros históricos preservados


# Handoff técnico: aplicación de órdenes Checkout Pro - incremento 4B

## Cierre técnico local 4B de REQ-003

Timestamp: 2026-09-17T10:57:38-03:00
Estado: COMPLETED
Agente documental: Codex - implementador documental local
Dispositivo: laptop
Rama: `feature/checkout-pro-payment-order-application`
Commit técnico y HEAD: `1ba5ab10c4606903f59b0562c698e233ff0dfbe5`
Implementación: 2026-09-17T10:39:29-03:00
Aprobación de Testing: 2026-09-17T10:46:15-03:00
Agente verificador: `03 - Testing - Test Executor`
Resultado: incremento técnico validado localmente; publicación, PR y merge pendientes.

`PaymentOrderApplicationService` recibe identidad confiable del actor y contrato,
recarga al usuario activo con rol profesional y comprueba ownership tanto en
`ContractRequest` como en `Professional`. Solo permite contratos `CONFIRMADA`.
La obligación final es única por contrato mediante FK nullable y constraint única,
sin atribuir contratos a registros legacy. El importe deriva exclusivamente de
`precio_acordado`, en ARS; el cliente no proporciona importe ni `professional_id`.

Referencias, concepto no sensible, clave idempotente y timestamps UTC del comando
se generan una sola vez. `PaymentOrderReservation` conserva el comando durable
con estados `PREPARED`, `CALL_IN_PROGRESS`, `SUCCEEDED` y `UNCERTAIN`. La primera
transacción confirma la reserva y el claim antes del adaptador. Durante la llamada
no queda sesión, conexión ni transacción propia abierta. Una segunda transacción
registra mediante 4A la orden, auditoría y resultado de reserva atómicamente,
revalidando autorización y contenido. Replay exitoso devuelve la misma orden;
cambios materiales producen conflicto. Tras un claim durable, error, incertidumbre
o caída conservan el bloqueo: no hay nueva clave ni llamada automática; la
recuperación queda pendiente de una operación futura autorizada.

Migración `20260917_01`, descendiente de `20260916_01`, head único.
Commit técnico: diez archivos, 1070 inserciones y 3 eliminaciones, inspeccionados
directamente. Evidencia de Testing suministrada para este cierre, no reejecutada:
focales 26/26; regresiones PSP/pagos 141/141; PostgreSQL 6/6; suite 531 ejecutadas,
526 aprobadas, 5 omisiones históricas, 0 fallos y 0 errores. `compileall`, Alembic,
upgrade–downgrade–upgrade y `git diff --check`: aprobados; sin hallazgos P0–P3.

REQ-003 conserva `estado: APROBADO` e `implementacion: PENDIENTE`. Se cierra
únicamente 4B técnico local, no el flujo productivo ni la arquitectura 2.0.
Pendientes: endpoints/frontera pública, creación HTTP real en Mercado Pago,
checkout/QR, integración de órdenes con webhooks y conciliación, efectos PRO,
comisiones, facturación, publicación, PR, merge y producción. Las capacidades
previas de consulta/webhook del repositorio no constituyen este flujo de creación.
Validaciones de esta sesión: controles documentales de UTF-8, mojibake, enlaces,
diff completo y whitespace. Tests, Docker, PostgreSQL y Alembic no ejecutados.
Sin troubleshooting nuevo ni decisiones comerciales adicionales.

Próximo paso: planificar y revisar la integración real de creación de órdenes con
Mercado Pago y su frontera pública, con planificación y revisión separadas.
Para retomar, verificar Git, leer [REQ-003](../REQUISITOS/REQ-003-creacion-de-ordenes-de-cobro-checkout-pro.md)
y este handoff y revisar este cierre documental antes de planificar el siguiente
incremento.
El registro 4A siguiente permanece histórico; su próximo paso 4B queda cumplido
solo en el alcance técnico interno aquí descrito.

Corrección documental focal: 2026-09-17T11:04:24-03:00, Codex - implementador
documental local. Se retiraron controles operativos transitorios del cierre 4B;
publicación, PR, merge y producción siguen pendientes. Se precisó la evolución
de órdenes sucesoras y se actualizó el avance técnico vigente en Backlog/Roadmap,
sin modificar la evidencia de Testing ni los registros históricos.

## Cierre técnico interno del incremento 4A de REQ-003

Timestamp: 2026-09-16T22:40:04-03:00
Estado: COMPLETED
Agente: 01 - Documentation Engineer / Codex local
Dispositivo/origen: laptop / repositorio local MANDOBRA
Motivo: documentar 4A ya implementado y aprobado localmente, sin cerrar el
producto ni aprobar arquitectura 2.0.
Rama: `feature/checkout-pro-payment-order-persistence`
HEAD: `4373b64e419360f7ca3f649efc8f97580c6b42d8`
Commit: `feat: add durable payment order persistence`
Push/publicación, PR y merge de este incremento: pendientes;
no ejecutados ni verificados remotamente en esta sesión. Merge: NO, fuera de
la autorización documental. No se actualizaron referencias ni ramas.

Trabajo completado en `4373b64`: modelo independiente `PaymentOrder`, migración
`20260916_01` (head único, padre `20260911_02`), replay durable y conflictos
materiales, una orden activa por obligación, bloqueo de obligación, estados
`ACTIVE`, `EXPIRED`, `CANCELLED`, vencimiento contractual de 72 horas,
cancelación local auditable, constraints e identidad PSP contextual,
auditoría atómica y comportamiento concurrente PostgreSQL. SQLite conserva
compatibilidad y rollback transaccional; no sustituye las garantías PostgreSQL.
El servicio participa de la transacción del llamador y no realiza commit propio.
La orden externa no se almacena en `PaymentAttemptRecord.external_attempt_id`.

Evidencia aprobada comunicada por el usuario, no reejecutada aquí: focales de
persistencia/migración `11/11`; regresiones relacionadas `141/141`; PostgreSQL
`6/6`; suite completa `515` ejecutadas, `510` aprobadas, `5` omisiones históricas,
`0` fallos y `0` errores; compileall, Alembic y git diff --check aprobados;
revalidación independiente sin hallazgos P0-P3. La inspección estática del
commit y del grafo de migraciones confirma el head único `20260916_01`.
Tests, compileall, Docker, PostgreSQL y Alembic NO ejecutados en esta sesión
documental. No se modificaron modelos, servicios, pruebas ni migraciones.

REQ-003 conserva `estado: APROBADO` e `implementacion: PENDIENTE`. Se agregan
criterios internos estrechos acreditados por 4A; se mantienen sin marcar los
criterios originales ambiguos o end-to-end. No existe un flujo disponible para
usuarios. `professional_id` almacenado no prueba autorización y la cancelación
local no cancela una preferencia remota.

Pendientes y riesgos: ownership derivado de sesión y `ContractRequest`, servicio
de aplicación público/autorizado, creación HTTP real en Mercado Pago,
recuperación de resultados externos inciertos, checkout/QR visibles,
webhooks/conciliación de órdenes, correlación con pagos, efectos PRO, comisiones,
facturación y producción. Sin errores nuevos identificados por la inspección;
no hubo troubleshooting ni decisiones comerciales nuevas.

Documentación modificada: REQ-003, Master Spec, README de requisitos, Backlog,
Roadmap, Changelog, sprint PSP, decisiones arquitectónicas y este handoff.
Index revisado y conservado: no se crean documentos ni faltan enlaces de índice.
Validaciones documentales completadas: UTF-8 estricto válido en los nueve archivos,
sin mojibake detectado, enlaces relativos con destino existente, diff completo
revisado y `git diff --check` sin errores. Alcance exclusivamente Markdown bajo
`docs/`, sin archivos nuevos. Git advierte la conversión
LF/CRLF configurada; no se ejecutó normalización ni formateo.

Próximo paso recomendado: incremento 4B, servicio de aplicación y ownership
contractual, todavía sin Mercado Pago real. Para retomar, verificar la identidad
Git y preparar alcance y autorización específica
de 4B contra REQ-003 y `ContractRequest`. Esta posta NO autoriza implementar 4B.
El registro anterior se conserva como historia y queda
superado únicamente en el alcance técnico interno 4A y la rama/HEAD actuales.

Corrección documental focal: 2026-09-16T22:51:15-03:00, agente 01 - Documentation
Engineer. Se actualizó el título, se retiró información operativa transitoria
del cierre 4A y se precisó en REQ-003 el savepoint PostgreSQL, sin commit ni
rollback global de los helpers. Se conserva el registro histórico siguiente.

## Avance técnico de REQ-003

Título original del registro histórico: Handoff tecnico: contrato neutral PSP y
simulador determinista.

Timestamp: 2026-09-14T20:43:27-03:00
Estado: COMPLETED
Resultado: REQ_003_AVANCE_TECNICO_VALIDADO_LOCALMENTE_PUBLICACION_PR_Y_MERGE_PENDIENTES
Agente: Codex - implementador documental local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/checkout-pro-payment-order-contract`
HEAD: `12c64187bce3137057c6e3e4a261b1f600b2867b`
Push a GitHub: NO; la rama continúa sin publicación verificada en esta sesión
Merge: NO; no autorizado

Trabajo integrado en la rama: `6d6dd2f` implementó el contrato neutral de
creación, DTOs, validaciones puras y pruebas; `12c6418` agregó el adaptador
determinista en memoria y sus pruebas de idempotencia, aislamiento y
concurrencia local. Este cierre documental no modificó código ni repitió tests
de aplicación.

REQ-003 conserva estado formal `APROBADO` y su implementación productiva
completa permanece `PENDIENTE`. El contrato puro y el fake determinista son un
avance técnico parcial implementado y probado. Persistencia, ownership,
unicidad durable, Mercado Pago real, HTTP, checkout productivo, QR/interfaz,
conciliación, efectos financieros y PRO siguen pendientes. No existe
autorización de producción. La publicación de la rama, el PR y el merge
continúan pendientes y requieren autorización separada.

## Especificación Checkout Pro Payment Order Contract

Timestamp: 2026-09-14T10:21:05-03:00
Estado: COMPLETED
Resultado: ESPECIFICACION_CHECKOUT_PRO_PAYMENT_ORDER_CONTRACT_PREPARADA_PENDIENTE_DE_REVISION
Responsable funcional: Cristian Sánchez
Agente: Codex - implementador técnico documental
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/checkout-pro-payment-order-contract`
HEAD/base: `9199d548dd312f65d84414f30e6193ab386bdc53`
Estado Git inicial: `develop` limpia, staging vacío y sincronización 0/0 con
`origin/develop`; referencia remota verificada en el mismo SHA

Trabajo completado: creación de REQ-003 y trazabilidad en Master Spec, REQ-001,
decisiones de arquitectura, backlog, roadmap, sprint, changelog y handoff. Se
documentó una orden en ARS con importe Decimal, vencimiento exacto a 72 horas y
una única URL presentable como enlace o QR. El QR presencial basado en
sucursales/cajas se excluye del MVP.

Primer incremento autorizado para preparación: protocolo neutral separado,
DTOs inmutables, validaciones puras, errores tipados mínimos, fake determinista
y pruebas unitarias. No se implementó código. Persistencia, ownership efectivo,
concurrencia PostgreSQL, HTTP/SDK, credenciales, QR gráfico, frontend, WhatsApp,
workers, retries, webhooks, conciliación, PRO y producción permanecen fuera.

Pendiente: revisión documental independiente. No hubo staging, commit, push,
PR, merge, rebase, reset, clean, stash ni deploy. La rama no fue publicada.

## Post-merge PR #14 - adaptador de consulta Mercado Pago

Timestamp: 2026-09-14T09:06:21-03:00
Estado: COMPLETED
Resultado: POST_MERGE_MERCADOPAGO_PAYMENT_QUERY_ADAPTER_REGISTRADO_PENDIENTE_DE_REVISION_DOCUMENTAL
Agente: Codex - implementador técnico documental
Dispositivo/origen: laptop / Codex Desktop local
Rama: `develop`
HEAD local/remoto: `b816c69026f329466619291c413e7b15c758e9df`
Rama integrada: `feature/mercadopago-payment-query-adapter`
Base previa: `1cb89cdb647cd358d66b4a013f9f671d1cfb8388`

El PR #14, `feat: agregar adaptador de consulta de pagos de Mercado Pago`, fue
fusionado hacia `develop` sin conflictos informados. Integró, en orden,
`2547f483329b6c17c5cbc86e25ab73e4f9d2463c` (contrato),
`c2cdc1aaa920b74b4ba4fb3581a935fdea72cd5e` (cliente HTTP) y
`47632ad4d008e7b414a3699793578343a8595bd4` (adaptador PSP). El cambio acumulado
abarca 13 archivos, 2044 inserciones y 35 eliminaciones.

Verificación Git post-merge: el commit final es ancestro de `develop`, segundo
padre del merge `b816c69026f329466619291c413e7b15c758e9df`; ambos árboles tienen identidad
`da0d0a86ca664b4216545f243821cbec1ef2d43b`. `develop`, `origin/develop` y la
referencia remota consultada coinciden, con divergencia 0/0. El veredicto remoto
previo fue `APROBADO_PARA_MERGE`; no se informaron conflictos. No hubo checks ni
GitHub Actions remotos, una limitación de evidencia CI y no un fallo funcional.

Evidencia local histórica reutilizada del mismo árbol: focales 49/49,
regresiones PSP/pagos 165/165, PostgreSQL real 15/15 y suite completa 476
ejecutadas, 471 aprobadas, 5 omitidas, 0 fallos y 0 errores; `compileall`,
enlaces, whitespace y `git diff --check` aprobados. No se repitieron las pruebas
ni PostgreSQL después del merge porque el contenido integrado es idéntico al
aprobado y probado.

Quedaron integradas las capacidades neutrales de contrato, cliente HTTP y
adaptador de consulta, separadas de la creación. No hay sesión de base abierta
durante HTTP y la conciliación persiste después en una segunda transacción
breve. La configuración es inmutable, el token está protegido y los recursos
HTTP —incluido `HTTPError`— se cierran de forma segura. El webhook permanece sin
consulta ni conciliación financiera automática.

Alembic conserva el único head `20260911_02`; no se agregaron migraciones ni
dependencias. No existen creación de pagos/cobros, QR, credenciales reales,
SDK, retries, workers, frontend o deploy, y la integración no autoriza
producción. Pendiente: revisión documental independiente. En esta sesión no se
ejecutaron pruebas de aplicación, Docker, PostgreSQL, Alembic ni operaciones de
integración Git.

## Adaptador PSP Mercado Pago - P2 corregidos

Timestamp: 2026-09-13T23:27:35-03:00
Estado: COMPLETED
Resultado: MERCADOPAGO_PAYMENT_QUERY_PSP_ADAPTER_CORREGIDO_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/mercadopago-payment-query-adapter`
HEAD/commit base: `c2cdc1aaa920b74b4ba4fb3581a935fdea72cd5e`
Estado Git inicial: once cambios locales conocidos, staging vacío y dos commits
previos preservados

Se preservan los dos hallazgos P2 recibidos como antecedente. El adaptador y el
cliente HTTP quedaron implementados como dataclasses congeladas con slots. No
es posible reasignar proveedor, modo, referencia al cliente, token, transporte
o timeout después de construirlos. `provider` conserva siempre
`mercadopago`; `provider` y `live_mode` son propiedades de lectura.

El transporte estándar cierra explícitamente cada `urllib.error.HTTPError` una
sola vez para autenticación, ausencia, rate limit, otros 4xx, 5xx y códigos
inesperados. Nunca lee el cuerpo y tampoco conserva sus headers. Un fallo del
cierre se contiene sin encadenarlo ni exponer URL, token, headers o cuerpo; la
clasificación neutral original permanece intacta.

Validación: focal completa 49/49; regresiones PSP/pagos 131/131; PostgreSQL real
15/15 sobre `trax_payment_persistence_test_mp_adapter_p2_20260913`; suite
completa 476 ejecutadas, 471 aprobadas, 5 omitidas, 0 fallos y 0 errores. La
base descartable fue bajada a base por el gate, eliminada y confirmada ausente;
`trax_db` permaneció presente. Pendiente: retest independiente.

No hubo migraciones nuevas ni cambios de alcance. No hubo staging, commit,
push, PR, merge, rebase ni deploy.

## Adaptador PSP de consulta de pagos Mercado Pago

Timestamp: 2026-09-13T22:54:24-03:00
Estado: COMPLETED
Resultado: MERCADOPAGO_PAYMENT_QUERY_PSP_ADAPTER_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/mercadopago-payment-query-adapter`
HEAD/commit base: `c2cdc1aaa920b74b4ba4fb3581a935fdea72cd5e`
Estado Git inicial: árbol y staging limpios; dos commits previos preservados

Decisión aplicada: se agregaron el protocolo neutral de consulta
`PSPPaymentQueryAdapter` y el DTO mínimo inmutable `PSPPaymentQueryResult`, con
identificador externo y `PaymentAttemptStatus`. `PSPAdapter`, su creación y
`get_attempt()` permanecen intactos. El bloqueo histórico previo se conserva.

`MercadoPagoPSPAdapter` implementa únicamente esa capacidad, con proveedor fijo
`mercadopago`, modo explícito e inmutable y cliente inyectado. Valida el ID
antes de la única consulta. Estados autoritativos se entregan al procesador;
`404`, transporte, `429`, `5xx` y estados no representables se traducen a
incertidumbre neutral. Autenticación, configuración y contrato producen error
neutral explícito sin escritura.

El procesador ahora exige coincidencia del proveedor y modo del adaptador antes
de leer/correlacionar eventos. La lectura termina y cierra su sesión antes de la
consulta; `apply_reconciliation()` se ejecuta después en una segunda transacción
atómica. El webhook no invoca automáticamente este recorrido.

Se agregó transporte productivo de biblioteca estándar con contexto TLS
verificado, host fijo, timeout obligatorio y redirects/retries deshabilitados.
Las pruebas no usan red ni credenciales reales.

Validación: focal 45/45; regresiones PSP/pagos 161/161; PostgreSQL real 15/15
sobre `trax_payment_persistence_test_mp_adapter_20260913`; suite completa 472
ejecutadas, 467 aprobadas, 5 omitidas, 0 fallos y 0 errores. La base descartable
fue eliminada y confirmada ausente; `trax_db` permaneció presente. `compileall`,
Alembic, enlaces, whitespace y `git diff --check` se verifican al cierre.

No se agregaron migraciones, SDK, workers, retries, frontend ni creación de
cobros. Pendiente: revisión independiente antes del tercer commit. No hubo
staging, commit, push, PR, merge, rebase ni deploy.

## Bloqueo contractual del adaptador de consulta Mercado Pago

Timestamp: 2026-09-13T22:43:20-03:00
Estado: BLOCKED
Resultado: MERCADOPAGO_PAYMENT_QUERY_PSP_ADAPTER_BLOQUEADO_POR_CONTRATO_NEUTRAL
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/mercadopago-payment-query-adapter`
HEAD/commit base: `c2cdc1aaa920b74b4ba4fb3581a935fdea72cd5e`
Estado Git inicial: árbol y staging limpios; dos commits previos preservados

Bloqueante confirmado contra código: `PSPAdapter.get_attempt()` declara como
salida `PaymentAttempt`, que requiere `internal_reference`, `amount`, `currency`,
`idempotency_key` y `created_at`, además de identidad y estado. El contrato HTTP
aprobado de `GET /v1/payments/{id}` no obtiene esos metadatos y el procesador
solo consume `attempt_id` y `status`. Completar el DTO exigiría inventar valores,
abrir persistencia desde el adaptador o ampliar el contrato HTTP sin autoridad.

También falta una definición para `create_attempt()`, método obligatorio de
`PSPAdapter` pero expresamente fuera del incremento de consulta. Implementar un
método ficticio que siempre falle satisfaría solo la comprobación estructural,
no el contrato neutral.

Decisión requerida: aprobar una segregación de capacidades del contrato
neutral o definir que el procesador dependa de un resultado mínimo de consulta.
Hasta entonces no se implementaron adaptador ni transporte productivo y no se
ejecutaron pruebas, PostgreSQL ni controles posteriores de implementación. No
hubo staging, commit, push, PR, merge, rebase ni deploy.

## Corrección P2 del Bearer del cliente HTTP de pagos

Timestamp: 2026-09-13T22:16:45-03:00
Estado: COMPLETED
Resultado: MERCADOPAGO_PAYMENT_QUERY_HTTP_CLIENT_CORREGIDO_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/mercadopago-payment-query-adapter`
HEAD/commit base: `2547f483329b6c17c5cbc86e25ab73e4f9d2463c`
Estado Git: seis cambios locales esperados, staging vacío, sin commit ni push

Se preserva el registro histórico del hallazgo. La validación parcial del token
fue sustituida por una allowlist ASCII completa compatible con `b64token`: una
parte principal no vacía formada por letras ASCII, números y `-._~+/`, con `=`
permitido solo como padding final. La longitud máxima es 2048 caracteres y el
valor no se recorta, normaliza ni transforma.

Las regresiones cubren controles C0/C1, `DEL`, zero-width space, NBSP,
controles bidireccionales, caracteres Unicode similares, whitespace, padding,
vacío, exceso de longitud y formatos válidos representativos de Mercado Pago.
Cualquier token inválido se rechaza antes de construir headers o llamar al
transporte; el valor no aparece en mensaje, `repr`, traceback, causa, contexto,
argumentos ni atributos de la excepción.

Validación: focal cliente/contrato 26/26, regresiones PSP/pagos 151/151 y suite
completa 462 ejecutadas, 457 aprobadas, 5 omitidas, 0 fallos y 0 errores. Los
controles estáticos finales quedan registrados al cerrar la sesión.

Las demás garantías del cliente permanecen intactas. Pendiente: retest
independiente antes de autorizar el segundo commit. No hubo staging, commit,
push, PR, merge, rebase ni deploy.

## Cliente HTTP de consulta de pagos Mercado Pago

Timestamp: 2026-09-13T12:38:36-03:00
Estado: COMPLETED
Resultado: MERCADOPAGO_PAYMENT_QUERY_HTTP_CLIENT_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/mercadopago-payment-query-adapter`
HEAD/commit base: `2547f483329b6c17c5cbc86e25ab73e4f9d2463c`
Estado Git inicial: árbol y staging limpios; primer commit preservado

Trabajo completado: cliente para una única consulta autenticada `GET` al host
fijo de Mercado Pago, desacoplado mediante transporte callable. El ID se valida
antes de construir la URL; la solicitud no lleva body ni query, usa únicamente
Bearer y aceptación JSON, timeout explícito de hasta 30 segundos, redirects
deshabilitados y ningún retry.

La frontera de respuesta clasifica `401/403`, `404`, otros `4xx`, y como
recuperables `429`, fallos de transporte y `5xx`. No inspecciona cuerpos de
error. Un `200` exige JSON UTF-8, `Content-Type` inequívoco, máximo 1 MiB,
objeto y claves únicas; después reutiliza el contrato puro del primer commit.
Errores de transporte y decoder se absorben sin encadenamiento sensible.

El token no se almacena en DTO ni aparece en `repr`, logs, errores o
tracebacks. No se leen variables de entorno y no se implementan integración
con `PSPAdapter`, persistencia, actualización financiera, SDK, retries o red
real en pruebas. No se agregó migración ni dependencia.

Validación: focal cliente/contrato 25/25, regresiones PSP/pagos 150/150 y suite
completa 461 ejecutadas, 456 aprobadas, 5 omitidas, 0 fallos y 0 errores.
`compileall`, head Alembic, enlaces, whitespace y `git diff --check` se
verifican como controles finales. PostgreSQL no aplica a este cliente aislado.

Pendiente: revisión independiente antes del segundo commit. Staging, commit,
push, PR, merge y deploy no están autorizados en esta sesión.

## Corrección P2 del contrato de consulta de pagos

Timestamp: 2026-09-13T12:13:00-03:00
Estado: COMPLETED
Resultado: MERCADOPAGO_PAYMENT_QUERY_CONTRACT_CORREGIDO_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/mercadopago-payment-query-adapter`
HEAD/commit base: `1cb89cdb647cd358d66b4a013f9f671d1cfb8388`
Estado Git: cinco cambios locales esperados, staging vacío, sin commit ni push

Se conserva el registro histórico previo y se corrige exclusivamente el P2 de
`status_detail`. El valor opcional continúa limitado a 128 caracteres, pero
ahora debe ser un token que comience con letra ASCII minúscula y contenga solo
letras ASCII minúsculas, números o guion bajo. Se bloquean tokens puramente
numéricos y cualquier secuencia de 13 a 19 dígitos consecutivos.

La regresión cubre PAN numérico, secuencias largas con prefijo/sufijo, espacios,
mayúsculas, guiones, Unicode y ausencia de filtración mediante texto,
representación, traceback, causa, contexto, argumentos o atributos. Se
mantienen válidos los tokens oficiales representativos y quedan intactos la
identidad, el modo y los mapeos financieros.

Validación: focal 14/14, regresiones PSP/pagos 139/139 y suite completa 450
ejecutadas, 445 aprobadas, 5 omitidas, 0 fallos y 0 errores. Los controles
finales de enlaces, whitespace y `git diff --check` quedaron aprobados.

Pendiente: retest independiente antes de autorizar integración. No se agregan
HTTP, SDK, credenciales, persistencia, dependencias ni migraciones. No hubo
staging, commit, push, PR, merge, rebase ni deploy.

## Contrato de consulta de pagos Mercado Pago

Timestamp: 2026-09-13T11:52:01-03:00
Estado: COMPLETED
Resultado: MERCADOPAGO_PAYMENT_QUERY_CONTRACT_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/mercadopago-payment-query-adapter`
HEAD/commit base: `1cb89cdb647cd358d66b4a013f9f671d1cfb8388`
Estado Git: cinco cambios locales esperados, staging vacío, sin commit ni push

Trabajo completado: contrato puro para transformar una respuesta ya
decodificada de `GET /v1/payments/{id}` a estado neutral. Valida un ID de path
numérico ASCII y acotado, objeto JSON inequívoco en la frontera, `id` entero
estricto, coincidencia de identidad, `live_mode` booleano estricto y entorno.
El DTO resultante es inmutable y no conserva el payload.

Mapeo explícito: `approved` a `APPROVED`; `pending`, `in_process` y `authorized`
a `PENDING`; `rejected` y `cancelled` a `REJECTED`. `refunded`, `charged_back`
y estados desconocidos producen una excepción neutral que exige conciliación
explícita. `status_detail` se conserva solo como token seguro de hasta 128
caracteres; ningún error expone los valores recibidos.

Validación: focal 13/13, regresiones PSP/pagos 138/138 y suite completa 449
ejecutadas, 444 aprobadas, 5 omitidas, 0 fallos y 0 errores. La primera corrida
agrupada usó por herencia PostgreSQL y un test portable falló al ejecutar
`PRAGMA`; se clasificó como configuración de entorno y la repetición aislada
con SQLite aprobó 138/138. `compileall`, head Alembic único, enlaces,
whitespace y `git diff --check` se verifican en el cierre.

Fuente: [Obtener pago - Mercado Pago Developers](https://www.mercadopago.com.ar/developers/es/reference/online-payments/subscriptions/get-payment/get).
No aplica PostgreSQL y no se agregó migración. Permanecen fuera de alcance
HTTP, credenciales, SDK, persistencia, actualización financiera y conexión real
con Mercado Pago. Pendiente: revisión independiente antes de autorizar commit.
No hubo staging, commit, push, PR, merge, rebase ni deploy.

## Integracion post-merge del Webhook de Mercado Pago

Timestamp: 2026-09-13T00:00:12-03:00
Estado: COMPLETED
Resultado: POST_MERGE_MERCADOPAGO_WEBHOOK_INGRESS_REGISTRADO_PENDIENTE_DE_REVISION_DOCUMENTAL
Agente: Codex - implementador documental local
Dispositivo/origen: laptop / Codex Desktop local
Rama actual/destino: `develop`
Rama integrada: `feature/mercadopago-webhook-ingress`
HEAD local y `origin/develop`: `c8dc017be48a2a3526947de50c9121986047e2d4`
Base previa: `08471f76900cde263a7a4590ff77f60751ffd704`
Pull Request integrado: `#13`
Estado Git previo: árbol limpio, staging vacío y divergencia `0/0`

Integración registrada: el PR #13 incorporó `73b3fd9` (firma), `199be11`
(contrato de notificación) y `540d953` (ingreso HTTP). El merge `c8dc017`
contiene 12 archivos, 1851 inserciones y 0 eliminaciones; no agregó migraciones
y mantiene `20260911_02` como head Alembic.

Identidad de evidencia: los árboles Git de `540d953` y `c8dc017` coinciden
exactamente. Por esa identidad se conserva como evidencia previa la validación
del commit integrado: focal 44/44, regresiones PSP 63/63, pagos 65/65,
PostgreSQL 2/2 y suite completa 436 ejecutadas, 431 aprobadas y 5 omitidas,
sin fallos ni errores. No se repitieron pruebas después del merge.

Desviación de proceso: la integración ocurrió después de una aprobación local
para crear commit y abrir PR, pero antes de obtener un gate remoto independiente
`APROBADO_PARA_MERGE`. Esta observación no representa una regresión funcional,
no reemplaza el gate omitido y no atribuye validaciones posteriores al merge.

Límites vigentes: no existen credenciales productivas, consulta al PSP,
conciliación automática, OAuth, SDK, workers, retries ni deploy. Pendiente:
revisión documental independiente de este registro antes de su integración.
Esta sesión no ejecuta pruebas, staging, commit, push, PR, merge, rebase,
reset, clean, stash ni deploy.

## Ingreso HTTP de Webhooks de Mercado Pago - P2 corregidos

Timestamp: 2026-09-12T23:27:36-03:00
Estado: COMPLETED
Resultado: MERCADOPAGO_WEBHOOK_HTTP_INGRESS_CORREGIDO_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/mercadopago-webhook-ingress`
HEAD/commit base: `199be11cb6b85cd5a9b963e93097aebca31d3638`
Estado Git: ocho cambios locales conocidos, staging vacío, sin commit ni push

Corrección de metadatos: `X-Request-Id` se valida como un único valor exacto.
Se rechaza si WSGI plegó múltiples headers con coma, si aparece más de una vez,
si está vacío o si contiene whitespace exterior. Este corte devuelve `400`
antes de llamar al verificador o tocar la sesión; el valor válido permanece
literalmente intacto para el manifiesto.

Corrección JSON: la ruta lee los bytes originales y usa una frontera auxiliar
con sentinel. La decodificación UTF-8 y `json.loads()` emplean
`object_pairs_hook` para detectar duplicados en cualquier objeto, incluido
`data`, y `parse_constant` para rechazar `NaN`/`Infinity`. Los errores internos
se absorben dentro del helper y no quedan encadenados ni se filtran en
excepciones, respuestas o logs.

Validación: focal HTTP, firma, contrato y configuración 44/44; regresiones PSP
63/63; persistencia, orquestación y workflow 65/65; PostgreSQL real 2/2 sobre
`trax_mp_webhook_test_ingress_p2_20260912`; suite completa 436 ejecutadas, 431
aprobadas, 5 omitidas, 0 fallos y 0 errores; `compileall` aprobado y head
Alembic único `20260911_02`.

Durante la validación se corrigió además el aislamiento de la nueva captura de
logs para no materializar un logger que Alembic pudiera deshabilitar en pruebas
posteriores. La reproducción exacta y la suite completa final quedaron verdes.

Limpieza: la base descartable fue eliminada y confirmada ausente; `trax_db`
permaneció intacta. Se conservan los hallazgos previos como historia. Pendiente:
retest independiente antes del tercer commit. No hubo staging, commit, push,
PR, merge, rebase ni deploy.

## Ingreso HTTP de Webhooks de Mercado Pago

Timestamp: 2026-09-12T19:34:39-03:00
Estado: COMPLETED
Resultado: MERCADOPAGO_WEBHOOK_HTTP_INGRESS_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/mercadopago-webhook-ingress`
HEAD/commit base: `199be11cb6b85cd5a9b963e93097aebca31d3638`
Estado Git: cambios locales sin staging, commit ni push

Trabajo completado: blueprint público con `POST /api/webhooks/mercadopago`,
registrado en la aplicación y exento de sesión de usuario y CSRF. La única
credencial de ingreso es la firma HMAC validada con el secreto de configuración
`MERCADOPAGO_WEBHOOK_SECRET`; el secreto nunca se hardcodea ni se registra.
Query y headers se conservan como pares para no colapsar duplicados.

Orden de seguridad: se valida la firma antes de interpretar el cuerpo; después
se exige un tipo JSON apropiado y JSON válido, se invoca el contrato de
notificación y se genera `received_at` en UTC. La ruta registra mediante el
servicio existente, confirma la transacción antes de responder y ejecuta
rollback ante conflicto o error. Nuevo y replay son indistinguibles con
`200 {"status":"accepted"}` y no exponen IDs internos. Los errores `400`,
`401`, `409`, `500` y `503` son genéricos y no contienen payload, SQL, firma,
secreto, manifiesto ni traceback.

Validación: focal HTTP, firma, contrato y configuración 39/39; regresiones PSP
58/58; persistencia, orquestación y workflow 65/65; suite completa 431
ejecutadas, 426 aprobadas, 5 omitidas, 0 fallos y 0 errores; PostgreSQL real
2/2 sobre `trax_mp_webhook_test_ingress_20260912`; `compileall` aprobado y
head Alembic único `20260911_02`.

Limpieza: la base descartable fue migrada, validada, vaciada y eliminada; se
confirmó su ausencia y la presencia intacta de `trax_db`. No existe migración
nueva. La ruta no consulta al PSP, no concilia, no interpreta `action` como
estado financiero y no agrega SDK, OAuth, workers ni retries.

Pendiente: revisión independiente antes del tercer commit. Archivos locales:
`app/__init__.py`, `app/config/config.py`,
`app/routes/mercadopago_webhook_routes.py`,
`tests/test_mercadopago_webhook_routes.py`,
`tests/postgresql_mercadopago_webhook_ingress_e2e.py` y los tres registros
documentales. No hubo staging, commit, push, PR, merge, rebase ni deploy.

## Contrato de notificacion Webhook - P2 corregido

Timestamp: 2026-09-12T19:03:04-03:00
Estado: COMPLETED
Resultado: MERCADOPAGO_WEBHOOK_NOTIFICATION_CONTRACT_CORREGIDO_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/mercadopago-webhook-ingress`
HEAD/commit base: `73b3fd951315d6f2876b7745347dea04c63b3a64`
Estado Git: cinco cambios locales conocidos, staging vacío, sin commit ni push

Corrección P2: `_parse_iso_datetime()` encapsula `datetime.fromisoformat()`,
captura internamente `ValueError`/`TypeError` y devuelve un sentinel privado.
La excepción de dominio neutral se lanza posteriormente fuera del `except`,
por lo que no conserva el error interno como causa ni contexto. Ningún mensaje,
representación o metadato incorpora el timestamp recibido.

La prueba adversarial usa un marcador sensible y verifica `str`, `repr`,
`traceback.format_exception`, `__cause__` y `__context__`. Se revisó el resto
del contrato: no hay otro parseo de fecha equivalente. Firma, normalización,
hash y DTO permanecen intactos.

Validación: focal 21/21; regresiones PSP 47/47; persistencia, orquestación y
workflow 65/65; suite completa 420 ejecutadas, 415 aprobadas, 5 omitidas,
0 fallos y 0 errores; `compileall` aprobado; head Alembic único `20260911_02`.
PostgreSQL no aplica a este contrato puro.

Se conserva el hallazgo histórico. Pendiente: retest independiente antes del
segundo commit. No existen ruta pública, persistencia, SDK ni integración real
con Mercado Pago. No hubo staging, commit, push, PR, merge, rebase ni deploy.

## Contrato de notificacion Webhook de Mercado Pago

Timestamp: 2026-09-12T18:42:12-03:00
Estado: COMPLETED
Resultado: MERCADOPAGO_WEBHOOK_NOTIFICATION_CONTRACT_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/mercadopago-webhook-ingress`
HEAD/commit base: `73b3fd951315d6f2876b7745347dea04c63b3a64`
Estado Git: cinco cambios locales conocidos, staging vacío, sin commit ni push

Trabajo completado: parser/normalizador puro de notificaciones ya decodificadas
que recibe query, headers, cuerpo y tiempo de recepción de forma explícita.
Verifica la firma antes de validar el cuerpo, rechaza estructuras ambiguas o
inesperadas y exige coherencia exacta de recurso y tópico. Produce el DTO
neutral `PSPEvent` con proveedor `mercadopago`, modo derivado de `live_mode` y
hash SHA-256 determinista del contenido validado estable. El payload crudo no
se almacena y `received_at` no participa en el hash de redelivery.

Validación: firma y notificación 20/20; regresiones PSP 46/46; persistencia,
orquestación y workflow 65/65; suite completa 419 ejecutadas, 414 aprobadas,
5 omitidas, 0 fallos y 0 errores; `compileall`, whitespace y head Alembic único
`20260911_02` aprobados. Todo se ejecutó con SQLite en memoria; PostgreSQL no
aplica y no se utilizó ni modificó `trax_db`.

Archivos locales: `app/services/mercadopago_webhook_notification.py`,
`tests/test_mercadopago_webhook_notification.py` y los tres registros
documentales autorizados. Pendiente: revisión independiente antes del segundo
commit. No existen ruta Flask, endpoint público, base de datos conectada,
consulta a Mercado Pago, SDK, credenciales, migración, interpretación
financiera ni procesador invocado. No hubo staging, commit, push, PR, merge,
rebase ni deploy.

## Verificador de firma Webhook de Mercado Pago - P2 corregido

Timestamp: 2026-09-12T18:20:35-03:00
Estado: COMPLETED
Resultado: MERCADOPAGO_WEBHOOK_SIGNATURE_VALIDATOR_CORREGIDO_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/mercadopago-webhook-ingress`
HEAD/commit base: `08471f76900cde263a7a4590ff77f60751ffd704`
Estado Git: cinco cambios locales conocidos, staging vacío, sin commit ni push

Corrección P2: el parser aplica trim y minúsculas a las claves antes de
registrarlas. De este modo `ts`/`TS` y `v1`/`V1` son una misma clave semántica,
y cualquier duplicado se rechaza antes de poder sobrescribir el primero,
incluso si ambos valores coinciden. Los valores de `ts` y `v1` no se
normalizan; se conserva el tratamiento estructural previo de espacios.

Validación: focal 10/10; firma más regresiones PSP 36/36; persistencia,
orquestación y workflow 65/65; suite completa 409 ejecutadas, 404 aprobadas,
5 omitidas, 0 fallos y 0 errores; `compileall` aprobado; head Alembic único
`20260911_02`. PostgreSQL no aplica por tratarse de lógica criptográfica pura.

Se conserva el `REQUIERE_CORRECCIONES` histórico. Pendientes: retest
independiente y futura capa HTTP. No se implementaron rutas, endpoint público,
SDK, credenciales, inbox conectado ni integración real con Mercado Pago. No
hubo staging, commit, push, PR, merge, rebase ni deploy.

## Verificador de firma Webhook de Mercado Pago

Timestamp: 2026-09-12T16:17:29-03:00
Estado: COMPLETED
Resultado: MERCADOPAGO_WEBHOOK_SIGNATURE_VALIDATOR_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/mercadopago-webhook-ingress`
HEAD/commit base: `08471f76900cde263a7a4590ff77f60751ffd704`
Estado Git: cambios locales sin staging, commit ni push
Fuente oficial: [Notificaciones de pago de Mercado Pago](https://www.mercadopago.com.ar/developers/es/docs/checkout-pro-preferences/payment-notifications)

Trabajo completado: verificador criptográfico aislado que extrae sin ambigüedad
`ts` y `v1`, arma `id:<data.id>;request-id:<x-request-id>;ts:<ts>;`, calcula
HMAC-SHA256 hexadecimal y compara mediante `hmac.compare_digest()`. La decisión
aprobada reemplaza el uso literal previo: sólo la copia de `data.id` destinada
al manifiesto se pasa a minúsculas; el resultado inmutable conserva el valor
original. No se normalizan `x-request-id`, `ts`, secreto u otros valores.

Distinción contractual: la estructura de firma, el manifiesto, HMAC-SHA256 y
la minúscula de `data.id` proceden de la documentación oficial. MANDOBRA adopta
por separado una política fail-closed más estricta: exige `x-signature`,
`x-request-id`, `data.id`, `ts`, `v1` y secreto. No se agregó ventana temporal
porque la fuente no fija una tolerancia obligatoria.

Validación: focal 9/9; firma más regresiones PSP 35/35; persistencia,
orquestación y workflow 65/65; suite completa 408 ejecutadas, 403 aprobadas,
5 omitidas, 0 fallos y 0 errores; `compileall` aprobado; head Alembic único
`20260911_02`; PostgreSQL no aplica por ser lógica criptográfica pura.

Pendientes: revisión independiente y futura capa web que traduzca una firma
inválida a HTTP 401. No existen aún ruta Flask, endpoint público, configuración
productiva, inbox conectado, consulta de pagos, SDK, OAuth, QR, checkout,
workers, retries ni procesamiento financiero. No hubo staging, commit, push,
PR, merge, rebase ni deploy.

## Integracion post-merge del procesamiento de eventos PSP

Timestamp: 2026-09-12T14:03:46-03:00
Estado: COMPLETED
Resultado: POST_MERGE_PSP_EVENT_PROCESSING_REGISTRADO_PENDIENTE_DE_REVISION_DOCUMENTAL
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama actual/destino: `develop`
Rama origen: `feature/psp-event-processing`
HEAD local y `origin/develop`: `a96a55311283d331c70e49aad3550ec6f7b1a566`
Pull Request integrado: `#12`
Estado Git previo: árbol limpio, staging vacío y divergencia `0/0`

Integración verificada: merge limpio y sin conflictos de `f45f32c` (inbox
PSP), `9951d25` (identidad contextual PSP) y `3c243b5` (procesador de
conciliación). El diff del merge contiene 23 archivos, 1996 inserciones y 9
eliminaciones. Incluye las migraciones `20260911_01` y `20260911_02`, con
`20260911_02` como head final registrado. La revisión remota concluyó
`APROBADO_PARA_MERGE`.

Identidad de evidencia: el SHA local, el remoto y su árbol coinciden
exactamente con el contenido revisado y probado. Por eso continúa vigente la
evidencia histórica: procesador 9/9; procesador, inbox e identidad 26/26;
persistencia, orquestación y workflow 65/65; PostgreSQL 14/14; suite completa
399 ejecutadas, 394 aprobadas y 5 omitidas; `compileall`, enlaces y
`git diff --check` aprobados. No se repitieron pruebas, Docker, PostgreSQL ni
Alembic después del merge.

Límites: infraestructura neutral solamente. No acredita webhook público,
validación de firma, HTTP, SDK, OAuth, credenciales, Mercado Pago real,
workers, retries automáticos, QR, checkout, créditos, PRO, ARCA ni producción.
Pendiente: revisión documental independiente de estos tres Markdown. Esta
sesión no realiza staging, commit, push, PR, merge, rebase ni deploy.

## Procesador PSP - P1 de topicos corregido

Timestamp: 2026-09-12T13:32:58-03:00
Estado: COMPLETED
Resultado: PSP_EVENT_RECONCILIATION_PROCESSOR_CORREGIDO_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/psp-event-processing`
HEAD/commit base: `9951d2503d9b70353ddcd674d6c750cbb2436997`
Estado Git: seis cambios locales conocidos, staging vacío, sin commit ni push

Corrección: el constructor recibe obligatoriamente tópicos de pago, los
canonicaliza mediante trim/minúsculas y conserva un `frozenset` privado. No hay
comodín ni tópico hardcodeado en el servicio. Tras validar proveedor y modo,
un tópico ajeno devuelve el resultado inmutable `UNSUPPORTED_TOPIC` antes de
cualquier correlación o llamada externa.

La reproducción adversarial `merchant_order`, con ID coincidente y
`action=payment.approved`, se ejecutó dos veces: no buscó el intento, no llamó
al adaptador y dejó el estado financiero `PENDING` sin cambios. Proveedor y
modo incompatibles conservan el mismo corte temprano sin llamada.

Validación: focal 9/9; inbox, identidad y procesador 26/26; persistencia,
orquestación y workflow 65/65; PostgreSQL 14/14 sobre
`trax_payment_persistence_test_topics_20260912`; suite completa 399 ejecutadas,
394 aprobadas, 5 omitidas, 0 fallos y 0 errores; `compileall` y head único
`20260911_02` aprobados. Sin migración nueva.

El `REQUIERE_CORRECCIONES` histórico permanece como evidencia. Pendiente:
retest independiente. No existen Mercado Pago real, endpoint webhook, HTTP,
firmas, SDK, workers, retries ni integración productiva. No hubo staging,
commit, push, PR, merge, rebase ni deploy.

## Procesador neutral de conciliacion por eventos PSP

Timestamp: 2026-09-12T13:10:46-03:00
Estado: COMPLETED
Resultado: PSP_EVENT_RECONCILIATION_PROCESSOR_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/psp-event-processing`
HEAD/commit base: `9951d2503d9b70353ddcd674d6c750cbb2436997`
Estado Git: cambios locales sin staging, commit ni push

Trabajo completado: coordinador neutral con resultados inmutables y explícitos;
lectura/correlación contextual en una transacción breve; cierre total de sesión
antes de una única consulta por invocación a `PSPAdapter`; segunda transacción
con lock y transición mediante `apply_reconciliation()`. El evento nunca se
interpreta como estado financiero. Los intentos legacy no correlacionan y los
terminales no provocan otra llamada.

Validación: focal 7/7; inbox e identidad 24/24; persistencia, orquestación y
workflow 65/65; gate PostgreSQL 14/14 sobre
`trax_payment_persistence_test_eventprocessor_20260912`; suite completa 397
ejecutadas, 392 aprobadas, 5 omitidas, 0 fallos y 0 errores; `compileall` y head
Alembic único `20260911_02` aprobados. No se agregó migración.

Pendientes: revisión independiente antes del tercer commit y del PR único.
No existe Mercado Pago real, endpoint webhook público, validación de firma,
HTTP, SDK, credenciales, workers, retries ni integración productiva. No hubo
staging, commit, push, PR, merge, rebase ni deploy.

## Identidad PSP contextual - P2/P3 corregidos

Timestamp: 2026-09-11T22:54:46-03:00
Estado: COMPLETED
Resultado: PAYMENT_ATTEMPT_PSP_IDENTITY_CORREGIDA_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/psp-event-processing`
HEAD/commit base: `f45f32ce3c032b6a4b7404886b9c2558cdb5e62a`
Estado Git: cambios locales sin staging, commit ni push

Corrección: `create_or_get_obligation()` recupera un replay sólo cuando el
driver expone SQLSTATE `23505` y `diag.constraint_name` igual a
`uq_payment_obligations_reference`. Diagnósticos ausentes, `23514` u otra
constraint propagan el `IntegrityError` original; el rollback continúa bajo
control del llamador. También se eliminó el whitespace final señalado.

Validación: focal 14/14; regresiones 82/82; gate PostgreSQL 13/13 sobre
`trax_payment_persistence_test_integrity_20260911`; suite completa 390
ejecutadas, 385 aprobadas, 5 omitidas, 0 fallos y 0 errores; `compileall` y head
único `20260911_02` aprobados. La base descartable se eliminó y se verificó
ausente. El `REQUIERE_CORRECCIONES` histórico se conserva y esta corrección
requiere retest independiente. No hubo commit, push, PR, merge ni deploy.

## Identidad PSP contextual - decisión implementada

Timestamp: 2026-09-11T22:26:39-03:00
Estado: COMPLETED
Resultado: PAYMENT_ATTEMPT_PSP_IDENTITY_IMPLEMENTADA_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/psp-event-processing`
HEAD/commit base: `f45f32ce3c032b6a4b7404886b9c2558cdb5e62a`
Estado Git: cambios locales sin staging, commit ni push

Se conserva el bloqueo histórico y se registra su resolución contractual:
proveedor, `psp_live_mode` e ID externo conforman la identidad PSP. La migración
`20260911_02` agrega los campos nullable, exige proveedor/modo juntos y aplica
unicidad parcial sólo con los tres valores presentes. No existe backfill; filas
anteriores permanecen legacy/unscoped.

Servicios: alta con contexto opcional, búsqueda contextual exacta, asociación
única y no reemplazable, canonicalización compartida de proveedor y exclusión
de intentos legacy. Los flujos neutrales existentes continúan sin contexto.

Validación: focal 23/23; regresiones 81/81; gate PostgreSQL 12/12 sobre
`trax_payment_persistence_test_pspidentity_20260911`; suite completa 389
ejecutadas, 384 aprobadas, 5 omitidas, 0 fallos y 0 errores. Pendientes del
cierre: `compileall`, head, whitespace, eliminación de la base y revisión
independiente. No se implementó el procesador ni integración productiva.

## Procesador de conciliacion de eventos PSP - bloqueo contractual

Timestamp: 2026-09-11T22:16:16-03:00
Estado: BLOCKED
Resultado: PSP_EVENT_RECONCILIATION_PROCESSOR_BLOQUEADO_POR_DEFINICION_DE_CORRELACION
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/psp-event-processing`
HEAD: `f45f32ce3c032b6a4b7404886b9c2558cdb5e62a`
Estado Git inicial: limpio y staging vacío
Estado Git final: tres documentos modificados sin staging, commit ni push

Diagnóstico: `psp_event_inbox` conserva proveedor, modo e ID externo del
recurso; `payment_attempts` sólo conserva `external_attempt_id`, sin proveedor,
modo ni unicidad sobre ese valor. Por ello no existe una clave que permita
correlacionar inequívocamente y una búsqueda global podría actualizar un pago
de otro proveedor o entorno.

Decisión pendiente: aprobar una identidad PSP completa en el intento y sus
reglas de unicidad/backfill, o aprobar una relación explícita evento-intento y
el mecanismo confiable que la crea. Hasta entonces no implementar el
procesador, no agregar una búsqueda global ni inferir la asociación. No hubo
cambios de código, migraciones o tests ejecutados; tampoco commit, push, PR,
merge ni deploy.

## Bandeja de eventos PSP - P1/P2 corregidos

Timestamp: 2026-09-11T20:57:36-03:00
Estado: COMPLETED
Resultado: PSP_EVENT_INBOX_FOUNDATION_CORREGIDA_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/psp-event-processing`
HEAD/commit base: `3b6bc44d0bddfa108b4b18e6d04e23f5c0b34fee`
Estado Git final: 14 cambios locales conocidos, staging vacio, sin commit ni push

La revision independiente historica `REQUIERE_CORRECCIONES` se preserva. Se
corrigieron P1 y P2 exclusivamente: `received_at` ya no integra la comparación
material de replay y la primera recepción permanece inmutable; el SHA-256 se
normaliza a minúsculas en el DTO. La misma regla fue comprobada en replay
secuencial y en recuperación concurrente PostgreSQL.

Validación: focal 11/11; regresiones 75/75; gate PostgreSQL 3/3 sobre
`trax_psp_event_test_retest_20260911`; suite completa 383 ejecutadas, 378
aprobadas, 5 omitidas, 0 fallos y 0 errores. `compileall`, head Alembic único,
whitespace y limpieza de la base se verifican en el cierre. Migración
`20260911_01` preservada sin cambios adicionales.

Pendiente: retest independiente antes del primer commit. No se implementaron
procesamiento financiero, payload crudo, firmas, HTTP, PSP real, workers,
relación con intentos, dependencias ni integración Git.

## Bandeja persistente de eventos PSP - primer incremento local

Timestamp: 2026-09-11T20:09:34-03:00
Estado: COMPLETED
Resultado: PSP_EVENT_INBOX_FOUNDATION_IMPLEMENTADA_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/psp-event-processing`
HEAD/commit base: `3b6bc44d0bddfa108b4b18e6d04e23f5c0b34fee`
Antecedente integrado: PR #11, feature `f10616c`, merge `3b6bc44`
Estado Git: cambios locales sin staging, commit ni push

Trabajo completado: contrato inmutable de evento neutral, modelo y servicio de
bandeja, migracion `20260911_01` descendiente de `20260910_01`, pruebas
portables y gate PostgreSQL. Replay identico converge; contenido distinto bajo
la misma identidad produce conflicto; eventos distintos del mismo recurso se
conservan. El helper no confirma transacciones ni llama proveedores.

Validacion: focal 9/9; regresiones 73/73; PostgreSQL 3/3 sobre
`trax_psp_event_test_foundation_20260911`; suite completa 381 ejecutadas, 376
aprobadas, 5 omitidas, 0 fallos y 0 errores. La base descartable fue eliminada
y su ausencia confirmada. `compileall`, head Alembic, enlaces y whitespace se
registran en el cierre final.

Limitaciones: no acredita autenticidad, recepción HTTP ni orden de entrega; no
guarda payload crudo, firmas o secretos y no interpreta estados financieros.
No se agregaron Mercado Pago, consultas externas, workers, créditos, PRO,
ARCA, interfaz ni dependencias. Es el primer incremento de una rama con dos
commits; falta revisión independiente y el segundo incremento antes de abrir
un único PR. No hubo commit, push, PR, merge ni deploy en esta sesión.

## Workflow persistente de pagos - semantica aprobada implementada

Timestamp: 2026-09-11T19:22:09-03:00
Estado: COMPLETED
Resultado: PERSISTENT_PAYMENT_WORKFLOW_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/persistent-payment-workflow`
HEAD/commit base: `dfbb7e3f53e61638eb52113286870eca1b59d031`
Estado Git inicial: seis cambios locales esperados, sin staging
Estado Git final: seis cambios locales sin staging, commit ni push

Definicion resuelta: la regla inicial que exigia `PENDING` ante incertidumbre
fue reemplazada despues de contrastarla con el esquema `20260910_01` y la
semantica del dominio. Una respuesta incierta queda con estado financiero
`NULL`, resultado `RECONCILIATION_REQUIRED`, conciliacion requerida e ID
externo opcional. `PENDING` se usa solo ante una respuesta autoritativa. La
conciliacion explicita puede resolver el estado desconocido a `PENDING`,
`APPROVED` o `REJECTED`.

Trabajo completado: se formalizo la regla en el workflow y se reforzaron las
pruebas portables y PostgreSQL, incluyendo observacion independiente de la
fila incierta, variantes con y sin ID, las tres transiciones autorizadas,
replay, conflictos y el limite de dos transacciones sin adaptador dentro de
ellas. No se creo ni modifico una migracion.

Validacion: workflow 13/13; focal mas regresiones 68/68; gate PostgreSQL 10/10
sobre `trax_payment_persistence_test_workflow_contract_20260911`; suite
completa 372 ejecutadas, 367 aprobadas, 5 omisiones historicas, 0 fallos y 0
errores; `compileall` aprobado; head Alembic unico `20260910_01`; enlaces
relativos y `git diff --check` aprobados. La base descartable quedo en cero
tablas, fue eliminada y su ausencia se confirmo.

Limitaciones y pendientes: revision independiente e integracion Git. No se
agregaron Mercado Pago, HTTP, webhooks, checkout, creditos, PRO, ARCA,
interfaz, dependencias ni procesamiento automatico. No hubo commit, push, PR,
merge ni deploy. Proximo paso: revision independiente de los seis archivos
locales; no integrar sin nueva autorizacion explicita.

## Workflow persistente de pagos - definicion requerida

Timestamp: 2026-09-11T19:09:43-03:00
Estado: BLOCKED
Resultado: PERSISTENT_PAYMENT_WORKFLOW_BLOQUEADO_POR_DEFINICION_DE_ESTADO_INCIERTO
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/persistent-payment-workflow`
HEAD/commit base: `dfbb7e3f53e61638eb52113286870eca1b59d031`
Estado Git inicial: limpio, staging vacio y `develop` sincronizado 0/0
Estado Git final: cambios locales sin staging, commit ni push

Trabajo completado: servicio `PersistentPaymentWorkflow`, pruebas portables y
extensiones del gate PostgreSQL. La obligacion se confirma antes de invocar al
adaptador; no existe sesion activa durante la llamada; el resultado se confirma
en otra transaccion. Replays terminales no llaman nuevamente, los conflictos
se detectan antes de la llamada, y los fallos posteriores pueden recuperarse
mediante la idempotencia neutral del adaptador. La conciliacion es explicita y
sin loops, cron o retries automaticos.

Validacion ejecutada: focal y regresiones 67/67; gate PostgreSQL 10/10 sobre
`trax_payment_persistence_test_workflow_20260911`; suite completa 371
ejecutadas, 366 aprobadas, 5 omisiones historicas, 0 fallos y 0 errores;
`compileall` aprobado; head Alembic unico `20260910_01`. La base descartable
quedo en cero tablas, fue eliminada y su ausencia se confirmo. Enlaces
relativos y `git diff --check`: aprobados en el control documental final.

Bloqueante: el paquete exige que una respuesta incierta se persista con
`financial_status=PENDING`, mientras el constraint integrado
`ck_payment_attempts_result_coherent` exige `financial_status IS NULL` para
`RECONCILIATION_REQUIRED`. Cumplir ambos es imposible con el esquema actual.
No se creo ni modifico una migracion. Se requiere decidir si se conserva
`NULL` como estado financiero desconocido o se autoriza una revisión de esquema
y contrato para representar `PENDING`.

No se modificaron rutas ni UI y no se incorporaron Mercado Pago, HTTP, SDK,
OAuth, webhooks, checkout, creditos, suscripciones, PRO, ARCA o deploy. No se
realizo commit, push, PR ni merge. Proximo paso: resolver exclusivamente la
representacion de incertidumbre y luego repetir la validacion afectada.

## Integracion y verificacion post-merge de persistencia neutral

Timestamp: 2026-09-11T15:46:40-03:00
Estado: COMPLETED
Resultado: PAYMENT_PERSISTENCE_FOUNDATION_INTEGRADA_Y_VERIFICADA_POST_MERGE
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama actual/destino: `develop`
Commit de caracteristica: `fae81e62f1526a0daa229f03efbc19c918dc8ff0`
Merge commit / HEAD local y remoto: `8dd773692004453d663742be02048f79cae0aa0c`
Pull Request integrado: `#10`
Archivos integrados: 14
Alembic head: `20260910_01`
Estado Git previo al registro: arbol limpio, staging vacio y divergencia 0/0

El PR fue fusionado antes de completar el gate final solicitado. Por esa
desviacion, Testing no pudo emitir una autorizacion preventiva de merge. La
verificacion post-merge comprobo que el contenido remoto integrado coincide
exactamente con el commit previamente probado y aprobado, sin diferencias de
alcance ni defectos funcionales detectados. Se decidio conservar la integracion
y no iniciar una reversion. La observacion corresponde al proceso y no
constituye una regresion del codigo.

Las pruebas no se repitieron despues del merge. Se conserva como evidencia
historica del commit probado: focal portable y regresiones 55/55; PostgreSQL
real 7/7; suite completa 359 ejecutadas, 354 aprobadas, 5 omisiones historicas,
0 fallos y 0 errores; `compileall`, enlaces y `git diff --check` aprobados. La
base PostgreSQL descartable fue eliminada y `trax_db` permanecio intacta.

Esta integracion no acredita Mercado Pago, pagos productivos, webhooks,
checkout, creditos, PRO, ARCA, deploy o la arquitectura general 2.0. Esta
actualizacion modifica unicamente los tres documentos autorizados y debe quedar
sin staging ni commit hasta su revision.

## Correccion P2 - clasificacion de violaciones de integridad

Timestamp: 2026-09-11T14:41:40-03:00
Estado: READY_TO_RESUME
Resultado: PAYMENT_PERSISTENCE_FOUNDATION_CORREGIDA_LOCALMENTE_PENDIENTE_DE_RETEST
Agente: Codex - implementador tecnico local
Dispositivo/origen: laptop / Codex Desktop local
Rama: `feature/payment-persistence-foundation`
HEAD/commit base: `c78c5176cf3c43cdbab673454fc6a625b1b3c0fa`
Estado Git: 14 cambios locales autorizados, sin staging, commit ni push
Revision independiente historica: `REQUIERE_CORRECCIONES`; se conserva como
evidencia del P2 y no se reemplaza por una aprobacion anticipada

Se ajusto unicamente `register_or_get_attempt()`: el camino de recuperación de
la carrera idempotente exige SQLSTATE `23505` y
`diag.constraint_name=uq_payment_attempts_idempotency_key`. Si el driver no
identifica ambos valores, o informa FK/check/otra constraint, el
`IntegrityError` se relanza intacto. El servicio mantiene `flush()`, savepoint
y transaccion superior controlada por el llamador, sin commits internos.

Validacion: focal 55/55; gate PostgreSQL real 7/7 sobre
`trax_payment_persistence_test_p2_20260911`; suite completa 359 ejecutadas, 354
aprobadas, 5 omisiones historicas, 0 fallos y 0 errores; `compileall` aprobado;
head Alembic unico `20260910_01`. La base descartable quedo en cero tablas, fue
eliminada y su ausencia se confirmo. Enlaces relativos y `git diff --check`:
aprobados en el control final.

No se modificaron esquema ni migracion. `trax_db`, Mercado Pago, PSP real,
webhooks, produccion y diseño general 2.0 no fueron acreditados. Proximo paso:
retest independiente del P2 y del paquete local completo. No ejecutar commit,
push, PR, merge o deploy sin autorizacion expresa.

## Persistencia neutral minima de pagos

Timestamp: 2026-09-11T14:00:30-03:00
Estado: READY_TO_RESUME
Resultado: PAYMENT_PERSISTENCE_FOUNDATION_IMPLEMENTADA_LOCALMENTE_PENDIENTE_DE_REVISION
Dispositivo/origen: laptop / Codex Desktop local
Agente: Codex - implementador tecnico local
Objetivo: persistir obligaciones e intentos ya producidos por el orquestador
neutral, con idempotencia, conciliacion y limites transaccionales explicitos
Rama: `feature/payment-persistence-foundation`
HEAD/commit base: `c78c5176cf3c43cdbab673454fc6a625b1b3c0fa`
Estado Git inicial: limpio; `develop` y `origin/develop` sincronizados
Estado Git final: cambios locales sin staging, commit ni push
Push, PR, merge y deploy: no realizados; no autorizados
Integracion previa: PR #9 integrado mediante
`c78c5176cf3c43cdbab673454fc6a625b1b3c0fa`

Trabajo completado:

- Modelos `PaymentObligation` y `PaymentAttemptRecord` registrados en el
  metadata de SQLAlchemy.
- Migracion `20260910_01` sobre `20260904_01`, con dos tablas, constraints e
  indice nombrados y downgrade inverso.
- Servicio de persistencia con sesion explicita, replay, conflicto,
  recuperacion y conciliacion; no ejecuta `commit()` ni llama al PSP.
- Pruebas portables y de migracion, prueba adversarial de la guarda y gate
  PostgreSQL real de concurrencia, visibilidad, locks, FK, rollback y
  recuperacion de sesion.

Validaciones:

- Focal portable mas regresiones PSP/orquestador: 55/55.
- Gate PostgreSQL: 6/6 sobre
  `trax_payment_persistence_test_20260911a`; ciclo
  upgrade/downgrade/upgrade aprobado, limpieza a cero tablas verificada y base
  eliminada con cero coincidencias posteriores.
- Suite completa Docker/SQLite aislada: 359 ejecutadas, 354 aprobadas, 5
  omisiones historicas, 0 fallos y 0 errores.
- `compileall`: aprobado. Head Alembic unico: `20260910_01`.
- Enlaces relativos y `git diff --check`: aprobados en la verificacion final.

No se modifico ni reseteo `trax_db`. No se implementaron llamadas PSP,
Mercado Pago, HTTP, SDK, OAuth, webhooks, checkout, interfaz persistente,
creditos, comisiones, suscripciones, PRO, ARCA o Enterprise. La coordinacion
durable alrededor de una llamada externa queda pendiente de otro incremento y
el diseño 2.0 permanece `PROPUESTO_NO_APROBADO`.

Proximo paso recomendado: revision independiente del diff local, incluida la
migracion y la evidencia PostgreSQL. No hacer commit, push, PR o merge sin una
autorizacion posterior expresa.

## Interfaz interna del simulador de pagos

Timestamp: 2026-09-10T21:46:04-03:00
Estado: READY_TO_RESUME
Resultado: PAYMENT_ORCHESTRATION_AND_SIMULATOR_UI_APROBADOS_PARA_COMMIT_Y_PR
Dispositivo/origen: laptop / Codex Desktop local
Agente: Codex - implementador tecnico y frontend local
Objetivo: permitir una inspeccion visual interna de una obligacion y de la
interpretacion neutral de la respuesta PSP simulada
Rama: `feature/payment-orchestration-in-memory`
HEAD/commit base observado: `a4951a27f0f0bef5fa834ad25159abfc875ec59e`
Estado Git inicial: limpio y sin staging; rama sin upstream remoto
Push, PR, merge y deploy: no realizados; no autorizados
Revision independiente: `APROBADO_PARA_SEGUNDO_COMMIT_Y_PR` del
`2026-09-10T22:02:38-03:00`; hallazgos P0-P3: ninguno

- Se agrego la ruta GET/POST `/dev/qa/payments/simulator` al blueprint `dev`.
  Reutiliza `_require_dev_qa_panel()`, solo existe en development/testing y
  exige `ENABLE_DEV_QA_PANEL`; deshabilitada o en produccion responde 404.
- Cada POST crea `ScenarioController`, `InMemoryPSPSimulator` y
  `InMemoryPaymentOrchestrator` nuevos. La seleccion artificial queda en la
  ruta de desarrollo; no se modificaron `PSPAdapter`, el orquestador ni el
  simulador ya versionados.
- La pantalla server-rendered usa `Decimal`, conserva entradas ante error y
  presenta aprobado, rechazado, pendiente e incertidumbre como conciliacion
  requerida. No expone excepciones, inventa IDs o conserva historial.
- Se usaron componentes `.trax-*`, tokens `--trax-ds-*`, etiquetas,
  `fieldset`/`legend`, errores textuales, foco visible y `aria-live`; no se
  agrego JavaScript ni dependencia.

Archivos creados: `app/templates/dev_payment_simulator.html`,
`app/static/css/dev-payment-simulator.css` y
`tests/test_dev_payment_simulator.py`. Archivos modificados:
`app/routes/dev_routes.py`, `docs/CHANGELOG.md`, este handoff y
`docs/SPRINTS/2026-09-06_PRO_REFINAMIENTO_COMERCIAL_Y_PSP.md`.
Migraciones y dependencias: ninguna.

Validaciones finales informadas por la revision independiente: interfaz +
orquestador 29/29; contrato/simulador 24/24; suite completa 347 ejecutadas,
342 aprobadas, 5 omisiones historicas, 0 fallos y 0 errores. `compileall`,
HTML, enlaces y `git diff --check`: aprobados. QA visual aprobada en temas
claro/oscuro, movil/desktop y teclado. PostgreSQL no se ejecuto porque no
aplica.

Limitaciones: interfaz interna de desarrollo, un procesamiento aislado por
envio, sin persistencia, historial, polling o conciliacion automatica. No
acredita checkout, pagos reales, viabilidad PSP, HTTP, SDK, OAuth, webhooks,
creditos, reservas, suscripciones, PRO, Mercado Pago o ARCA. El diseño general
2.0 permanece `PROPUESTO_NO_APROBADO`; Mercado Pago y la revision
juridica/contable continuan pendientes.

Proximo paso: preparar el segundo commit y un unico PR solo con autorizacion
expresa posterior. Esta aprobacion documental no autoriza staging, commit,
push, PR, merge o deploy.

## Orquestacion neutral de pagos implementada localmente

Timestamp: 2026-09-10T21:23:10-03:00
Estado: READY_TO_RESUME
Resultado: PAYMENT_ORCHESTRATION_IN_MEMORY_IMPLEMENTADA_LOCALMENTE_PENDIENTE_DE_REVISION
Dispositivo/origen: laptop / Codex Desktop local
Agente: Codex - implementador tecnico local
Objetivo: traducir una obligacion monetaria y la respuesta de `PSPAdapter` a
un resultado neutral, inmutable y conciliable para MANDOBRA
Rama: `feature/payment-orchestration-in-memory`
Commit base: `e7ec86f217ebbbd836f7434092041e6abefbbe4a`
Estado Git inicial: limpio, staging vacio y `develop` sincronizado 0/0 con
`origin/develop`
Push, PR, merge y deploy: no realizados; no autorizados

- Se creo `app/services/payment_orchestration.py` con `PaymentObligation`,
  `PaymentOrchestrationResult`, cuatro resultados diferenciados y el servicio
  `InMemoryPaymentOrchestrator`.
- La creacion delega una sola vez en el contrato neutral. Aprobacion, rechazo y
  pendiente conservan el estado financiero; la incertidumbre produce
  `RECONCILIATION_REQUIRED` y puede conservar un ID o `None`.
- La conciliacion es una accion unica y explicita: consulta por ID cuando
  existe o repite la misma solicitud idempotente cuando no existe. Una nueva
  incertidumbre permanece conciliable. No se inventan IDs ni se ejecutan
  reintentos, temporizadores o bucles.
- La solicitud exige `Decimal` positivo y finito, rechaza `float`, cero,
  negativos, `NaN` e infinitos, y no cuantiza ni redondea.
- Los errores de no encontrado e idempotencia permanecen diferenciados desde
  el contrato; la solicitud invalida usa un error propio y neutral.

Archivos creados: `app/services/payment_orchestration.py` y
`tests/test_payment_orchestration.py`. Documentacion modificada:
`docs/CHANGELOG.md`, este handoff y
`docs/SPRINTS/2026-09-06_PRO_REFINAMIENTO_COMERCIAL_Y_PSP.md`.
Migraciones y dependencias: ninguna.

Validaciones: focal del orquestador 19/19; focal PSP 24/24; suite completa
Docker 337 ejecutadas, 332 aprobadas, 5 omitidas, 0 fallos y 0 errores;
`compileall` aprobado. PostgreSQL no se ejecuto porque no aplica al incremento
en memoria. Se observaron solo advertencias legacy/deprecaciones preexistentes
y el contenedor huerfano `trax-pro-contrast-qa`, que no fue eliminado.

Limitaciones: no acredita persistencia, concurrencia o atomicidad PostgreSQL,
autenticidad u orden de webhooks ni viabilidad tecnica, contractual o
comercial de un PSP. No conecta Mercado Pago, ARCA, HTTP, SDK, rutas, creditos,
reservas, suscripciones, PRO o flujos productivos. El diseño 2.0 permanece
`PROPUESTO_NO_APROBADO`; Mercado Pago y la revision juridica/contable siguen
pendientes.

Proximo paso recomendado: revision independiente del diff local. No hacer
staging, commit, push, PR, merge, rebase, deploy ni iniciar otro incremento sin
autorizacion expresa.

## Validacion local post-merge de PR #8

Timestamp: 2026-09-10T13:42:55-03:00
Estado: COMPLETED
Resultado: PSP_ADAPTER_CONTRACT_INTEGRADO_POST_MERGE_VALIDADO_LOCALMENTE_PENDIENTE_DE_REVISION_DOCUMENTAL
Dispositivo/origen: laptop / Codex Desktop local
Agente: Codex - implementador tecnico local
Objetivo: validar localmente el contrato neutral PSP despues de su integracion
Rama: `develop`
Base previa: `2e7de49dfde6c20bc798089139ea235534ea0a75`
PR: #8
Merge/HEAD: `f9c0e394af413cfcb0c1aa8142a85af16ad3729b`
Segundo padre: `8f709e64149d7dfbdeb9c2e1a319f7134ae6f0f4`
Estado remoto: `origin/develop` coincide con el merge validado
Integracion Git de esta sesion: no realizada; no autorizada

- Se confirmaron ubicacion, remoto, rama, HEAD, upstream, ausencia de
  divergencia y parentesco del merge. El staging permanecio vacio.
- Alcance validado: `PSPAdapter` neutral, intento inmutable, estados y errores
  neutrales diferenciados, ID opcional ante incertidumbre, simulador en
  memoria determinista, controlador FIFO, idempotencia y recuperacion por
  consulta.
- Pruebas focales: 24 ejecutadas y aprobadas, 0 fallos, 0 errores y 0
  omisiones. Suite completa Docker: 318 ejecutadas, 313 aprobadas, 5 omitidas,
  0 fallos y 0 errores. `compileall`, enlaces relativos y `git diff --check`:
  aprobados.
- PostgreSQL no se ejecuto y no aplica a este incremento. No hubo migraciones,
  cambios de dependencias ni modificaciones de codigo durante esta sesion.
- Limitaciones: la evidencia no acredita persistencia, concurrencia o
  atomicidad PostgreSQL, autenticidad u orden de webhooks ni viabilidad
  tecnica, contractual o comercial de un PSP. No conecta Mercado Pago, ARCA,
  HTTP, SDK o flujos productivos.
- El diseño general 2.0 permanece `PROPUESTO_NO_APROBADO`; Mercado Pago y la
  revision juridica/contable continuan pendientes.

Cambios sin commit: este handoff, `docs/CHANGELOG.md` y
`docs/SPRINTS/2026-09-06_PRO_REFINAMIENTO_COMERCIAL_Y_PSP.md`, exclusivamente
documentales y sin staging. Tests no ejecutados: PostgreSQL, por no aplicar.
Errores conocidos: ninguno del incremento; se observaron advertencias legacy
y deprecaciones no bloqueantes ya existentes durante la suite.

Proximo paso recomendado: revision independiente del diff documental y, solo
con autorizacion posterior, su integracion. No hacer staging, commit, push,
PR, merge, rebase, deploy ni eliminar ramas como parte de este handoff.

## Correccion P2 de determinismo en PR #8

Timestamp: 2026-09-09T20:42:09-03:00
Estado: READY_TO_RESUME
Resultado: PSP_ADAPTER_CONTRACT_P2_CORREGIDO_PR_ACTUALIZADO_PENDIENTE_DE_RETEST
Dispositivo/origen: laptop / Codex Desktop local
Agente: Codex - implementador tecnico local
Rama: `feature/psp-adapter-contract`
PR: #8
Commit observado: `64eed3fdbf16ff55f7994b246a87b514a41a31bb`

- Hallazgo P2: una cola vacia fallaba despues de invocar `id_factory` y
  `clock`, por lo que dependencias con estado podian avanzar sin creacion.
- Correccion: `ScenarioController` permite inspeccionar sin consumir; la
  creacion valida primero la existencia del escenario, luego ID y reloj, y
  consume exactamente un escenario inmediatamente antes de almacenar.
- ID duplicado, reloj invalido, validacion, replay, conflicto y consulta no
  consumen escenarios.
- Focal: 24/24. Suite completa Docker: 318/318 ejecutadas, 313 aprobadas,
  5 omisiones historicas, 0 fallos y 0 errores. `compileall`, enlaces relativos
  y `git diff --check`: aprobados.
- PostgreSQL no aplica. No se agregaron persistencia, locks, capas, modelos,
  migraciones ni integraciones productivas.
- PR #8 permanece abierto y no esta aprobado para merge; requiere retest
  independiente despues del nuevo commit y push autorizados.

## Retest independiente aprobado para commit

Timestamp: 2026-09-09T20:23:34-03:00
Estado: READY_TO_RESUME
Resultado: PSP_ADAPTER_CONTRACT_APROBADO_PARA_COMMIT
Agente: Codex - ejecutor de integracion autorizado
Rama: `feature/psp-adapter-contract`
Commit base: `2e7de49dfde6c20bc798089139ea235534ea0a75`
Retest independiente: `APROBADO_PARA_COMMIT` del
`2026-09-09T20:14:06-03:00`

- P1 y P3: `RESUELTO`; hallazgos actuales P0-P3: ninguno.
- Focal 22/22; suite completa 311/316, con 5 omisiones historicas,
  0 fallos y 0 errores.
- `compileall`, enlaces relativos y `git diff --check`: aprobados.
- PostgreSQL no se ejecuto ni se acredita; no aplica al incremento en memoria.
- Estado Git al registrar el retest: seis archivos locales, staging vacio,
  sin commit, push o PR todavia.
- Permanecen fuera de alcance persistencia, webhooks, Mercado Pago, ARCA e
  integracion productiva. El diseño general 2.0 continua
  `PROPUESTO_NO_APROBADO`.

## Correcciones posteriores a revision independiente

Timestamp: 2026-09-09T20:01:57-03:00
Estado: READY_TO_RESUME
Resultado: PSP_ADAPTER_CONTRACT_CORREGIDO_LOCALMENTE_PENDIENTE_DE_RETEST
Dispositivo/origen: laptop / Codex Desktop local
Agente: 02 - Implementacion - Builder
Rama: `feature/psp-adapter-contract`
Commit base: `2e7de49dfde6c20bc798089139ea235534ea0a75`
Revision recibida: `REQUIERE_CORRECCIONES` del
`2026-09-09T19:53:36-03:00`, con P1 contractual y P3 de cobertura

- P1: `UncertainResponseError` admite omitir `attempt_id`; la ausencia se
  representa con `None`, un ID conocido debe ser cadena no vacia y se conserva
  sin normalizar. El simulador adjunta su ID conocido; un proveedor real puede
  no tenerlo y la conciliacion conserva la clave idempotente del llamador.
- P3: la proteccion de dependencias inspecciona imports mediante AST en ambos
  modulos; las cinco reexportaciones historicas se validan por identidad; se
  cubrieron orden, rechazo atomico y aislamiento de `enqueue`, y diferenciacion
  observable de los tres errores neutrales.
- Focal: 22/22 aprobadas. Suite completa Docker: 311/316 aprobadas, 5 omisiones
  historicas, 0 fallos y 0 errores. `compileall`, enlaces relativos y
  `git diff --check`: aprobados. Gates PostgreSQL: no ejecutados; no aplican al
  incremento en memoria.
- Estado Git: seis archivos locales, staging vacio, sin commit ni push.
- Limitaciones: sin persistencia, garantias PostgreSQL, HTTP, SDK, webhooks,
  Mercado Pago, ARCA o integracion productiva. El diseño 2.0 continua
  `PROPUESTO_NO_APROBADO`; revision juridica/contable pendiente.

Proximo paso: retest independiente focal. No declarar aprobado ni ejecutar
staging, commit, push, PR, merge, rebase o deploy sin autorizacion.

## Incremento 2.0-B implementado localmente

Timestamp: 2026-09-08T23:01:15-03:00
Estado: READY_TO_RESUME
Resultado: PSP_ADAPTER_CONTRACT_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Dispositivo/origen: laptop / Codex Desktop local
Agente: 02 - Implementacion - Builder
Objetivo: separar el contrato PSP neutral de la configuracion artificial de
escenarios del simulador.
Rama: `feature/psp-adapter-contract`
Commit base: `2e7de49dfde6c20bc798089139ea235534ea0a75`
Estado Git inicial: limpio y sincronizado con `origin/develop`
Estado Git final: cambios locales sin staging ni commit
Push, PR, merge y deploy: no realizados; no autorizados

- Se creo `app/services/psp_contract.py` como autoridad unica del `Protocol`,
  DTO inmutable, estados financieros y errores neutrales.
- `InMemoryPSPSimulator.create_attempt` conserva solo referencia, `Decimal`,
  moneda y clave idempotente. `ScenarioController` configura por separado una
  secuencia FIFO determinista y aislada por instancia.
- Nuevas operaciones consumen un escenario; replay, conflictos y validaciones
  no lo consumen. La falta de escenario falla antes de almacenar estado.
- En el simulador, la incertidumbre crea un solo intento `PENDING`, adjunta el
  identificador que conoce y permite consulta y replay sin repetir el error ni
  consumir otro escenario. El contrato neutral admite que otro adaptador no
  conozca el ID y lo represente con `None`.
- Compatibilidad: el simulador reexporta los nombres historicos del estado y
  DTO, referenciando las definiciones neutrales sin duplicarlas.

Archivos modificados: `app/services/psp_simulator.py`,
`tests/test_psp_simulator.py`, `docs/CHANGELOG.md`, este handoff y
`docs/SPRINTS/2026-09-06_PRO_REFINAMIENTO_COMERCIAL_Y_PSP.md`. Archivo creado:
`app/services/psp_contract.py`. Migraciones y dependencias: ninguna.

Validaciones: focal 17/17; suite completa Docker 306/311, con 5 omisiones
historicas, 0 fallos y 0 errores; `compileall`, enlaces relativos y
`git diff --check` aprobados. PostgreSQL gates no ejecutados porque el
incremento permanece exclusivamente en memoria.

Limitaciones: no acredita persistencia, concurrencia o atomicidad PostgreSQL,
autenticidad de webhooks ni viabilidad PSP. No conecta Mercado Pago o ARCA ni
flujos productivos. El diseño 2.0 continua `PROPUESTO_NO_APROBADO` y la revision
juridica/contable sigue pendiente.

Proximo paso: revision independiente del diff de los seis archivos. No hacer
staging, commit, push, PR, merge, rebase, deploy ni iniciar obligaciones de
pago sin autorizacion expresa.

---

# Handoff tecnico: simulador PSP determinista en memoria

## Integracion confirmada

Timestamp: 2026-09-08T22:40:33-03:00
Estado: COMPLETED
Resultado: SIMULADOR_PSP_EN_MEMORIA_INTEGRADO
Agente: Codex - ejecutor de integracion autorizado
Rama: `develop`
Commit del simulador: `50babd206369d47d68765e0dbf0fd3f2f42c21d0`
Push: normal a `origin/develop`, confirmado
Hash remoto observado: `50babd206369d47d68765e0dbf0fd3f2f42c21d0`

- Validaciones: focal 21/21; suite completa 310/315, con 5 omisiones
  historicas, 0 fallos y 0 errores; `compileall`, enlaces relativos y
  `git diff --check` aprobados.
- Integrado refiere solo al componente aislado en memoria y sus pruebas. No se
  conecto a rutas, servicios ni flujos productivos.
- No se acreditan persistencia, concurrencia o atomicidad PostgreSQL,
  autenticidad de webhooks ni viabilidad PSP.
- El diseño general 2.0 continua `PROPUESTO_NO_APROBADO`. Mercado Pago, ARCA y
  revision juridica/contable permanecen pendientes.
- Merge, rebase, force push y deploy: no realizados.

## Aprobacion independiente previa a integracion

Timestamp: 2026-09-08T22:37:42-03:00
Estado: READY_TO_RESUME
Resultado: SIMULADOR_PSP_EN_MEMORIA_APROBADO_PARA_COMMIT
Agente: Codex - revisor tecnico y funcional independiente
Rama y commit base: `develop` en
`1e85c6e592f970b2640a1e71d5b9a7019f8b3383`

- Revision independiente emitida el `2026-09-08T22:28:13-03:00`:
  `APROBADO_PARA_COMMIT`, sin hallazgos P0-P3.
- Focal: 21/21 aprobadas. Suite completa en Docker: 310/315 aprobadas,
  5 omisiones historicas, 0 fallos y 0 errores.
- `compileall`, enlaces relativos y `git diff --check`: aprobados.
- La evidencia no acredita persistencia, concurrencia o atomicidad PostgreSQL,
  autenticidad de webhooks ni viabilidad de Mercado Pago, y no implementa o
  valida ARCA.
- El simulador permanece aislado de flujos productivos. El diseño general 2.0
  continua `PROPUESTO_NO_APROBADO`; Mercado Pago y la revision
  juridica/contable siguen pendientes.
- Estado Git: cinco archivos locales, sin staging ni commit al registrar esta
  aprobacion. Push, merge y deploy: no realizados.

Timestamp: 2026-09-07T22:40:12-03:00
Estado: READY_TO_RESUME
Resultado: SIMULADOR_PSP_EN_MEMORIA_IMPLEMENTADO_LOCALMENTE_PENDIENTE_DE_REVISION
Dispositivo/origen: laptop / Codex Desktop local
Agente: 02 - Implementacion - Builder
Objetivo: implementar exclusivamente un simulador PSP determinista, aislado y
en memoria para probar el contrato basico sin integracion productiva.
Rama y commit base: `develop` en
`1e85c6e592f970b2640a1e71d5b9a7019f8b3383`
Estado Git inicial: limpio y sin divergencia informada
Estado Git final: cambios locales sin staging ni commit
Push, PR, merge y deploy: NO realizados; no autorizados

## Reanudacion y revalidacion

Timestamp: 2026-09-08T21:46:39-03:00

- Los cinco archivos locales fueron reconocidos expresamente como trabajo
  previo esperado y se inspeccionaron completos.
- El simulador y sus 21 pruebas ya satisfacian el alcance; no se modifico su
  comportamiento.
- Focal repetida: 21 aprobadas, 0 fallidas y 0 omitidas.
- Suite completa repetida: 54 descubiertas, 21 aprobadas, 0 fallos de asercion,
  33 errores de importacion y 0 omitidas por dependencias ausentes.
- `compileall`, enlaces relativos y `git diff --check`: aprobados. El estado
  Git final conserva exclusivamente los cinco archivos esperados.

## Trabajo completado

- Se creo `app/services/psp_simulator.py` con almacenamiento privado por
  instancia, DTO inmutable, identificadores y reloj inyectados, estados
  `APPROVED`, `REJECTED` y `PENDING`, y resultado de llamada `UNCERTAIN`.
- La incertidumbre de transporte crea internamente un intento `PENDING`, eleva
  una excepcion especifica y permite recuperarlo mediante replay idempotente.
- La huella canonica compara referencia recortada, valor numerico exacto
  `Decimal` y moneda recortada en mayusculas. No cuantiza ni redondea.
- Se distinguen errores de no encontrado, conflicto idempotente, respuesta
  incierta y configuracion invalida.
- Los resultados devueltos son inmutables y no existe estado global mutable.

## Validacion y limitacion

- Focal `tests.test_psp_simulator`: 21/21 aprobadas; 0 fallidas; 0 omitidas.
- Suite completa: 54 descubiertas; 21 aprobadas; 0 fallos de asercion; 33
  errores de importacion; 0 omitidas.
- Limitacion de entorno: Python 3.12.14 de Codex Desktop no contiene Flask,
  SQLAlchemy, Alembic ni Werkzeug. No se instalaron dependencias y, por la
  exclusion del incremento, no se uso Docker.
- `python -m compileall -q app scripts tests`: aprobado.
- Enlaces relativos y `git diff --check`: aprobados.
- Queda pendiente repetir la suite en un runtime del proyecto con dependencias
  disponibles.

## Limites

El simulador no acredita persistencia, atomicidad o concurrencia PostgreSQL,
autenticidad, entrega u orden de webhooks, ni viabilidad tecnica, contractual o
comercial de Mercado Pago. No selecciona proveedor o arquitectura productiva y
no se conecta con ningun flujo operativo.

Archivos creados: `app/services/psp_simulator.py` y
`tests/test_psp_simulator.py`. Documentacion modificada:
`docs/CHANGELOG.md`, `docs/HANDOFFS/ACTIVE_HANDOFF.md` y
`docs/SPRINTS/2026-09-06_PRO_REFINAMIENTO_COMERCIAL_Y_PSP.md`.

Proximo paso: revisar el diff; para cerrar la validacion completa, repetir la
suite en un runtime ya configurado con las dependencias del proyecto. No
instalar, integrar ni publicar sin autorizacion.

---

# Handoff tecnico: cierre documental Sprint 1 PRO

Timestamp: 2026-09-07T21:54:36-03:00
Estado: COMPLETED
Resultado: CERRADO_DOCUMENTALMENTE_INTEGRACION_GIT_PENDIENTE
Dispositivo/origen: laptop / Codex Desktop local
Agente: 01 - Documentation Engineer
Objetivo: registrar el resultado de la revision independiente y cerrar el
alcance documental de Sprint 1.
Rama y ultimo commit observados: `develop` en
`1d22f87adc358eae20121ea727142b0276cf337e`
Estado Git: cuatro Markdown modificados, sin staging ni commit
Push, nuevo PR, merge y deploy: NO realizados; no autorizados

- El Agente 02 informo el `2026-09-07T21:41:54-03:00`: sin hallazgos, diff
  `APROBADO_PARA_COMMIT` y criterios documentales de cierre satisfechos.
- Sprint 1 queda `CERRADO_DOCUMENTALMENTE`; la integracion Git del presente
  registro permanece pendiente.
- Mercado Pago, revision juridica/contable y aclaracion de la estimacion de
  25-43 horas siguen pendientes y bloquean solo capacidades dependientes.
- El diseño 2.0 sigue `PROPUESTO_NO_APROBADO` y no autoriza implementacion.
- La ausencia de reviews nativas de GitHub permanece atribuida al informe
  disponible; no fue verificada de forma independiente en esta sesion.

Archivos modificados: `docs/HANDOFFS/ACTIVE_HANDOFF.md`, `docs/CHANGELOG.md`,
`docs/ROADMAP.md` y
`docs/SPRINTS/2026-09-06_PRO_REFINAMIENTO_COMERCIAL_Y_PSP.md`.

Tests de aplicacion: NO EJECUTADOS; alcance exclusivamente documental.
Validaciones: coherencia de estados, enlaces relativos y `git diff --check`.
Proximo paso: solicitar autorizacion separada para staging y commit del paquete.
No iniciar implementacion ni ejecutar push, PR, merge, deploy o cambios de rama.

---

# Handoff tecnico: preparacion de cierre documental Sprint 1 PRO

Timestamp: 2026-09-07T21:31:53-03:00
Estado: READY_TO_RESUME
Resultado: LISTO_PARA_REVISION_DE_DIFF
Dispositivo/origen: laptop / Codex Desktop local
Agente: 01 - Documentation Engineer
Objetivo: actualizar la trazabilidad posterior al merge de PR #7, incorporar
observaciones propuestas del diseño 2.0 y preparar la matriz de cierre.
Rama y ultimo commit observados: `develop` en
`1d22f87adc358eae20121ea727142b0276cf337e`
Estado Git inicial: limpio y sincronizado con `origin/develop` segun referencias
locales
Estado Git final esperado: cambios sin commit exclusivamente Markdown bajo
`docs/`
Push, nuevo PR, merge y deploy: NO realizados; no autorizados

## Estado anterior superado

Los bloques del `2026-09-06T19:38:40-03:00` y
`2026-09-06T19:22:08-03:00` describen correctamente el estado anterior al
commit y al merge. Quedan preservados como historia, pero fueron superados por
la integracion de PR #7.

## Evidencia recuperada

- Commit documental: `817fb4f3888a44984b951badc655eceeec2b9df8`.
- PR: #7, rama origen `docs/pro-commercial-psp-refinement`, destino `develop`.
- Merge: `1d22f87adc358eae20121ea727142b0276cf337e`, fechado
  `2026-09-06T20:11:47-03:00`; Git local confirma que contiene el commit.
- La revision focalizada anterior informo `APROBADO_PARA_COMMIT` en la
  conversacion. No fue una review nativa de GitHub.
- El informe del Agente 02 del `2026-09-07T20:59:03-03:00` registro cero
  reviews nativas en PR #7 y mantuvo pendiente el cierre documental.
- No existe una regla vigente que obligue a inventar o exigir retroactivamente
  una review nativa para registrar el merge.

## Trabajo completado en esta sesion

- Se actualizo Changelog, Roadmap y el documento del ciclo con el estado real
  post-merge.
- Se separaron pendientes, bloqueos por capacidad y responsables propuestos;
  ninguna propuesta se presenta como asignacion aceptada.
- Se incorporaron como `PROPUESTO_NO_APROBADO` las correcciones al diseño 2.0:
  pago mixto separado de cobertura total con creditos; confirmacion interna
  atomica para diferencia cero; unicidad por obligacion/periodo e importe; y
  consumo parcial de lotes preservando saldo y vencimiento.
- El rango de 25-43 horas quedo pendiente de aclarar como total o restante y
  de mapear a entregables, sin inventar una estimacion.
- Se preparo la matriz de criterios de cierre. El resultado no es una
  aprobacion ni un cierre automatico.

## Pendientes, bloqueantes y responsables propuestos

- Revision del diff documental actual: pendiente; proximo gate del Sprint 1.
- MP-01 a MP-16: sin enviar y sin respuesta. Bloquean las capacidades PSP que
  dependen de cada pregunta, no el contrato conceptual completo. Responsable
  propuesto: responsable tecnico MANDOBRA para coordinar; Mercado Pago para
  responder. No constituye asignacion aceptada.
- Revision juridica/contable: sin dictamen. Bloquea consentimiento, presentacion
  economica, reversas, comisiones y definiciones fiscales relacionadas.
  Responsable propuesto: producto para coordinar especialistas por designar.
- Producto/economia: precio, base y porcentaje, conversion, moneda, redondeo,
  impuestos, reservas y eventos tardios. Responsable propuesto: Cristian
  Sánchez/producto con contabilidad; asignacion no aceptada formalmente.
- Arquitectura 2.0 y ADR: pendientes de revision y aprobacion expresa. No se
  aprobaron modelos, constraints, SDK, endpoints, migraciones ni proveedor.
- Facturacion opcional permanece separada de contratacion y cobro; su evaluacion
  fiscal es un incremento propio.

## Archivos, validaciones y restricciones

Archivos modificados: `docs/HANDOFFS/ACTIVE_HANDOFF.md`, `docs/CHANGELOG.md`,
`docs/ROADMAP.md` y
`docs/SPRINTS/2026-09-06_PRO_REFINAMIENTO_COMERCIAL_Y_PSP.md`.

Migraciones relacionadas: ninguna. Tests de aplicacion: NO EJECUTADOS; no
aplican al alcance documental. La validacion final debe comprobar alcance,
whitespace, enlaces y coherencia de estados.

Proximo paso exacto: realizar una revision independiente del diff documental y
de la matriz de cierre. Solo despues de un resultado explicito decidir si el
Sprint 1 puede marcarse `APROBADO` o `CERRADO`.

No iniciar implementacion, aprobar arquitectura 2.0, contactar terceros,
instalar dependencias, modificar codigo/modelos/bases/configuracion, ni ejecutar
commit, push, PR, merge, rebase, reset, clean, cambio de rama o deploy.

---

# Handoff tecnico: correcciones posteriores a revision focalizada PRO

Timestamp: 2026-09-06T19:38:40-03:00
Estado: READY_TO_RESUME
Resultado del ciclo: CORRECCIONES_DOCUMENTALES_LISTAS_PARA_REVISION_FOCALIZADA
Dispositivo/origen: laptop / Codex Desktop local
Agente: 01 - Documentation Engineer
Objetivo: corregir cuatro hallazgos P1 y dos P2 sin ampliar el alcance del
paquete documental.
Rama: `docs/pro-commercial-psp-refinement`
Commit base y ultimo commit observado: `1548935`
Estado Git: paquete Markdown bajo `docs/` sin commit
Push, PR y merge: NO realizados; no autorizados

## Correcciones realizadas

- REQ-001 diferencia origen del trabajo y canal de pago: trabajos externos
  cobrados mediante MANDOBRA pueden generar creditos; efectivo y pagos fuera
  de MANDOBRA no los generan.
- Reserva aprobada: indisponibilidad sin consumo, consumo solo tras pago
  completo, liberacion definitiva con vencimiento original, no reactivacion de
  creditos vencidos y conciliacion de estados inciertos/reintentos.
- Tarjeta vinculada requerida comercialmente aun con creditos completos, con
  viabilidad pendiente y separacion respecto de autorizacion de debito/datos.
- Switch definido como preferencia/autorizacion sincronizada con el PSP; el
  sistema previene duplicados sin imponer al usuario una antelacion desconocida.
- Se agregaron precio, cargo y total previos, neto profesional estimado,
  obligacion unica en contratos internos y efectivo configurable sin creditos.
- Se incorporaron criterios de aceptacion verificables para esas reglas.
- Master Spec enumera las capacidades comerciales realmente pendientes y deja
  la extension de 60 dias solo como antecedente historico reemplazado.

## Estado y pendientes

- La nueva correccion NO esta aprobada: requiere revision focalizada antes de
  commit o transferencia operativa al Agente 02.
- Permanecen pendientes plazo de reserva, acreditaciones tardias, precio,
  porcentaje/base, costos, impuestos, reversas, antelacion, viabilidad PSP y
  validacion juridica/contable.
- No se aprobaron arquitectura, modelos, migraciones, proveedor o SDK nuevos.
- Tests de aplicacion: NO EJECUTADOS - alcance documental.
- No se modificaron codigo, configuracion, bases ni dependencias.

Proximo paso: revisar focalmente REQ-001, Master Spec, Changelog y este handoff;
si el resultado es aprobado, solicitar autorizacion separada para commit. No
iniciar implementacion ni contactos externos.

---

# Handoff tecnico: refinamiento documental comercial PRO y PSP

Timestamp: 2026-09-06T19:22:08-03:00
Estado: COMPLETED
Resultado del ciclo: DOCUMENTACION_CONSOLIDADA_LISTA_PARA_REVISION_Y_AGENTE_02
Dispositivo/origen: laptop / Codex Desktop local
Agente: 01 - Documentation Engineer
Objetivo: consolidar reglas comerciales PRO, corregir contradicciones,
incorporar expedientes juridico/contable y Mercado Pago, actualizar
planificacion, enlaces y cierre post-merge.
Rama: `docs/pro-commercial-psp-refinement`
Commit base y ultimo commit observado: `1548935`
Estado Git inicial: limpio
Estado Git final: cambios Markdown bajo `docs/` sin commit
Push a GitHub: NO realizado
PR: NO creado
Merge: NO; tarea documental local sin autorizacion de publicacion

## Trabajo completado

- PR #5 y PRO Entitlement Foundation quedaron registrados como integrados en
  `develop` mediante merge `1548935`, con resultado informado
  `APROBADO_POST_MERGE` y evidencia 294/289/0/5.
- REQ-001 conserva implementacion parcial y reemplaza la regla historica de 60
  dias por creditos, umbral y periodos transaccionales de 30 dias.
- Se separaron decisiones aprobadas, propuestas juridico-operativas y
  pendientes de producto/proveedor.
- Se incorporaron los expedientes de Mercado Pago y revision juridica/contable
  como borradores no enviados.
- Se alinearon REQ-002, Master Spec, indices, Roadmap, Backlog, arquitectura,
  Changelog y documentos de sprint.

## Pendientes y bloqueantes

- Revision humana del diff documental y aprobacion antes de commit/publicacion.
- MP-01 a MP-16: todas pendientes; no se contacto a Mercado Pago.
- Revision juridica y contable: pendiente; el expediente no es dictamen.
- Producto: precio, porcentaje/base, conversion de creditos, reversas, reservas,
  aprobaciones tardias, cambios de precio, consentimiento y beneficios finales.
- Arquitectura: ADR PSP/eventos, ledger/compensaciones, concurrencia, secretos y
  observabilidad, posteriores a viabilidad y decisiones aprobadas.
- Facturacion: evaluacion directa/proveedor pendiente; implementacion separada.

## Validacion y alcance

- Archivos modificados: exclusivamente Markdown bajo `docs/`.
- Tests de aplicacion: NO EJECUTADOS - no aplican al alcance documental.
- Migraciones, bases, Docker, dependencias y contactos externos: NO ejecutados.
- Commit, push, PR, merge y deploy: NO ejecutados.
- `git diff --check`: PASS. Enlaces relativos de los archivos modificados y
  nuevos: destinos existentes. El checker general solo detecto el placeholder
  historico `../TROUBLESHOOTING/archivo.md` de la plantilla de handoff, fuera
  del alcance y no introducido por este ciclo.

## Proximo paso recomendado

Transferir a Agente 02 un encargo exclusivamente de evaluacion y preparacion:
mapa de brechas, viabilidad separada marketplace/suscripcion, comparacion
ARCA/proveedores, slicing de sprints 2 y 3, estrategia de pruebas, estimaciones
y decisiones previas a codigo. No implementar ni contactar terceros sin nueva
autorizacion.

Para retomar: confirmar rama, HEAD y estado; revisar primero este bloque, el
[plan del ciclo](../SPRINTS/2026-09-06_PRO_REFINAMIENTO_COMERCIAL_Y_PSP.md),
[REQ-001](../REQUISITOS/REQ-001-activacion-y-vigencia-pro.md),
[consultas PSP](../CONSULTAS/MERCADO_PAGO_v0_1.md) y
[base juridica](../LEGAL/BASE_REVISION_JURIDICA_v0_2.md).

No ejecutar implementacion, tests, migraciones, contacto externo, commit,
push, PR, merge, rebase, reset, clean, stash, amend ni deploy sin autorizacion.

---

# Handoff tecnico: correccion responsive y teclado de admin usuarios

Timestamp: 2026-09-05T20:27:36-03:00
Estado: READY_TO_RESUME
Resultado del ciclo: CORRECCION_IMPLEMENTADA_VALIDADA_LOCALMENTE_PENDIENTE_RETESTING_QA
Dispositivo/origen: Codex Desktop local
Agente: 02 - Implementacion - Builder
Objetivo: corregir el overflow global desktop y la visibilidad inicial del
control `Suspender` al navegar por teclado en `/admin/usuarios`.
Rama: `feature/pro-entitlement-foundation`
Commit base: `fe048c4810cc337dfd1c3498d9f96579453cd065`
PR asociado: #5, abierto y bloqueado para merge hasta retesting independiente
de 05 - QA funcional
Estado Git: seis cambios correctivos locales sin commit
Push a GitHub: NO realizado
Merge: NO; no autorizado

## Trabajo completado

- Se reprodujo 1453px de ancho documental frente a 1440px de viewport y el
  control `Suspender` terminando en 449.25px frente a 390px de viewport.
- Un wrapper exclusivo de admin usuarios contiene el scroll horizontal, tiene
  nombre accesible, foco por teclado, foco visible y scroll padding con tokens.
  La tabla sigue siendo `<table>`, conserva ocho columnas y todas las acciones.
- Implementacion valido claro/oscuro en 1440x900 y 390x844. Resultado:
  documento 1425/1425 desktop y 375/390 mobile; `Suspender` quedo entre
  247.48px y 351.44px dentro del wrapper de 12px a 363.20px. El wrapper
  mantuvo scroll interno de 1216px y cero errores de consola.
- No se agrego JavaScript, `!important`, colores hardcodeados, ocultamiento
  global de overflow ni cambios en logica PRO, rutas, servicios o migraciones.

## Validaciones

- Focal Design System/Admin/PRO: 30 ejecutados, 30 aprobados, 0 fallidos,
  0 errores y 0 omitidos.
- Suite completa: 294 ejecutados, 289 aprobados, 0 fallidos, 0 errores y
  5 omitidos historicos.
- `python -m compileall -q app scripts tests`: PASS.
- `python -m alembic heads`: `20260904_01 (head)`.
- `git diff --check`: PASS.
- La suite historica de migraciones ejercito downgrade solo en sus bases
  temporales; no hubo downgrade sobre la base QA ni sobre `trax_db`.

## Archivos locales modificados

- `app/static/css/styles.css`
- `app/templates/admin_usuarios.html`
- `tests/test_design_system_v2.py`
- `docs/CHANGELOG.md`
- `docs/SPRINTS/2026-09-04_PRO_ENTITLEMENT_FOUNDATION.md`
- `docs/HANDOFFS/ACTIVE_HANDOFF.md`

## Playwright, axe-core y pendientes

- No existen `package.json`, lockfiles, configuracion o tests Playwright, ni
  axe-core versionado. No se instalaron ni modificaron dependencias.
- Propuesta minima pendiente de autorizacion: `@playwright/test@1.62.1` y
  `@axe-core/playwright@4.13.0` como devDependencies; crear `package.json`,
  lock, `playwright.config.js` y `tests/e2e/admin-users-responsive.spec.js`;
  ejecutar con `npx playwright test`.
- Pendiente: retesting independiente en 05 - QA funcional. El PR #5 permanece
  bloqueado para merge; Coverage continua pendiente y no bloqueante.
- Proximo paso recomendado: auditoria tecnica focal y envio del paquete a QA.
- Para retomar: confirmar rama, SHA y estado Git; leer este bloque y revisar
  exclusivamente los seis archivos listados.
- No ejecutar commit, push, nuevo PR, merge, rebase, reset, clean, stash,
  amend ni deploy sin autorizacion explicita.

---

# Handoff tecnico: correccion focal de contraste oscuro PRO

Timestamp: 2026-09-05T19:45:29-03:00
Estado: READY_TO_RESUME
Resultado del ciclo: CORRECCION_IMPLEMENTADA_VALIDADA_LOCALMENTE_PENDIENTE_RETESTING_QA
Dispositivo/origen: Codex Desktop local
Agente: 02 - Implementacion - Builder
Objetivo: corregir exclusivamente el P1 visual de contraste oscuro informado
por QA funcional para las superficies PRO y administracion de usuarios.
Rama: `feature/pro-entitlement-foundation`
Commit base y ultimo commit: `f35797a1852e4b0293b1618ac03fdbbdba0510ae`
PR asociado: #5, abierto, no modificado y bloqueado para merge hasta el
retesting independiente de 05 - QA funcional
Estado Git: cambios correctivos locales sin commit
Push a GitHub: NO realizado
Merge: NO; no autorizado

## Trabajo completado

- Las tarjetas de `/profesional/pro/upgrade` y la tabla, navegacion, estados y
  acciones de `/admin/usuarios` consumen tokens del Design System v2 dentro de
  alcances exclusivos de pantalla.
- Se agrego cobertura estatica de regresion para impedir el regreso de fondos
  o textos hardcodeados en las superficies corregidas.
- Implementacion realizo la medicion visual claro/oscuro en 390x844 y
  1440x900: contraste principal 17.74:1 en claro y 16.98:1 en oscuro; texto
  secundario 6.93:1 en oscuro. No hubo overflow de documento en movil ni
  errores de consola.
- Implementacion comprobo la revocacion con la ruta administrativa real sobre
  SQLite efimero: el usuario paso de PRO a WORK y luego se mostro Elegible en
  upgrade. `trax_db` no fue migrada, reseteada ni modificada.

## Validaciones

- Focal Design System/PRO: 30 ejecutados, 30 aprobados, 0 fallidos, 0 errores,
  0 omitidos.
- Suite completa: 294 ejecutados, 289 aprobados, 0 fallidos, 0 errores y
  5 omitidos historicos.
- `python -m compileall -q app scripts tests`: PASS.
- `python -m alembic heads`: `20260904_01 (head)`.
- `git diff --check`: PASS.

## Archivos locales modificados

- `app/static/css/styles.css`
- `app/templates/admin_usuarios.html`
- `tests/test_design_system_v2.py`
- `docs/CHANGELOG.md`
- `docs/SPRINTS/2026-09-04_PRO_ENTITLEMENT_FOUNDATION.md`
- `docs/HANDOFFS/ACTIVE_HANDOFF.md`

## Pendientes, riesgos y reanudacion

- Pendiente: retesting independiente del P1 por 05 - QA funcional, revision
  del diff y autorizacion explicita antes de cualquier commit o push. El PR #5
  permanece bloqueado para merge. Coverage permanece pendiente y no bloqueante.
- Riesgo conocido preexistente: la tabla administrativa densa conserva scroll
  horizontal interno; en desktop su ancho puede superar el viewport. No fue
  introducido ni ampliado por esta correccion focal.
- Proximo paso recomendado: auditoria tecnica focal del paquete visual y, si
  resulta aprobado, solicitar autorizacion para un commit correctivo en la
  misma rama y la actualizacion del PR #5.
- Para retomar: confirmar rama, commit, estado Git, leer este handoff y revisar
  los seis archivos indicados antes de actuar.
- No ejecutar commit, push, merge, rebase, reset, clean, stash, amend, nuevo PR
  ni deploy sin autorizacion explicita.

---

# Handoff tecnico: revalidacion independiente posterior a correcciones P1

Timestamp: 2026-09-05T14:49:25-03:00
Estado: COMPLETED
Resultado del ciclo: APROBADO
Dispositivo/origen: Codex Desktop local
Agente: 03 - Testing - Test Executor
Objetivo: revalidar independientemente PRO Entitlement despues de las
correcciones P1 de gates Alembic y rollback PostgreSQL.
Rama: `feature/pro-entitlement-foundation`
Commit probado: `e5b4ba9be651772afe86683b8f7a6494b2afb0f7`
Commit funcional anterior: `fe979ce278607bfcf243ff2dbab31984d4b1e7ee`
PR asociado: #5
Estado Git inicial: limpio
Push a GitHub: NO realizado en esta sesion
Merge: NO; no autorizado

## Evidencia valida

- Se invalido expresamente la suite cortada por el cierre de Docker y no se
  utilizo como evidencia.
- Tras reiniciar Docker se eliminaron las cuatro bases residuales con prefijo
  `trax_pro_entitlement_test_` y se verifico `ABSENT`.
- `python -m compileall -q app scripts tests`: PASS.
- Suite focal Alembic, PRO y migraciones: 43 ejecutados, 43 aprobados, 0
  fallidos, 0 errores, 0 omitidos.
- Suite completa posterior al reinicio: 293 ejecutados, 288 aprobados, 0
  fallidos, 0 errores y 5 omitidos historicos.
- Validacion dinamica Alembic: 6/6 PASS; confirma head unico obtenido del
  grafo, revision aplicada exacta, ascendencia de `20260726_07` y rechazo de
  multiples heads, base vacia, atrasada, desconocida o sin ancestro requerido.
- Head del repositorio: `20260904_01 (head)`.
- Gate PostgreSQL PRO: 2/2 PASS. El caso de rollback provoco una FK invalida
  real al insertar auditoria, confirmo desde otra conexion que dos
  entitlements seguian activos y que no persistio AuditLog, recupero la sesion
  mediante rollback y completo una revocacion valida posterior.
- Gate PostgreSQL contracting concurrency: 8/8 PASS.
- Gate PostgreSQL negotiation concurrency: 8/8 PASS.
- Gate PostgreSQL OperationCommand partial migration: 21/21 PASS.
- Ningun gate PostgreSQL obligatorio quedo omitido.
- `git diff --check 18e46fd...e5b4ba9` y verificacion final: PASS.
- Coverage: PENDIENTE y no bloqueante; `coverage.py` no esta declarado y no se
  instalaron dependencias.

## PostgreSQL y limpieza

- Evidencia valida ejecutada exclusivamente sobre bases nuevas con nombres
  `trax_pro_entitlement_test_resume2_pro`,
  `trax_pro_entitlement_test_resume2_contracting`,
  `trax_pro_entitlement_test_resume2_negotiation` y
  `trax_pro_entitlement_test_resume2_partial`.
- Las cuatro bases fueron eliminadas despues de finalizar los procesos.
- Verificacion final de bases `trax_pro_entitlement_test_*`: `ABSENT`.
- `trax_db` conserva revision `20260726_07`; no fue reseteada ni migrada.
- Staging, produccion y volumenes no fueron modificados.

## Hallazgos, archivos y cierre

- P0/P1 nuevos: ninguno.
- Observaciones no bloqueantes: advertencias legacy/deprecacion ya existentes
  de SQLAlchemy y `datetime.utcnow()`.
- Codigo productivo, migraciones y tests: sin modificaciones en esta sesion.
- Unico archivo modificado: `docs/HANDOFFS/ACTIVE_HANDOFF.md` por cierre
  obligatorio.
- Los dos P1 previos quedan VERIFICADOS como cerrados.
- Veredicto final: `APROBADO`.
- Proximo paso recomendado: revision/integracion de PR #5 mediante el flujo
  autorizado. No realizar commit, push, PR, merge, rebase, reset, clean,
  stash, amend ni deploy sin autorizacion expresa.

---

# Handoff tecnico: cierre P1 de prueba dinamica Alembic

Timestamp: 2026-09-04T20:02:58-03:00
Estado: READY_TO_RESUME
Resultado del ciclo: CORRECCIONES_IMPLEMENTADAS_PENDIENTES_DE_RETESTING
Dispositivo/origen: Codex Desktop local
Agente: 02 - Implementacion - Builder
Objetivo: eliminar la dependencia fija del head vigente en la prueba real del
helper Alembic, sin modificar el helper, los gates ni el nucleo PRO.
Rama: `feature/pro-entitlement-foundation`
Commit base: `fe979ce278607bfcf243ff2dbab31984d4b1e7ee`
Estado Git: paquete correctivo local sin commit
Push a GitHub: NO; las correcciones locales no fueron publicadas
PR: #5 permanece abierto y no mergeado
Merge: NO; no autorizado

## Trabajo completado

- La prueba real construye `ScriptDirectory` desde `alembic.ini`, obtiene los
  heads mediante `get_heads()` y exige exactamente uno.
- El unico head real se usa como revision aplicada y resultado esperado del
  helper; una migracion descendiente futura no requiere editar esta prueba.
- Se preservaron los escenarios adversariales y no cambio codigo funcional.
- Helper Alembic: 6 ejecutados, 6 aprobados, 0 fallidos, 0 omitidos.
- Migraciones historicas: 16 ejecutados, 16 aprobados, 0 fallidos, 0 omitidos.
- Suite completa: 293 ejecutados, 288 aprobados, 0 fallidos, 5 omitidos.
- `compileall -q tests`, `git diff --check` y busqueda de referencias: PASS.

## Proximo paso y restricciones

Transferir el paquete correctivo validado a una nueva revision tecnica. No
ejecutar commit, push, nuevo PR, merge, rebase, reset, clean, stash, amend ni
deploy sin autorizacion expresa.

---

# Handoff tecnico: ejecucion independiente del fundamento PRO

Timestamp: 2026-09-04T19:25:31-03:00
Estado: READY_TO_RESUME
Resultado del ciclo: CORRECCIONES_IMPLEMENTADAS_PENDIENTES_DE_RETESTING
Dispositivo/origen: Codex Desktop local
Agente: 03 - Testing - Test Executor
Objetivo: validar independientemente el fundamento tecnico de autorizacion PRO.
Rama: `feature/pro-entitlement-foundation`
Commit probado: `fe979ce278607bfcf243ff2dbab31984d4b1e7ee`
Estado Git inicial: limpio
Push a GitHub: NO
Merge: NO; no autorizado

## Evidencia ejecutada

- Identidad de rama y commit: PASS.
- `git diff --check develop...fe979ce`: PASS.
- `python -m compileall -q app scripts tests` dentro de `trax-web`: PASS.
- Suite focal PRO: 21 ejecutados, 21 aprobados, 0 fallidos, 0 omitidos.
- Suite completa: 287 tests descubiertos; ejecucion final sin fallos y con las
  5 omisiones historicas esperadas.
- Gate PostgreSQL PRO: 1 ejecutado, 1 aprobado, 0 fallidos, 0 omitidos.
- Runner PostgreSQL de migracion parcial: 21 ejecutados, 21 aprobados, 0
  fallidos, 0 omitidos en repeticion aislada.
- `alembic heads`: `20260904_01 (head)`.
- Coverage: NO EJECUTADO; `coverage.py` no esta declarado ni disponible y no
  se autorizo instalar dependencias.
- Playwright, axe-core y responsive: NO REQUERIDOS por el paquete para este
  incremento.

## Hallazgos y bloqueantes

- P1 TEST: `postgresql_contracting_concurrency_e2e.py` y
  `postgresql_negotiation_concurrency_e2e.py` conservan una expectativa fija
  de revision `20260726_07`; con el head vigente `20260904_01` ambos fallan en
  `setUpClass` antes de ejecutar casos.
- P1 COBERTURA: la atomicidad de revocacion y `AuditLog` esta probada en la
  suite focal SQLite, pero el gate PRO PostgreSQL no fuerza ese rollback; la
  evidencia PostgreSQL obligatoria del paquete queda pendiente.
- P2 DOCUMENTACION: el handoff anterior seguia describiendo el incremento como
  cambios sin commit sobre `18e46fd`, aunque el paquete y el HEAD probado son
  `fe979ce`.
- Una repeticion del runner parcial sufrio dos errores de entorno porque la
  primera base efimera desaparecio durante la corrida. La repeticion aislada
  posterior paso 21/21, por lo que no se clasifica como defecto del producto.

## Bases PostgreSQL y seguridad

- Bases efimeras utilizadas:
  `trax_pro_entitlement_test_executor_20260904` y
  `trax_pro_entitlement_test_partial_20260904`.
- Ambas fueron eliminadas; no quedan bases con prefijo
  `trax_pro_entitlement_test`.
- `trax_db`, staging, produccion y volumenes no fueron reseteados ni migrados.
- No se imprimieron secretos ni se conservaron credenciales o datos reales.

## Archivos modificados y proximo paso

- Modificado en esta sesion: `docs/HANDOFFS/ACTIVE_HANDOFF.md` exclusivamente.
- Codigo productivo, migraciones y tests: sin modificaciones.
- Proximo paso recomendado: actualizar los dos gates historicos para aceptar el
  head vigente sin debilitar sus invariantes y ampliar el gate PostgreSQL PRO
  con rollback real de revocacion y auditoria; luego repetir el paquete.
- No realizar commit, push, PR, merge, rebase, reset, clean, stash ni deploy sin
  autorizacion expresa.

## Correcciones implementadas por Builder

Timestamp: 2026-09-04T19:50:24-03:00

- Commit evaluado y base de las correcciones:
  `fe979ce278607bfcf243ff2dbab31984d4b1e7ee`.
- Los gates posteriores a `upgrade("head")` validan dinamicamente un unico
  head, una unica revision aplicada, coincidencia exacta y ascendencia desde
  `20260726_07`; los checkpoints historicos explicitos se conservaron.
- El gate PRO PostgreSQL fuerza una FK invalida durante el commit conjunto de
  dos revocaciones y AuditLog, comprueba rollback desde conexion independiente,
  recuperacion de sesion y una revocacion valida posterior.
- Helper Alembic: 5 ejecutados, 5 aprobados, 0 fallidos, 0 omitidos.
- Migraciones historicas: 16 ejecutados, 16 aprobados, 0 fallidos, 0 omitidos.
- Gates PostgreSQL historicos: contratacion 8/8, negociacion 8/8, reviews 10/10
  y rutas/moderacion 8/8.
- Gate PostgreSQL PRO: 2 ejecutados, 2 aprobados, 0 fallidos, 0 omitidos.
- Suite focal PRO: 21 ejecutados, 21 aprobados, 0 fallidos, 0 omitidos.
- Suite completa: 292 ejecutados, 287 aprobados, 0 fallidos, 5 omitidos.
- Coverage permanece PENDIENTE y no bloqueante; `coverage.py` no fue instalado.
- PR #5 no fue modificado, cerrado ni mergeado.

Estado final: READY_TO_RESUME; resultado
`CORRECCIONES_IMPLEMENTADAS_PENDIENTES_DE_RETESTING`.

---

# Handoff tecnico: cierre focal P1 del guard PostgreSQL

Timestamp: 2026-09-04T13:19:30-03:00
Estado: COMPLETED
Resultado del ciclo: CORRECCION_P1_FOCAL_VALIDADA
Dispositivo/origen: Codex Desktop local
Agente: 02 - Implementacion - Builder
Rama: `feature/pro-entitlement-foundation`
Commit base y ultimo commit: `18e46fd6bf6d05b73884b7ba3fdbb335f66d7d7e`
Estado Git: incremento PRO y correccion focal sin commit
Push a GitHub: NO
Merge: NO; no autorizado

## Objetivo y resultado

Cerrar exclusivamente el P1 pendiente del guard PostgreSQL, sin modificar la
implementacion funcional PRO. El nombre se valida mediante `fullmatch()` contra
`^trax_pro_entitlement_test(?:_[a-z0-9]+(?:_[a-z0-9]+)*)?$`, sin parametros y
con el limite PostgreSQL de 63 bytes. La autorizacion de reset y el dialecto
PostgreSQL siguen siendo obligatorios.

## Archivos modificados en esta correccion

- `tests/postgresql_pro_entitlement_e2e.py`
- `tests/test_pro_entitlement_foundation.py`
- `docs/postgres_dev.md`
- `docs/SPRINTS/2026-09-04_PRO_ENTITLEMENT_FOUNDATION.md`
- `docs/HANDOFFS/ACTIVE_HANDOFF.md`

No se modificaron modelos, servicios, rutas, templates, seed ni migraciones
durante esta correccion focal.

## Tests y migraciones

- Guard focal: 5 ejecutados, 5 aprobados, 0 fallidos, 0 omitidos.
- Suite focal PRO: 21 ejecutados, 21 aprobados, 0 fallidos, 0 omitidos.
- Suite completa: 287 ejecutados, 282 aprobados, 0 fallidos, 5 omitidos.
- Gate PostgreSQL real: 1 ejecutado, 1 aprobado, 0 fallidos, 0 omitidos sobre
  `trax_pro_entitlement_test_finalaudit_20260904`.
- Rechazo instrumentado de `trax_db`: 1 ejecutado y aprobado; engine no creado.
- Revision de `trax_db` antes y despues: `20260726_07`; no fue migrada.
- Base descartable eliminada despues de la validacion; volumenes preservados.
- `compileall`: PASS.
- `alembic heads`: `20260904_01 (head)`.
- `git diff --check`: PASS.

## Pendientes, riesgos y proximo paso

El P1 del guard queda cerrado. REQ-001 sigue en implementacion parcial; PSP,
pagos, suscripcion comercial, renovaciones y REQ-002 permanecen fuera de este
alcance. Proximo paso recomendado: revision tecnica final y, si resulta
aprobada, solicitar autorizacion para commit. No ejecutar commit, push, PR,
merge, rebase, reset, clean, stash ni deploy sin autorizacion expresa.

---

# Handoff tecnico: correcciones de auditoria del nucleo PRO

Timestamp: 2026-09-04T10:29:16-03:00
Estado: COMPLETED
Resultado del ciclo: CORRECCIONES_P1_VALIDADAS
Dispositivo/origen: Codex Desktop local
Agente: 02 - Implementacion - Builder
Rama: `feature/pro-entitlement-foundation`
Commit base y ultimo commit: `18e46fd6bf6d05b73884b7ba3fdbb335f66d7d7e`
Estado Git: cambios sin commit del incremento PRO y sus correcciones autorizadas
Push a GitHub: NO
Merge: NO; pendiente de nueva revision y autorizacion

## Objetivo

Corregir los hallazgos P1/P2/P3 de la auditoria sin descartar la implementacion
existente ni ampliar REQ-001.

## Trabajo completado

- Revocacion limitada por `user_id` a PRO ACTIVA, fuente TRANSACTIONAL o
  SUBSCRIPTION, vencimiento no nulo y futuro.
- Revocacion y AuditLog preparados en una sesion y confirmados con un unico
  commit; cualquier excepcion ejecuta rollback y se propaga.
- `create_audit_log()` conserva el commit para callers legacy mediante un
  helper interno sin commit. La atomicidad de otras acciones administrativas
  queda registrada como deuda fuera de alcance.
- Gate PostgreSQL endurecido antes de crear el engine: solo acepta
  `trax_pro_entitlement_test` o `trax_pro_entitlement_test_<sufijo>`.
- Downgrade documentado y probado como reversible estructuralmente pero no para
  la clasificacion de `source_type`; el re-upgrade devuelve NULL.
- Seed QA temporalmente idempotente: conserva vencimientos futuros y renueva la
  misma fila vencida por 365 dias sinteticos de QA.
- Frontera UTC centralizada para timestamps PRO sobre columnas legacy UTC
  naive.
- Frontmatter de REQ-001 corregido a `IMPLEMENTACION_PARCIAL` sin cambiar su
  estado `APROBADO`.

## Migracion y gate PostgreSQL

- Head: `20260904_01`.
- Base descartable usada: `trax_pro_entitlement_test_20260904_102916`.
- Upgrade/downgrade/re-upgrade: PASS; perdida de clasificacion confirmada.
- Gate: 1 ejecutado, 1 aprobado, 0 fallidos, 0 omitidos.
- Intento contra `trax_db`: rechazado antes de crear el engine.
- Revision de `trax_db` antes y despues: `20260726_07`; sin mutacion.
- La base descartable fue eliminada; `trax_db` y los volumenes se preservaron.

## Tests y validaciones

- Focalizadas finales: 20 ejecutadas, 20 aprobadas, 0 fallidas, 0 omitidas.
- Suite final: 286 ejecutadas, 281 aprobadas, 5 omitidas, 0 fallidas.
- `compileall`: PASS.
- `alembic heads`: `20260904_01 (head)`.
- `git diff --check`: PASS.
- Dos fallos intermitentes ajenos a PRO aparecieron en corridas previas; ambos
  pasaron aislados. Se aislo el estado del limiter en las pruebas PRO y la
  corrida completa final paso.

## Riesgos y pendientes

- El downgrade pierde deliberadamente `source_type`; exige respaldo y
  autorizacion cuando la clasificacion deba conservarse.
- Otras acciones administrativas legacy aun pueden contener commits internos;
  su refactorizacion no fue autorizada en este ciclo.
- PSP, pagos, suscripcion comercial, renovaciones y REQ-002 siguen pendientes.

## Proximo paso

Ejecutar una nueva revision tecnica del diff. No realizar commit, push, PR,
merge ni deploy sin autorizacion explicita.

---

# Handoff tecnico: fundacion del entitlement PRO

Timestamp: 2026-09-04T10:03:12-03:00
Estado: COMPLETED
Resultado del ciclo: IMPLEMENTACION_PARCIAL_VALIDADA
Dispositivo/origen: Codex Desktop local
Agente: 02 - Implementacion - Builder
Rama: `feature/pro-entitlement-foundation`
Commit base y ultimo commit: `18e46fd6bf6d05b73884b7ba3fdbb335f66d7d7e`
Estado Git: cambios sin commit exclusivamente del incremento enumerado abajo
Push a GitHub: NO
Merge: NO; pendiente de revision y autorizacion

## Objetivo

Implementar el primer incremento de REQ-001: evaluador central de entitlement
PRO con elegibilidad, fuente valida, vencimiento UTC, bloqueo de concesiones
legacy/manuales y un unico entitlement QA local.

## Trabajo completado

- Se agrego `Subscription.source_type`, nullable para preservar historia y con
  constraint para TRANSACTIONAL o SUBSCRIPTION.
- `has_pro_access()` exige PROFESIONAL ACTIVO, verificacion PROFESIONAL
  APROBADA, PRO ACTIVA, fuente reconocida y expiracion futura.
- Puntos, verificacion aislada, legacy, ENTERPRISE, filas indefinidas o vencidas
  y cuentas no elegibles no conceden capacidades.
- Las rutas profesional y administrativa ya no crean acceso PRO; la accion
  visual administrativa fue retirada y la pantalla profesional informa la
  indisponibilidad comercial.
- La revocacion administrativa cancela todas las filas PRO activas del usuario
  sin afectar una eventual fila FREE activa.
- El seed QA deja exactamente a `electricidad.pro@demo.trax.local` con una
  fuente SUBSCRIPTION temporal y conserva el bloqueo production/prod.
- Se creo ADR-001 y se actualizo la trazabilidad documental.

## Parcialmente completado y pendientes

REQ-001 permanece parcial. Faltan PSP, prueba de 30 dias, extensiones de 60
dias, pagos, suscripcion comercial, renovaciones, mora y contracargos.
REQ-002, Facturacion, ARCA, IA y ENTERPRISE operativo quedaron fuera de alcance.

## Migracion

- `20260904_01_pro_entitlement_foundation.py`, lineal desde `20260726_07`.
- Upgrade y downgrade verificados en SQLite y PostgreSQL 16 descartable.
- Registros legacy conservados con `source_type=NULL`.

## Tests ejecutados

- Baseline: 266 ejecutados, 261 aprobados, 5 omitidos, 0 fallidos.
- Focalizados finales: 14 ejecutados, 14 aprobados, 0 omitidos, 0 fallidos.
- Suite final: 280 ejecutados, 275 aprobados, 5 omitidos, 0 fallidos.
- Gate PostgreSQL: 1 ejecutado y aprobado, sin omisiones.
- `python -m compileall -q app scripts tests`: PASS.
- `python -m alembic heads`: `20260904_01 (head)`.
- `git diff --check`: PASS.

## Errores y troubleshooting

- El primer gate no importo `app` al ejecutarse como archivo; se corrigio el
  bootstrap de `PROJECT_ROOT`, patron ya usado por scripts del repositorio.
- La primera regresion mostro 36 asserts que fijaban el head historico; se
  actualizaron solo las expectativas ejecutadas despues de `upgrade head`.
- No se creo troubleshooting separado: causa y solucion fueron directas y
  quedaron cubiertas por tests.

## Archivos modificados o creados

- `app/models/subscription.py`
- `app/services/subscription_service.py`
- `app/routes/main_routes.py`
- `app/templates/solicitar_upgrade_pro.html`
- `app/templates/admin_usuarios.html`
- `scripts/dev_seed_professionals.py`
- `migrations/versions/20260904_01_pro_entitlement_foundation.py`
- `tests/test_pro_entitlement_foundation.py`
- `tests/test_pro_entitlement_migration.py`
- `tests/postgresql_pro_entitlement_e2e.py`
- `tests/test_sprint7_contract_review_migration.py`
- `tests/test_sprint7_negotiation_migration.py`
- `docs/ADR/README.md`
- `docs/ADR/ADR-001-pro-entitlement-foundation.md`
- `docs/REQUISITOS/REQ-001-activacion-y-vigencia-pro.md`
- `docs/REQUISITOS/MASTER_SPEC.md`
- `docs/ROADMAP.md`, `docs/BACKLOG.md`, `docs/CHANGELOG.md`
- `docs/QA_LOCAL.md`, `docs/INDEX.md`
- `docs/SPRINTS/2026-09-04_PRO_ENTITLEMENT_FOUNDATION.md`
- `docs/HANDOFFS/ACTIVE_HANDOFF.md`

## Riesgos y proximo paso

- No aplicar la migracion antes de desplegar el codigo produciria errores por
  columna ausente; no existe autorizacion de deploy.
- Las fuentes comerciales aun no tienen productores reales.
- Proximo paso: revision tecnica del diff; si se aprueba, autorizar commit y
  push de la rama. No mergear ni desplegar automaticamente.

## Instrucciones para retomar

1. Confirmar rama y estado Git sin descartar cambios.
2. Revisar diff completo y evidencia de tests.
3. Mantener fuera de alcance REQ-002 y proveedores externos.
4. No ejecutar commit, push, PR, merge, rebase, reset, clean, stash o deploy sin
   autorizacion expresa.

---

# Registro historico superado: especificacion PRO y Facturacion MVP

Timestamp: 2026-09-03T21:55:15-03:00
Estado: COMPLETED
Resultado del ciclo: COMPLETED
Alcance: especificacion funcional documental de activacion y vigencia PRO y de
Facturacion MANDOBRA PRO MVP

## Identificacion

- Dispositivo/origen: Codex Desktop local.
- Agente o sesion de origen: Codex / Documentation Engineer Senior.
- Rama actual: `docs/spec-pro-facturacion-mvp` (estado provisto y verificado
  antes de iniciar esta tarea; no se repitio el preflight por instruccion).
- Commit base y ultimo commit informado: `e0eed2`.
- Cambios sin commit: SI; nueve archivos Markdown bajo `docs/` enumerados en
  este handoff.
- Rama subida a GitHub: NO; no se ejecuto push ni se verificaron remotos por
  restriccion expresa.
- Destino previsto: `02 - Implementacion y Refinacion`.

## Objetivo de la sesion

Formalizar como requisitos separados y aprobados la activacion y vigencia de
MANDOBRA PRO y Facturacion MANDOBRA MVP como beneficio opcional de PRO, sin
implementar codigo, proveedores, integraciones, migraciones, tests ni cambios
visuales.

## Trabajo completado

- Se creo [REQ-001](../REQUISITOS/REQ-001-activacion-y-vigencia-pro.md) con
  catalogo `FREE`, `PRO`, `ENTERPRISE`, elegibilidad profesional y reglas para
  PRO transaccional y por suscripcion.
- Se creo [REQ-002](../REQUISITOS/REQ-002-facturacion-pro-mvp.md) con el alcance
  fiscal MVP de persona humana, monotributo activo y Factura C.
- Se separaron expresamente Facturacion, entitlement PRO y configuracion ARCA.
- Se registro el contraste con el codigo actual: activacion inmediata/manual,
  lector de puntos legacy, falta de control de vencimiento y ausencia de PSP,
  ARCA, facturacion e IA productiva.
- Se actualizaron Master Spec, Roadmap, Backlog, Changelog e indices con
  implementacion marcada como `PENDIENTE`.
- Se conservaron preguntas abiertas separadas de las decisiones aprobadas.

## Trabajo parcialmente completado

Ninguno dentro del alcance documental autorizado.

## Pendientes

- Porcentaje de comision; precio, periodicidad, beneficios y limites completos
  de PRO; renovacion, cancelacion, mora, contracargos y periodo de gracia.
- Politica de migracion de accesos PRO actuales y concesiones administrativas.
- Seleccion y validacion del PSP y estrategia del entitlement.
- Integracion directa con ARCA o proveedor; custodia y rotacion de
  certificados; validacion de monotributo; datos del receptor; retencion,
  almacenamiento, entrega, limites, correcciones, anulaciones, notas de credito
  y contingencia.
- Proveedor y modelo de IA, costos y revisiones legal, fiscal, contable y de
  seguridad.
- Modelo futuro de `ENTERPRISE`; no se autorizo crear el actor `EMPRESA`.
- Implementacion y pruebas de ambos requisitos, sujetas a nueva autorizacion.

## Bloqueantes

- BLOQUEANTE para implementar PRO transaccional: seleccionar y validar PSP y
  cerrar politicas comerciales y de contracargos.
- BLOQUEANTE para implementar Facturacion: resolver integracion fiscal,
  custodia de credenciales, politicas de datos y revisiones legal, fiscal,
  contable y de seguridad.
- No existen bloqueantes para el cierre de esta especificacion documental.

## Archivos creados

- `docs/REQUISITOS/REQ-001-activacion-y-vigencia-pro.md`: requisito aprobado;
  implementacion pendiente, sin commit.
- `docs/REQUISITOS/REQ-002-facturacion-pro-mvp.md`: requisito aprobado;
  implementacion pendiente, sin commit.

## Archivos modificados

- `docs/REQUISITOS/README.md`: indice de requisitos aprobados, sin commit.
- `docs/REQUISITOS/MASTER_SPEC.md`: resumen, actores, estado actual, capacidades
  aprobadas y pendientes, sin commit.
- `docs/ROADMAP.md`: especificaciones aprobadas e implementaciones pendientes,
  sin commit.
- `docs/BACKLOG.md`: pendientes consolidados y enlazados, sin commit.
- `docs/INDEX.md`: enlaces a REQ-001 y REQ-002, sin commit.
- `docs/CHANGELOG.md`: cambios exclusivamente documentales, sin commit.
- `docs/HANDOFFS/ACTIVE_HANDOFF.md`: reemplazo del handoff activo para este
  ciclo, sin commit.

## Migraciones relacionadas

Ninguna. No se crearon ni ejecutaron migraciones.

## Tests y validaciones ejecutados

- Inspeccion estatica dirigida de `Subscription`, `subscription_service`,
  verificacion, decoradores, ruta de upgrade, administracion, Planes y puntos
  legacy: EJECUTADA; confirma el contexto registrado en los requisitos.
- Verificacion de las 16 secciones obligatorias en REQ-001 y REQ-002:
  EJECUTADA; resultado `HEADINGS_OK` para ambos documentos.
- Comprobacion de enlaces Markdown relativos en los documentos creados o
  actualizados: EJECUTADA; resultado `RELATIVE_LINKS_OK`.
- Comprobacion de identificadores: EJECUTADA; `REQ-001` y `REQ-002` son los
  primeros identificadores de requisito y no reutilizan un `REQ-NNN` previo.
- `git status --short`: EJECUTADO; cambios exclusivamente Markdown bajo
  `docs/`.
- `git diff --check`: EJECUTADO; sin errores, con advertencias informativas de
  conversion futura LF a CRLF para archivos rastreados.
- `git diff --stat`: EJECUTADO; revisado antes del cierre del handoff.
- `git diff -- docs`: EJECUTADO; revisado antes del cierre del handoff.

## Tests y validaciones no ejecutados

- Tests de aplicacion: NO EJECUTADOS - no aplican al alcance documental.
- Aplicacion: NO EJECUTADA; no aplica al alcance documental.
- Migraciones: NO EJECUTADAS; no existen cambios de esquema.
- Integraciones PSP, ARCA e IA: NO EJECUTADAS; no estan implementadas ni fueron
  autorizadas.

## Resultados de tests

- Aprobados: validaciones documentales de estructura, enlaces, alcance y diff.
- Fallidos: ninguno.
- Omitidos: suite de aplicacion, por no aplicar al alcance documental.
- Resultado general: PASS documental; implementacion NO EJECUTADA.

## Errores conocidos

- Ninguno durante la edicion documental.
- CONTRADICCION vigente y no corregida en codigo: la UI publica conserva
  `Plus`, mientras el catalogo aprobado es `FREE`, `PRO`, `ENTERPRISE`.
- CONTRADICCION vigente y no corregida en codigo: el upgrade usa puntos legacy
  o verificacion, mientras REQ-001 exige cuenta activa, verificacion aprobada y
  una fuente de entitlement vigente.

## Troubleshooting relacionado

Ninguno.

## Decisiones tomadas

- APROBADO: `FREE`, `PRO`, `ENTERPRISE` es el catalogo canonico; `Plus` queda
  fuera.
- APROBADO: la primera implementacion PRO corresponde a profesionales con
  cuenta activa y verificacion aprobada; puntos legacy no conceden PRO.
- APROBADO: modalidad transaccional y suscripcion mantienen el mismo
  entitlement `PRO`.
- APROBADO: Facturacion es un modulo separado, opcional y exclusivo de PRO
  vigente; no activa ni extiende PRO.
- APROBADO: el alcance fiscal inicial es persona humana, monotributo activo y
  Factura C, con borrador asistido y confirmacion humana obligatoria.
- PENDIENTE: proveedor PSP, integracion fiscal, custodia de secretos, proveedor
  de IA, modelos, precios y porcentajes.
- PENDIENTE: crear ADR cuando se aprueben decisiones arquitectonicas con impacto
  transversal o costosas de revertir.

## Documentacion actualizada

- [REQ-001](../REQUISITOS/REQ-001-activacion-y-vigencia-pro.md).
- [REQ-002](../REQUISITOS/REQ-002-facturacion-pro-mvp.md).
- [Indice de requisitos](../REQUISITOS/README.md).
- [Master Spec](../REQUISITOS/MASTER_SPEC.md).
- [Roadmap](../ROADMAP.md).
- [Backlog](../BACKLOG.md).
- [Indice documental](../INDEX.md).
- [Changelog](../CHANGELOG.md).
- Este handoff activo.

## Riesgos

- Implementar antes de cerrar politicas abiertas puede producir accesos,
  cobros o efectos fiscales incorrectos.
- Webhooks duplicados o fuera de orden pueden degradar vigencia e idempotencia.
- Una custodia inadecuada puede exponer secretos y datos fiscales.
- IA sin limites estrictos puede inventar datos o aparentar asesoramiento
  fiscal.
- El codigo legacy puede seguir concediendo PRO por puntos hasta que una
  implementacion autorizada aplique REQ-001.

## Proximo paso recomendado

Iniciar `02 - Implementacion y Refinacion` con una revision tecnica de REQ-001
y REQ-002 que produzca un plan de implementacion por fases y ADR pendientes,
sin escribir codigo hasta cerrar las decisiones bloqueantes y obtener
autorizacion explicita.

## Handoff exacto para 02 - Implementacion y Refinacion

1. Verificar estado Git, rama y ultimo commit antes de actuar.
2. Confirmar que los nueve cambios Markdown sin commit enumerados siguen
   presentes e intactos.
3. Leer completos REQ-001, REQ-002, Master Spec y este handoff.
4. Contrastar nuevamente el plan con el codigo y migraciones vigentes si cambia
   el commit base.
5. Separar la implementacion de entitlement PRO del modulo de Facturacion.
6. Proponer fases, invariantes, migraciones, pruebas PostgreSQL, controles de
   seguridad y ADR, sin seleccionar proveedores no aprobados.
7. Resolver o elevar las preguntas bloqueantes antes de implementar.
8. No modificar codigo, migraciones o UI sin autorizacion explicita para la
   fase de implementacion.

## Acciones que NO deben realizarse

- No asumir que REQ-001 o REQ-002 ya estan implementados.
- No elegir Mercado Pago, otro PSP, integracion ARCA ni proveedor de IA sin
  evaluacion y aprobacion.
- No almacenar claves fiscales en texto plano.
- No usar puntos legacy como elegibilidad PRO.
- No crear el actor `EMPRESA` por la sola existencia conceptual de
  `ENTERPRISE`.
- No ejecutar commit, push, PR, merge, rebase, reset, clean, stash ni cambios
  de rama sin autorizacion expresa.
- No mezclar cambios ajenos o fuera de `docs/` con este ciclo documental.

## Criterio de cierre

Este ciclo queda `COMPLETED` cuando los dos requisitos y su trazabilidad
documental estan presentes, los cambios permanecen exclusivamente bajo
`docs/`, las validaciones documentales no informan errores y se entrega este
handoff. El cierre no requiere ni autoriza commit, push, PR, merge o
implementacion.

---

# Actualizacion posterior al merge de PRO y Facturacion MVP

Timestamp: 2026-09-04T08:27:58-03:00
Estado: COMPLETED
Estado vigente: MERGED
Resultado: COMPLETED
Documento: `docs/HANDOFFS/ACTIVE_HANDOFF.md`
Motivo: cerrar la trazabilidad posterior a la integracion del ciclo documental
de PRO y Facturacion MVP.
Evidencia: commit documental, Pull Request y merge commit verificados; `develop`
local y `origin/develop` sincronizados en `e26e598` desde la laptop.
Responsable: Codex / Documentation Engineer Senior
Dispositivo: laptop
Rama de esta actualizacion: `docs/close-pro-facturacion-handoff`
Commit base: `e26e5989e259ad142dfe994817566c3b6d5ff8d1`

## Registro superado

El registro original de `2026-09-03T21:55:15-03:00` se conserva integro porque
describe correctamente el estado previo al commit. Su estado operativo queda
SUPERSEDED por esta actualizacion posterior: los nueve archivos Markdown que
entonces estaban sin commit ya fueron versionados e integrados en `develop`.

## Integracion verificada

- Commit documental: `9f3b20899704e2667411c45fde3b529909bd53ca`.
- Pull Request: `#3`.
- URL: `https://github.com/cristhian-star/TRAX-PLATFORM/pull/3`.
- Rama origen: `docs/spec-pro-facturacion-mvp`.
- Rama destino: `develop`.
- Merge commit: `e26e5989e259ad142dfe994817566c3b6d5ff8d1`.
- Merge realizado: `2026-09-04T00:52:14-03:00`.
- Cambios integrados: nueve archivos Markdown bajo `docs/`.
- Sincronizacion posterior: verificada en la laptop.
- `develop` local y `origin/develop`: sincronizados en `e26e598`.
- Arbol de trabajo previo a esta actualizacion: limpio.

## Alcance y validacion

- Esta actualizacion modifica exclusivamente
  `docs/HANDOFFS/ACTIVE_HANDOFF.md`.
- No cambia decisiones funcionales ni declara implementados REQ-001 o REQ-002.
- Tests de aplicacion: NO EJECUTADOS - no aplican al alcance documental.
- No se ejecutaron migraciones ni la aplicacion.
- No se realizo commit, push, Pull Request ni merge como parte de esta
  actualizacion.

## Proximo paso

Transferir el analisis a `02 - Implementacion y Refinacion` para preparar el
plan tecnico por fases de REQ-001 y REQ-002. Esta transferencia no autoriza
todavia implementacion, cambios de codigo, migraciones, seleccion de
proveedores ni decisiones funcionales adicionales.

## Restricciones vigentes

- No asumir que PRO o Facturacion MVP ya estan implementados.
- No iniciar implementacion sin autorizacion expresa.
- No seleccionar PSP, integracion fiscal o proveedor de IA sin evaluacion y
  aprobacion.
- No realizar commit, push, PR o merge durante este cierre local.
