import { useState, useEffect, useRef } from 'preact/hooks';
import { html, Icon, Modal, StepDots, HeaderMeta } from '../ui.mjs';
import { pick } from '../i18n.mjs';
import { blocksOf } from '../markdown.mjs';
import { backdropFor } from '../theme.mjs';
import { apiPost } from '../api.mjs';
import { enableWakeLock, disableWakeLock } from '../wakeLock.mjs';
import { QrScanner, cameraSupported } from '../scan.mjs';

function fmtDur(min) {
  const m = Math.max(0, Math.round(min));
  const h = Math.floor(m / 60);
  const mm = m % 60;
  return h > 0 ? `${h} h ${mm} min` : `${mm} min`;
}

// Shared renderer for an info category (used by detail screen + consent modals)
function InfoContent({ cat, lang }) {
  if (!cat) return null;
  if (cat.type === 'dir') {
    return html`<div class="gk-dir">
      ${(cat.entries || []).map((e, i) => html`<div class="gk-dir__row" key=${i}>
        <span class="gk-dir__label">${pick(e.label, lang)}</span>
        <span class="gk-dir__value">${e.value}</span>
      </div>`)}
    </div>`;
  }
  const blocks = blocksOf(pick(cat.body, lang));
  return html`<div class="gk-article">
    ${blocks.map((b, i) => b.head
      ? html`<h4 key=${i}>${b.text}</h4>`
      : html`<p key=${i}>${b.text}</p>`)}
  </div>`;
}

export function Kiosk({ ctx, initialPin }) {
  const { t, lang, setLang, boot, showToast, setMode } = ctx;
  const s = boot.settings || {};
  const questions = (boot.health && boot.health.questions) || [];
  const info = boot.info || [];
  const catByKey = (k) => info.find((c) => c.key === k);

  const [screen, setScreen] = useState(initialPin ? 'cocode' : 'welcome');
  const [form, setForm] = useState({ first: '', last: '', company: '', host: '', plate: '' });
  const [answers, setAnswers] = useState({});
  const [consent, setConsent] = useState({ ds: false, hy: false, sf: false });
  const [tried, setTried] = useState(false);
  const [hasSig, setHasSig] = useState(false);
  const [pin, setPin] = useState('');
  const [qr, setQr] = useState('');
  const [greet, setGreet] = useState('');
  const [autoSec, setAutoSec] = useState(0);
  const [coCode, setCoCode] = useState(initialPin || '');
  const [coError, setCoError] = useState(false);
  const [coScan, setCoScan] = useState(false);   // checkout: camera opened on demand
  const [coMinutes, setCoMinutes] = useState(0);
  const [busy, setBusy] = useState(false);
  const [infoModal, setInfoModal] = useState(null);
  const [selectedInfo, setSelectedInfo] = useState(null);
  // returning-visitor pass ("Besucherausweis")
  const [returning, setReturning] = useState(false);
  const [profileToken, setProfileToken] = useState('');
  const [createPass, setCreatePass] = useState(false);
  const [retCode, setRetCode] = useState('');
  const [retErr, setRetErr] = useState(false);
  const [passQr, setPassQr] = useState('');
  const [passToken, setPassToken] = useState('');

  const canvasRef = useRef(null);
  const drawing = useRef(false);
  const pen = useRef(null);
  const autoTimer = useRef(null);

  // Keep the device awake while the kiosk is on screen.
  useEffect(() => { enableWakeLock(); return () => disableWakeLock(); }, []);
  useEffect(() => () => clearInterval(autoTimer.current), []);

  const setField = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  function resetForm() {
    setForm({ first: '', last: '', company: '', host: '', plate: '' });
    setAnswers({});
    setConsent({ ds: false, hy: false, sf: false });
    setTried(false); setHasSig(false); setPin(''); setQr(''); setGreet('');
    setCoCode(''); setCoError(false); setCoScan(false); setCoMinutes(0);
    setReturning(false); setProfileToken(''); setCreatePass(false);
    setRetCode(''); setRetErr(false); setPassQr(''); setPassToken('');
  }
  function goWelcome() { clearInterval(autoTimer.current); resetForm(); setScreen('welcome'); }
  function startCheckIn() { resetForm(); setScreen('data'); }
  function startCheckOut() { resetForm(); setScreen('cocode'); }
  function startReturn() { resetForm(); setScreen('return'); }

  async function doLookup(code) {
    const c = (code || '').trim();
    if (!c) return;
    setBusy(true);
    try {
      const r = await apiPost('/api/profile/lookup', { code: c });
      setForm({
        first: r.first_name || '', last: r.last_name || '',
        company: r.company || '', host: r.host || '', plate: r.plate || '',
      });
      setReturning(true); setProfileToken(r.token || ''); setRetErr(false);
      setTried(false); setScreen('data');
    } catch (_) {
      setRetErr(true);
    } finally { setBusy(false); }
  }

  function startAuto(secsOverride) {
    clearInterval(autoTimer.current);
    const base = secsOverride != null ? secsOverride : (parseInt(s.auto_return_seconds, 10) || 20);
    const secs = Math.max(5, Math.min(90, base));
    setAutoSec(secs);
    autoTimer.current = setInterval(() => {
      setAutoSec((n) => {
        if (n <= 1) { clearInterval(autoTimer.current); setTimeout(goWelcome, 0); return 0; }
        return n - 1;
      });
    }, 1000);
  }

  // --- validation -----------------------------------------------------------
  const dataValid = () => form.first.trim() && form.last.trim() && form.company.trim() && form.host.trim();
  function nextFromData() {
    setTried(true);
    if (dataValid()) { setScreen('health'); setTried(false); }
  }
  const setAns = (id, val) => setAnswers((a) => ({ ...a, [id]: val }));
  const correctOf = (q) => (q.correct_answer ? 'yes' : 'no');
  const allAnswered = () => questions.length > 0 && questions.every((q) => answers[q.id]);
  const anyWrong = () => questions.some((q) => answers[q.id] && answers[q.id] !== correctOf(q));
  function nextFromHealth() {
    setTried(true);
    if (allAnswered() && !anyWrong()) { setScreen('consent'); setTried(false); }
  }
  const toggleConsent = (k) => setConsent((c) => ({ ...c, [k]: !c[k] }));
  function nextFromConsent() {
    setTried(true);
    if (consent.ds && consent.hy && consent.sf) { setScreen('sign'); setTried(false); }
  }

  // --- signature ------------------------------------------------------------
  function initCanvas() {
    const c = canvasRef.current;
    if (!c) return;
    const r = c.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    c.width = r.width * dpr; c.height = r.height * dpr;
    const cx = c.getContext('2d');
    cx.scale(dpr, dpr);
    cx.lineWidth = 2.6; cx.lineJoin = 'round'; cx.lineCap = 'round'; cx.strokeStyle = '#14233f';
    pen.current = cx;
  }
  useEffect(() => { if (screen === 'sign') requestAnimationFrame(initCanvas); }, [screen]);
  const ptOf = (e) => { const r = canvasRef.current.getBoundingClientRect(); return { x: e.clientX - r.left, y: e.clientY - r.top }; };
  function sigDown(e) {
    if (!pen.current) initCanvas();
    drawing.current = true;
    const p = ptOf(e); pen.current.beginPath(); pen.current.moveTo(p.x, p.y);
    if (!hasSig) setHasSig(true);
    e.preventDefault();
  }
  function sigMove(e) {
    if (!drawing.current || !pen.current) return;
    const p = ptOf(e); pen.current.lineTo(p.x, p.y); pen.current.stroke();
    e.preventDefault();
  }
  function sigUp() { drawing.current = false; }
  function clearSig() {
    const c = canvasRef.current;
    if (c && pen.current) { const r = c.getBoundingClientRect(); pen.current.clearRect(0, 0, r.width, r.height); }
    setHasSig(false);
  }

  // --- submit ---------------------------------------------------------------
  async function finishCheckIn() {
    if (!hasSig) { setTried(true); return; }
    setBusy(true);
    try {
      const payload = {};
      questions.forEach((q) => { payload[q.id] = answers[q.id] === 'yes'; });
      const sig = canvasRef.current ? canvasRef.current.toDataURL('image/png') : '';
      const res = await apiPost('/api/checkin', {
        first_name: form.first.trim(), last_name: form.last.trim(),
        company: form.company.trim(), host: form.host.trim(), plate: form.plate.trim(),
        answers: payload, consent, signature: sig,
        save_profile: createPass && !returning,
        profile_token: returning ? profileToken : undefined,
      });
      setPin(res.pin); setQr(res.qr_svg || ''); setGreet(form.first.trim());
      setPassQr(res.pass_qr || ''); setPassToken(res.pass_token || '');
      // More time to scan when a visitor pass QR is shown (60 s), less without (30 s).
      setScreen('done'); startAuto(res.pass_qr ? 60 : 30);
    } catch (e) {
      if (e.status === 422) { setScreen('health'); setTried(true); showToast(t.healthBlockMsg); }
      else { showToast(t.signRequired); }
    } finally { setBusy(false); }
  }

  async function submitCheckout(codeArg) {
    // codeArg may come from the QR scanner; onClick passes an event, so only
    // trust it when it's actually a string.
    const code = (typeof codeArg === 'string' ? codeArg : coCode).trim();
    if (!code) return;
    setBusy(true);
    try {
      const res = await apiPost('/api/checkout', { code });
      setCoMinutes(res.minutes || 0); setCoError(false); setScreen('codone'); startAuto();
    } catch (_) { setCoError(true); } finally { setBusy(false); }
  }

  // --- brand / header -------------------------------------------------------
  const dark = s.kiosk_backdrop === 'anthrazit';
  const rootStyle = { background: backdropFor(s.kiosk_backdrop) };
  const companyName = s.company_name || 'GateKeeper';
  const monogram = companyName.trim().slice(0, 2).toUpperCase();

  const Brand = html`<div class="gk-brand">
    ${s.logo_url
      ? html`<img class="gk-brand__logo" src=${s.logo_url} alt="" />`
      : html`<div class="gk-brand__logo gk-brand__logo--mono">${monogram}</div>`}
    <div>
      <div class="gk-brand__name">${companyName}</div>
      <div class="gk-brand__sub">${t.brandSub}</div>
    </div>
  </div>`;

  const Header = html`<div class="gk-kiosk__top">
    ${Brand}
    <div class="gk-headright">
      <${HeaderMeta} lang=${lang} setLang=${setLang} />
      <button class="gk-iconbtn gk-adminbtn" title=${t.adminBadge} onClick=${() => setMode('admin')} aria-label="Admin">
        <${Icon} name="badge" size=${20} color=${dark ? '#9fb0cf' : '#8a96ad'} />
      </button>
    </div>
  </div>`;

  // --- screen renderers -----------------------------------------------------
  function renderWelcome() {
    return html`<div style=${{ width: '100%', maxWidth: '640px' }}>
      <div class="gk-kicker" style=${{ textAlign: 'center' }}>${t.welcomeKicker}</div>
      <h1 style=${{ textAlign: 'center', fontSize: '34px', margin: '8px 0 6px', color: dark ? '#fff' : 'var(--navy)' }}>${t.welcomeHi}</h1>
      <p style=${{ textAlign: 'center', color: dark ? '#a9b6d0' : 'var(--muted)', margin: '0 0 26px' }}>${t.welcomeSub}</p>
      <div class="gk-welcome-actions">
        <button class="gk-tile gk-tile--primary" onClick=${startCheckIn}>
          <div class="gk-tile__icon"><${Icon} name="exit" size=${26} color="#fff" /></div>
          <div><div class="gk-tile__title">${t.checkIn}</div><div class="gk-tile__sub">${t.checkInSub}</div></div>
        </button>
        <button class="gk-tile" onClick=${startCheckOut}>
          <div class="gk-tile__icon"><${Icon} name="logout" size=${26} color="var(--accent)" /></div>
          <div><div class="gk-tile__title">${t.checkOut}</div><div class="gk-tile__sub">${t.checkOutSub}</div></div>
        </button>
      </div>
      <div class="gk-welcome-return">
        <button class="gk-return-link" onClick=${startReturn}>
          <${Icon} name="badge" size=${17} color="var(--accent)" /><span>${t.returningLink}</span>
        </button>
      </div>
      <div class="gk-welcome-infowrap">
        <button class="gk-pillbtn" onClick=${() => setScreen('info')}>
          <${Icon} name="info" size=${18} color="var(--accent)" />
          <span>${t.welcomeInfoBtn}</span>
          <${Icon} name="chev" size=${16} color="var(--faint)" />
        </button>
      </div>
    </div>`;
  }

  function renderData() {
    const err = tried && !dataValid();
    return html`<div class="gk-card">
      <${StepDots} index=${0} />
      <div class="gk-card__head" style=${{ marginTop: '18px' }}>
        <h2 class="gk-card__title">${returning ? t.welcomeBack : t.dataTitle}</h2>
        <div class="gk-card__sub">${t.dataSub}</div>
      </div>
      <div class="gk-fields">
        <div class="gk-fields gk-fields--2">
          ${textField('first', t.fFirstName, t.phFirstName, true)}
          ${textField('last', t.fLastName, t.phLastName, true)}
        </div>
        ${textField('company', t.fCompany, t.phCompany, true)}
        ${textField('host', t.fHost, t.phHost, true)}
        ${s.collect_plate ? textField('plate', t.fPlate, t.phPlate, false) : null}
      </div>
      ${err ? html`<div class="gk-alert gk-alert--error"><${Icon} name="alert" size=${18} /> ${t.req}</div>` : null}
      <div class="gk-actions gk-actions--split">
        <button class="gk-btn gk-btn--ghost" onClick=${goWelcome}>${t.cancel}</button>
        <button class="gk-btn" onClick=${nextFromData}>${t.next}</button>
      </div>
    </div>`;
  }

  function textField(key, label, ph, required) {
    const err = tried && required && !form[key].trim();
    return html`<label class=${'gk-field' + (err ? ' has-error' : '')}>
      <span class="gk-field__label">${label}${required ? html`<b> *</b>` : html` <em>${t.optional}</em>`}</span>
      <input class="gk-input" value=${form[key]} placeholder=${ph}
        onInput=${(e) => setField(key, e.target.value)} />
    </label>`;
  }

  function renderHealth() {
    const incomplete = tried && !allAnswered() && !anyWrong();
    const blocked = tried && anyWrong();
    return html`<div class="gk-card">
      <${StepDots} index=${1} />
      <div class="gk-card__head" style=${{ marginTop: '18px' }}>
        <h2 class="gk-card__title">${t.healthTitle}</h2>
        <div class="gk-card__sub">${t.healthSub}</div>
      </div>
      ${pick(boot.health.intro, lang) ? html`<p class="gk-health-intro">${pick(boot.health.intro, lang)}</p>` : null}
      <div class="gk-qlist">
        ${questions.map((q) => {
          const a = answers[q.id];
          const correct = correctOf(q);
          const yesBad = a === 'yes' && correct !== 'yes';
          const noBad = a === 'no' && correct !== 'no';
          return html`<div class="gk-q" key=${q.id}>
            <div class="gk-q__text">${pick(q.text, lang)}</div>
            <div class="gk-yn">
              <button class=${a === 'yes' ? (yesBad ? 'bad' : 'on-yes') : ''} onClick=${() => setAns(q.id, 'yes')}>${t.yes}</button>
              <button class=${a === 'no' ? (noBad ? 'bad' : 'on-no') : ''} onClick=${() => setAns(q.id, 'no')}>${t.no}</button>
            </div>
          </div>`;
        })}
      </div>
      ${blocked ? html`<div class="gk-alert gk-alert--error"><${Icon} name="alert" size=${18} /> ${t.healthBlockMsg}</div>` : null}
      ${incomplete ? html`<div class="gk-alert gk-alert--warn"><${Icon} name="alert" size=${18} /> ${t.healthIncompleteMsg}</div>` : null}
      <div class="gk-actions gk-actions--split">
        <button class="gk-btn gk-btn--ghost" onClick=${() => { setScreen('data'); setTried(false); }}>${t.back}</button>
        <button class="gk-btn" onClick=${nextFromHealth}>${t.next}</button>
      </div>
    </div>`;
  }

  function consentRow(k, text, linkKey) {
    const cat = catByKey(linkKey);
    return html`<div class=${'gk-check' + (consent[k] ? ' is-on' : '')} onClick=${() => toggleConsent(k)}>
      <div class="gk-check__box">${consent[k] ? html`<${Icon} name="check" size=${16} color="#fff" width=${2.4} />` : null}</div>
      <div class="gk-check__text">
        ${text}${' '}
        ${cat ? html`<a href="#" onClick=${(e) => { e.preventDefault(); e.stopPropagation(); setInfoModal(linkKey); }}>${pick(cat.title, lang)} (${t.linkShow})</a>` : null}
      </div>
    </div>`;
  }

  function renderConsent() {
    const err = tried && !(consent.ds && consent.hy && consent.sf);
    return html`<div class="gk-card">
      <${StepDots} index=${2} />
      <div class="gk-card__head" style=${{ marginTop: '18px' }}>
        <h2 class="gk-card__title">${t.consentTitle}</h2>
        <div class="gk-card__sub">${t.consentSub}</div>
      </div>
      <div class="gk-consent">
        ${consentRow('ds', t.cDsgvo, 'datenschutz')}
        ${consentRow('hy', t.cHygiene, 'hygiene')}
        ${consentRow('sf', t.cSafety, 'sicherheit')}
      </div>
      ${!returning ? html`<div class=${'gk-check gk-check--opt' + (createPass ? ' is-on' : '')}
        onClick=${() => setCreatePass((v) => !v)} style=${{ marginTop: '12px' }}>
        <div class="gk-check__box">${createPass ? html`<${Icon} name="check" size=${16} color="#fff" width=${2.4} />` : null}</div>
        <div class="gk-check__text"><b>${t.createPassLabel}</b><div class="gk-check__hint">${t.createPassHint}</div></div>
      </div>` : null}
      ${err ? html`<div class="gk-alert gk-alert--error"><${Icon} name="alert" size=${18} /> ${t.consentIncomplete}</div>` : null}
      <div class="gk-actions gk-actions--split">
        <button class="gk-btn gk-btn--ghost" onClick=${() => { setScreen('health'); setTried(false); }}>${t.back}</button>
        <button class="gk-btn" onClick=${nextFromConsent}>${t.next}</button>
      </div>
    </div>`;
  }

  function renderSign() {
    const err = tried && !hasSig;
    return html`<div class="gk-card">
      <${StepDots} index=${3} />
      <div class="gk-card__head" style=${{ marginTop: '18px' }}>
        <h2 class="gk-card__title">${t.signTitle}</h2>
        <div class="gk-card__sub">${t.signSub}</div>
      </div>
      <div class=${'gk-sign-wrap' + (err ? ' has-error' : '')}>
        <canvas ref=${canvasRef} class="gk-sign"
          onPointerDown=${sigDown} onPointerMove=${sigMove} onPointerUp=${sigUp} onPointerLeave=${sigUp}></canvas>
        ${!hasSig ? html`<div class="gk-sign-hint">${t.signHint}</div>` : null}
      </div>
      <div class="gk-row" style=${{ justifyContent: 'flex-end', marginTop: '10px' }}>
        <button class="gk-btn gk-btn--ghost" onClick=${clearSig}><${Icon} name="trash" size=${16} /> ${t.clear}</button>
      </div>
      ${err ? html`<div class="gk-alert gk-alert--error"><${Icon} name="alert" size=${18} /> ${t.signRequired}</div>` : null}
      <div class="gk-actions gk-actions--split">
        <button class="gk-btn gk-btn--ghost" onClick=${() => { setScreen('consent'); setTried(false); }}>${t.back}</button>
        <button class="gk-btn" disabled=${busy} onClick=${finishCheckIn}>${t.finishCheckin}</button>
      </div>
    </div>`;
  }

  function renderDone() {
    return html`<div class="gk-card gk-done">
      <div class="gk-done__badge"><${Icon} name="check" size=${36} color="var(--green)" width=${2.6} /></div>
      <h2 class="gk-card__title">${t.doneTitle}</h2>
      ${greet ? html`<p class="gk-card__sub">${t.welcomeHi}, ${greet}!</p>` : null}
      <div style=${{ marginTop: '18px', fontWeight: 600, color: 'var(--muted-2)' }}>${t.yourCode}</div>
      <div class="gk-pin">${String(pin).split('').map((d, i) => html`<span key=${i}>${d}</span>`)}</div>
      <p class="gk-card__sub" style=${{ marginTop: '14px' }}>${t.codeHint}</p>
      ${passQr ? html`<div class="gk-passcard">
        <div class="gk-passcard__head"><${Icon} name="badge" size=${18} color="var(--accent)" /> ${t.passTitle}</div>
        <div class="gk-passcard__qr" dangerouslySetInnerHTML=${{ __html: passQr }}></div>
        ${passToken ? html`<div class="gk-passcard__code">GKP:${passToken}</div>` : null}
        <div class="gk-passcard__hint">${t.passHint}</div>
      </div>` : null}
      <div class="gk-actions" style=${{ justifyContent: 'center' }}>
        <button class="gk-btn gk-btn--lg" onClick=${goWelcome}>${t.finishBtn}</button>
      </div>
      <div class="gk-auto">${autoReturnText()}</div>
    </div>`;
  }

  function autoReturnText() {
    const m = { de: `Zurück zum Start in ${autoSec}s …`, en: `Returning to start in ${autoSec}s …`,
      fr: `Retour à l’accueil dans ${autoSec}s …`, es: `Volviendo al inicio en ${autoSec}s …` };
    return m[lang] || m.de;
  }

  function renderCoCode() {
    const cam = cameraSupported();
    return html`<div class="gk-card">
      <div class="gk-card__head">
        <h2 class="gk-card__title">${t.checkoutTitle}</h2>
        <div class="gk-card__sub">${t.checkoutSub}</div>
      </div>
      <input class="gk-input gk-code-input" autocomplete="off" spellcheck="false"
        value=${coCode} placeholder=${t.codePlaceholder}
        onInput=${(e) => { setCoCode(e.target.value); setCoError(false); }}
        onKeyDown=${(e) => { if (e.key === 'Enter') submitCheckout(); }} />
      ${coError ? html`<div class="gk-alert gk-alert--error"><${Icon} name="alert" size=${18} /> ${t.invalidCode}</div>` : null}
      ${cam ? (coScan
        ? html`<div style=${{ marginTop: '16px' }}>
            <${QrScanner} onResult=${(text) => { setCoScan(false); setCoCode(text); setCoError(false); submitCheckout(text); }} />
            <div style=${{ textAlign: 'center', marginTop: '10px' }}>
              <button class="gk-btn gk-btn--ghost gk-btn--sm" onClick=${() => setCoScan(false)}><${Icon} name="x" size=${15} /> ${t.scanClose}</button>
            </div>
          </div>`
        : html`<div>
            <div class="gk-or">${t.orLabel}</div>
            <button class="gk-btn gk-btn--outline" style=${{ width: '100%', justifyContent: 'center' }}
              onClick=${() => { setCoScan(true); setCoError(false); }}>
              <${Icon} name="badge" size=${18} /> ${t.scanPassBtn}</button>
          </div>`) : null}
      <div class="gk-actions gk-actions--split" style=${{ marginTop: '20px' }}>
        <button class="gk-btn gk-btn--ghost" onClick=${goWelcome}>${t.cancel}</button>
        <button class="gk-btn" disabled=${busy} onClick=${() => submitCheckout()}>${t.checkoutBtn}</button>
      </div>
    </div>`;
  }

  function renderCoDone() {
    return html`<div class="gk-card gk-done">
      <div class="gk-done__badge"><${Icon} name="check" size=${36} color="var(--green)" width=${2.6} /></div>
      <h2 class="gk-card__title">${t.checkoutDoneTitle}</h2>
      <p class="gk-card__sub">${t.checkoutDoneSub}</p>
      <div style=${{ marginTop: '16px', color: 'var(--muted-2)' }}>${t.visitDuration}</div>
      <div style=${{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '30px', color: 'var(--navy)' }}>${fmtDur(coMinutes)}</div>
      <div class="gk-actions" style=${{ justifyContent: 'center' }}>
        <button class="gk-btn gk-btn--lg" onClick=${goWelcome}>${t.finishBtn}</button>
      </div>
      <div class="gk-auto">${autoReturnText()}</div>
    </div>`;
  }

  function renderInfoHub() {
    return html`<div class="gk-card gk-card--wide">
      <div class="gk-row" style=${{ marginBottom: '18px' }}>
        <button class="gk-btn gk-btn--ghost" onClick=${goWelcome}><${Icon} name="back" size=${18} /> ${t.back}</button>
      </div>
      <div class="gk-card__head"><h2 class="gk-card__title">${t.infoTitle}</h2><div class="gk-card__sub">${t.infoHubSub}</div></div>
      <div class="gk-info-grid">
        ${info.map((c) => html`<button class="gk-info-tile" key=${c.key} onClick=${() => { setSelectedInfo(c.key); setScreen('infodetail'); }}>
          <div class="gk-info-tile__icon" style=${{ background: (c.accent || '#2f6fed') + '1f', color: c.accent || '#2f6fed' }}>
            <${Icon} name=${c.icon} size=${24} color=${c.accent || '#2f6fed'} />
          </div>
          <div class="gk-info-tile__title">${pick(c.title, lang)}</div>
        </button>`)}
      </div>
    </div>`;
  }

  function renderInfoDetail() {
    const cat = catByKey(selectedInfo);
    return html`<div class="gk-card gk-card--wide">
      <div class="gk-row" style=${{ marginBottom: '18px' }}>
        <button class="gk-btn gk-btn--ghost" onClick=${() => setScreen('info')}><${Icon} name="back" size=${18} /> ${t.infoBack}</button>
      </div>
      <div class="gk-row" style=${{ gap: '12px', marginBottom: '16px' }}>
        ${cat ? html`<div class="gk-info-tile__icon" style=${{ background: (cat.accent || '#2f6fed') + '1f' }}>
          <${Icon} name=${cat.icon} size=${24} color=${cat.accent || '#2f6fed'} /></div>` : null}
        <h2 class="gk-card__title">${cat ? pick(cat.title, lang) : ''}</h2>
      </div>
      <${InfoContent} cat=${cat} lang=${lang} />
    </div>`;
  }

  function renderReturn() {
    const cam = cameraSupported();
    return html`<div class="gk-card">
      <div class="gk-row" style=${{ marginBottom: '14px' }}>
        <button class="gk-btn gk-btn--ghost" onClick=${goWelcome}><${Icon} name="back" size=${18} /> ${t.back}</button>
      </div>
      <div class="gk-card__head">
        <h2 class="gk-card__title">${t.returnTitle}</h2>
        <div class="gk-card__sub">${t.returnSub}</div>
      </div>
      ${cam
        ? html`<${QrScanner} onResult=${(text) => { setRetCode(text); doLookup(text); }} />`
        : html`<div class="gk-alert gk-alert--warn"><${Icon} name="info" size=${18} /> ${t.cameraNeedsHttps}</div>`}
      <label class="gk-field" style=${{ marginTop: '16px' }}>
        <span class="gk-field__label">${t.passCodeLabel}</span>
        <input class="gk-input" autofocus autocomplete="off" spellcheck="false"
          value=${retCode} placeholder=${t.passCodePh}
          onInput=${(e) => { setRetCode(e.target.value); setRetErr(false); }}
          onKeyDown=${(e) => { if (e.key === 'Enter') doLookup(retCode); }} />
      </label>
      ${retErr ? html`<div class="gk-alert gk-alert--error"><${Icon} name="alert" size=${18} /> ${t.lookupFail}</div>` : null}
      <div class="gk-actions gk-actions--split">
        <button class="gk-btn gk-btn--ghost" onClick=${goWelcome}>${t.cancel}</button>
        <button class="gk-btn" disabled=${busy} onClick=${() => doLookup(retCode)}>${t.next}</button>
      </div>
    </div>`;
  }

  const SCREENS = {
    welcome: renderWelcome, data: renderData, health: renderHealth, consent: renderConsent,
    sign: renderSign, done: renderDone, cocode: renderCoCode, codone: renderCoDone,
    info: renderInfoHub, infodetail: renderInfoDetail, return: renderReturn,
  };
  const body = (SCREENS[screen] || renderWelcome)();

  const modalCat = infoModal ? catByKey(infoModal) : null;

  return html`<div class=${'gk-kiosk' + (dark ? ' gk-kiosk--dark' : '')} style=${rootStyle}>
    ${Header}
    <div class="gk-screen" key=${screen}>${body}</div>
    <${Modal} open=${!!modalCat} onClose=${() => setInfoModal(null)}
      title=${modalCat ? pick(modalCat.title, lang) : ''} closeLabel=${t.closeBtn}
      icon=${modalCat ? html`<${Icon} name=${modalCat.icon} size=${22} color=${modalCat.accent} />` : null}>
      <${InfoContent} cat=${modalCat} lang=${lang} />
    <//>
  </div>`;
}
