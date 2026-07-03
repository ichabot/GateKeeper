import { useState, useEffect, useRef } from 'preact/hooks';
import { html, Icon } from '../ui.mjs';
import { apiGet, apiPut, apiPost, apiDelete, download } from '../api.mjs';
import { applyAccent, ACCENT_KEYS, PALETTES, isHexAccent } from '../theme.mjs';
import { fmtDate } from '../format.mjs';

const SUBS = [
  { key: 'mail', label: 'setMail' },
  { key: 'design', label: 'setDesign' },
  { key: 'kiosk', label: 'setKiosk' },
  { key: 'users', label: 'setUsers' },
  { key: 'dsgvo', label: 'setDsgvo' },
  { key: 'content', label: 'setContent' },
];

function Switch({ checked, onChange, label }) {
  return html`<label class="gk-switch">
    <input type="checkbox" checked=${!!checked} onChange=${(e) => onChange(e.target.checked)} />
    <span>${label}</span>
  </label>`;
}

export function SettingsTab({ hub }) {
  const { ctx, showToast, reloadStats } = hub;
  const { t } = ctx;
  const [sub, setSub] = useState('mail');
  const [loaded, setLoaded] = useState(false);
  const [branding, setBranding] = useState({ company_name: '', logo_url: '', accent: 'blau' });
  const [kiosk, setKiosk] = useState({ kiosk_backdrop: 'hell', collect_plate: true, auto_return_seconds: 20 });
  const [privacy, setPrivacy] = useState({ retention_days: 90 });
  const [smtp, setSmtp] = useState({ smtp_host: '', smtp_port: 587, smtp_user: '', smtp_sender: '', smtp_recipients: '', emergency_recipients: '', use_tls: true, enabled: false, password_set: false });
  const [smtpPassword, setSmtpPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const logoInput = useRef(null);

  function apply(data) {
    setBranding(data.branding); setKiosk(data.kiosk); setPrivacy(data.privacy); setSmtp(data.smtp);
    setLoaded(true);
  }
  function load() { apiGet('/api/admin/settings').then(apply).catch(() => setLoaded(true)); }
  useEffect(() => { load(); }, []);

  async function save() {
    setBusy(true);
    try {
      const payload = {
        branding: { company_name: branding.company_name, accent: branding.accent },
        kiosk: {
          kiosk_backdrop: kiosk.kiosk_backdrop, collect_plate: kiosk.collect_plate,
          auto_return_seconds: Number(kiosk.auto_return_seconds) || 20,
        },
        privacy: { retention_days: Number(privacy.retention_days) || 90 },
        smtp: {
          smtp_host: smtp.smtp_host, smtp_port: Number(smtp.smtp_port) || 587, smtp_user: smtp.smtp_user,
          smtp_sender: smtp.smtp_sender, smtp_recipients: smtp.smtp_recipients,
          emergency_recipients: smtp.emergency_recipients, use_tls: smtp.use_tls, enabled: smtp.enabled,
        },
      };
      if (smtpPassword) payload.smtp.smtp_password = smtpPassword;
      const data = await apiPut('/api/admin/settings', payload);
      apply(data); setSmtpPassword('');
      showToast(t.tSettingsSaved);
      ctx.reloadBoot();
    } catch (_) { /* ignore */ } finally { setBusy(false); }
  }

  async function testSmtp() {
    setBusy(true);
    try {
      await save();
      await apiPost('/api/admin/smtp/test', {});
      showToast(t.smtpOk);
    } catch (_) { showToast(t.smtpFail); } finally { setBusy(false); }
  }

  async function onLogoFile(e) {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    const fd = new FormData(); fd.append('logo', file);
    try {
      const r = await apiPost('/api/admin/settings/logo', fd);
      setBranding((b) => ({ ...b, logo_url: r.logo_url }));
      showToast(t.tSettingsSaved); ctx.reloadBoot();
    } catch (_) { /* ignore */ }
    e.target.value = '';
  }
  async function removeLogo() {
    try { await apiDelete('/api/admin/settings/logo'); setBranding((b) => ({ ...b, logo_url: '' })); ctx.reloadBoot(); } catch (_) { /* */ }
  }
  function chooseAccent(k) { setBranding((b) => ({ ...b, accent: k })); applyAccent(k); }

  if (!loaded) return html`<div class="gk-panel"><div class="gk-empty"><div class="gk-spinner" style=${{ margin: '0 auto' }}></div></div></div>`;

  const field = (label, value, onInput, opts = {}) => html`<label class="gk-field" style=${{ marginBottom: '14px' }}>
    <span class="gk-field__label">${label}</span>
    <input class="gk-input" type=${opts.type || 'text'} value=${value} placeholder=${opts.ph || ''}
      onInput=${(e) => onInput(e.target.value)} /></label>`;

  let panel;
  if (sub === 'mail') {
    panel = html`<div>
      <p class="gk-muted" style=${{ marginTop: 0 }}>${t.mailHint}</p>
      ${field(t.fldServer, smtp.smtp_host, (v) => setSmtp({ ...smtp, smtp_host: v }))}
      <div class="gk-fields gk-fields--2">
        ${field(t.fldPort, smtp.smtp_port, (v) => setSmtp({ ...smtp, smtp_port: v }), { type: 'number' })}
        ${field(t.fldUser, smtp.smtp_user, (v) => setSmtp({ ...smtp, smtp_user: v }))}
      </div>
      ${field(t.fldPassword, smtpPassword, setSmtpPassword, { type: 'password', ph: smtp.password_set ? '••••••••' : '' })}
      <div class="gk-muted" style=${{ fontSize: '12.5px', margin: '-8px 0 14px' }}>${t.pwKeep}</div>
      ${field(t.fldFrom, smtp.smtp_sender, (v) => setSmtp({ ...smtp, smtp_sender: v }))}
      ${field(t.fldReportRecipients, smtp.smtp_recipients, (v) => setSmtp({ ...smtp, smtp_recipients: v }))}
      ${field(t.fldRecipients, smtp.emergency_recipients, (v) => setSmtp({ ...smtp, emergency_recipients: v }))}
      <div class="gk-muted" style=${{ fontSize: '12.5px', margin: '-8px 0 14px' }}>${t.recipientsHint}</div>
      <div class="gk-row" style=${{ gap: '20px', marginBottom: '16px' }}>
        <${Switch} checked=${smtp.use_tls} onChange=${(v) => setSmtp({ ...smtp, use_tls: v })} label=${t.useTls} />
        <${Switch} checked=${smtp.enabled} onChange=${(v) => setSmtp({ ...smtp, enabled: v })} label=${t.smtpEnabled} />
      </div>
      <div class="gk-actions gk-actions--split">
        <button class="gk-btn gk-btn--ghost" disabled=${busy} onClick=${testSmtp}><${Icon} name="mail" size=${16} /> ${t.testSmtp}</button>
        <button class="gk-btn" disabled=${busy} onClick=${save}>${t.save}</button>
      </div>
    </div>`;
  } else if (sub === 'design') {
    const accentIsCustom = isHexAccent(branding.accent);
    const accentPicker = accentIsCustom
      ? (branding.accent[0] === '#' ? branding.accent : '#' + branding.accent)
      : ((PALETTES[branding.accent] && PALETTES[branding.accent][0]) || '#2f6fed');
    const onHexInput = (v) => {
      let val = (v || '').trim();
      if (val && val[0] !== '#') val = '#' + val;
      setBranding((b) => ({ ...b, accent: val }));
      if (/^#[0-9a-fA-F]{6}$/.test(val)) applyAccent(val);
    };
    panel = html`<div>
      <p class="gk-muted" style=${{ marginTop: 0 }}>${t.designHint}</p>
      ${field(t.fldCompany, branding.company_name, (v) => setBranding({ ...branding, company_name: v }))}
      <div class="gk-field" style=${{ marginBottom: '18px' }}>
        <span class="gk-field__label">${t.fldLogo}</span>
        <div class="gk-row" style=${{ gap: '16px' }}>
          ${branding.logo_url
            ? html`<img class="gk-logo-preview" src=${branding.logo_url} alt="" />`
            : html`<div class="gk-logo-preview" style=${{ display: 'grid', placeItems: 'center', color: 'var(--faint)' }}><${Icon} name="info" size=${22} /></div>`}
          <div class="gk-row" style=${{ gap: '8px' }}>
            <button class="gk-btn gk-btn--outline" onClick=${() => logoInput.current && logoInput.current.click()}><${Icon} name="upload" size=${16} /> ${t.uploadLogo}</button>
            ${branding.logo_url ? html`<button class="gk-btn gk-btn--ghost" onClick=${removeLogo}>${t.removeLogo}</button>` : null}
          </div>
          <input ref=${logoInput} type="file" accept=".png,.svg,.jpg,.jpeg,.webp" style=${{ display: 'none' }} onChange=${onLogoFile} />
        </div>
        <div class="gk-muted" style=${{ fontSize: '12.5px', marginTop: '8px' }}>${t.logoHint}</div>
      </div>
      <div class="gk-field" style=${{ marginBottom: '18px' }}>
        <span class="gk-field__label">${t.fldAccent}</span>
        <div class="gk-swatches" style=${{ marginBottom: '12px' }}>
          ${ACCENT_KEYS.map((k) => html`<button key=${k} class=${'gk-swatch' + (branding.accent === k ? ' is-on' : '')}
            style=${{ background: PALETTES[k][0] }} title=${k} onClick=${() => chooseAccent(k)}></button>`)}
        </div>
        <div class="gk-row" style=${{ gap: '10px', alignItems: 'center' }}>
          <input type="color" class=${'gk-color' + (accentIsCustom ? ' is-on' : '')} value=${accentPicker}
            onInput=${(e) => chooseAccent(e.target.value)} />
          <input class="gk-input" style=${{ maxWidth: '150px' }} spellcheck="false"
            value=${accentIsCustom ? branding.accent : ''} placeholder="#1F4C5C"
            onInput=${(e) => onHexInput(e.target.value)} />
          <span class="gk-muted" style=${{ fontSize: '12.5px' }}>${t.customColor}</span>
        </div>
      </div>
      <div class="gk-actions"><button class="gk-btn" disabled=${busy} onClick=${save}>${t.save}</button></div>
    </div>`;
  } else if (sub === 'kiosk') {
    panel = html`<div>
      <p class="gk-muted" style=${{ marginTop: 0 }}>${t.kioskHint}</p>
      <label class="gk-field" style=${{ marginBottom: '16px' }}>
        <span class="gk-field__label">${t.fldBackdrop}</span>
        <select class="gk-select" value=${kiosk.kiosk_backdrop} onChange=${(e) => setKiosk({ ...kiosk, kiosk_backdrop: e.target.value })}>
          <option value="hell">${t.backdropHell}</option>
          <option value="anthrazit">${t.backdropAnthrazit}</option>
          <option value="schlicht">${t.backdropSchlicht}</option>
        </select>
      </label>
      <div style=${{ marginBottom: '16px' }}>
        <${Switch} checked=${kiosk.collect_plate} onChange=${(v) => setKiosk({ ...kiosk, collect_plate: v })} label=${t.fldPlate} />
      </div>
      ${field(t.fldAutoReturn, kiosk.auto_return_seconds, (v) => setKiosk({ ...kiosk, auto_return_seconds: v }), { type: 'number' })}
      <div class="gk-actions"><button class="gk-btn" disabled=${busy} onClick=${save}>${t.save}</button></div>
    </div>`;
  } else if (sub === 'users') {
    panel = html`<${Users} hub=${hub} />`;
  } else if (sub === 'dsgvo') {
    panel = html`<div>
      <p class="gk-muted" style=${{ marginTop: 0 }}>${t.dsgvoHint}</p>
      ${field(t.fldRetention, privacy.retention_days, (v) => setPrivacy({ ...privacy, retention_days: v }), { type: 'number' })}
      <div class="gk-muted" style=${{ fontSize: '12.5px', margin: '-8px 0 18px' }}>${t.retentionNote}</div>
      <div class="gk-actions" style=${{ marginBottom: '24px' }}><button class="gk-btn" disabled=${busy} onClick=${save}>${t.save}</button></div>
      <${PrivacyManage} hub=${hub} />
    </div>`;
  } else {
    panel = html`<${ContentIO} hub=${hub} />`;
  }

  return html`<div class="gk-panel">
    <div class="gk-page-head"><h2>${t.tabSettings}</h2></div>
    <div class="gk-subtabs">
      ${SUBS.map((s) => html`<button key=${s.key} class=${sub === s.key ? 'is-on' : ''} onClick=${() => setSub(s.key)}>${t[s.label]}</button>`)}
    </div>
    ${panel}
  </div>`;
}

// --- DSGVO: one search → one combined list (visits + badges) ---------------
// A single search box returns ONE list mixing matching visit records and
// returning-visitor badges ("Besucherausweise"), each row tagged by type and
// individually deletable. Badges are always shown (all when idle); visit
// history is only searched once the term is 2+ chars (it can be large).
function PrivacyManage({ hub }) {
  const { ctx, showToast, reloadStats } = hub;
  const { t, lang } = ctx;
  const [term, setTerm] = useState('');
  const [visits, setVisits] = useState([]);
  const [badges, setBadges] = useState([]);
  const [searching, setSearching] = useState(false);

  const q = term.trim();

  // Nothing is shown until you actually search (min. 2 chars).
  useEffect(() => {
    if (q.length < 2) { setBadges([]); setVisits([]); setSearching(false); return undefined; }
    let alive = true;
    setSearching(true);
    const id = setTimeout(async () => {
      try {
        const [br, vr] = await Promise.all([
          apiGet('/api/admin/profiles?q=' + encodeURIComponent(q)),
          apiGet('/api/admin/visitors?scope=history&q=' + encodeURIComponent(q)),
        ]);
        if (!alive) return;
        setBadges(br.profiles || []);
        setVisits(vr.visitors || []);
      } catch (_) {
        if (alive) { setBadges([]); setVisits([]); }
      } finally {
        if (alive) setSearching(false);
      }
    }, 250);
    return () => { alive = false; clearTimeout(id); };
  }, [q]);

  async function delVisit(v) {
    if (!window.confirm(t.confirmDelete)) return;
    try {
      await apiDelete(`/api/admin/visitors/${v.id}`);
      showToast(t.tDeleted);
      setVisits((rs) => rs.filter((x) => x.id !== v.id));
      reloadStats();
    } catch (_) { /* ignore */ }
  }

  async function delBadge(p) {
    if (!window.confirm(t.confirmDeleteProfile)) return;
    try {
      await apiDelete(`/api/admin/profiles/${p.id}`);
      showToast(t.tProfileDeleted);
      setBadges((rs) => rs.filter((x) => x.id !== p.id));
    } catch (_) { /* ignore */ }
  }

  // Combined list: badges (stored identity) first, then visit records.
  const items = [
    ...badges.map((p) => ({ kind: 'badge', data: p })),
    ...visits.map((v) => ({ kind: 'visit', data: v })),
  ];

  const rowBox = { justifyContent: 'space-between', padding: '10px 4px', borderBottom: '1px solid var(--line)' };
  const renderRow = (it) => it.kind === 'badge'
    ? html`<div class="gk-row" key=${'p' + it.data.id} style=${rowBox}>
        <div>
          <div class="gk-row" style=${{ gap: '8px' }}><b>${it.data.name}</b> <span class="gk-tag">${t.tagBadge}</span></div>
          <div class="gk-muted" style=${{ fontSize: '12px' }}>${it.data.company} · ${t.colLastSeen}: ${fmtDate(it.data.last_seen_at, lang)} · ${t.colCreated}: ${fmtDate(it.data.created_at, lang)}</div>
        </div>
        <button class="gk-iconbtn" title=${t.delete} onClick=${() => delBadge(it.data)}><${Icon} name="trash" size=${18} color="var(--red)" /></button>
      </div>`
    : html`<div class="gk-row" key=${'v' + it.data.id} style=${rowBox}>
        <div>
          <div class="gk-row" style=${{ gap: '8px' }}><b>${it.data.name}</b> <span class="gk-tag gk-tag--muted">${t.tagVisit}</span></div>
          <div class="gk-muted" style=${{ fontSize: '12px' }}>${it.data.company} · ${fmtDate(it.data.arrival, lang)}</div>
        </div>
        <button class="gk-iconbtn" title=${t.delete} onClick=${() => delVisit(it.data)}><${Icon} name="trash" size=${18} color="var(--red)" /></button>
      </div>`;

  return html`<div>
    <div class="gk-panel__title" style=${{ marginBottom: '4px' }}>${t.searchDelete}</div>
    <p class="gk-muted" style=${{ marginTop: 0, fontSize: '12.5px' }}>${t.searchAllHint}</p>
    <div class="gk-search" style=${{ marginBottom: '14px' }}>
      <${Icon} name="search" size=${18} />
      <input class="gk-input" placeholder=${t.searchDeletePh} value=${term} onInput=${(e) => setTerm(e.target.value)} />
    </div>
    ${q.length < 2
      ? html`<div class="gk-empty">${t.searchTypeHint}</div>`
      : (searching && items.length === 0)
        ? html`<div class="gk-empty"><div class="gk-spinner" style=${{ margin: '0 auto' }}></div></div>`
        : items.length === 0
          ? html`<div class="gk-empty">${t.noResults}</div>`
          : items.map(renderRow)}
  </div>`;
}

// --- Admin users (accounts) -----------------------------------------------
function Users({ hub }) {
  const { ctx, showToast } = hub;
  const { t } = ctx;
  const [rows, setRows] = useState(null);
  const [busy, setBusy] = useState(false);
  const [nu, setNu] = useState('');       // new username
  const [np, setNp] = useState('');       // new password
  const [resetId, setResetId] = useState(null);
  const [resetPw, setResetPw] = useState('');

  function load() {
    apiGet('/api/admin/users').then((r) => setRows(r.users)).catch(() => setRows([]));
  }
  useEffect(() => { load(); }, []);

  async function create() {
    if (nu.trim().length < 3 || np.length < 6) { showToast(t.userValidation); return; }
    setBusy(true);
    try {
      await apiPost('/api/admin/users', { username: nu.trim(), password: np });
      setNu(''); setNp(''); showToast(t.tUserCreated); load();
    } catch (e) {
      const err = e && e.data && e.data.error;
      showToast(err === 'exists' ? t.userExists : (err === 'bad_username' || err === 'weak_password' ? t.userValidation : t.saveFail));
    } finally { setBusy(false); }
  }

  async function doReset(u) {
    if (resetPw.length < 6) { showToast(t.userValidation); return; }
    setBusy(true);
    try {
      await apiPut(`/api/admin/users/${u.id}/password`, { password: resetPw });
      setResetId(null); setResetPw(''); showToast(t.tPasswordReset);
    } catch (_) { showToast(t.saveFail); } finally { setBusy(false); }
  }

  async function del(u) {
    if (!window.confirm(t.confirmDeleteUser.replace('%s', u.username))) return;
    try {
      await apiDelete(`/api/admin/users/${u.id}`);
      showToast(t.tUserDeleted); load();
    } catch (e) {
      showToast(e && e.data && e.data.error === 'self' ? t.cannotDeleteSelf : t.saveFail);
    }
  }

  return html`<div>
    <div class="gk-panel__title" style=${{ marginBottom: '4px' }}>${t.usersTitle}</div>
    <p class="gk-muted" style=${{ marginTop: 0, fontSize: '12.5px' }}>${t.usersHint}</p>

    ${rows == null
      ? html`<div class="gk-empty"><div class="gk-spinner" style=${{ margin: '0 auto' }}></div></div>`
      : rows.map((u) => html`<div key=${u.id} style=${{ borderBottom: '1px solid var(--line)', padding: '12px 4px' }}>
          <div class="gk-row" style=${{ justifyContent: 'space-between' }}>
            <div class="gk-row" style=${{ gap: '9px' }}>
              <${Icon} name="badge" size=${18} color="var(--accent)" />
              <b>${u.username}</b>
              ${u.is_self ? html`<span class="gk-tag">${t.youBadge}</span>` : null}
            </div>
            <div class="gk-row" style=${{ gap: '4px' }}>
              <button class="gk-btn gk-btn--ghost gk-btn--sm" onClick=${() => { setResetId(resetId === u.id ? null : u.id); setResetPw(''); }}>
                <${Icon} name="pen" size=${15} /> ${t.resetPassword}</button>
              ${u.is_self ? null : html`<button class="gk-iconbtn" title=${t.delete} onClick=${() => del(u)}><${Icon} name="trash" size=${18} color="var(--red)" /></button>`}
            </div>
          </div>
          ${resetId === u.id ? html`<div class="gk-row" style=${{ gap: '8px', marginTop: '10px' }}>
            <input class="gk-input" type="password" autocomplete="new-password" placeholder=${t.newPasswordPh}
              value=${resetPw} onInput=${(e) => setResetPw(e.target.value)}
              onKeyDown=${(e) => { if (e.key === 'Enter') doReset(u); }} />
            <button class="gk-btn gk-btn--sm" disabled=${busy} onClick=${() => doReset(u)}>${t.save}</button>
          </div>` : null}
        </div>`)}

    <div class="gk-panel" style=${{ boxShadow: 'none', background: 'var(--soft)', marginTop: '18px' }}>
      <div class="gk-panel__title" style=${{ marginBottom: '12px' }}>${t.addUser}</div>
      <div class="gk-fields gk-fields--2">
        <label class="gk-field"><span class="gk-field__label">${t.fldUsername}</span>
          <input class="gk-input" value=${nu} autocomplete="off" onInput=${(e) => setNu(e.target.value)} /></label>
        <label class="gk-field"><span class="gk-field__label">${t.fldNewPassword}</span>
          <input class="gk-input" type="password" value=${np} autocomplete="new-password"
            onInput=${(e) => setNp(e.target.value)} onKeyDown=${(e) => { if (e.key === 'Enter') create(); }} /></label>
      </div>
      <div class="gk-muted" style=${{ fontSize: '12.5px', margin: '6px 0 14px' }}>${t.pwMinHint}</div>
      <div class="gk-actions"><button class="gk-btn" disabled=${busy} onClick=${create}><${Icon} name="plus" size=${16} /> ${t.createUser}</button></div>
    </div>
  </div>`;
}

// --- Content export / import ----------------------------------------------
function ContentIO({ hub }) {
  const { ctx, showToast } = hub;
  const { t } = ctx;
  const [mode, setMode] = useState('replace');
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [busy, setBusy] = useState(false);
  const fileInput = useRef(null);

  async function doImport(isPreview) {
    if (!file) return;
    setBusy(true);
    try {
      const fd = new FormData(); fd.append('file', file);
      const res = await apiPost(`/api/admin/content/import?mode=${mode}&preview=${isPreview ? 1 : 0}`, fd);
      if (isPreview) { setPreview(res); }
      else { setPreview(null); setFile(null); showToast(t.importedToast); ctx.reloadBoot(); }
    } catch (e) { showToast((e.data && e.data.detail) || t.importFailed); } finally { setBusy(false); }
  }

  return html`<div>
    <p class="gk-muted" style=${{ marginTop: 0 }}>${t.contentHint}</p>
    <div class="gk-panel" style=${{ boxShadow: 'none', background: 'var(--soft)' }}>
      <div class="gk-panel__title" style=${{ marginBottom: '10px' }}>${t.exportContent}</div>
      <button class="gk-btn gk-btn--outline" onClick=${() => download('/api/admin/content/export')}>
        <${Icon} name="download" size=${16} /> ${t.exportContent}</button>
    </div>
    <div class="gk-panel" style=${{ boxShadow: 'none', background: 'var(--soft)', marginTop: '14px' }}>
      <div class="gk-panel__title" style=${{ marginBottom: '10px' }}>${t.importContent}</div>
      <div class="gk-row" style=${{ gap: '10px', flexWrap: 'wrap', marginBottom: '12px' }}>
        <button class="gk-btn gk-btn--outline" onClick=${() => fileInput.current && fileInput.current.click()}>
          <${Icon} name="upload" size=${16} /> ${t.chooseFile}</button>
        <span class="gk-muted">${file ? file.name : '—'}</span>
        <input ref=${fileInput} type="file" accept="application/json,.json" style=${{ display: 'none' }}
          onChange=${(e) => { setFile(e.target.files[0] || null); setPreview(null); }} />
      </div>
      <div class="gk-row" style=${{ gap: '16px', marginBottom: '14px' }}>
        <span class="gk-field__label">${t.importMode}:</span>
        <label class="gk-row" style=${{ gap: '6px' }}><input type="radio" name="impmode" checked=${mode === 'replace'} onChange=${() => setMode('replace')} /> ${t.modeReplace}</label>
        <label class="gk-row" style=${{ gap: '6px' }}><input type="radio" name="impmode" checked=${mode === 'fill'} onChange=${() => setMode('fill')} /> ${t.modeFill}</label>
      </div>
      ${preview ? html`<div class="gk-alert gk-alert--warn" style=${{ marginTop: 0 }}>
        <${Icon} name="info" size=${18} />
        <span>${t.importPreview}: ${preview.info_categories} × ${t.tabInfo}, ${preview.questions} × ${t.fldQuestion}${preview.has_branding ? `, ${t.setDesign}` : ''}${preview.has_logo ? ', Logo' : ''}</span>
      </div>` : null}
      <div class="gk-row" style=${{ gap: '10px', marginTop: '14px' }}>
        <button class="gk-btn gk-btn--ghost" disabled=${!file || busy} onClick=${() => doImport(true)}>${t.importPreview}</button>
        <button class="gk-btn" disabled=${!file || busy} onClick=${() => doImport(false)}>${t.importApply}</button>
      </div>
    </div>
  </div>`;
}
