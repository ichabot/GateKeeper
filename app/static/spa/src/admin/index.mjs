import { useState, useEffect, useCallback } from 'preact/hooks';
import { html, Icon, Modal, HeaderMeta, LangFlags } from '../ui.mjs';
import { apiGet, apiPost } from '../api.mjs';
import { fmtDur } from '../format.mjs';
import { LiveTab } from './live.mjs';
import { HistoryTab } from './history.mjs';
import { StatsTab } from './stats.mjs';
import { AuditTab } from './audit.mjs';
import { InfoTab } from './info.mjs';
import { HealthTab } from './health.mjs';
import { SettingsTab } from './settings.mjs';

const TABS = [
  { key: 'live', icon: 'users', label: 'tabLive' },
  { key: 'history', icon: 'history', label: 'tabHistory' },
  { key: 'stats', icon: 'chart', label: 'tabStats' },
  { key: 'audit', icon: 'listaudit', label: 'tabAudit' },
  { key: 'info', icon: 'info', label: 'tabInfo' },
  { key: 'health', icon: 'clipboard', label: 'tabHealth' },
  { key: 'settings', icon: 'gear', label: 'tabSettings' },
];

const TAB_COMPONENTS = {
  live: LiveTab, history: HistoryTab, stats: StatsTab, audit: AuditTab,
  info: InfoTab, health: HealthTab, settings: SettingsTab,
};

function LoginView({ ctx, onLogin }) {
  const { t, lang, setLang } = ctx;
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true); setError(false);
    try {
      const res = await apiPost('/api/admin/login', { username, password });
      onLogin(res.user);
    } catch (_) { setError(true); } finally { setBusy(false); }
  }

  return html`<div class="gk-login">
    <form class="gk-login__card gk-anim-in" onSubmit=${submit}>
      <div class="gk-login__badge"><${Icon} name="badge" size=${15} color="var(--accent)" /> ${t.adminBadge}</div>
      <h2 style=${{ fontSize: '22px', margin: '0 0 20px' }}>${t.loginTitle}</h2>
      <label class="gk-field" style=${{ marginBottom: '14px' }}>
        <span class="gk-field__label">${t.userLabel}</span>
        <input class="gk-input" value=${username} autocomplete="username"
          onInput=${(e) => setUsername(e.target.value)} />
      </label>
      <label class="gk-field" style=${{ marginBottom: '14px' }}>
        <span class="gk-field__label">${t.pwLabel}</span>
        <input class="gk-input" type="password" value=${password} autocomplete="current-password"
          onInput=${(e) => setPassword(e.target.value)} />
      </label>
      ${error ? html`<div class="gk-alert gk-alert--error"><${Icon} name="alert" size=${18} /> ${t.wrongPw}</div>` : null}
      <button class="gk-btn gk-btn--block" style=${{ marginTop: '18px' }} disabled=${busy} type="submit">${t.signIn}</button>
      <div class="gk-row" style=${{ justifyContent: 'space-between', alignItems: 'flex-end', marginTop: '18px' }}>
        <${LangFlags} lang=${lang} setLang=${setLang} />
        <button class="gk-mode-link" onClick=${(e) => { e.preventDefault(); ctx.setMode('kiosk'); }}>
          <${Icon} name="monitor" size=${16} /> Kiosk</button>
      </div>
    </form>
  </div>`;
}

function ForcePasswordChange({ ctx, onDone }) {
  const { t } = ctx;
  const [current, setCurrent] = useState('');
  const [pw1, setPw1] = useState('');
  const [pw2, setPw2] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError('');
    if (pw1.length < 8) { setError(t.pwTooShort); return; }
    if (pw1 !== pw2) { setError(t.pwMismatch); return; }
    setBusy(true);
    try {
      await apiPost('/api/admin/account/password', { current_password: current, new_password: pw1 });
      onDone();
    } catch (err) {
      const code = err && err.data && err.data.error;
      setError(
        code === 'wrong_current' ? t.pwWrongCurrent
          : code === 'same_password' ? t.pwSame
            : code === 'weak_password' ? t.pwTooShort
              : t.saveFail,
      );
    } finally { setBusy(false); }
  }

  return html`<div class="gk-login">
    <form class="gk-login__card gk-anim-in" onSubmit=${submit}>
      <div class="gk-login__badge"><${Icon} name="badge" size=${15} color="var(--accent)" /> ${t.adminBadge}</div>
      <h2 style=${{ fontSize: '22px', margin: '0 0 6px' }}>${t.pwChangeTitle}</h2>
      <p class="gk-muted" style=${{ margin: '0 0 20px' }}>${t.pwChangeSub}</p>
      <label class="gk-field" style=${{ marginBottom: '14px' }}>
        <span class="gk-field__label">${t.pwCurrent}</span>
        <input class="gk-input" type="password" value=${current} autocomplete="current-password"
          onInput=${(e) => setCurrent(e.target.value)} />
      </label>
      <label class="gk-field" style=${{ marginBottom: '14px' }}>
        <span class="gk-field__label">${t.pwNew}</span>
        <input class="gk-input" type="password" value=${pw1} autocomplete="new-password"
          onInput=${(e) => setPw1(e.target.value)} />
      </label>
      <label class="gk-field" style=${{ marginBottom: '14px' }}>
        <span class="gk-field__label">${t.pwConfirm}</span>
        <input class="gk-input" type="password" value=${pw2} autocomplete="new-password"
          onInput=${(e) => setPw2(e.target.value)} />
      </label>
      ${error ? html`<div class="gk-alert gk-alert--error"><${Icon} name="alert" size=${18} /> ${error}</div>` : null}
      <button class="gk-btn gk-btn--block" style=${{ marginTop: '18px' }} disabled=${busy} type="submit">${t.pwSaveBtn}</button>
    </form>
  </div>`;
}

export function Admin({ ctx }) {
  const { t, lang, setLang, showToast } = ctx;
  const [authed, setAuthed] = useState(null); // null = checking
  const [user, setUser] = useState(null);
  const [tab, setTab] = useState('live');
  const [stats, setStats] = useState(null);
  const [sigView, setSigView] = useState(null);
  const [notfallOpen, setNotfallOpen] = useState(false);
  const [notfallBusy, setNotfallBusy] = useState(false);

  useEffect(() => {
    apiGet('/api/admin/session')
      .then((r) => { setUser(r.user); setAuthed(true); })
      .catch(() => setAuthed(false));
  }, []);

  const reloadStats = useCallback(() => {
    apiGet('/api/admin/stats').then(setStats).catch(() => {});
  }, []);
  useEffect(() => { if (authed) reloadStats(); }, [authed, reloadStats]);

  const openSig = useCallback(async (vid, name) => {
    try {
      const r = await apiGet(`/api/admin/visitors/${vid}/signature`);
      setSigView({ url: r.signature || '', name });
    } catch (_) { /* ignore */ }
  }, []);

  async function sendNotfall() {
    setNotfallBusy(true);
    try {
      await apiPost('/api/admin/emergency', {});
      showToast(t.tNotfallSent);
      setNotfallOpen(false);
    } catch (e) {
      showToast((e.data && e.data.detail) || t.smtpFail);
    } finally { setNotfallBusy(false); }
  }

  if (authed === null) return html`<div class="gk-boot"><div class="gk-spinner"></div></div>`;
  if (!authed) return html`<${LoginView} ctx=${ctx} onLogin=${(u) => { setUser(u); setAuthed(true); }} />`;
  if (user && user.must_change_password) {
    return html`<${ForcePasswordChange} ctx=${ctx}
      onDone=${() => { setUser({ ...user, must_change_password: false }); showToast(t.pwChanged); }} />`;
  }

  const hub = { ctx, showToast, reloadStats, openSig };
  const TabComp = TAB_COMPONENTS[tab] || LiveTab;

  const kpis = [
    { label: t.statNowLabel, value: stats ? stats.now : '—' },
    { label: t.statTodayLabel, value: stats ? stats.today : '—' },
    { label: t.statWeekLabel, value: stats ? stats.week : '—' },
    { label: t.statAvgLabel, value: stats && stats.avg_minutes != null ? fmtDur(stats.avg_minutes) : '—' },
  ];

  return html`<div class="gk-admin">
    <div class="gk-topbar">
      <div class="gk-brand">
        <div class="gk-brand__logo gk-brand__logo--mono"><${Icon} name="badge" size=${22} color="#fff" /></div>
        <div><div class="gk-brand__name">GateKeeper</div><div class="gk-brand__sub">${t.adminBadge}</div></div>
      </div>
      <div class="gk-topbar__actions">
        <${HeaderMeta} lang=${lang} setLang=${setLang} />
        <button class="gk-btn gk-btn--danger" onClick=${() => setNotfallOpen(true)}>
          <${Icon} name="alert" size=${18} color="#fff" /> ${t.notfall}</button>
        <button class="gk-iconbtn" title="Kiosk" onClick=${() => ctx.setMode('kiosk')}><${Icon} name="monitor" size=${20} /></button>
        <button class="gk-btn gk-btn--ghost" onClick=${async () => { await apiPost('/api/admin/logout', {}).catch(() => {}); setAuthed(false); }}>
          <${Icon} name="logout" size=${18} /> ${t.logout}</button>
      </div>
    </div>

    <div class="gk-admin__body">
      <nav class="gk-sidebar">
        ${TABS.map((tb) => html`<button key=${tb.key} class=${'gk-navbtn' + (tab === tb.key ? ' is-on' : '')}
          onClick=${() => setTab(tb.key)}>
          <${Icon} name=${tb.icon} size=${20} color=${tab === tb.key ? '#fff' : 'currentColor'} />
          <span>${t[tb.label]}</span>
        </button>`)}
      </nav>

      <main class="gk-content">
        <div class="gk-content__inner">
          <div class="gk-kpis">
            ${kpis.map((k, i) => html`<div class="gk-kpi" key=${i}>
              <div class="gk-kpi__label">${k.label}</div>
              <div class="gk-kpi__value">${k.value}</div>
            </div>`)}
          </div>
          <div class="gk-anim-in" key=${tab}><${TabComp} hub=${hub} stats=${stats} /></div>
        </div>
      </main>
    </div>

    <${Modal} open=${notfallOpen} onClose=${() => setNotfallOpen(false)}
      title=${t.notfallTitle} closeLabel=${t.closeBtn}
      icon=${html`<${Icon} name="alert" size=${22} color="var(--red)" />`}>
      <p class="gk-muted" style=${{ marginTop: 0 }}>${t.notfallSub}</p>
      <div class="gk-panel" style=${{ boxShadow: 'none', background: 'var(--soft)', marginBottom: '18px' }}>
        <div class="gk-kpi__label">${t.notfallPresent}</div>
        <div class="gk-kpi__value">${stats ? stats.now : '—'}</div>
      </div>
      <button class="gk-btn gk-btn--danger gk-btn--block" disabled=${notfallBusy} onClick=${sendNotfall}>
        <${Icon} name="mail" size=${18} color="#fff" /> ${t.notfallSend}</button>
    <//>

    <${Modal} open=${!!sigView} onClose=${() => setSigView(null)}
      title=${(sigView && sigView.name) || t.signatureView} closeLabel=${t.closeBtn}
      icon=${html`<${Icon} name="pen" size=${20} color="var(--accent)" />`}>
      ${sigView && sigView.url
        ? html`<img class="gk-sig-view" src=${sigView.url} alt="" />`
        : html`<p class="gk-muted">—</p>`}
    <//>
  </div>`;
}
