import { useEffect, useState } from 'react';
import { currentSession, login, MESSAGES, safeRedirect } from '../lib/auth.js';
import './LoginPage.css';

const LOGO_SRC = '/protolearn-logo.png'; // drop the real logo file into /public

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [logoFailed, setLogoFailed] = useState(false);

  useEffect(() => {
    document.title = 'Login | ProtoLearn';
    let cancelled = false;
    currentSession().then((dest) => {
      if (dest && !cancelled) window.location.assign(safeRedirect(dest));
    });
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    if (submitting) return;
    if (!username.trim() || !password) {
      setError(MESSAGES.empty);
      return;
    }
    setError('');
    setSubmitting(true);
    const result = await login(username.trim(), password);
    if (result.ok) {
      // Full navigation so server-rendered destinations (e.g. /manage/) load correctly.
      window.location.assign(safeRedirect(result.redirect));
      return;
    }
    setPassword('');
    setError(result.message);
    setSubmitting(false);
  }

  return (
    <main className="pl-login">
      <div className="pl-login__card">
        <div className="pl-login__brand">
          {logoFailed ? (
            <span className="pl-login__wordmark">
              Proto<span>Learn</span>
            </span>
          ) : (
            <img
              src={LOGO_SRC}
              alt="ProtoLearn"
              className="pl-login__logo"
              onError={() => setLogoFailed(true)}
            />
          )}
        </div>

        <h1 className="pl-login__title">Login</h1>

        <form className="pl-login__form" onSubmit={handleSubmit} noValidate>
          <div className="pl-login__field">
            <label htmlFor="pl-username">Username</label>
            <input
              id="pl-username"
              name="username"
              type="text"
              autoComplete="username"
              autoCapitalize="none"
              spellCheck="false"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              aria-invalid={Boolean(error)}
              aria-describedby={error ? 'pl-login-error' : undefined}
              disabled={submitting}
            />
          </div>

          <div className="pl-login__field">
            <label htmlFor="pl-password">Password</label>
            <div className="pl-login__password">
              <input
                id="pl-password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                aria-invalid={Boolean(error)}
                aria-describedby={error ? 'pl-login-error' : undefined}
                disabled={submitting}
              />
              <button
                type="button"
                className="pl-login__toggle"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                aria-pressed={showPassword}
              >
                {showPassword ? <EyeOffIcon /> : <EyeIcon />}
              </button>
            </div>
          </div>

          {error && (
            <p id="pl-login-error" className="pl-login__error" role="alert">
              {error}
            </p>
          )}

          <button type="submit" className="pl-login__submit" disabled={submitting}>
            {submitting ? 'LOGGING IN…' : 'LOGIN'}
          </button>
        </form>
      </div>
    </main>
  );
}

function EyeIcon() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function EyeOffIcon() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 19c-6.5 0-10-7-10-7a18.5 18.5 0 0 1 5.06-5.94" />
      <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c6.5 0 10 7 10 7a18.5 18.5 0 0 1-2.16 3.19" />
      <path d="M14.12 14.12a3 3 0 1 1-4.24-4.24" />
      <line x1="2" y1="2" x2="22" y2="22" />
    </svg>
  );
}
