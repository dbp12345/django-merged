(function () {
  function buildTableHtml(tx) {
    if (!tx || !tx.length) return '<em>No transactions</em>';
    let html = '<table class="adminlist"><thead><tr>';
    html += '<th>paycheckId</th><th>payPeriodId</th><th>checkDate</th><th>gross</th><th>net</th><th>components</th>';
    html += '</tr></thead><tbody>';
    tx.forEach(function (t) {
      const pid = t.paycheckId || t.id || t.checkId || '';
      const pp = t.payPeriodId || t.payperiodId || '';
      const cd = t.checkDate || t.payDate || '';
      const gross = (t.grossAmount || t.gross || '') ;
      const net = (t.netAmount || t.net || '') ;
      const comps = (t.checkComponents && t.checkComponents.length) || (t.components && t.components.length) || 0;
      html += '<tr><td>' + pid + '</td><td>' + pp + '</td><td>' + cd + '</td><td>' + gross + '</td><td>' + net + '</td><td>' + comps + '</td></tr>';
    });
    html += '</tbody></table>';
    return html;
  }

  function initPanel(panel) {
    const url = panel.dataset.url;
    if (!url) {
      panel.querySelector('.tx-loading').style.display = 'none';
      const err = panel.querySelector('.tx-error');
      err.textContent = 'No data-url';
      err.style.display = 'block';
      return;
    }

    fetch(url, { credentials: 'same-origin', headers: { 'Accept': 'application/json' } })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (data) {
        panel.querySelector('.tx-loading').style.display = 'none';
        if (data.error) {
          const e = panel.querySelector('.tx-error');
          e.textContent = data.error;
          e.style.display = 'block';
          return;
        }
        const tx = data.transactions || [];
        panel.querySelector('.tx-table').innerHTML = buildTableHtml(tx);
      })
      .catch(function (err) {
        panel.querySelector('.tx-loading').style.display = 'none';
        const e = panel.querySelector('.tx-error');
        e.textContent = String(err);
        e.style.display = 'block';
      });
  }

  // Инициализация для всех панелей на странице
  document.addEventListener('DOMContentLoaded', function () {
    const panels = document.querySelectorAll('.tx-panel');
    panels.forEach(function (p) { initPanel(p); });
  });
})();
