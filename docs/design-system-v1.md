# TRAX Design System v1

## 1. Alcance

Esta propuesta define la base visual para implementar el UX Map v1 de TRAX.
No rediseña pantallas, no cambia flujos y no modifica backend, modelos,
servicios ni persistencia.

La entrega se compone de:

- Especificacion visual y de comportamiento.
- Tokens CSS semanticos, aislados y sin enlazar a las pantallas actuales.
- Reglas responsive y de accesibilidad para la implementacion posterior.

## 2. Direccion visual

TRAX debe sentirse como una herramienta de trabajo: precisa, resistente,
moderna y confiable. La identidad toma referencias industriales sin recurrir a
texturas pesadas ni decoracion mecanica literal.

### Principios

1. **Trabajo antes que decoracion:** jerarquia clara y alta densidad util.
2. **Accion visible:** una accion primaria dominante por contexto.
3. **Confianza verificable:** badges y reputacion con significado consistente.
4. **Urgencia controlada:** Emergencia se distingue sin convertir toda la UI en roja.
5. **Mobile first:** controles tactiles, lectura rapida y contenido apilable.
6. **Color con funcion:** ningun color se usa solo por ornamentacion.

### Personalidad

- Industrial, no rustica.
- Premium, no ostentosa.
- Tecnica, no fria.
- Directa, no agresiva.
- Profesional, no corporativa generica.

## 3. Paleta TRAX

### 3.1 Colores de marca

| Token | Valor | Uso |
|---|---:|---|
| `--trax-steel-950` | `#0B1220` | Fondos oscuros, texto de maxima jerarquia |
| `--trax-steel-900` | `#111C2E` | Header oscuro, hero, superficies elevadas |
| `--trax-steel-800` | `#1C2A3D` | Hover sobre fondo oscuro |
| `--trax-orange-700` | `#B9380A` | Active/pressed y texto naranja accesible |
| `--trax-orange-600` | `#D3440E` | CTA primario sobre blanco |
| `--trax-orange-500` | `#F05A1A` | Acentos grandes, iconos, seleccion |
| `--trax-cyan-700` | `#087A8C` | Texto informativo sobre fondo claro |
| `--trax-cyan-500` | `#0EA5B7` | Indicadores, links tecnicos, foco complementario |

El naranja existente evoluciona de `#FF5A1F` a una escala semantica. Para
botones con texto blanco se usa `orange-600`; `orange-500` queda para
superficies grandes o acentos donde el contraste de texto no dependa de el.

### 3.2 Neutros

| Token | Valor | Uso |
|---|---:|---|
| `--trax-gray-950` | `#111827` | Texto principal |
| `--trax-gray-800` | `#1F2937` | Texto secundario fuerte |
| `--trax-gray-700` | `#374151` | Etiquetas |
| `--trax-gray-600` | `#4B5563` | Texto secundario accesible |
| `--trax-gray-500` | `#6B7280` | Metadatos, solo en tamanos suficientes |
| `--trax-gray-300` | `#D1D5DB` | Bordes de controles |
| `--trax-gray-200` | `#E5E7EB` | Divisores |
| `--trax-gray-100` | `#F3F4F6` | Fondo secundario |
| `--trax-gray-50` | `#F8FAFC` | Fondo de pagina |
| `--trax-white` | `#FFFFFF` | Superficie principal |

### 3.3 Estados

| Estado | Base | Fondo suave | Texto/borde |
|---|---:|---:|---:|
| Exito | `#15803D` | `#F0FDF4` | `#166534` |
| Error | `#B42318` | `#FEF3F2` | `#912018` |
| Advertencia | `#B54708` | `#FFFAEB` | `#93370D` |
| Informacion | `#087A8C` | `#ECFEFF` | `#155E75` |
| Emergencia | `#C81E1E` | `#FFF1F2` | `#991B1B` |

### 3.4 Distribucion recomendada

- 70 % neutros y superficies.
- 20 % acero/grafito para estructura y jerarquia.
- 10 % naranja, cian y colores de estado.
- El rojo de Emergencia no reemplaza el CTA principal fuera de ese flujo.
- No combinar naranja y rojo en una misma accion.

## 4. Tipografia

### 4.1 Familia

```css
font-family:
    Inter,
    ui-sans-serif,
    system-ui,
    -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    sans-serif;
```

`Inter` ya figura en la base actual, pero no se debe descargar en esta fase. Si
no esta instalada, la pila usa fuentes seguras del sistema sin salto de layout.

### 4.2 Escala

| Estilo | Mobile | Desktop | Peso | Line-height |
|---|---:|---:|---:|---:|
| Display | 36 px | 52 px | 800 | 1.08 |
| H1 | 32 px | 44 px | 800 | 1.12 |
| H2 | 26 px | 34 px | 750 | 1.2 |
| H3 | 21 px | 24 px | 700 | 1.25 |
| Body lg | 18 px | 18 px | 400 | 1.55 |
| Body | 16 px | 16 px | 400 | 1.55 |
| Body sm | 14 px | 14 px | 400 | 1.45 |
| Label | 14 px | 14 px | 650 | 1.35 |
| Caption | 12 px | 12 px | 600 | 1.4 |

### 4.3 Reglas

- Un solo H1 por pantalla.
- No usar cuerpo menor a 14 px en informacion operativa.
- Mayusculas solo para badges, eyebrow y etiquetas cortas.
- Tracking positivo de `0.04em` a `0.08em` en mayusculas.
- Evitar peso 900/950 para parrafos y botones; reduce legibilidad.
- Numeros de precio, reputacion y tiempos usan cifras tabulares si estan disponibles.

## 5. Espaciado, radios y elevacion

### 5.1 Escala de espaciado

Base de 4 px:

`4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80`

- Separacion label/control: 8 px.
- Separacion entre campos: 20 px.
- Padding de card mobile: 16 px.
- Padding de card desktop: 24 px.
- Separacion entre secciones mobile: 48 px.
- Separacion entre secciones desktop: 72-80 px.

### 5.2 Radios

| Token | Valor | Uso |
|---|---:|---|
| Small | 6 px | Badges, tags |
| Medium | 10 px | Inputs, botones |
| Large | 16 px | Cards y paneles |
| XL | 24 px | Hero/search container |
| Pill | 999 px | Chips y estados compactos |

La forma por defecto deja de ser completamente pill. Los radios medios dan una
sensacion mas tecnica y aprovechan mejor el espacio.

### 5.3 Sombras

- `sm`: borde/elevacion minima para controles.
- `md`: cards interactivas.
- `lg`: panel de tabs y modales.
- Evitar sombras profundas en todas las cards.
- En hover, priorizar borde y desplazamiento de 1 px antes que sombras grandes.

## 6. Sistema de botones

### 6.1 Variantes

| Variante | Uso | Fondo | Texto | Borde |
|---|---|---|---|---|
| Primary | Accion principal | Orange 600 | Blanco | Orange 600 |
| Secondary | Alternativa relevante | Blanco | Steel 900 | Gray 300 |
| Tertiary | Accion de baja prioridad | Transparente | Steel 900 | Transparente |
| Dark | CTA sobre fondo claro premium | Steel 900 | Blanco | Steel 900 |
| Emergency | Accion urgente confirmada | Emergency 600 | Blanco | Emergency 600 |
| Danger | Destructiva | Blanco | Error 700 | Error 300 |

### 6.2 Tamanos

| Tamano | Altura minima | Padding horizontal | Texto |
|---|---:|---:|---:|
| Small | 36 px | 12 px | 14 px |
| Medium | 44 px | 16 px | 15 px |
| Large | 52 px | 20 px | 16 px |

### 6.3 Estados

- Default.
- Hover: oscurecer un nivel y elevar 1 px.
- Active: sin elevacion, oscurecer dos niveles.
- Focus-visible: anillo exterior de 3 px con separacion de 2 px.
- Disabled: fondo Gray 200, texto Gray 500, sin sombra.
- Loading: conservar ancho, mostrar spinner y `aria-busy="true"`.

### 6.4 Reglas

- Una accion primary por panel.
- En mobile, CTA principal a ancho completo cuando cierra un formulario.
- Icono opcional de 18-20 px; nunca reemplaza el texto principal.
- Los botones destructivos no usan el mismo relleno rojo que Emergencia.
- Copy con verbo y objeto: `Enviar propuesta`, `Buscar profesionales`.

## 7. Inputs y formularios

### 7.1 Anatomia

```text
Label requerido
[ Prefijo | Valor o placeholder             | Sufijo ]
Ayuda, contador o mensaje de error
```

### 7.2 Base

- Altura de input/select: 48 px.
- Textarea: minimo 120 px.
- Fondo blanco.
- Borde Gray 300 de 1 px.
- Radio medium.
- Texto Gray 950.
- Placeholder Gray 500.
- Label siempre visible.
- Padding horizontal de 14 px.

### 7.3 Estados

| Estado | Borde | Fondo | Mensaje |
|---|---|---|---|
| Default | Gray 300 | Blanco | Ayuda opcional |
| Hover | Gray 500 | Blanco | Sin cambio |
| Focus | Steel 900 | Blanco | Anillo Cyan 500 |
| Filled | Gray 400 | Blanco | Ayuda opcional |
| Success | Success 600 | Success soft | Confirmacion breve |
| Error | Error 600 | Error soft | Error especifico |
| Disabled | Gray 200 | Gray 100 | Explicar si hace falta |
| Read-only | Gray 300 | Gray 50 | Sin apariencia de CTA |

### 7.4 Agrupacion

- Mobile: una columna.
- Desde 640 px: dos columnas solo para campos relacionados.
- Direccion, descripcion y archivos ocupan ancho completo.
- Acciones al final: secundaria primero, primaria ultima en desktop.
- En mobile: primaria arriba si ambas acciones se apilan.

### 7.5 Validacion

- Validar al salir del campo o al enviar, no en cada tecla.
- Asociar mensaje con `aria-describedby`.
- Usar icono + texto + color.
- El error explica como corregir: `Ingresá una zona`, no `Valor inválido`.
- Mantener los datos tras un error del servidor.

## 8. Cards de profesionales

### 8.1 Objetivo

Permitir comparar confianza, especialidad, zona y disponibilidad antes de abrir
el perfil.

### 8.2 Anatomia

```text
┌─────────────────────────────────────────────────┐
│ Avatar/imagen  Nombre o empresa       [Guardar] │
│                Especialidad · Zona              │
│                [WORK] [PRO] [VERIFICADO]        │
│                                                 │
│ ★ 4,8 (36)   Responde en...   Disponibilidad    │
│ Resumen de servicios, maximo 2-3 lineas         │
│                                                 │
│ [Ver perfil]                 [Solicitar trabajo]│
└─────────────────────────────────────────────────┘
```

### 8.3 Reglas

- La reputacion no se comunica solo con estrellas.
- Badges inmediatamente despues de identidad/especialidad.
- No mostrar precio ficticio o `desde` sin fuente real.
- `Guardar` es icono con label accesible; no usa corazon textual.
- Card completa no es link si contiene varios controles.
- Hover: borde Steel 300 y sombra `md`.
- Profesional promovido usa etiqueta `Destacado`, no un borde naranja completo.
- En mobile, imagen de 64 px y acciones apilables.

## 9. Cards de oportunidades

### 9.1 Objetivo

Ayudar al profesional a decidir rapidamente si una oportunidad es relevante.

### 9.2 Anatomia

```text
┌─────────────────────────────────────────────────┐
│ Rubro · Publicada hace 2 h          [Guardar]   │
│ Titulo del trabajo                              │
│ Zona / modalidad · Fecha esperada               │
│ Resumen del alcance, maximo 3 lineas            │
│                                                 │
│ Presupuesto/rango   4 propuestas   [EMERGENCIA] │
│ [Ver oportunidad]                               │
└─────────────────────────────────────────────────┘
```

### 9.3 Reglas

- Titulo y contexto antes que presupuesto.
- Mostrar presupuesto solo cuando sea dato confirmado.
- Emergencia aparece como badge y prioridad de orden, no anima la card.
- Metadatos en una fila con wrap.
- Estado `Cerrada` desactiva el CTA y explica la razon.
- Las cards guardadas mantienen señal textual, no solo color.
- Desktop: una columna amplia o grilla de dos; evitar tres columnas estrechas.

## 10. Badges

### 10.1 Base

- Altura: 24 px.
- Padding: 4 px 8 px.
- Radio small.
- Texto: 11-12 px, peso 700, mayusculas.
- Icono opcional: 12-14 px.
- Borde de 1 px.
- No usar sombra.

### 10.2 Semantica

| Badge | Significado visual | Fondo | Texto/borde |
|---|---|---|---|
| WORK | Perfil habilitado para trabajar | Steel 100 | Steel 800 |
| PRO | Nivel profesional/premium | Orange 50 | Orange 700 |
| VERIFICADO | Identidad o dato verificado | Cyan 50 | Cyan 700 |
| EMERGENCIA | Necesidad urgente | Rose 50 | Emergency 700 |

### 10.3 Reglas

- El badge debe tener definicion de producto antes de implementarse.
- `VERIFICADO` no implica calidad, garantia ni recomendacion.
- `PRO` no reemplaza reputacion.
- `WORK` no debe aparecer siempre si no agrega informacion.
- Maximo tres badges visibles; el resto va en detalle.
- No depender del color: todos conservan texto.

## 11. Tabs de operaciones

### 11.1 Referencia

Patron de buscador tipo Argenprop, adaptado a cuatro intenciones distintas:
Contratacion, Presupuestos, Emergencias y Propuestas.

### 11.2 Anatomia

```text
┌──────────────────────────────────────────────────────────┐
│ Contratacion | Presupuestos | Emergencias | Propuestas   │
├──────────────────────────────────────────────────────────┤
│ Titulo y ayuda del tab                                   │
│ Campos contextuales                         [CTA]         │
└──────────────────────────────────────────────────────────┘
```

### 11.3 Estados

- Inactive: fondo transparente, texto Gray 600.
- Hover: fondo Gray 100, texto Steel 900.
- Active: texto Steel 950, indicador inferior Orange 600 de 3 px.
- Focus-visible: anillo visible, independiente del estado active.
- Disabled: solo si existe una razon explicable; evitarlo en Home.
- Emergencias activa mantiene indicador rojo solo dentro de su flujo.

### 11.4 Responsive

- Mobile: scroll horizontal con tabs completos, sin truncar a iconos.
- Tablet/desktop: cuatro tabs de igual ancho.
- El panel tiene radio XL y sombra `lg`; los tabs se integran en su cabecera.
- Altura tactil minima: 48 px.
- Implementacion futura con `tablist`, `tab`, `tabpanel` y teclado WAI-ARIA.

## 12. Estados visuales

### 12.1 Exito

- Fondo Success soft, borde Success 200, icono y titulo Success 700.
- Mensaje confirma accion y proximo paso.
- CTA principal lleva a seguimiento, no repite el envio.

### 12.2 Error

- Error inline cerca del origen.
- Error global solo cuando afecta toda la operacion.
- Nunca borrar el formulario.
- CTA: `Reintentar` o accion concreta.

### 12.3 Advertencia

- Fondo Warning soft y borde Warning 300.
- Se usa para consecuencias, vencimientos y datos incompletos.
- No bloquear salvo riesgo real.

### 12.4 Vacio

```text
[Icono lineal]
Titulo que describe el estado
Explicacion breve
[Accion primaria] [Alternativa]
```

- No usar ilustraciones infantiles.
- Explicar si el usuario puede cambiar filtros, crear una solicitud o volver.
- Altura compacta dentro de listas; panel amplio solo en pagina vacia.

### 12.5 Cargando

- Skeleton con la misma geometria del contenido.
- Spinner solo para acciones puntuales.
- Evitar shimmer intenso; respetar `prefers-reduced-motion`.
- Despues de 10 segundos, ofrecer mensaje y recuperacion.
- No mostrar porcentajes simulados.

### 12.6 Emergencia

- Encabezado con borde/indicador rojo y texto claro.
- El resto de la pantalla conserva neutros.
- Contacto y estado tienen prioridad visual.
- No usar pulsos, flashes ni cuenta regresiva sin informacion real.

## 13. Layout responsive base

### 13.1 Contenedor

```text
Mobile:  100% - 32 px, padding lateral 16 px
Tablet:  100% - 48 px, padding lateral 24 px
Desktop: max-width 1200 px, padding lateral 32 px
Wide:    max-width 1280 px solo para listados/comparadores
```

### 13.2 Breakpoints orientativos

| Nombre | Desde | Uso |
|---|---:|---|
| `sm` | 480 px | Ajustes de controles |
| `md` | 768 px | Dos columnas, header expandido |
| `lg` | 1024 px | Sidebar, grids principales |
| `xl` | 1280 px | Comparadores y listados amplios |

Los componentes deben responder al espacio disponible; los breakpoints son
guias, no contratos rigidos.

### 13.3 Grid

- Mobile: 4 columnas conceptuales, gap 16 px.
- Tablet: 8 columnas, gap 20 px.
- Desktop: 12 columnas, gap 24 px.
- Contenido principal + sidebar: 8/4 o 9/3.
- Formularios: max-width de 720 px salvo buscador horizontal.
- Texto largo: ancho maximo de 68 caracteres.

### 13.4 Patrones

- Home/search: hero + panel de tabs superpuesto solo en desktop.
- Listados: filtros en drawer mobile y sidebar desktop.
- Detalle: contenido + resumen sticky desktop; una columna mobile.
- Comparador: cards apiladas mobile, columnas seleccionables desktop.
- CTA sticky mobile solo cuando no tapa campos, errores ni contenido final.

## 14. Accesibilidad basica

- Contraste AA: 4.5:1 en texto normal y 3:1 en texto grande/controles.
- Foco visible de 3 px en todos los elementos interactivos.
- Objetivo tactil minimo de 44 x 44 px; preferido 48 px.
- Labels persistentes; placeholder nunca reemplaza label.
- Estados comunicados por texto/icono ademas de color.
- Orden de DOM igual al orden visual.
- Zoom a 200 % sin perdida de contenido ni scroll horizontal de pagina.
- Soporte para `prefers-reduced-motion`.
- Iconos decorativos con `aria-hidden`; controles icon-only con nombre accesible.

## 15. Compatibilidad con la UI actual

La hoja `design-tokens.css` se entrega sin enlazar desde `base.html`. Por eso:

- No cambia ninguna pantalla existente.
- No reemplaza las variables actuales de `styles.css`.
- Puede revisarse y versionarse antes de migrar componentes.
- La adopcion puede hacerse componente por componente.

Durante la migracion se pueden mapear aliases:

| Actual | Futuro |
|---|---|
| `--navy` | `--trax-color-brand-strong` |
| `--orange` | `--trax-color-action-primary` |
| `--cyan` | `--trax-color-info` |
| `--soft` | `--trax-color-surface-subtle` |
| `--ink` | `--trax-color-text` |
| `--muted` | `--trax-color-text-muted` |
| `--line` | `--trax-color-border` |
| `--green` | `--trax-color-success` |

## 16. Orden de implementacion posterior

1. Enlazar tokens y mapear aliases sin cambiar componentes.
2. Migrar botones y foco.
3. Migrar inputs, validacion y formularios.
4. Migrar badges.
5. Crear tabs de operaciones.
6. Migrar cards de profesionales.
7. Crear cards de oportunidades.
8. Unificar estados vacios, error, exito y carga.
9. Aplicar layout responsive por flujo.
10. Ejecutar auditoria visual y de accesibilidad.

## 17. Criterios de aceptacion de Design System v1

- La paleta distingue marca, accion, informacion, estado y emergencia.
- Tipografia y espaciado funcionan sin dependencias externas.
- Botones, inputs, cards, badges y tabs tienen anatomia y estados definidos.
- La propuesta es mobile first y mantiene contraste alto.
- Emergencia es prioritaria sin dominar visualmente todo TRAX.
- Los tokens no alteran las pantallas existentes hasta ser enlazados.
- La especificacion permite implementar componentes sin decidir nuevamente su estilo base.
