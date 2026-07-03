import { useState, useEffect } from 'preact/hooks';
import { html, Icon } from '../ui.mjs';
import { apiGet, apiDelete, download } from '../api.mjs';
import { fmtTime, fmtDate, fmtDur, minutesBetween } from '../format.mjs';

function buildQuery(scope, f) {
  const p = new URLSearchParams();
  p.set('scope', scope);
  if (f.q) p.set('q', f.q);
  if (f.from) p.set('from', f.from);
  if (f.to) p.set('to', f.to);
  return p.toString();
}

export function HistoryTab({ hub }) {
  const { ctx, showToast, reloadStats, openSig } = hub;
  const { t, lang } = ctx;
  const [f, setF] = useState({ q: '', from: '', to: '' });
  const [rows, setRows] = useState(null);

  useEffect(() => {
    let alive = true;
    const id = setTimeout(() => {
      apiGet('/api/admin/visitors?' + buildQuery('history', f))
        .then((r) => { if (alive) setRows(r.visitors); })
        .catch(() => { if (alive) setRows([]); });
    }, 250);
    return () => { alive = false; clearTimeout(id); };
  }, [f]);

  async function del(v) {
    if (!window.confirm(t.confirmDelete)) return;
    try {
      await apiDelete(`/api/admin/visitors/${v.id}`);
      showToast(t.tDeleted);
      setF((x) => ({ ...x })); // trigger reload
      reloadStats();
    } catch (_) { /* ignore */ }
  }

  const set = (k, v) => setF((x) => ({ ...x, [k]: v }));
  const query = buildQuery('history', f);

  let body;
  if (rows == null) body = html`<div class="gk-empty"><div class="gk-spinner" style=${{ margin: '0 auto' }}></div></div>`;
  else if (rows.length === 0) body = html`<div class="gk-empty">${t.emptyHistory}</div>`;
  else body = html`<div class="gk-table-wrap"><table class="gk-table">
    <thead><tr>
      <th>${t.colName}</th><th>${t.colCompany}</th><th>${t.colHost}</th>
      <th>${t.colDate}</th><th>${t.colCheckIn}</th><th>${t.colCheckOut}</th>
      <th>${t.colStatus}</th><th></th>
    </tr></thead>
    <tbody>
      ${rows.map((v) => html`<tr key=${v.id}>
        <td class="gk-table__name">${v.name}</td>
        <td>${v.company}</td>
        <td>${v.host || '—'}</td>
        <td>${fmtDate(v.arrival, lang)}</td>
        <td>${fmtTime(v.arrival, lang)}</td>
        <td>${v.departure ? fmtTime(v.departure, lang) : '—'}</td>
        <td>${v.on_site
          ? html`<span class="gk-badge gk-badge--in">${t.statusIn}</span>`
          : v.auto_checked_out
            ? html`<span class="gk-badge gk-badge--missed">${t.statusMissed}</span>`
            : html`<span class="gk-badge gk-badge--out">${t.statusOut}</span>`}</td>
        <td><div class="gk-rowactions">
          ${v.has_signature ? html`<button class="gk-iconbtn" title=${t.viewSignature} onClick=${() => openSig(v.id, v.name)}><${Icon} name="pen" size=${18} /></button>` : null}
          <button class="gk-iconbtn" title=${t.delete} onClick=${() => del(v)}><${Icon} name="trash" size=${18} color="var(--red)" /></button>
        </div></td>
      </tr>`)}
    </tbody>
  </table></div>`;

  return html`<div class="gk-panel">
    <div class="gk-toolbar">
      <div class="gk-search">
        <${Icon} name="search" size=${18} />
        <input class="gk-input" placeholder=${t.searchPlaceholder} value=${f.q}
          onInput=${(e) => set('q', e.target.value)} />
      </div>
      <label class="gk-field"><span class="gk-field__label">${t.from}</span>
        <input class="gk-input gk-date" type="date" value=${f.from} onInput=${(e) => set('from', e.target.value)} /></label>
      <label class="gk-field"><span class="gk-field__label">${t.to}</span>
        <input class="gk-input gk-date" type="date" value=${f.to} onInput=${(e) => set('to', e.target.value)} /></label>
      <button class="gk-btn gk-btn--outline" onClick=${() => download('/api/admin/export/csv?' + query)}>
        <${Icon} name="download" size=${16} /> ${t.exportCsv}</button>
      <button class="gk-btn gk-btn--outline" onClick=${() => download('/api/admin/export/pdf?' + query)}>
        <${Icon} name="download" size=${16} /> ${t.exportPdf}</button>
    </div>
    ${body}
  </div>`;
}
