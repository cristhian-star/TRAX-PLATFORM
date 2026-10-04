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
