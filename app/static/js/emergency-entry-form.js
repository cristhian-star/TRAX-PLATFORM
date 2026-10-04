/* Optional character count; native form and validation also work without JS. */
(function () {
    'use strict';
    const field = document.getElementById('emergency-description');
    const count = document.getElementById('emergency-description-count');
    if (!field || !count) return;
    const update = () => { count.textContent = String(Array.from(field.value).length); };
    field.addEventListener('input', update);
    window.addEventListener('pageshow', update);
    update();
}());
