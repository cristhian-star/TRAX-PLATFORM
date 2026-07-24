# Design System v2 TRAX

## Principios

El Design System v2 normaliza la identidad visual existente de TRAX. No reemplaza la experiencia actual: la ordena para que nuevas pantallas puedan construirse con tokens y componentes reutilizables.

Reglas permanentes:

- Usar variables `--trax-ds-*` como contrato canonico.
- Evitar colores hardcodeados cuando exista un token equivalente.
- Mantener semantica HTML nativa.
- Migrar pantallas de forma progresiva y controlada.
- Conservar compatibilidad visual mientras existan clases legacy.

## Jerarquia De Archivos

| Archivo | Estado | Uso |
| --- | --- | --- |
| `app/static/css/design-system-v2.css` | Estable inicial | Tokens canonicos y componentes `.trax-*`. |
| `app/static/css/design-tokens.css` | Legacy | Tokens v1 mantenidos por compatibilidad. |
| `app/static/css/styles.css` | Legacy amplio | Estilos globales historicos y compatibilidad. |
| CSS por modulo | Legacy / piloto | Composicion especifica de cada pantalla. |

## Tokens Canonicos

Los tokens principales usan el prefijo `--trax-ds-*`.

Categorias cubiertas:

- Colores: fondos, superficies, texto, bordes, marca, estados, overlay y foco.
- Tipografia: familia, tamanos, pesos, line-height y letter-spacing.
- Espaciado: escala `space-1` a `space-20`.
- Bordes: grosor, estilo y radios.
- Sombras: small, medium, large, popover, modal y focus.
- Layout: contenedores, gutters, gaps y breakpoints.
- Movimiento: duraciones y easing.
- Controles: alturas, input, select, textarea y placeholders.

Los alias `--trax-color-*`, `--trax-radius-*`, `--trax-shadow-*`, `--trax-space-*` y equivalentes pueden permanecer mientras apuntan al contrato v2.

## Breakpoints

Escala canonica:

| Token | Valor | Uso recomendado |
| --- | --- | --- |
| `--trax-ds-breakpoint-sm` | `40rem` | Mobile amplio. |
| `--trax-ds-breakpoint-md` | `48rem` | Tablet. |
| `--trax-ds-breakpoint-lg` | `64rem` | Desktop. |
| `--trax-ds-breakpoint-xl` | `80rem` | Desktop ancho. |

Los breakpoints legacy siguen existiendo y deben migrarse por pantalla en fases posteriores.

## Componentes Disponibles

### Page Shell

```html
<main class="trax-page">
    <section class="trax-container trax-page__content">
        ...
    </section>
</main>
```

Clases:

- `.trax-page`
- `.trax-container`
- `.trax-page__header`
- `.trax-page__title`
- `.trax-page__description`
- `.trax-page__actions`
- `.trax-page__content`
- `.trax-grid`
- `.trax-grid--auto`

### Botones

```html
<button class="trax-button trax-button--primary" type="submit">Guardar</button>
<a class="trax-button trax-button--secondary" href="/">Volver</a>
```

Variantes:

- `.trax-button--primary`
- `.trax-button--secondary`
- `.trax-button--ghost`
- `.trax-button--danger`
- `.trax-button--small`
- `.trax-button--large`
- `.trax-button--icon-only`

Estados:

- `:hover`
- `:focus-visible`
- `:active`
- `:disabled`
- `[aria-disabled="true"]`
- `.is-disabled`
- `.is-loading`

### Formularios

```html
<div class="trax-field">
    <label class="trax-field__label" for="email">Email</label>
    <input class="trax-input" id="email" aria-describedby="email-help">
    <small class="trax-field__help" id="email-help">Texto de ayuda.</small>
</div>
```

Clases:

- `.trax-field`
- `.trax-field__label`
- `.trax-field__control`
- `.trax-field__help`
- `.trax-field__error`
- `.trax-input`
- `.trax-select`
- `.trax-textarea`
- `.trax-checkbox`
- `.trax-radio`

### Cards

```html
<article class="trax-card">
    <header class="trax-card__header">...</header>
    <div class="trax-card__body">...</div>
    <footer class="trax-card__footer">...</footer>
</article>
```

Variantes:

- `.trax-card--interactive`
- `.trax-card--elevated`
- `.trax-card--compact`

### Badges

```html
<span class="trax-badge trax-badge--success">Activo</span>
```

Variantes:

- neutral: `.trax-badge`
- `.trax-badge--primary`
- `.trax-badge--success`
- `.trax-badge--warning`
- `.trax-badge--danger`
- `.trax-badge--info`

### Alertas

```html
<div class="trax-alert trax-alert--warning" role="alert">
    <p class="trax-alert__title">Atencion</p>
    <p class="trax-alert__body">Mensaje breve.</p>
</div>
```

Variantes:

- `.trax-alert--success`
- `.trax-alert--warning`
- `.trax-alert--danger`
- `.trax-alert--info`

### Estados Vacios

```html
<div class="trax-empty-state">
    <span class="trax-empty-state__icon" aria-hidden="true">0</span>
    <h2 class="trax-empty-state__title">Sin resultados</h2>
    <p class="trax-empty-state__description">Ajusta los filtros para intentar nuevamente.</p>
</div>
```

## Modo Oscuro

El cambio de tema debe modificar variables globales en `.theme-light` y `.theme-dark`. Los componentes `.trax-*` no deben duplicar paletas por tema si existe un token disponible.

## Accesibilidad

Requisitos minimos:

- `:focus-visible` visible en controles interactivos.
- `aria-invalid` y `aria-describedby` en campos con errores.
- Errores con texto, no solo color.
- Botones deshabilitados perceptibles.
- Targets tactiles adecuados.
- Compatibilidad con `prefers-reduced-motion`.
- No ocultar semantica nativa de `button`, `input`, `select`, `textarea`, `fieldset` o `legend`.

## Compatibilidad Legacy

Durante la migracion se permite usar clases nuevas y legacy en el mismo elemento:

```html
<button class="trax-button trax-button--primary auth-submit">Ingresar</button>
```

La clase `.trax-*` define el componente reutilizable. La clase legacy conserva composicion o ajustes especificos de pantalla.

## Migracion Piloto

Estado actual:

| Superficie | Estado | Alcance |
| --- | --- | --- |
| Login | Piloto | Page shell, card, field, input, button, alert. |
| Registro | Piloto | Page shell, card, field, input, radio, checkbox, button, alert. |
| Rubro solicitado | Piloto | Card compacta, badge, alerta y boton. |
| Navbar | Legacy estable | No migrado en esta fase. |
| Home | Pendiente | No migrar hasta estabilizar componentes. |
| Perfil profesional | Pendiente | Riesgo medio por mapa, portfolio y modales. |
| Marketplace de presupuestos | Pendiente | Riesgo alto por flujos y cards densas. |
| Emergencias | Pendiente | Riesgo medio/alto por estados y filtros. |
| Admin y tablas | Pendiente | Requiere estrategia especifica. |

## Reglas Para CSS Por Modulo

- Usar CSS por modulo solo para layout o composicion propia de la pantalla.
- No redefinir botones, inputs, badges o alerts si existe componente `.trax-*`.
- No aplicar estilos globales a `button`, `input`, `table`, `form` o nombres genericos sin namespace.
- Antes de crear una variante nueva, validar si puede resolverse con tokens o modificadores existentes.

## Pendientes

- Normalizar tablas.
- Crear modal canonico.
- Crear loader canonico.
- Migrar empty states existentes.
- Auditar breakpoints legacy.
- Reducir `styles.css` una vez que existan pruebas visuales por pantalla.
- Definir estrategia para navbar sin alterar su comportamiento actual.
