/* Provisional selection only: no requests, storage or reservation operation. */
(() => {
  const planner = document.querySelector('[data-shift-planner]');
  if (!planner) return;
  const shifts = [...planner.querySelectorAll('[data-shift]')];
  const count = planner.querySelector('[data-selection-count]');
  const list = planner.querySelector('[data-selection-list]');
  const acceptance = planner.querySelector('[data-shift-accept]');
  function update() {
    const chosen = shifts.filter(input => input.checked && !input.disabled);
    count.textContent = chosen.length === 1 ? '1 turno seleccionado provisionalmente' : `${chosen.length} turnos seleccionados provisionalmente`;
    list.replaceChildren();
    chosen.forEach(input => {
      const item = document.createElement('li');
      item.textContent = input.dataset.summary;
      list.append(item);
    });
    acceptance.checked = false;
  }
  shifts.forEach(input => input.addEventListener('change', update));
  update();
})();
