(() => {
  const root = document.querySelector('[data-emergency-config]');
  if (!root) return;
  const form = root.querySelector('form');
  const value = name => form.elements[name]?.value || '';
  const checked = name => form.elements[name]?.checked;
  function update() {
    const mode = value('mode');
    root.querySelectorAll('[data-price-group]').forEach(group => { group.hidden = group.dataset.priceGroup !== mode; });
    const prices = root.querySelector('[data-preview-prices]');
    prices.replaceChildren();
    const fields = mode === 'PACKAGE' ? [['package_amount','Visita + diagnóstico']] : [['visit_amount','Visita técnica'],['diagnosis_amount','Diagnóstico']];
    fields.forEach(([name,label]) => {
      const line = document.createElement('p');
      const raw = value(name).trim();
      const valid = /^[0-9]{1,10}([.,][0-9]{1,2})?$/.test(raw) && Number(raw.replace(',','.')) > 0;
      line.textContent = `${label}: ${checked(name + '_free') ? 'Sin cargo' : !raw ? 'Sin configurar' : valid ? 'ARS ' + raw.replace(',','.') : 'Revisá el importe'}`;
      prices.append(line);
    });
    root.querySelector('[data-preview-zone]').textContent = ['coverage_location','coverage_city','coverage_province'].map(value).filter(Boolean).join(' · ') || 'Zona sin configurar';
    root.querySelector('[data-preview-notes]').textContent = value('notes');
    root.querySelector('[data-preview-discount]').textContent = checked('discount_repair') ? 'Estos importes se descuentan si se acepta la reparación.' : '';
  }
  form.addEventListener('input', update);
  form.addEventListener('change', update);
  const radius = root.querySelector('[data-coverage-radius]');
  const slider = root.querySelector('[data-radius-slider]');
  root.querySelector('[data-radius-slider-label]').hidden = false;
  slider.addEventListener('input', () => { radius.value = slider.value; radius.dispatchEvent(new Event('change', {bubbles:true})); });
  radius.addEventListener('input', () => { if (radius.value) slider.value = radius.value; radius.dispatchEvent(new Event('change', {bubbles:true})); });
  update();
})();
