import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import htm from 'htm';
import { LANGS, LOCALES } from './i18n.mjs';

export const html = htm.bind(h);

// --- Icons -----------------------------------------------------------------
const PATHS = {
  phone: 'M6 3h4l2 5-2.6 1.5a12 12 0 0 0 5.6 5.6L17 14l5 2v4a2 2 0 0 1-2 2A18 18 0 0 1 2 5a2 2 0 0 1 2-2z',
  user: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4 21c0-4 4-6 8-6s8 2 8 6',
  exit: 'M14 3h5a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-5M10 17l5-5-5-5M15 12H3',
  drop: 'M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z',
  shield: 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z',
  lock: 'M7 10V7a5 5 0 0 1 10 0v3M5 10h14v11H5zM12 15v2',
  info: 'M12 16v-5M12 8.01V8M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z',
  users: 'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM22 21v-2a4 4 0 0 0-3-3.87M16 3.13A4 4 0 0 1 16 11',
  history: 'M3 12a9 9 0 1 0 3-6.7L3 8m0-5v5h5M12 7v5l3 2',
  chart: 'M4 20V10M10 20V4M16 20v-7M22 20H2',
  listaudit: 'M9 5h11M9 12h11M9 19h11M4 5h.01M4 12h.01M4 19h.01',
  clipboard: 'M9 3h6a1 1 0 0 1 1 1v1h2a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h2V4a1 1 0 0 1 1-1zM9 5v1h6V5',
  gear: 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19.4 15a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-2.7 1.1V21a2 2 0 1 1-4 0v-.1A1.6 1.6 0 0 0 7 19.4a1.6 1.6 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.6 1.6 0 0 0-1.1-2.7H1a2 2 0 1 1 0-4h.1A1.6 1.6 0 0 0 2.6 7a1.6 1.6 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.6 1.6 0 0 0 1.8.3H7a1.6 1.6 0 0 0 1-1.5V1a2 2 0 1 1 4 0v.1a1.6 1.6 0 0 0 2.7 1.1 1.6 1.6 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0-.3 1.8V7a1.6 1.6 0 0 0 1.5 1H23a2 2 0 1 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1z',
  globe: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM3 12h18M12 3a15 15 0 0 1 0 18 15 15 0 0 1 0-18z',
  alert: 'M12 9v4M12 17h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z',
  logout: 'M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9',
  download: 'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3',
  upload: 'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12',
  trash: 'M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2m2 0v14a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V6',
  plus: 'M12 5v14M5 12h14',
  check: 'M20 6 9 17l-5-5',
  x: 'M18 6 6 18M6 6l12 12',
  pen: 'M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z',
  search: 'M21 21l-4.3-4.3M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16z',
  back: 'M19 12H5M12 19l-7-7 7-7',
  chev: 'M9 6l6 6-6 6',
  monitor: 'M3 4h18v12H3zM8 20h8M12 16v4',
  badge: 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM12 2 4 5v6c0 5 3.4 8 8 9 4.6-1 8-4 8-9V5l-8-3z',
  mail: 'M4 4h16a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1zM3 6l9 7 9-7',
};

export function Icon({ name, size = 22, color = 'currentColor', width = 1.7 }) {
  const d = PATHS[name] || PATHS.info;
  return html`<svg width=${size} height=${size} viewBox="0 0 24 24" fill="none" aria-hidden="true"
    ><path d=${d} stroke=${color} stroke-width=${width} stroke-linecap="round" stroke-linejoin="round" /></svg>`;
}

// --- Modal -----------------------------------------------------------------
export function Modal({ open, title, icon, onClose, closeLabel = 'Schließen', children, wide }) {
  if (!open) return null;
  return html`
    <div class="gk-modal-overlay" onClick=${onClose}>
      <div class=${'gk-modal' + (wide ? ' gk-modal--wide' : '')} onClick=${(e) => e.stopPropagation()}>
        <div class="gk-modal__head">
          <div class="gk-modal__title">${icon}<span>${title}</span></div>
          <button class="gk-iconbtn" onClick=${onClose} aria-label=${closeLabel}>
            <${Icon} name="x" size=${20} />
          </button>
        </div>
        <div class="gk-modal__body">${children}</div>
      </div>
    </div>`;
}

// --- Toast -----------------------------------------------------------------
export function Toast({ message }) {
  if (!message) return null;
  return html`<div class="gk-toast" role="status">${message}</div>`;
}

// --- Step dots (4-step wizard) --------------------------------------------
export function StepDots({ index }) {
  return html`<div class="gk-steps">
    ${[0, 1, 2, 3].map((i) => html`<span key=${i}
      class=${'gk-step' + (i === index ? ' is-active' : '') + (i < index ? ' is-done' : '')}></span>`)}
  </div>`;
}

// --- Labelled field --------------------------------------------------------
export function Field({ label, hint, error, children, required }) {
  return html`
    <label class=${'gk-field' + (error ? ' has-error' : '')}>
      <span class="gk-field__label">${label}${required ? html`<b> *</b>` : hint ? html` <em>${hint}</em>` : null}</span>
      ${children}
    </label>`;
}

export function Spinner() {
  return html`<div class="gk-spinner"></div>`;
}

// --- Language flags + live clock (shared header cluster) --------------------
// Inline SVG so nothing loads from a CDN (CSP-safe) and flag emoji rendering
// (broken on some desktops) is avoided.
const FLAGS = {
  de: '<svg viewBox="0 0 24 16" xmlns="http://www.w3.org/2000/svg"><rect width="24" height="16" fill="#000"/><rect y="5.333" width="24" height="5.333" fill="#D00"/><rect y="10.666" width="24" height="5.334" fill="#FFCE00"/></svg>',
  en: '<svg viewBox="0 0 24 16" xmlns="http://www.w3.org/2000/svg"><rect width="24" height="16" fill="#012169"/><path d="M0 0 24 16M24 0 0 16" stroke="#fff" stroke-width="3.2"/><path d="M0 0 24 16M24 0 0 16" stroke="#C8102E" stroke-width="1.6"/><path d="M12 0V16M0 8H24" stroke="#fff" stroke-width="5.2"/><path d="M12 0V16M0 8H24" stroke="#C8102E" stroke-width="3.1"/></svg>',
  fr: '<svg viewBox="0 0 24 16" xmlns="http://www.w3.org/2000/svg"><rect width="24" height="16" fill="#fff"/><rect width="8" height="16" fill="#002654"/><rect x="16" width="8" height="16" fill="#CE1126"/></svg>',
  es: '<svg viewBox="0 0 24 16" xmlns="http://www.w3.org/2000/svg"><rect width="24" height="16" fill="#AA151B"/><rect y="4" width="24" height="8" fill="#F1BF00"/></svg>',
};

export function LangFlags({ lang, setLang }) {
  return html`<div class="gk-flags">
    ${LANGS.map((l) => html`<button key=${l} type="button" aria-label=${l.toUpperCase()}
      class=${'gk-flag-btn' + (lang === l ? ' is-on' : '')}
      onClick=${(e) => { e.preventDefault(); setLang(l); }}>
      <span class="gk-flag" dangerouslySetInnerHTML=${{ __html: FLAGS[l] || '' }}></span>
      <span class="gk-flag-btn__lbl">${l.toUpperCase()}</span>
    </button>`)}
  </div>`;
}

export function Clock({ lang }) {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 15000);
    return () => clearInterval(id);
  }, []);
  const locale = LOCALES[lang] || 'de-DE';
  const time = now.toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' });
  const date = now.toLocaleDateString(locale, { weekday: 'long', day: 'numeric', month: 'long' });
  return html`<div class="gk-clock">
    <div class="gk-clock__time">${time}</div>
    <div class="gk-clock__date">${date}</div>
  </div>`;
}

// Clock + divider + flags — the top-right cluster used on every screen.
export function HeaderMeta({ lang, setLang }) {
  return html`<div class="gk-headmeta">
    <${Clock} lang=${lang} />
    <div class="gk-headmeta__div"></div>
    <${LangFlags} lang=${lang} setLang=${setLang} />
  </div>`;
}
