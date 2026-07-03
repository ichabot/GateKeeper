// Keep the iPad (or any device) awake while the kiosk is active.
//
// Primary: Screen Wake Lock API (iPadOS 16.4+, requires HTTPS). It is
// re-acquired automatically after the tab is hidden/shown or the lock is
// released by the system. On unsupported/older devices, pair the app with
// iOS Guided Access (documented in the README) — the browser cannot force
// the screen awake there.

let _sentinel = null;
let _enabled = false;

async function _acquire() {
  if (!_enabled) return;
  if (!('wakeLock' in navigator)) return;
  try {
    _sentinel = await navigator.wakeLock.request('screen');
    _sentinel.addEventListener('release', () => { _sentinel = null; });
  } catch (_) {
    // user gesture may be required, or not permitted — retry on next visibility.
    _sentinel = null;
  }
}

function _onVisibility() {
  if (document.visibilityState === 'visible' && _enabled && !_sentinel) {
    _acquire();
  }
}

// Some browsers only grant the lock after a user gesture — re-acquire on the
// first interaction if the initial (load-time) request was rejected.
function _onInteract() {
  if (_enabled && !_sentinel) _acquire();
}

export function enableWakeLock() {
  if (_enabled) return;
  _enabled = true;
  document.addEventListener('visibilitychange', _onVisibility);
  document.addEventListener('pointerdown', _onInteract, { passive: true });
  _acquire();
}

export function disableWakeLock() {
  _enabled = false;
  document.removeEventListener('visibilitychange', _onVisibility);
  document.removeEventListener('pointerdown', _onInteract);
  if (_sentinel) {
    _sentinel.release().catch(() => {});
    _sentinel = null;
  }
}

export function wakeLockSupported() {
  return 'wakeLock' in navigator;
}
