// Camera QR scanning for the kiosk (progressive enhancement).
//
// Camera access requires a secure context (HTTPS or localhost); on a plain
// http:// LAN address the browser blocks getUserMedia. When unavailable the
// return screen falls back to the always-present code input (a keyboard-wedge
// scanner types into it, or staff enter the code by hand).
//
// The QR decoder (jsQR) is a vendored UMD bundle loaded lazily on first use;
// it assigns window.jsQR as a side effect (no CDN at runtime).

import { useRef, useEffect, useState } from 'preact/hooks';
import { html } from './ui.mjs';

export function cameraSupported() {
  return !!(
    window.isSecureContext &&
    navigator.mediaDevices &&
    typeof navigator.mediaDevices.getUserMedia === 'function'
  );
}

let _jsqrPromise = null;
async function loadJsQR() {
  if (window.jsQR) return window.jsQR;
  if (!_jsqrPromise) _jsqrPromise = import('../vendor/jsqr.js').catch(() => null);
  await _jsqrPromise;
  return window.jsQR || null;
}

export function QrScanner({ onResult }) {
  const videoRef = useRef(null);
  const [err, setErr] = useState('');

  useEffect(() => {
    let stream = null;
    let raf = 0;
    let stopped = false;
    let last = 0;
    const canvas = document.createElement('canvas');

    function cleanup() {
      stopped = true;
      if (raf) cancelAnimationFrame(raf);
      if (stream) stream.getTracks().forEach((t) => t.stop());
      stream = null;
    }

    function tick(ts) {
      if (stopped) return;
      raf = requestAnimationFrame(tick);
      if (ts - last < 140) return; // throttle decoding
      last = ts;
      const v = videoRef.current;
      const jsQR = window.jsQR;
      if (!v || !jsQR || v.readyState < 2) return;
      const w = v.videoWidth, h = v.videoHeight;
      if (!w || !h) return;
      canvas.width = w; canvas.height = h;
      const cx = canvas.getContext('2d', { willReadFrequently: true });
      cx.drawImage(v, 0, 0, w, h);
      let img;
      try { img = cx.getImageData(0, 0, w, h); } catch (_) { return; }
      const res = jsQR(img.data, w, h, { inversionAttempts: 'dontInvert' });
      if (res && res.data) {
        cleanup();
        onResult(res.data);
      }
    }

    async function start() {
      const jsQR = await loadJsQR();
      if (stopped) return;
      if (!jsQR) { setErr('lib'); return; }
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: 'environment' } },
        });
      } catch (_) {
        setErr('cam');
        return;
      }
      if (stopped) { cleanup(); return; }
      const v = videoRef.current;
      if (!v) { cleanup(); return; }
      v.srcObject = stream;
      v.setAttribute('playsinline', '');
      try { await v.play(); } catch (_) { /* autoplay quirks */ }
      raf = requestAnimationFrame(tick);
    }

    start();
    return cleanup;
  }, []);

  // On any failure (permission denied, no decoder) fall back silently to the
  // code input the parent always renders below.
  if (err) return null;

  return html`<div class="gk-scan">
    <video ref=${videoRef} class="gk-scan__video" muted autoplay playsinline></video>
    <div class="gk-scan__frame"></div>
  </div>`;
}
