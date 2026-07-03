import { useState, useEffect } from 'preact/hooks';
import { html } from '../ui.mjs';
import { apiGet } from '../api.mjs';
import { fmtDateTime } from '../format.mjs';

const LABELS = {
  login: { de: 'Admin-Anmeldung', en: 'Admin sign-in', fr: 'Connexion admin', es: 'Acceso admin' },
  logout: { de: 'Abmeldung', en: 'Sign-out', fr: 'Déconnexion', es: 'Cierre de sesión' },
  checkout_admin: { de: 'Auscheckung über Admin', en: 'Check-out via admin', fr: 'Départ via admin', es: 'Salida vía admin' },
  delete: { de: 'Datensatz gelöscht (DSGVO)', en: 'Record deleted (GDPR)', fr: 'Enregistrement supprimé (RGPD)', es: 'Registro eliminado (RGPD)' },
  export_csv: { de: 'CSV-Export · Verlauf', en: 'CSV export · History', fr: 'Export CSV · Historique', es: 'Exportación CSV · Historial' },
  export_pdf: { de: 'PDF-Export · Verlauf', en: 'PDF export · History', fr: 'Export PDF · Historique', es: 'Exportación PDF · Historial' },
  emergency: { de: 'Notfall-Meldung gesendet', en: 'Emergency alert sent', fr: 'Alerte d’urgence envoyée', es: 'Alerta de emergencia enviada' },
  settings_saved: { de: 'Einstellungen gespeichert', en: 'Settings saved', fr: 'Paramètres enregistrés', es: 'Ajustes guardados' },
  info_saved: { de: 'Informationen gespeichert', en: 'Information saved', fr: 'Informations enregistrées', es: 'Información guardada' },
  health_saved: { de: 'Fragebogen gespeichert', en: 'Questionnaire saved', fr: 'Questionnaire enregistré', es: 'Cuestionario guardado' },
  content_import: { de: 'Inhalte importiert', en: 'Content imported', fr: 'Contenus importés', es: 'Contenidos importados' },
};

function label(action, lang) {
  const m = LABELS[action];
  return m ? (m[lang] || m.de) : action;
}

export function AuditTab({ hub }) {
  const { ctx } = hub;
  const { t, lang } = ctx;
  const [rows, setRows] = useState(null);

  useEffect(() => {
    apiGet('/api/admin/audit').then((r) => setRows(r.audit)).catch(() => setRows([]));
  }, []);

  let body;
  if (rows == null) body = html`<div class="gk-empty"><div class="gk-spinner" style=${{ margin: '0 auto' }}></div></div>`;
  else if (rows.length === 0) body = html`<div class="gk-empty">—</div>`;
  else body = html`<div class="gk-audit">
    ${rows.map((a, i) => html`<div class="gk-audit__row" key=${i}>
      <div class="gk-audit__time">${fmtDateTime(a.time, lang)}</div>
      <div>${label(a.action, lang)}${a.detail ? html` · <span class="gk-muted">${a.detail}</span>` : null}</div>
      <div class="gk-audit__user">${a.user || '—'}</div>
    </div>`)}
  </div>`;

  return html`<div class="gk-panel">
    <div class="gk-panel__head"><div class="gk-panel__title">${t.tabAudit}</div></div>
    ${body}
  </div>`;
}
