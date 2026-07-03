import { useState, useEffect } from 'preact/hooks';
import { html, Icon } from '../ui.mjs';
import { apiGet, apiPut } from '../api.mjs';
import { pick, LANGS } from '../i18n.mjs';

function LangEdit({ value, onChange }) {
  return html`<div class="gk-seg">
    ${LANGS.map((l) => html`<button key=${l} class=${value === l ? 'is-on' : ''} onClick=${() => onChange(l)}>${l}</button>`)}
  </div>`;
}

export function InfoTab({ hub }) {
  const { ctx, showToast } = hub;
  const { t, lang } = ctx;
  const [cats, setCats] = useState(null);
  const [selKey, setSelKey] = useState(null);
  const [editLang, setEditLang] = useState(lang);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    apiGet('/api/admin/info').then((r) => {
      setCats(r.info);
      if (r.info && r.info.length) setSelKey(r.info[0].key);
    }).catch(() => setCats([]));
  }, []);

  if (cats == null) return html`<div class="gk-panel"><div class="gk-empty"><div class="gk-spinner" style=${{ margin: '0 auto' }}></div></div></div>`;

  const sel = cats.find((c) => c.key === selKey);
  const updateSel = (mut) => setCats((cs) => cs.map((c) => (c.key === selKey ? mut({ ...c }) : c)));
  const setTitle = (v) => updateSel((c) => ({ ...c, title: { ...c.title, [editLang]: v } }));
  const setBody = (v) => updateSel((c) => ({ ...c, body: { ...c.body, [editLang]: v } }));
  const setEntryLabel = (i, v) => updateSel((c) => ({ ...c, entries: c.entries.map((e, idx) => (idx === i ? { ...e, label: { ...e.label, [editLang]: v } } : e)) }));
  const setEntryValue = (i, v) => updateSel((c) => ({ ...c, entries: c.entries.map((e, idx) => (idx === i ? { ...e, value: v } : e)) }));
  const addEntry = () => updateSel((c) => ({ ...c, entries: [...(c.entries || []), { label: { de: '', en: '', fr: '', es: '' }, value: '' }] }));
  const removeEntry = (i) => updateSel((c) => ({ ...c, entries: c.entries.filter((_, idx) => idx !== i) }));

  async function save() {
    if (!sel) return;
    setBusy(true);
    try {
      await apiPut(`/api/admin/info/${sel.key}`, { title: sel.title, body: sel.body, entries: sel.entries });
      showToast(t.savedToast);
      ctx.reloadBoot();
    } catch (_) { /* ignore */ } finally { setBusy(false); }
  }

  return html`<div class="gk-panel">
    <div class="gk-page-head"><h2>${t.tabInfo}</h2><p>${t.adminInfoHint}</p></div>
    <div class="gk-editor">
      <div class="gk-editor__list">
        ${cats.map((c) => html`<button key=${c.key} class=${'gk-editor__item' + (c.key === selKey ? ' is-on' : '')}
          onClick=${() => setSelKey(c.key)}>
          <${Icon} name=${c.icon} size=${18} color=${c.accent} /> ${pick(c.title, editLang) || c.key}
        </button>`)}
      </div>
      <div>
        ${sel ? html`
          <div class="gk-row" style=${{ justifyContent: 'space-between', marginBottom: '16px' }}>
            <span class="gk-field__label">${t.editLangLabel}</span>
            <${LangEdit} value=${editLang} onChange=${setEditLang} />
          </div>
          <label class="gk-field" style=${{ marginBottom: '16px' }}>
            <span class="gk-field__label">${t.fldTitle}</span>
            <input class="gk-input" value=${sel.title[editLang] || ''} onInput=${(e) => setTitle(e.target.value)} />
          </label>
          ${sel.type === 'dir'
            ? html`<div>
                ${(sel.entries || []).map((e, i) => html`<div class="gk-row" key=${i} style=${{ gap: '10px', marginBottom: '10px', alignItems: 'flex-end' }}>
                  <label class="gk-field gk-grow"><span class="gk-field__label">${t.fldLabel}</span>
                    <input class="gk-input" value=${e.label[editLang] || ''} onInput=${(ev) => setEntryLabel(i, ev.target.value)} /></label>
                  <label class="gk-field gk-grow"><span class="gk-field__label">${t.fldValue}</span>
                    <input class="gk-input" value=${e.value || ''} onInput=${(ev) => setEntryValue(i, ev.target.value)} /></label>
                  <button class="gk-iconbtn" title=${t.delete} onClick=${() => removeEntry(i)}><${Icon} name="trash" size=${18} color="var(--red)" /></button>
                </div>`)}
                <button class="gk-btn gk-btn--ghost" onClick=${addEntry}><${Icon} name="plus" size=${16} /> ${t.addEntry}</button>
              </div>`
            : html`<label class="gk-field">
                <span class="gk-field__label">${t.fldBody}</span>
                <textarea class="gk-textarea" style=${{ minHeight: '260px' }} value=${sel.body[editLang] || ''}
                  onInput=${(e) => setBody(e.target.value)}></textarea>
              </label>`}
          <div class="gk-actions">
            <button class="gk-btn" disabled=${busy} onClick=${save}>${t.saveInfo}</button>
          </div>
        ` : null}
      </div>
    </div>
  </div>`;
}
