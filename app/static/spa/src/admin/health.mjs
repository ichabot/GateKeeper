import { useState, useEffect } from 'preact/hooks';
import { html, Icon } from '../ui.mjs';
import { apiGet, apiPut } from '../api.mjs';
import { LANGS } from '../i18n.mjs';

function LangEdit({ value, onChange }) {
  return html`<div class="gk-seg">
    ${LANGS.map((l) => html`<button key=${l} class=${value === l ? 'is-on' : ''} onClick=${() => onChange(l)}>${l}</button>`)}
  </div>`;
}

let _tmpId = -1;

export function HealthTab({ hub }) {
  const { ctx, showToast } = hub;
  const { t, lang } = ctx;
  const [intro, setIntro] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [editLang, setEditLang] = useState(lang);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    apiGet('/api/admin/health').then((r) => {
      setIntro(r.intro || { de: '', en: '', fr: '', es: '' });
      setQuestions(r.questions || []);
    }).catch(() => setIntro({ de: '', en: '', fr: '', es: '' }));
  }, []);

  if (intro == null) return html`<div class="gk-panel"><div class="gk-empty"><div class="gk-spinner" style=${{ margin: '0 auto' }}></div></div></div>`;

  const setQText = (id, v) => setQuestions((qs) => qs.map((q) => (q.id === id ? { ...q, text: { ...q.text, [editLang]: v } } : q)));
  const setCorrect = (id, val) => setQuestions((qs) => qs.map((q) => (q.id === id ? { ...q, correct_answer: val } : q)));
  const removeQ = (id) => setQuestions((qs) => qs.filter((q) => q.id !== id));
  const addQ = () => setQuestions((qs) => [...qs, { id: _tmpId--, text: { de: '', en: '', fr: '', es: '' }, correct_answer: false, active: true }]);

  async function save() {
    setBusy(true);
    try {
      const payload = {
        intro,
        questions: questions.map((q) => ({
          id: typeof q.id === 'number' && q.id > 0 ? q.id : null,
          text: q.text, correct_answer: !!q.correct_answer, active: q.active !== false,
        })),
      };
      const r = await apiPut('/api/admin/health', payload);
      setIntro(r.intro); setQuestions(r.questions);
      showToast(t.savedToast);
      ctx.reloadBoot();
    } catch (_) { /* ignore */ } finally { setBusy(false); }
  }

  return html`<div class="gk-panel">
    <div class="gk-page-head"><h2>${t.tabHealth}</h2><p>${t.adminHealthHint}</p></div>
    <div class="gk-row" style=${{ justifyContent: 'space-between', marginBottom: '16px' }}>
      <span class="gk-field__label">${t.editLangLabel}</span>
      <${LangEdit} value=${editLang} onChange=${setEditLang} />
    </div>
    <label class="gk-field" style=${{ marginBottom: '20px' }}>
      <span class="gk-field__label">${t.fldIntro}</span>
      <textarea class="gk-textarea" style=${{ minHeight: '80px' }} value=${intro[editLang] || ''}
        onInput=${(e) => setIntro({ ...intro, [editLang]: e.target.value })}></textarea>
    </label>

    ${questions.map((q, i) => html`<div class="gk-qedit" key=${q.id}>
      <div class="gk-qedit__head">
        <span class="gk-qedit__num">${t.fldQuestion} ${i + 1}</span>
        <button class="gk-iconbtn" title=${t.delete} onClick=${() => removeQ(q.id)}><${Icon} name="trash" size=${18} color="var(--red)" /></button>
      </div>
      <label class="gk-field" style=${{ marginBottom: '12px' }}>
        <input class="gk-input" value=${q.text[editLang] || ''} onInput=${(e) => setQText(q.id, e.target.value)} />
      </label>
      <div class="gk-row" style=${{ gap: '12px' }}>
        <span class="gk-field__label">${t.expectLabel}:</span>
        <div class="gk-yn">
          <button class=${q.correct_answer ? 'on-yes' : ''} onClick=${() => setCorrect(q.id, true)}>${t.yes}</button>
          <button class=${!q.correct_answer ? 'on-no' : ''} onClick=${() => setCorrect(q.id, false)}>${t.no}</button>
        </div>
      </div>
    </div>`)}

    <div class="gk-actions gk-actions--split">
      <button class="gk-btn gk-btn--ghost" onClick=${addQ}><${Icon} name="plus" size=${16} /> ${t.addQuestion}</button>
      <button class="gk-btn" disabled=${busy} onClick=${save}>${t.save}</button>
    </div>
  </div>`;
}
