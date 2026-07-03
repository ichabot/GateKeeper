// Accent palettes (mirror of backend seed_content.ACCENTS) and kiosk backdrops.
export const PALETTES = {
  blau:       ['#2f6fed', '#1c4fd1', '#eef3fc'],
  gruen:      ['#1f9d6b', '#157a52', '#e9f7f1'],
  violett:    ['#7c5cd6', '#5f3fc0', '#f1edfb'],
  anthrazit:  ['#2b3d5e', '#14233f', '#eef1f6'],
  bernstein:  ['#e0701e', '#c25c10', '#fdf1e7'],
};

export const ACCENT_KEYS = Object.keys(PALETTES);

export function applyAccent(name) {
  const p = PALETTES[name] || PALETTES.blau;
  const r = document.documentElement.style;
  r.setProperty('--accent', p[0]);
  r.setProperty('--accent-dark', p[1]);
  r.setProperty('--accent-soft', p[2]);
}

export const BACKDROPS = {
  hell:      'radial-gradient(120% 80% at 50% 0%, #eef2f9, #dde3ef)',
  anthrazit: 'radial-gradient(120% 80% at 50% 0%, #2a3550, #161d2e)',
  schlicht:  '#e9edf4',
};

export function backdropFor(name) {
  return BACKDROPS[name] || BACKDROPS.hell;
}
