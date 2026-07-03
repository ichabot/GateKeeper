import { useState, useEffect, useCallback } from 'preact/hooks';
import { html, Icon } from '../ui.mjs';
import { apiGet, apiPost, download } from '../api.mjs';
import { fmtTime, fmtDur, minutesBetween } from '../format.mjs';

export function LiveTab({ hub }) {
  const { ctx, showToast, reloadStats, openSig } = hub;
  const { t, lang } = ctx;
  const [rows, setRows] = useState(null);
  const [nowIso, setNowIso] = useState(new Date().toISOString());

  const load = useCallback(() => {
    apiGet('/api/admin/visitors?scope=live').then((r) => setRows(r.visitors)).catch(() => setRows([]));
  }, []);
  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    const id = setInterval(() => setNowIso(new Date().toISOString()), 30000);
    return () => clearInterval(id);
  }, []);

  async function checkout(v) {
    try {
      await apiPost(`/api/admin/visitors/${v.id}/checkout`, {});
      showToast(t.tCheckedOut);
      load(); reloadStats();
    } catch (_) { /* ignore */ }
  }

  let body;
  if (rows == null) body = html`<div class="gk-empty"><div class="gk-spinner" style=${{ margin: '0 auto' }}></div></div>`;
  else if (rows.length === 0) body = html`<div class="gk-empty">${t.emptyLive}</div>`;
  else body = html`<div class="gk-table-wrap"><table class="gk-table">
    <thead><tr>
      <th>${t.colName}</th><th>${t.colCompany}</th><th>${t.colHost}</th>
      <th>${t.colCheckIn}</th><th>${t.colDuration}</th><th></th>
    </tr></thead>
    <tbody>
      ${rows.map((v) => html`<tr key=${v.id}>
        <td class="gk-table__name">${v.name}</td>
        <td>${v.company}</td>
        <td>${v.host || '—'}</td>
        <td>${fmtTime(v.arrival, lang)}</td>
        <td>${fmtDur(minutesBetween(v.arrival, nowIso))}</td>
        <td><div class="gk-rowactions">
          ${v.has_signature ? html`<button class="gk-iconbtn" title=${t.viewSignature} onClick=${() => openSig(v.id, v.name)}><${Icon} name="pen" size=${18} /></button>` : null}
          <button class="gk-btn gk-btn--subtle" onClick=${() => checkout(v)}><${Icon} name="logout" size=${16} /> ${t.checkOut}</button>
        </div></td>
      </tr>`)}
    </tbody>
  </table></div>`;

  return html`<div class="gk-panel">
    <div class="gk-panel__head">
      <div class="gk-panel__title">${t.tabLive}</div>
      <button class="gk-btn gk-btn--outline" onClick=${() => download('/api/admin/export/csv?scope=live')}>
        <${Icon} name="download" size=${16} /> ${t.exportCsv}</button>
    </div>
    ${body}
  </div>`;
}
