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
