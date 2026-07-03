import { render } from 'preact';
import { useState, useEffect, useCallback } from 'preact/hooks';
import { html, Toast } from './ui.mjs';
import { apiGet } from './api.mjs';
import { tt } from './i18n.mjs';
import { applyAccent } from './theme.mjs';
import { Kiosk } from './kiosk/index.mjs';
import { Admin } from './admin/index.mjs';

const EMPTY_BOOT = { settings: {}, health: { intro: {}, questions: [] }, info: [] };

function App() {
  const [boot, setBoot] = useState({ loaded: false });
  const [lang, setLang] = useState('de');
  const [mode, setMode] = useState('kiosk');
  const [toast, setToast] = useState('');
  const [initialPin] = useState(() => new URLSearchParams(location.search).get('co') || '');

  const showToast = useCallback((msg) => setToast(msg), []);
  useEffect(() => {
    if (!toast) return undefined;
    const id = setTimeout(() => setToast(''), 2600);
    return () => clearTimeout(id);
  }, [toast]);

  const loadBoot = useCallback(async () => {
    try {
      const data = await apiGet('/api/bootstrap');
      applyAccent((data.settings && data.settings.accent) || 'blau');
      setBoot({ loaded: true, ...EMPTY_BOOT, ...data });
    } catch (_) {
      setBoot({ loaded: true, error: true, ...EMPTY_BOOT });
    }
  }, []);
  useEffect(() => { loadBoot(); }, [loadBoot]);

  if (!boot.loaded) {
    return html`<div class="gk-boot"><div class="gk-spinner"></div></div>`;
  }

  const ctx = { lang, setLang, t: tt(lang), boot, reloadBoot: loadBoot, showToast, setMode };

  return html`
    ${mode === 'admin'
      ? html`<${Admin} ctx=${ctx} />`
      : html`<${Kiosk} ctx=${ctx} initialPin=${initialPin} />`}
    <${Toast} message=${toast} />
  `;
}

const root = document.getElementById('app');
root.className = '';
root.innerHTML = ''; // drop the static boot spinner before mounting
render(html`<${App} />`, root);
