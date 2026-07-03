import { LOCALES } from './i18n.mjs';

const loc = (lang) => LOCALES[lang] || 'de-DE';

export function fmtDur(min) {
  const m = Math.max(0, Math.round(min || 0));
  const h = Math.floor(m / 60);
  const mm = m % 60;
  return h > 0 ? `${h} h ${mm} min` : `${mm} min`;
}

export function fmtTime(iso, lang) {
  if (!iso) return '—';
  return new Date(iso).toLocaleTimeString(loc(lang), { hour: '2-digit', minute: '2-digit' });
}

export function fmtDate(iso, lang) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString(loc(lang), { day: '2-digit', month: '2-digit', year: '2-digit' });
}

export function fmtDateTime(iso, lang) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString(loc(lang), {
    day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit',
  });
}

export function weekdayShort(isoDate, lang) {
  return new Date(isoDate + 'T00:00:00').toLocaleDateString(loc(lang), { weekday: 'short' });
}

export function minutesBetween(aIso, bIso) {
  if (!aIso || !bIso) return null;
  return Math.round((new Date(bIso) - new Date(aIso)) / 60000);
}
