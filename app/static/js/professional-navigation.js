/* Native details remains usable without JavaScript; no modal focus trap. */
(() => {
    const menu = document.querySelector('.pw-mobile-menu');
    if (!menu) return;
    const trigger = menu.querySelector('summary');
    document.addEventListener('keydown', event => {
        if (event.key === 'Escape' && menu.open) {
            menu.open = false;
            trigger.focus();
        }
    });
    document.addEventListener('click', event => {
        if (menu.open && !menu.contains(event.target)) {
            const focusInside = menu.contains(document.activeElement);
            menu.open = false;
            if (focusInside) trigger.focus();
        }
    });
})();
