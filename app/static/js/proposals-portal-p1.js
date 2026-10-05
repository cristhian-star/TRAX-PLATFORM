/* Progressive enhancement: the native disclosure still works without JavaScript. */
(() => {
    const filters = document.querySelector('.proposals-p1__filter-disclosure');
    if (!filters) return;
    const desktop = window.matchMedia('(min-width: 64rem)');
    filters.open = desktop.matches;
    desktop.addEventListener('change', event => { filters.open = event.matches; });
})();
