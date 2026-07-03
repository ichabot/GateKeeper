import { html } from '../ui.mjs';
import { weekdayShort } from '../format.mjs';

export function StatsTab({ hub, stats }) {
  const { ctx } = hub;
  const { t, lang } = ctx;

  if (!stats) {
    return html`<div class="gk-panel"><div class="gk-empty"><div class="gk-spinner" style=${{ margin: '0 auto' }}></div></div></div>`;
  }

  const bars = stats.bars || [];
  const max = Math.max(1, ...bars.map((b) => b.count));

  return html`<div class="gk-panel">
    <div class="gk-panel__head">
      <div><div class="gk-panel__title">${t.chartTitle}</div>
      <div class="gk-muted" style=${{ fontSize: '13px', marginTop: '2px' }}>${t.chartSub}</div></div>
    </div>
    <div class="gk-bars">
      ${bars.map((b) => html`<div class="gk-bar" key=${b.date}>
        <div class="gk-bar__count">${b.count}</div>
        <div class="gk-bar__col" style=${{ height: Math.round((b.count / max) * 100) + '%' }}></div>
        <div class="gk-bar__label">${weekdayShort(b.date, lang)}</div>
      </div>`)}
    </div>
  </div>`;
}
