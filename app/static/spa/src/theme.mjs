// Accent palettes (mirror of backend seed_content.ACCENTS) and kiosk backdrops.
export const PALETTES = {
  blau:       ['#2f6fed', '#1c4fd1', '#eef3fc'],
  gruen:      ['#1f9d6b', '#157a52', '#e9f7f1'],
  violett:    ['#7c5cd6', '#5f3fc0', '#f1edfb'],
  anthrazit:  ['#2b3d5e', '#14233f', '#eef1f6'],
  bernstein:  ['#e0701e', '#c25c10', '#fdf1e7'],
};

export const ACCENT_KEYS = Object.keys(PALETTES);

// A custom accent is a plain #rrggbb hex (stored instead of a palette key).
export function isHexAccent(name) {
  return typeof name === 'string' && /^#?[0-9a-fA-F]{6}$/.test(name.trim());
}

function _rgb(hex) {
  const n = parseInt(hex.trim().replace('#', ''), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
function _hex(rgb) {
  return '#' + rgb.map((v) => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, '0')).join('');
}
// Mix `rgb` toward `target` by factor t (0..1).
function _mix(rgb, target, t) {
  return rgb.map((v, i) => v + (target[i] - v) * t);
}

export function applyAccent(name) {
  let accent, dark, soft;
  if (PALETTES[name]) {
    [accent, dark, soft] = PALETTES[name];
  } else if (isHexAccent(name)) {
    const rgb = _rgb(name);
    accent = _hex(rgb);
    dark = _hex(_mix(rgb, [0, 0, 0], 0.22));        // darker for hover/pressed states
    soft = _hex(_mix(rgb, [255, 255, 255], 0.9));   // very light tint for backgrounds
  } else {
    [accent, dark, soft] = PALETTES.blau;
  }
  const r = document.documentElement.style;
  r.setProperty('--accent', accent);
  r.setProperty('--accent-dark', dark);
  r.setProperty('--accent-soft', soft);
}

export const BACKDROPS = {
  hell:      'radial-gradient(120% 80% at 50% 0%, #eef2f9, #dde3ef)',
  anthrazit: 'radial-gradient(120% 80% at 50% 0%, #2a3550, #161d2e)',
  schlicht:  '#e9edf4',
};

export function backdropFor(name) {
  return BACKDROPS[name] || BACKDROPS.hell;
}
