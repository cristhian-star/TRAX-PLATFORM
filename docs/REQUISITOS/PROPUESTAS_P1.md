# Propuestas P1 — Portal público

Actualización: 2026-10-04T15:04:39-03:00. Estado: implementado y aprobado por Testing independiente, pendiente de commit.
Base: feature/ux-ui-foundation, 26ee98d0e0b18c3589fcf39f151ed70929309930.

## Contrato construido

GET /propuestas permite lectura anónima y autenticada de ProposalRequest PUBLICADA.
Reutiliza industria, categoria, rubro y ubicacion como filtros combinables GET.
Mantiene la búsqueda parcial ilike existente (incluidos sus comodines SQL); no hay
búsqueda libre por título o descripción. Las opciones de industria/categoría proceden
de valores distintos de publicaciones reales, no constituyen otra taxonomía.
Parámetros conocidos repetidos o de más de 120 caracteres: 400 seguro. Desconocidos:
ignorados. Valores textuales sin coincidencia: listado vacío, sin escritura.
page admite 1–1000; per_page 1–50, predeterminado 12. Valores numéricos inválidos:
400. Orden created_at descendente, desempate id descendente. Conteo y paginación SQL;
postulaciones agregadas por página, sin consultas por tarjeta. Fuera de rango: 200
con aviso y retorno a primera página. Los enlaces conservan filtros y tamaño.
El formulario usa GET nativo y funciona sin JavaScript, incluido el campo rubro
asociado mediante el atributo form. Limpiar vuelve a la URL canónica sin filtros.

## Presentación y permisos

Estructura de referencia: filtros laterales, encabezado, buscador por rubro,
tarjetas horizontales y panel informativo derecho. Una columna en móvil con título
primero. CSS encapsulado en .proposals-p1, tokens DS v2, temas claro y oscuro,
foco visible, controles de 48 px y enlace de limpieza de 44 px mínimo.

Cada tarjeta entrega título, descripción escapada truncada a 240 caracteres,
categoría, rubro/especialidad y ubicación cuando existen, fecha real de publicación,
conteo de postulaciones y Presupuesto estimado únicamente si no es nulo (incluye cero).
No entrega columnas privadas del propietario ni mensajes de postulaciones.
El texto libre publicado no dispone de detección automática de PII: P1 no promete
anonimizar datos que un autor haya incluido en título, descripción o ubicación.

Ver propuesta conserva el detalle canónico. Postularme conduce al detalle, donde
permanece el formulario POST existente con CSRF. La presentación llama a
proposal_application_eligibility() y además oculta la acción al propietario y a
quien ya se postuló. La política persistida P0 sigue siendo autoridad; nunca se
habilita por flags de sesión. La creación conserva sus permisos existentes.
Home dirige Ver oportunidades a /propuestas; footer ya lo hacía. Navbar global
sin cambios: conserva su entrada al segmentador del Home.

## Límites y pendientes P2

Sin modelos, migraciones, nuevos permisos, estados, pagos ni cambios contractuales.
SINGLE y EXTERNAL permanecen vigentes; cantidad_profesionales no se muestra como
capacidad operativa. Sin monto firme, vencimientos, renovación, ranking, guardados,
verificaciones inventadas ni datos demostrativos en producción.
El detalle directo de propuestas cerradas/canceladas conserva su comportamiento
anterior; su política de visibilidad necesita definición posterior. No aparecen
en este portal. Quedan pendientes oferta firme, vigencia/renovación y contratación
múltiple, cada una con su diseño de dominio y autorización independientes.

## Evidencia

Prueba focal: tests/test_proposal_portal_p1.py. Ocho pruebas permanentes cubren datos
ORM, privacidad de columnas, filtros, paginación, inválidos, XSS, cero escrituras,
consultas constantes por página, elegibilidad persistida y vacío.
P0 y regresiones contractuales se ejecutan en SQLite en memoria. El gate real de
concurrencia PostgreSQL no se sustituye por SQLite y permanece omitido.
Revisión de navegador con fixtures aisladas (no datos de producción): 1440, 1280,
1024, 770, 768, 390 y 320 píxeles CSS efectivos, ambos temas. Sin overflow horizontal
ni controles del portal menores de 44 × 44. Filtro Ubicación verificado mediante
formulario real; foco por teclado visible; consola sin errores ni advertencias.
Contraste de texto calculado desde estilos computados y fondos compuestos: mínimo
4.56:1 claro y 8.01:1 oscuro. Bordes de campos reforzados localmente con #64748b.
Esto es revisión focal; no equivale a una certificación integral de accesibilidad.
Capturas externas al repositorio: p1-light-desktop.jpg, p1-dark-desktop.jpg,
p1-light-mobile.jpg y p1-dark-mobile.jpg. Preview temporal SQLite, sin PostgreSQL.

## Validación independiente

Testing independiente ejecutado el `2026-10-04T15:04:39-03:00` sobre
`feature/ux-ui-foundation` en `26ee98d0e0b18c3589fcf39f151ed70929309930`.

- Paquete focal y regresiones: 120 ejecutadas, 119 aprobadas, una omitida y
  cero fallos/errores. La omisión corresponde a concurrencia real que SQLite
  en memoria no representa.
- Suite completa: 891 ejecutadas, 884 aprobadas, siete omitidas y cero
  fallos/errores. Las omisiones corresponden a cuatro gates PostgreSQL sin
  `TRAX_POSTGRES_TEST_URL`, una concurrencia PostgreSQL, una comprobación
  exclusiva de imagen Docker y la zona IANA no disponible en el runtime.
- Algunos tests históricos de la suite ejecutaron upgrade/downgrade Alembic
  únicamente sobre SQLite temporal aislado. No se accedió ni modificó
  `trax_db` y el gate PostgreSQL quedó `NO EJECUTADO`.
- `compileall` de `app` y `scripts`, UTF-8, enlaces relativos y
  `git diff --check`: aprobados.
- QA real: temas claro y oscuro; anchos efectivos 1440, 1280, 1024, 770, 390
  y 320 px. El backend del navegador no expuso 768 exactos por escala; se
  comprobaron 767 y 769 px sin overflow como fronteras adyacentes.
- Altura mínima interactiva observada: 44 px. Contraste textual mínimo medido:
  5.48:1 en claro y 8.02:1 en oscuro. Foco visible y consola sin errores.
- Filtros combinados, paginación con parámetros, estado vacío, exclusión de
  cerradas/canceladas, actor pendiente sin CTA y actor aprobado con CTA hacia
  el formulario protegido: aprobados con fixtures SQLite aisladas.

Dictamen: `PROPUESTAS_P1_APROBADO_PARA_COMMIT`. La aprobación no acredita el
gate PostgreSQL omitido ni autoriza commit, push, merge o deploy.


## P1.1 — Accesos y refinamiento visual

Timestamp: 2026-10-04T15:51:19-03:00. Base: 557d4fca84ea7355f3832ebf14b8a3c6ab4eb020.
Estado: implementado, pendiente de Testing independiente. La aprobación histórica
P1 precedente no equivale a aprobación de este nuevo incremento.

Operaciones → Propuestas usa url_for del endpoint operations.marketplace_propuestas,
sin paso por Home. En /propuestas el enlace declara aria-current y el resumen de
Operaciones presenta el acento activo, tanto en navbar como en drawer.

El campo histórico del Home mezclaba la etiqueta Industria o rubro y opciones de
especialidades con name=categoria. Se sustituyó solamente en modo Propuestas por
un campo explícito Rubro, name=rubro, texto libre máximo 120 caracteres. Ubicación
se envía como ubicacion, también con máximo 120 caracteres. No se convierten las
antiguas etiquetas ni se agrega taxonomía. El formulario GET envía ambos valores
al endpoint canónico. Los otros modos permanecen intactos. Sin JavaScript, el Home
ofrece un enlace noscript al portal: el segmentador original requiere JavaScript;
el formulario y filtros del portal sí funcionan de forma nativa sin JavaScript.

Chips de filtros activos: muestran nombre y valor escapado, cada enlace remueve
solo su filtro, preserva los restantes y per_page y vuelve a página 1. Limpiar
elimina todos. Se conservan semántica ilike, validación y paginación de P1.
Los filtros inválidos mantienen HTTP 400 con pantalla local amigable y acción
Limpiar filtros y volver; no se vuelcan valores inválidos ni detalles internos.
Los errores generales reutilizan la infraestructura vigente.

Composición: búsqueda prioritaria, panel lateral diferenciado, tarjetas con acento
naranja, superficies y sombras DS v2, presupuesto destacado y hover sin traslación.
Descripción de tarjeta limitada a tres líneas; el detalle conserva el texto completo.
En móvil el buscador antecede a filtros; details/summary nativo permite abrir/cerrar.
Un controlador pequeño, sin dependencias, establece abierto desde 1024 px y cerrado
en tamaños menores al cargar o cruzar ese breakpoint; la elección manual se conserva
entre cambios de tamaño dentro del mismo rango. Sin JS permanece abierto y plegable.
Se conservan permisos, conteos públicos aprobados en P1, etiqueta Presupuesto estimado
y todos los límites de dominio anteriores. Sin nuevas capacidades de contratación.

Validaciones P1.1: tres pruebas permanentes añadidas al archivo focal (11 métodos
P1/P1.1 en total); navegación anónima/autenticada, Home, parámetros y eliminación
individual. EOF corregido a un solo salto final. Focales iniciales 41/41; suite
completa SQLite 894 ejecutadas, 887 aprobadas y 7 omitidas, sin fallos/errores.
Después de agregar el estado 400 amigable: 62/62 focales, navegación, P0, seguridad
y estados de error. No se repitió toda la suite tras ese último ajuste acotado.
compileall app scripts y sintaxis Node del controlador: correctos.

Navegador real: Home → Propuestas filtradas por Tableros/Palermo; búsqueda parcial
rubro=a → página 2 con parámetros conservados; quitar chip; limpiar; detalle;
Operaciones → portal. Matriz claro/oscuro de 1440,1280,1024,770,768,390,320 píxeles
CSS efectivos, filtros abiertos y cerrados (28 combinaciones): sin overflow ni
controles visibles menores a 44 × 44. Teclado Enter/Tab y foco visibles. Texto de
108 caracteres en chip a 320 px sin overflow. Error 400 deliberado y recuperación
comprobados. Contraste de texto estable mínimo 4.56:1 claro y 8.01:1 oscuro; fondos
DS v2. No es certificación integral WCAG. Preview únicamente con fixtures SQLite
sin datos de producción; capturas p11-light-desktop.jpg, p11-dark-desktop.jpg,
p11-light-mobile.jpg, p11-dark-mobile.jpg fuera del repositorio.

Pendientes: retest independiente y aprobación visual. Se mantienen los pendientes
P2 documentados arriba, incluida visibilidad directa de cerradas/canceladas.

### Validación independiente P1.1

Testing independiente ejecutado el `2026-10-04T16:13:06-03:00` sobre la rama
`feature/ux-ui-foundation`, HEAD
`557d4fca84ea7355f3832ebf14b8a3c6ab4eb020`, con staging vacío y los 12 paths
P1.1 declarados.

- Focal P1/P1.1: 11 ejecutadas y 11 aprobadas.
- Navegación, Home, navbar, DS, autenticación y errores: 59/59.
- Regresiones de Propuestas y contratos: 73 ejecutadas, 72 aprobadas y una
  omitida por requerir concurrencia PostgreSQL real.
- Suite completa final: 894 ejecutadas, 887 aprobadas, siete omitidas, cero
  fallos y cero errores en 209.845 segundos. Se ejecutó una sola vez después del
  último cambio ejecutable; la actualización documental posterior solo registra
  los resultados y no altera código ni pruebas.
- Las siete omisiones son cuatro gates PostgreSQL sin URL segura, una concurrencia
  PostgreSQL, una comprobación exclusiva de imagen Docker y una zona IANA no
  disponible. PostgreSQL real y Docker no fueron ejecutados ni acreditados.
- `compileall app scripts`, sintaxis Node, UTF-8, enlaces relativos, whitespace,
  salto final y `git diff --check`: aprobados.

En navegador real se verificaron el acceso directo Operaciones → Propuestas,
el recorrido Home con rubro/ubicación, caracteres especiales, paginación, chips,
limpieza, error HTTP 400 real anónimo/autenticado, estado vacío, privacidad,
escape XSS y elegibilidad centralizada. La matriz claro/oscuro cubrió 1440, 1280,
1024, 770, 768, 390 y 320 px sin overflow, con objetivos mínimos de 44 px, foco
visible, panel plegable operable mediante Enter y estado expandido/colapsado
expuesto por la semántica nativa. La consola no registró warnings ni errores.

No se utilizó ni modificó `trax_db`. El preview y las fixtures SQLite en memoria
fueron retirados. No se hallaron defectos P0, P1, P2 o P3 atribuibles al incremento.
Dictamen: `PROPUESTAS_P1_1_APROBADO_PARA_COMMIT`. Esto no autoriza commit, push,
merge ni deploy, y no acredita los gates omitidos.


## Ajuste visual posterior de botones y encabezado

Timestamp: 2026-10-04T16:23:51-03:00. Base 557d4fc. Pedido directo del responsable del producto.
El encabezado pequeño pasa a EXPLORÁ OPORTUNIDADES, turquesa y estilo tipográfico
similar al segmento de Propuestas del Home. Los botones del portal (crear/ingresar,
buscar, aplicar filtros, ver propuesta y restantes acciones del componente) usan
fondo negro y texto blanco en claro; fondo blanco y texto oscuro en oscuro.
Se reutilizan tokens DS v2 y se conservan foco, tamaño y destinos.
Sin cambios de Home, navegación, datos, permisos ni flujo. Once pruebas focales
aprobadas en SQLite memoria y revisión visual claro/oscuro. Pendiente aprobación
visual de este ajuste; se preserva el historial de Testing anterior.


---

## 2026-10-04T16:58:01-03:00 — Propuestas P1.1: carrusel fotográfico del encabezado

Estado: READY_TO_RESUME — implementado, pendiente de Testing independiente.
Origen: laptop; responsable: implementador local. Rama: feature/ux-ui-foundation.
HEAD conservado: 557d4fca84ea7355f3832ebf14b8a3c6ab4eb020; staging vacío.
Se preservaron los doce paths previos autorizados. No hubo commit, push, merge,
PR ni despliegue: no están autorizados. No se actualizó el remoto.

Se incorporaron 12 WebP en `app/static/images/proposals/hero/`, exclusivamente
como fondo del encabezado. Los originales quedaron intactos (hash antes/después).
Todos decodifican, sin archivos omitidos. Pillow 11.3.0: RGB, orientación EXIF,
WebP quality=80/method=6, sin ampliar, sin metadatos EXIF/XMP/ICC copiados.
Dimensiones comunes: 1448 × 1086. Orden determinista por nombre de fuente:

| Fuente | Destino | Bytes |
| --- | --- | ---: |
| 03.png | proposal-hero-01.webp | 141558 |
| 04.png | proposal-hero-02.webp | 165504 |
| 05 (2).png | proposal-hero-03.webp | 122510 |
| 05.png | proposal-hero-04.webp | 120998 |
| 06.png | proposal-hero-05.webp | 111668 |
| 07.png | proposal-hero-06.webp | 138952 |
| 09.png | proposal-hero-07.webp | 140786 |
| 10.png | proposal-hero-08.webp | 124142 |
| 11.png | proposal-hero-09.webp | 135060 |
| 13.png | proposal-hero-10.webp | 120942 |
| 16.png | proposal-hero-11.webp | 87352 |
| 20.png | proposal-hero-12.webp | 92420 |

El controlador existente `emergency-hero-carousel-v1.js` admite un modo fade
optativo: Propuestas usa 6000 ms / 700 ms, dos capas reutilizables, caché y carga
progresiva. Urgencias conserva su desplazamiento de 6500 ms / 900 ms.
Guardas de inicialización, visibilidad, pagehide/pageshow y BFCache preservadas.
No hay controles, vínculos ni foco en la capa decorativa; alt vacío/aria-hidden.
La primera imagen tiene src nativo, dimensiones y prioridad alta; permanece sin
JavaScript. Reduced motion evita autoplay y muestra la primera fotografía.
Las fallas de imágenes siguientes se omiten conservando el fondo válido.

Overlay local azul noche RGB(7,18,32), opacidades .90 / .74 al 60% / .70 al 100%.
Título blanco, subtítulo #e2e8f0 y encabezado pequeño #67e8f9; mismos colores sobre
las fotografías en ambos temas. Se reforzó el extremo derecho desde .62 a .70
para garantizar contraste incluso sobre blanco: mínimos calculados 7.08:1,
5.74:1 y 4.89:1 respectivamente. Sin cambios de datos, permisos, modelos,
migraciones, contratación, navbar ni estilos globales en este incremento.

Validación ejecutada sobre SQLite en memoria (sin PostgreSQL ni Docker):
- 54 pruebas OK: test_proposal_hero_carousel, test_proposal_portal_p1,
  test_proposal_eligibility, test_emergency_hero_carousel, test_emergency_entry,
  test_home_hero_carousel y test_navbar_drawer_ux04a.
- Reejecución focal final: test_proposal_hero_carousel, 2/2 OK, sin advertencias
  por respuestas de recursos abiertas.
- Node tests/js/emergency_hero_carousel.test.js: OK, incluidos fade 6000/700,
  inicialización única, reduced motion y BFCache; regresión Urgencias OK.
- compileall app scripts y sintaxis del controlador JavaScript: OK.
- Las doce imágenes responden HTTP 200 en el cliente Flask y decodifican.
- Navegador real, preview aislado en puerto 54873: claro/oscuro en 1440, 1280,
  1024, 770, 768, 390 y 320 px. Sin overflow horizontal; imagen cargada;
  buscador fuera del hero. Altura 208 px en escritorio/tablet, 241.81 px a 390
  y 301.33 px a 320; el texto puede crecer sin recorte. Rotación observada,
  sin vacíos observados; consola sin advertencias ni errores registrados.
- Evidencia de escritorio y móvil en ambos temas guardada fuera del repositorio.

Limitación de evidencia: no se emuló reduced motion ni JavaScript deshabilitado
visualmente en el navegador disponible; se verificaron mediante pruebas del
controlador y contrato HTML/CSS. No se ejecutó suite completa ni auditoría AA
integral; el cálculo anterior corresponde al texto del hero. Testing debe
completar esas comprobaciones y revisar transiciones en su entorno.

Archivos de este incremento: app/templates/listado_propuestas.html,
app/static/css/proposals-portal-p1.css, app/static/js/emergency-hero-carousel-v1.js,
tests/js/emergency_hero_carousel.test.js, tests/test_proposal_hero_carousel.py,
los doce assets indicados, docs/REQUISITOS/PROPUESTAS_P1.md y este handoff.
No hay fallas focales conocidas. Riesgo principal: controlador compartido,
cubierto por regresión, pendiente de retest independiente. Próximo paso:
revisar `/propuestas` en el preview aislado y ejecutar Testing del incremento;
no integrar ni tocar bases compartidas. Las aprobaciones históricas de P1.1
no aprueban automáticamente este carrusel. Estado final pendiente de Testing.

---

## 2026-10-04T17:14:45-03:00 — Gate final P1.1 con carrusel fotográfico

Estado: `PROPUESTAS_P1_1_CARRUSEL_APROBADO_PARA_COMMIT`.
Responsable: `03 — Testing - Test Executor` independiente. Origen: laptop.
Rama: `feature/ux-ui-foundation`. HEAD evaluado y conservado:
`557d4fca84ea7355f3832ebf14b8a3c6ab4eb020`. Staging vacío.

El inventario final contiene exclusivamente los 27 paths documentados: los doce
paths de P1.1 previos, el controlador y sus dos pruebas, y los doce WebP del
carrusel. No hay cambios en modelos, migraciones, esquema, dependencias,
permisos, elegibilidad, pagos, contratación o estados.

Evidencia ejecutada sobre SQLite en memoria, sin `trax_db`, PostgreSQL, Alembic
operativo ni Docker:

- focales P1/P1.1: 17 ejecutadas, 17 aprobadas, cero fallos, errores u omisiones;
- Urgencias, Home y controlador compartido: 37/37 aprobadas;
- navegación, estados de error, Design System y autenticación: 40/40 aprobadas;
- Node del controlador: Propuestas 6000/700, inicialización única, BFCache y
  reduced motion aprobados; regresión de Urgencias 6500/900 aprobada;
- suite completa final, ejecutada una sola vez: 896 ejecutadas, 889 aprobadas,
  siete omitidas, cero fallos y cero errores, en 229.359 segundos;
- las siete omisiones corresponden a cuatro gates PostgreSQL sin URL exclusiva,
  una concurrencia PostgreSQL, una comprobación exclusiva dentro de imagen
  Docker y una zona IANA ausente en el entorno;
- `compileall`, sintaxis de ambos JavaScript, UTF-8, whitespace, salto final y
  `git diff --check`: código de salida cero.

Los doce WebP son locales, decodificables, RGB, 1448 × 1086, no animados, sin
EXIF/XMP/ICC y pesan en total 1.501.892 bytes. GET y HEAD devolvieron 200 con
`image/webp`; las recargas condicionales observadas devolvieron 304 y no hubo
404. La primera imagen crítica pesa 141.558 bytes. El navegador solicitó solo
esa imagen desde HTML y precargó la siguiente después de inicializar el
controlador; las restantes se solicitaron progresivamente al avanzar. No hubo
descargas completas repetidas: la revalidación usó 304.

Validación manual en navegador real, temas claro y oscuro, a 1440, 1280, 1024,
770, 768, 390 y 320 px: cero overflow horizontal, cero solapamientos, recorte
central, buscador y filtros fuera del encabezado, controles visibles de al menos
44 px, foco de teclado visible y consola limpia. El encabezado conservó 208 px
en escritorio/tablet y creció por reflow a 241,8 px en 390 y 301,3 px en 320,
sin cambiar de altura durante la rotación. Los contrastes conservadores sobre
el punto más claro del overlay son 7,10:1 para blanco, 5,76:1 para subtítulo y
4,90:1 para turquesa.

Movimiento reducido se emuló en el navegador: la primera imagen permaneció
estática durante siete segundos, sin autoplay ni errores. JavaScript se retiró
en el harness aislado y se recargó: quedaron cero scripts, la primera imagen y
el contenido HTML continuaron visibles, y la búsqueda GET con rubro `Tableros`
y ubicación `Palermo` devolvió resultados filtrados sin overflow ni errores.
La capa fotográfica es decorativa (`alt=""`, `aria-hidden="true"`) y el texto
informativo permanece como HTML real.

Se revalidaron acceso anónimo, CLIENTE y PROFESIONAL verificado. Este último vio
los doce CTA elegibles de la página; CLIENTE no vio ninguno. `Ver propuesta`,
filtros individuales/combinados, caracteres especiales, chips, limpieza,
paginación, orden, solo `PUBLICADA`, GET sin escrituras, HTTP 400 real, XSS y
privacidad conservaron el contrato aprobado.

No se detectaron hallazgos P0, P1, P2 ni P3. Esta aprobación habilita solicitar
el commit del árbol validado; no ejecuta ni autoriza automáticamente commit,
push, PR, merge o deploy.


## Propuestas en el espacio privado profesional — 2026-10-30T10:23:56-03:00

Estado: IMPLEMENTADO LOCALMENTE; pendiente de revisión visual y testing independiente.
Cristian aprobó el boceto del panel privado como referencia de composición en el
encargo de esta sesión. Sus cifras, nombres y marca simplificada no se trasladan
al producto. La aprobación del boceto no aprueba visualmente esta implementación.

### Comportamiento y conexiones

Ruta canónica del menú: `/profesional/propuestas`. Tres vistas GET mediante
`vista=disponibles`, `vista=postulaciones` y `vista=publicaciones`, enlaces nativos
con `aria-current`. La primera reutiliza `build_proposal_portal`, sus filtros de
industria/categoría/rubro/ubicación, opciones reales, orden descendente, límites
y conteos agregados. Los enlaces de filtros/paginación conservan el destino privado.
Las otras vistas filtran por el actor persistido, paginan de a 12 y muestran
estados/fechas reales; publicaciones usa owner_user_id con fallback a cliente_id.
La relación de propuesta en postulaciones se carga con joinedload. Los contratos
visibles se consultan con ownership profesional, sin crearlos durante GET.

Shell, logo, menú, tema y notificaciones existentes conservados. Encabezado,
tres pestañas, búsqueda por rubro, filtros nativos desplegables, tarjetas con acento
naranja y paginación; sin banner ni selector entre módulos. CSS encapsulado en
`.pp-workspace`, componentes/tokens DS v2 y composición apilada móvil. Más recientes
es una etiqueta del orden real, sin opciones ficticias. Presupuesto estimado muestra
cero cuando existe; ausencia de importe se presenta como presupuesto a convenir.
Estados vacíos específicos, parámetros inválidos 400 y fallo de consulta 503 con
reintento seguro; no se muestran excepciones internas.

Detalle y creación mantienen `/propuestas/<id>` y `/propuestas/nueva`. Para un
profesional activo se renderizan dentro del shell privado, con regreso a una vista
permitida; clientes/anónimos conservan su presentación pública. El origen se
transporta como `vista`, limitado a tres valores, nunca como destino arbitrario.
Postularme abre el formulario; GET no postula. Ya te postulaste y autopostulación
se resuelven con los datos/evaluador canónicos. Gestión del propietario reutiliza
aceptación, descarte y cancelación existentes, con sus POST/CSRF y ownership.

### Ajuste contractual acotado y discrepancia documental

El código de creación ya admitía un profesional activo como publicador; Master Spec
5 describía sólo al cliente, y la fábrica contractual exigía CLIENTE. El encargo
aprueba explícitamente publicar una necesidad para contratar a otro profesional.
Por ello `create_contract_from_proposal_application` admite CLIENTE/PROFESIONAL
activos, siempre con ownership de la propuesta persistida. El lado contratante
profesional se admite exclusivamente en contratos de origen PROPOSAL para las
operaciones canónicas de propietario. DIRECT y BUDGET conservan la exigencia CLIENTE.
No se crea otro modelo ni máquina de estados: SINGLE, contrato inicial CREADA,
EXTERNAL, efectos/eventos/auditoría/notificaciones e idempotencia existentes.
La confirmación y su replay por ese propietario se prueban; no se amplía reputación
ni permiso de crear reseñas. El detalle contractual PROPOSAL usa el shell privado
para profesionales mediante el helper de layout existente, sin editar Presupuestos.

### Formularios y seguridad

Importes no finitos, conversiones inválidas, negativos y exceso de capacidad de
Numeric se rechazan antes de persistir (presupuesto Numeric(10,2), pretensión
Numeric(12,2)). Se conserva la precisión/semántica de almacenamiento actual.
Errores recuperables de postulación devuelven 400 con campos escapados, CSRF y
contexto, sin llevar textos a la URL; antes redirigían y perdían los campos.
En recuperación, el importe usa input textual con inputmode decimal para que el
navegador no borre un valor inválido; el servidor sigue validándolo. La creación
mantiene su respuesta 400 con datos repoblados. Éxito conserva redirect y un único
registro. No se alteran elegibilidad, cuentas activas, verificación ni planes.
Los campos libres del autor no se anonimizan automáticamente; no se agregan datos
privados del propietario a tarjetas ni mensajes ajenos en vistas propias.

### Inventario atribuible

Nuevos (6):
- `app/services/professional_proposals_service.py`.
- `app/static/css/professional-proposals.css`.
- `app/templates/professional_proposals.html`.
- `app/templates/proposal_layout.html`.
- `tests/test_professional_proposals.py`.
- `tests/postgresql_professional_proposals.py` (gate explícito, fuera del discovery habitual).

Existentes intervenidos (12):
- `app/routes/main_routes.py`: entrada privada y errores seguros.
- `app/routes/operation_routes.py`: contexto, recuperación, regresos y layout contractual PROPOSAL.
- `app/services/proposal_portal_service.py`: endpoint de navegación opcional, default público intacto.
- `app/services/proposal_service.py`: validación monetaria acotada.
- `app/services/contracting_core_service.py`: publicador profesional propietario de PROPOSAL.
- `app/services/contract_service.py`: lado contratante profesional sólo en PROPOSAL.
- `app/templates/detalle_propuesta.html`: contexto/CSRF de origen y repoblado.
- `app/templates/nueva_propuesta.html`: contexto y recuperación monetaria.
- `app/templates/components/_professional_navigation.html`: selección en formularios canónicos.
- `docs/REQUISITOS/PROPUESTAS_P1.md`, `docs/HANDOFFS/ACTIVE_HANDOFF.md`, `docs/CHANGELOG.md`.

### Validación realmente ejecutada

- Paquete Python de regresión: 86 pruebas, 85 aprobadas y una omitida explícitamente
  (`test_real_concurrent_independent_sessions`, no representa PostgreSQL en SQLite).
  Comando: `python -B -m unittest tests.test_professional_proposals tests.test_proposal_portal_p1 tests.test_proposal_eligibility tests.test_sprint7_proposal_to_contract tests.test_professional_workspace_ux tests.test_professional_workspace_ux_002 tests.test_sprint7_contracting_core tests.test_sprint7_contracting_foundations tests.test_sprint7_contracting_p0_iteration1 tests.test_sprint7_contracting_p1_iteration2 tests.test_sprint7_budget_to_contract`.
- Focal final: `python -B -m unittest tests.test_professional_proposals`: 10/10;
  incluye un caso nuevo de ciclo contractual del publicador profesional y su replay.
  Las nueve pruebas que solapan el paquete anterior no se suman como casos nuevos.
- PostgreSQL 16 descartable: 4/4 del gate `ProfessionalProposalsPostgres`:
  `test_professional_acceptance_concurrency`, `test_application_concurrency_no_duplicates`,
  `test_acceptance_rollback`, `test_other_domains_keep_client_role`.
  Migración al head existente `20261028_01` sólo en `proposals_qa`, puerto 55481.
  Inicialmente se intentó psycopg no instalado; se usó psycopg2 ya disponible.
  La restricción de red del sandbox exigió ejecución autorizada fuera de él.
- Chrome/Playwright: 30 combinaciones (tres pestañas × 320/390/768/1024/1440 ×
  claro/oscuro), sin overflow; controles primarios de al menos 44 px. Dos recorridos
  con/sin JavaScript real: filtros GET, error, campos conservados, reenvío y regreso.
  Cuatro comprobaciones adicionales de estados sin coincidencias/parámetro inválido,
  foco y reduced-motion real en 390/1440 y ambos temas. Contraste focal de botón:
  4.56:1 claro, 8.02:1 oscuro. No constituye auditoría AA integral.
- Los intentos iniciales de automatización tuvieron timeouts con click/espera de
  navegación; se verificó después el envío nativo por teclado. Se reiniciaron datos
  sintéticos para separar intentos previos de postulaciones ya creadas.
- Persistió un aviso CSP de script inline del shell (base.html conserva hash).
  No se declara consola limpia. Sin JS se verificó el flujo en tema claro; la
  selección/persistencia interactiva de tema requiere el mecanismo JS existente.
- Sin controladores productivos modificados: no se repitieron pruebas Node.
  Sintaxis Python por AST, UTF-8 sin BOM/NUL/U+FFFD y git diff --check comprobados.

[Evidencia durable, logs, baseline y capturas](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/professional-proposals-20261030/).
Capturas representativas: `review-dark-1440.png`, `review-light-1440.png`,
`review-dark-390.png`, `review-light-390.png`; también capturas de las tres vistas.
Fixtures de preview exclusivamente sintéticas, fuera del producto; fábrica normal,
sin composición de simulador. Preview 54963 detenido y contenedor PostgreSQL propio
retirado. Docker habitual, bases compartidas y cuenta QA no modificados.

### Integridad, límites y revisión

Baseline: `feature/professional-workspace-ux`, HEAD
`2e552f2fdc57c152c97f0486050574696f6b250e`, 108 paths pendientes, staging vacío,
618 archivos con SHA-256. Final: 18 archivos de este incremento (6 nuevos),
121 paths pendientes, staging vacío; rama/HEAD conservados. Los otros 606 archivos
del baseline conservan hash, incluidos INDEX, Presupuestos y Urgencias. En archivos
compartidos se conservaron comportamientos previos y se delimitaron cambios arriba.
Sin nuevas migraciones, dependencias, Git mutable ni modificación de modelos.

Revisión tras actualización manual de web:
`http://127.0.0.1:5050/profesional/propuestas` y sus tres valores de `vista`.
Comandos sugeridos para Cristian, NO ejecutados sobre el entorno habitual:

```powershell
docker compose --env-file .env.example -p mandobra_stabilization -f docker-compose.stabilization.yml build web
docker compose --env-file .env.example -p mandobra_stabilization -f docker-compose.stabilization.yml up -d --no-deps web
```

Pendientes: revisión visual de la implementación, testing independiente, accesibilidad
integral y dispositivo móvil físico. Continúan fuera de alcance renovación,
vencimientos nuevos, contratación múltiple, oferta profesional como segundo tipo,
pagos/facturación/canales externos y recepción de Urgencias. La política histórica
de lectura directa de propuestas cerradas/canceladas no se amplía. El rediseño
específico de creación/detalle sigue pendiente; sus campos históricos no habilitan
MULTIPLE. No se declara producción ni integración.

## Corrección focal P3 del gate PostgreSQL — 2026-10-30T11:38:15-03:00

Estado: READY_TO_RESUME. **P3 CORREGIDO LOCALMENTE; PENDIENTE DE RETEST INDEPENDIENTE.**
Laptop; rama `feature/professional-workspace-ux`, HEAD base conservado
`2e552f2fdc57c152c97f0486050574696f6b250e`. Staging vacío.

El hallazgo de QA identificó herencia de casos CLIENTE con un propietario convertido
a PROFESIONAL. Se extrajo la preparación a `tests/postgresql_contracting_fixture.py`,
un mixin sin casos ni herencia de TestCase. Cada suite declara su OWNER_ROLE:
PROFESIONAL para el gate especializado y CLIENTE para la suite original.
Cada caso comprueba el rol persistido. No se agregaron omisiones ni expectedFailure.
Los cuerpos AST de las cuatro pruebas especializadas y las ocho originales se
conservaron íntegros. El descubrimiento del módulo especializado pasó de 20 casos
(incluida la clase importada) a sus cuatro casos propios; el original conserva ocho.

Validación nueva: ejecución completa conjunta sobre PostgreSQL 16 descartable,
**12/12 aprobadas en 20.720 s**, sin omisiones: 4 PROFESIONAL y 8 CLIENTE.
No se seleccionaron nodos individuales. Se conservaron las comprobaciones de
concurrencia, rollback y restricciones de dominio. La preparación migró únicamente
la base descartable; no hubo cambios de migraciones ni acceso a la base habitual.
El contenedor exclusivo `mandobra-proposals-p3-20261030` fue retirado al terminar.
Docker habitual y cuenta QA permanecieron sin modificaciones.

Comando reproducible del gate completo, exclusivamente con una instancia descartable
`proposals_qa` en `127.0.0.1:55481` y credenciales de esa instancia:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TRAX_POSTGRES_TEST_URL='postgresql+psycopg2://USUARIO:CLAVE@127.0.0.1:55481/proposals_qa'
$env:TRAX_POSTGRES_TEST_ALLOW_RESET='1'
$env:DATABASE_URL=$env:TRAX_POSTGRES_TEST_URL
.\.venv\Scripts\python.exe -B -m unittest -v tests.postgresql_professional_proposals
```

Comando efectivamente ejecutado para ambos conjuntos completos, con las variables
anteriores configuradas para la instancia sintética exclusiva:

```powershell
.\.venv\Scripts\python.exe -B -m unittest -v tests.postgresql_professional_proposals tests.postgresql_contracting_concurrency_e2e
```

Estos comandos truncan la base de pruebas: nunca apuntarlos a bases compartidas.
Evidencia nueva: `proposals-p3-gate-20261030/gates-complete.log`, baseline SHA-256,
comparación de cuerpos de pruebas e integridad final. Ubicación durable:
[carpeta de evidencia](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/proposals-p3-gate-20261030/).
Los resultados anteriores de PostgreSQL seleccionados, Python, navegador y Node
permanecen históricos y no se contabilizan como ejecuciones nuevas. No se repitieron
navegador ni Node: interfaces y controladores no cambiaron.

Inventario focal: `tests/postgresql_professional_proposals.py`,
`tests/postgresql_contracting_concurrency_e2e.py`, nuevo
`tests/postgresql_contracting_fixture.py`, `docs/REQUISITOS/PROPUESTAS_P1.md`,
`docs/HANDOFFS/ACTIVE_HANDOFF.md` y `docs/CHANGELOG.md`.
Baseline: 121 paths pendientes y 624 archivos; cierre: 123 paths pendientes,
staging vacío. Los otros 619 archivos del baseline conservan SHA-256, incluidos
INDEX, Presupuestos, Urgencias y los ajustes autorizados de botones y estados vacíos
en las tres pestañas de Propuestas. Sintaxis Python, UTF-8 y git diff --check correctos.

Sin cambios productivos, permisos, interfaces, modelos ni dependencias. No hubo
commit, push, PR ni merge porque no están autorizados; no se consultó sincronización
remota. Próximo paso: retest independiente del gate completo y su suite original
con los comandos anteriores en PostgreSQL descartable. Preservar el trabajo previo;
no ejecutar estos gates contra la base habitual. No se declara aprobación visual,
integración ni habilitación productiva.

## Cierre técnico de Propuestas: retest P3 y ajustes visuales — 2026-10-30T12:22:37-03:00

Estado: COMPLETED (registro documental). Laptop; responsable: agente local MANDOBRA.
Dictamen independiente del **2026-10-30T12:16:21-03:00**:
**P3 CERRADO; SIN NUEVOS HALLAZGOS P0–P3 EN EL ALCANCE EVALUADO.**
Este dictamen sustituye el estado pendiente de retest de la corrección P3,
sin borrar sus antecedentes ni extender el alcance evaluado.

Resultados del retest independiente, no de una nueva ejecución en este cierre:

- PostgreSQL descartable: módulo profesional completo, **4/4 PROFESIONAL**;
  módulo original completo, **8/8 CLIENTE**. Doce casos únicos satisfactorios,
  sin selección manual de nodos ni omisiones en estos dos módulos.
- Navegador: **18 escenarios visuales nuevos**, doce con JavaScript y seis
  realmente sin JavaScript. Se acreditan los últimos cambios autorizados de las
  tres pestañas, no por continuidad de la evidencia visual anterior.
- Mensajes vacíos centrados y CTA redundantes retirados en Mis postulaciones y
  Mis publicaciones. Los filtros permanecen exclusivamente en Propuestas disponibles;
  Aplicar/Limpiar mantienen presentación consistente y navegación GET.
- El informe registra cero overflow, recortes o fallos de objetivos interactivos,
  foco visible y conservación de integridad. Se conserva el aviso CSP heredado.

Evidencia durable existente, sin recrearla:
[proposals-p3-visual-retest-20261030](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/proposals-p3-visual-retest-20261030/),
con `execution-summary.json`, `postgres-professional.log`, `postgres-original.log`,
`browser-results.json`, capturas e informes de integridad. Sus timestamps de archivo
preceden al timestamp del dictamen comunicado por el responsable.

Los resultados y omisiones anteriores permanecen históricos, incluido el caso
omitido de la tanda Python inicial. No se suman repeticiones como cobertura adicional
ni se presenta este retest focal como suite integral. No se ejecutaron pruebas,
Node, navegador, Docker ni migraciones durante este registro documental.
Se conservan los límites funcionales y pendientes anteriores, accesibilidad integral,
dispositivo móvil físico y CSP heredada. **La aprobación visual del usuario permanece
pendiente.** No se declara certificación AA, integración ni habilitación productiva.

Integridad inicial/final: rama `feature/professional-workspace-ux`, HEAD
`2e552f2fdc57c152c97f0486050574696f6b250e`, 123 paths pendientes y staging vacío.
Únicos archivos modificados en este cierre: `docs/REQUISITOS/PROPUESTAS_P1.md`,
`docs/HANDOFFS/ACTIVE_HANDOFF.md` y `docs/CHANGELOG.md`.
Los otros 622 archivos del inventario de 625 conservan SHA-256, incluidos INDEX,
Presupuestos, Urgencias, código, pruebas y ajustes visuales autorizados.
UTF-8 y git diff --check verificados. Sin operaciones Git mutables; commit, push,
PR y merge no realizados por estar fuera del alcance. Sin comprobación remota nueva.
Próximo paso: revisión visual de Cristian. Para retomar, reconfirmar identidad e
inventario y conservar el paquete pendiente; no asumir autorización de integración.

## Formulario Crear propuesta profesional — 2026-10-30T12:53:38-03:00

Estado: READY_TO_RESUME. Boceto aprobado por Cristian el 2026-10-30;
**FORMULARIO REDISEÑADO LOCALMENTE; PENDIENTE DE REVISIÓN VISUAL Y TESTING INDEPENDIENTE.**
La aprobación del boceto no constituye aprobación visual de esta implementación.

Se conserva el shell profesional, marca oficial, notificaciones, tema y Propuestas
activo. Encabezado compacto con Volver a Propuestas, Crear propuesta y
«Contá qué necesitás y recibí postulaciones.». Dos tarjetas alineadas arriba:
Datos del proyecto/Profesional que buscás y Ubicación y condiciones. Hasta 1024 px
se apilan en ese orden. Pie con aviso de no contratación, Cancelar y Publicar propuesta.
Volver y Cancelar conservan el regreso privado y su vista. CSS bajo `.pc-create`;
componentes y tokens DS v2, botón primario naranja, sin dependencias ni nuevo JS.
Se prioriza el contrato local: los doce campos conservan definiciones exactas,
incluidos límites, opciones, nombres, valores y recuperación escapada. El campo
cantidad no cambia la contratación SINGLE. El bloque CLIENTE anterior permanece
textualmente idéntico; sólo se selecciona el componente nuevo para el profesional.
Sin cambios de rutas, servicios, permisos, guardado, CSRF, modelos ni migraciones.

Inventario de este incremento (7 archivos):
- `app/templates/nueva_propuesta.html`: selección de presentación y CSS profesional.
- Nuevo `app/templates/components/_professional_proposal_create.html`: composición.
- Nuevo `app/static/css/professional-proposal-create.css`: estilo encapsulado responsive.
- `tests/test_professional_proposals.py`: una regresión de equivalencia de campos,
  separación CLIENTE/profesional, enlaces y GET sin escrituras.
- `docs/REQUISITOS/PROPUESTAS_P1.md`, `docs/HANDOFFS/ACTIVE_HANDOFF.md`, `docs/CHANGELOG.md`.

Validación nueva, separada de los cierres anteriores:
- `python -B -m unittest -q tests.test_professional_proposals tests.test_proposal_portal_p1`:
  **22/22 casos únicos aprobados**, SQLite en memoria. Incluye creación, permisos,
  CSRF, importes no finitos, errores repoblados, publicación y regresiones existentes.
- Comparación estructural adicional: doce bloques de campos idénticos; contenido
  CLIENTE idéntico al baseline. Sintaxis Python y UTF-8 correctos; git diff --check OK.
- Navegador Chrome real: **12 recorridos de creación**, cada uno con inicial,
  error monetario repoblado y publicación corregida (36 estados). Diez combinaciones
  con JS: 320/390/768/1024/1440 px, claro/oscuro; dos sin JS: 390/1440 px con el
  tema claro predeterminado real. CSRF activo, fábrica normal y datos sintéticos.
  Propuesta publicada visible en Mis publicaciones; fechas, selección, descripción
  escapada y cantidad recuperadas. Sin overflow; sin excepciones de página registradas.
- Comprobaciones adicionales, no sumadas a los 12 recorridos: Cancelar mediante
  puntero sin JS en móvil/escritorio, teclado y foco, movimiento reducido emulado,
  contraste computado en claro/oscuro. Botones/campos 48 px. Primario:
  blanco sobre #d3440e = 4,56:1; #0b1220 sobre #ff8a4c = 8,02:1.
  Texto del campo: 17,74:1 claro y 18,08:1 oscuro. Foco visible; transición 0 s
  con movimiento reducido. Esto no constituye auditoría AA integral.
- En automatización sin JS hubo timeout de espera de estabilidad; el envío se
  comprobó con teclado nativo, incluidos segmentos de fecha, y Cancelar con puntero
  tras desplazamiento instantáneo. No se alteró el producto para forzar la prueba.
- No se repitieron PostgreSQL ni Node: cambios de presentación y prueba HTML,
  sin cambios transaccionales ni controladores. El P3 y su cierre permanecen intactos.

Evidencia y capturas nuevas:
[proposal-create-20261030](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/proposal-create-20261030/).
`tests.log`, `browser-results.json`, `accessibility-focal.json`, baseline/integridad;
capturas `1440-light-js-initial.png`, `1440-dark-js-initial.png`,
`390-light-js-initial.png`, `390-dark-js-initial.png` y estados de error/publicación.
Preview aislado en 127.0.0.1:54966 detenido; sin listeners al cierre. Sin Docker,
base compartida, cuenta QA habitual, migraciones ni operaciones Git mutables.

Integridad: laptop, rama `feature/professional-workspace-ux`, HEAD
`2e552f2fdc57c152c97f0486050574696f6b250e`; baseline 123 paths pendientes y 625
archivos; final 125 paths pendientes, staging vacío. Los otros 620 archivos del
baseline conservan hash, incluidos INDEX, Presupuestos, Urgencias y las tres pestañas
de Propuestas. Se conservan antecedentes, dictámenes y omisiones históricas.
Sin commit/push/PR/merge: fuera de autorización. No se consultó sincronización remota.
Ruta de revisión tras actualización manual del entorno por Cristian:
`http://127.0.0.1:5050/propuestas/nueva?vista=publicaciones` (profesional autenticado).
Próximo paso: revisión visual y testing independiente; no actualizar Docker ni integrar
sin autorización. Pendientes: dispositivo físico, AA integral y límites previos del
módulo; no se declara habilitación productiva ni aprobación visual del usuario.

## Corrección focal P2 de validación de creación — 2026-10-30T13:32:34-03:00

Estado: READY_TO_RESUME. Hallazgo independiente del 2026-10-30T13:14:23-03:00.
**P2 CORREGIDO LOCALMENTE; PENDIENTE DE RETEST INDEPENDIENTE.**
Se conserva el dictamen previo, el cierre del P3 y la aprobación del boceto; no se
sustituyen por una aprobación propia de esta corrección ni de su implementación visual.

Causa: los límites HTML no estaban garantizados por el backend; el servicio aceptaba
valores inválidos y `cantidad_profesionales or 1` transformaba cero en uno.
Reproducción previa en SQLite sintético: seis casos (cantidad 0/-1/51, título 161,
descripción 1801 y modalidad Teleport), para CLIENTE y PROFESIONAL: **12 respuestas
302 y 12 publicaciones indebidas**. Tras corregir: mismos doce intentos, **400 y cero
publicaciones**. Evidencia antes/después conservada fuera del repositorio.

`validate_proposal_creation()` normaliza y valida los valores que se guardarían;
la ruta y el servicio directo reutilizan esa función. Cantidad entera 1–50 inclusive,
por defecto 1 sólo ante ausencia/None o cadena vacía tras strip. Cero, negativos,
fracciones, inválidos y fuera de rango se rechazan; no hay truncamiento de textos.
Título requerido hasta 160 y descripción requerida hasta 1800 tras normalización
strip existente. Catálogo único: Presencial, Remoto, Hibrido y A coordinar, sin
alterar los valores vigentes. Servicio valida antes de add/commit; HTTP antes de
persistencia/notificación y mantiene defensa adicional del servicio.

Errores 400 con nombre del campo, valores escapados en el cuerpo y sin llevarlos a
la URL. Cantidad usa entrada de texto en error para no perder valores inválidos.
Modalidad inválida muestra el valor escapado fuera del selector, cuya opción vacía
exige elegir una modalidad canónica; no agrega Teleport al catálogo ni elige
Presencial silenciosamente. CSRF, actor, permisos, CLIENTE, contexto profesional,
SINGLE, fechas y dinero conservados. Sin cambios de CSS, composición, históricos,
contratos, modelos, migraciones ni dependencias.

Inventario focal (9 archivos):
- `app/services/proposal_service.py`: validador común, catálogo y uso defensivo.
- `app/services/operation_request_service.py`: reutilización en validación HTTP.
- `app/routes/operation_routes.py`: pasa cantidad sin conversión previa y catálogo a la vista.
- `app/templates/nueva_propuesta.html` y
  `app/templates/components/_professional_proposal_create.html`: recuperación del campo
  cantidad y selección explícita de modalidad ante error, sin rediseño.
- Nuevo `tests/test_proposal_creation_validation.py`: siete casos de prueba con subcasos.
- `docs/REQUISITOS/PROPUESTAS_P1.md`, `docs/HANDOFFS/ACTIVE_HANDOFF.md`, `docs/CHANGELOG.md`.

Resultados nuevos:
- **34/34 pruebas únicas**, SQLite en memoria, ejecución final:
  `python -B -m unittest -q tests.test_proposal_creation_validation tests.test_professional_proposals tests.test_proposal_portal_p1 tests.test_sprint7_proposal_to_contract`.
  Cubre ambos roles, acceso directo, cantidades inválidas/default/límites, textos
  normalizados, modalidades canónicas, ausencia de escrituras SQL y de llamada de
  éxito en rechazos, un guardado y una llamada de notificación al corregir, fechas,
  importes no finitos, CSRF y derivación contractual existente.
- **8 recorridos focales Chrome**: CLIENTE/PROFESIONAL × 390/1440 px × JS/sin JS.
  Cada recorrido comprueba modalidad inválida, cantidad inválida y posterior envío
  corregido (400/400/302), preservación escapada y catálogo intacto. JS en oscuro;
  sin JS respeta el claro predeterminado. CSRF activo y datos sintéticos en preview.
- Sintaxis Python, UTF-8 y git diff --check correctos. No PostgreSQL ejecutado:
  reglas de entrada previas a persistencia, sin cambios de locks, transacciones,
  idempotencia, esquema o derivación contractual. No Node ni matriz visual completa.
- Corridas de desarrollo no se suman: la primera descubrió accidentalmente casos
  importados de la fixture; se corrigió el import a módulo. Una corrida intermedia
  detectó cuatro fallos de aserción por codificación del texto del test; corregidos
  antes de la ejecución final. No se eliminaron comprobaciones ni agregaron omisiones.

Evidencia durable:
[proposal-validation-p2-20261030](../../../.codex/visualizations/2026/09/21/01a0c628-6518-73a3-b7ca-d4ba209ac043/proposal-validation-p2-20261030/),
`before.json`, `after.json`, `tests-verified.log`, `browser-results.json`, capturas de
recuperación de ambos roles e inventarios SHA-256. Preview 127.0.0.1:54967 detenido;
sin listeners al cierre. Sin Docker habitual, bases compartidas ni cuenta QA.

Integridad inicial/final: laptop, rama `feature/professional-workspace-ux`, HEAD
`2e552f2fdc57c152c97f0486050574696f6b250e`; baseline 125 paths pendientes, 627 archivos;
final 127 paths pendientes, staging vacío. Otros 619 archivos conservados por hash,
incluidos INDEX, Presupuestos, Urgencias, estilos y ajustes de las tres pestañas.
No hubo commit, push, PR, merge ni otras operaciones Git mutables: no autorizadas.
No se consultó sincronización remota ni se migró ninguna base.
Próximo paso: retest independiente del P2 y revisión visual del usuario, aún pendiente.
Para retomar: verificar identidad e inventario y ejecutar las focales en entorno
sintético; no usar bases compartidas ni interpretar este informe como habilitación
productiva. Se conservan limitaciones anteriores: AA integral, dispositivo físico,
CSP heredada y capacidades futuras no habilitadas.

## Cierre técnico del formulario Crear propuesta — 2026-10-30T14:03:45-03:00

Estado: COMPLETED (cierre documental). Laptop; responsable: agente local MANDOBRA.
Dictamen independiente del **2026-10-30T13:52:08-03:00**:
**P2 CERRADO; SIN NUEVOS HALLAZGOS P0–P3 EN EL ALCANCE EVALUADO.**
Este registro sustituye el pendiente de retest del P2, conservando el hallazgo,
su corrección, el cierre del P3, los resultados históricos y sus limitaciones.

Resultados del retest independiente, con conteos separados:

- Pruebas: **34/34 aprobadas**.
- Reproducciones HTTP: **12/12**, rechazo correcto y sin escrituras.
- Llamadas directas al servicio: **12/12**, rechazo correcto y sin escrituras.
- Recorridos de navegador: **8/8 satisfactorios**.

No se suman estas categorías como una única suite ni se agregan las ejecuciones
anteriores a la cobertura nueva. El dictamen acredita fronteras válidas, recuperación
del formulario, ambos roles (CLIENTE y PROFESIONAL) y contratación SINGLE preservados.
Estos resultados pertenecen al retest independiente; no se ejecutaron pruebas nuevas
durante esta sesión documental.

Evidencia durable existente:
[proposal-validation-p2-independent-20261030](../../../.codex/visualizations/2026/09/02/01a06392-4542-7532-875d-7120e33afc38/proposal-validation-p2-independent-20261030/).
Incluye `tests.log`, `retest-output.json`, `browser-results-independent.json`, capturas,
controles estáticos e integridad. Se referencia sin recrear evidencias.

La aprobación del boceto por Cristian permanece registrada. **La aprobación visual
de la implementación sigue pendiente.** Esta corrección no fue validada en PostgreSQL;
no acredita AA integral, móvil físico, producción ni habilitación productiva.
Se conservan las demás limitaciones anteriores, avisos CSP y capacidades pendientes.

Integridad inicial/final: rama `feature/professional-workspace-ux`, HEAD
`2e552f2fdc57c152c97f0486050574696f6b250e`, 127 paths pendientes y staging vacío.
Únicos archivos modificados: `docs/REQUISITOS/PROPUESTAS_P1.md`,
`docs/HANDOFFS/ACTIVE_HANDOFF.md` y `docs/CHANGELOG.md`.
Los otros 625 archivos del inventario de 628 mantienen SHA-256, incluidos INDEX,
Presupuestos, Urgencias, código, pruebas, templates, CSS y JavaScript.
UTF-8 y git diff --check correctos. Sin nuevas pruebas, Docker, migraciones,
operaciones Git mutables ni acceso a bases compartidas. Commit/push/PR/merge no
realizados por estar fuera del alcance; sincronización remota no comprobada.
Próximo paso: revisión visual de Cristian. Para retomar, reconfirmar rama/HEAD,
staging e inventario y preservar antecedentes; este cierre no autoriza integración.
