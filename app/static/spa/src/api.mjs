// Fetch helpers. Admin mutations send the CSRF token in the X-CSRFToken header;
// public kiosk endpoints are CSRF-exempt on the server but the header is
// harmless there too.

let _csrf = null;

async function getCsrf() {
  if (_csrf) return _csrf;
  const r = await fetch('/api/csrf', { credentials: 'same-origin' });
  const j = await r.json();
  _csrf = j.csrf_token;
  return _csrf;
}

async function handle(r) {
  let data = null;
  try { data = await r.json(); } catch (_) { /* non-JSON */ }
  if (!r.ok) {
    const err = new Error((data && data.error) || ('HTTP ' + r.status));
    err.status = r.status;
    err.data = data || {};
    throw err;
  }
  return data;
}

export async function apiGet(path) {
  const r = await fetch(path, { credentials: 'same-origin' });
  return handle(r);
}

export async function apiSend(path, method, body) {
  const send = async () => {
    const token = await getCsrf();
    const opts = { method, credentials: 'same-origin', headers: { 'X-CSRFToken': token } };
    if (body !== undefined && !(body instanceof FormData)) {
      opts.headers['Content-Type'] = 'application/json';
      opts.body = JSON.stringify(body);
    } else if (body instanceof FormData) {
      opts.body = body;
    }
    return fetch(path, opts);
  };
  let r = await send();
  // If the CSRF token went stale, refresh once and retry.
  if (r.status === 400) {
    _csrf = null;
    r = await send();
  }
  return handle(r);
}

export const apiPost = (p, b) => apiSend(p, 'POST', b);
export const apiPut = (p, b) => apiSend(p, 'PUT', b);
export const apiDelete = (p) => apiSend(p, 'DELETE');

// Trigger a browser download for a GET endpoint (cookies flow automatically).
export function download(url) {
  const a = document.createElement('a');
  a.href = url;
  a.rel = 'noopener';
  document.body.appendChild(a);
  a.click();
  a.remove();
}
