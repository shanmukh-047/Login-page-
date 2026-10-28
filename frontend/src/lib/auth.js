// Talks to the Django session-auth API. No credentials are stored in this code
// or in the browser; Django sets an HttpOnly session cookie on success.

export const MESSAGES = {
  invalid: 'Invalid username or password.',
  offline: 'Unable to connect. Please try again.',
  empty: 'Please enter your username and password.',
};

function readCookie(name) {
  const match = document.cookie.split('; ').find((c) => c.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.split('=').slice(1).join('=')) : null;
}

async function ensureCsrfToken() {
  let token = readCookie('csrftoken');
  if (!token) {
    const res = await fetch('/api/auth/csrf/', { credentials: 'same-origin' });
    if (!res.ok) throw new Error('csrf');
    token = readCookie('csrftoken');
  }
  return token;
}

/** Resolves to { ok: true, redirect } or { ok: false, message }. Never throws. */
export async function login(username, password) {
  try {
    const token = await ensureCsrfToken();
    const res = await fetch('/api/auth/login/', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': token || '' },
      body: JSON.stringify({ username, password }),
    });
    if (res.ok) {
      const data = await res.json();
      return { ok: true, redirect: data.redirect || '/' };
    }
    if (res.status === 400 || res.status === 401) {
      return { ok: false, message: MESSAGES.invalid };
    }
    return { ok: false, message: MESSAGES.offline };
  } catch {
    return { ok: false, message: MESSAGES.offline };
  }
}

/** Returns the post-login destination if a session already exists, else null. */
export async function currentSession() {
  try {
    const res = await fetch('/api/auth/me/', { credentials: 'same-origin' });
    if (!res.ok) return null;
    const data = await res.json();
    return data.redirect || '/';
  } catch {
    return null;
  }
}

export function safeRedirect(path) {
  return typeof path === 'string' && path.startsWith('/') && !path.startsWith('//') ? path : '/';
}

/** Returns the logged-in user ({ username, first_name, is_staff }) or null. */
export async function getCurrentUser() {
  const res = await fetch('/api/auth/me/', { credentials: 'same-origin' });
  if (res.status === 401) return null;
  if (!res.ok) throw new Error('server');
  const data = await res.json();
  return data.user;
}

/** Ends the Django session. */
export async function logout() {
  const token = await ensureCsrfToken();
  await fetch('/api/auth/logout/', {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'X-CSRFToken': token || '' },
  });
}
