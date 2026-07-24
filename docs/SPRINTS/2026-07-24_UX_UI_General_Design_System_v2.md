# UX/UI General & Design System v2

## Objetivo

Consolidar el Design System v2 de TRAX como contrato visual reutilizable, validar las superficies piloto y dejar una estrategia clara para migraciones futuras.

## Diagnostico inicial

TRAX ya contaba con tokens `--trax-ds-*`, componentes `.trax-*`, migracion piloto en auth, rubro solicitado, flashes globales, notificaciones y modal WhatsApp. Persistia deuda en CSS legacy, breakpoints dispersos y pantallas complejas no migradas.

## Decisiones

- Cargar `design-system-v2.css` explicitamente desde `base.html`.
- Mantener `design-tokens.css` como compatibilidad v1.
- Dejar `styles.css` como capa legacy posterior.
- No migrar navbar, admin, tablas, marketplace, emergencias ni perfil profesional completo en este cierre.

## Tokens

El contrato canonico usa variables `--trax-ds-*` para fondos, superficies, texto, bordes, estados, sombras, espaciado, tipografia, layout, foco y movimiento.

## Componentes

Componentes validados:

- `trax-page`, `trax-container`, `trax-grid`.
- `trax-stack`, `trax-cluster`, `trax-divider`.
- `trax-button`.
- `trax-field`, `trax-input`, `trax-select`, `trax-textarea`, `trax-checkbox`, `trax-radio`.
- `trax-card`.
- `trax-badge`.
- `trax-alert`, `trax-toast-region`.
- `trax-empty-state`.
- `trax-modal`.

## Superficies migradas

- Login.
- Registro.
- Rubro solicitado.
- Flash messages globales.
- Notificaciones.
- Modal de consentimiento WhatsApp.

## Compatibilidad legacy

Las clases legacy pueden convivir con `.trax-*` durante la migracion. La clase canonica define el componente; la clase legacy conserva composicion especifica de pantalla.

## Accesibilidad

Se validaron labels visibles, `aria-describedby`, `aria-live`, `role`, focus visible, cierre descartable de alertas y atributos accesibles del modal WhatsApp.

## Responsive

Se validaron desktop y mobile en superficies migradas, sin overflow horizontal detectado.

## Modo oscuro

El modo claro/oscuro se mantiene por clases `theme-light` y `theme-dark` y variables globales. No se duplicaron paletas por componente.

## Tests

Total final: 99 tests.

Cobertura agregada o protegida:

- Contrato de tokens y componentes.
- Carga explicita del Design System v2.
- Auth migrado.
- Rubro solicitado.
- Flash messages por categoria.
- Notificaciones con elementos y estado vacio.
- Modal WhatsApp accesible.

## Validacion visual

Se revisaron login, registro, resultados, notificaciones, modal WhatsApp, theme switch, desktop/mobile, consola y overflow. No se detectaron errores de consola ni desbordes horizontales en las superficies verificadas.

## Riesgos pendientes

- `styles.css` sigue siendo una capa legacy amplia.
- Existen breakpoints dispersos en CSS por modulo.
- Navbar requiere migracion especifica.
- Home, Resultados, Perfil profesional, Dashboards, Presupuestos, Propuestas, Emergencias, Admin y tablas quedan pendientes.
- La eliminacion de CSS muerto requiere cobertura visual por pantalla.

## Deuda backend separada

- Reemplazar `Query.get()` por `db.session.get()`.
- Reemplazar `datetime.utcnow()` por timestamps timezone-aware.

## Criterios de aceptacion

- Contrato `--trax-ds-*` estable.
- Componentes canonicos documentados.
- Auth, notificaciones, flashes globales, modal WhatsApp y rubro solicitado migrados sin regresion.
- Claro/oscuro funcional.
- Desktop/mobile sin overflow en superficies revisadas.
- Teclado y focus visibles.
- Sin cambios de rutas.
- Sin cambios de logica de negocio.
- Sin migraciones.
- Suite completa en host y Docker.
- Documentacion actualizada.

## Resultado final

El Design System v2 queda consolidado como base visual canonica de TRAX y la rama queda lista para revision y merge a `develop`.

## Proximo Sprint recomendado

Migrar una superficie compleja por vez, comenzando por Home o Resultados, con capturas desktop/mobile y claro/oscuro antes de tocar dashboards, admin o tablas.
