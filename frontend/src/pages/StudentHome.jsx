import { useEffect, useState } from 'react';
import { getCurrentUser, logout, MESSAGES } from '../lib/auth.js';
import './LoginPage.css';

// Page students land on after logging in. Only visible with a valid session;
// anyone else is sent back to the login page at /admin.
export default function StudentHome() {
  const [user, setUser] = useState(null);
  const [error, setError] = useState('');
  const [leaving, setLeaving] = useState(false);

  useEffect(() => {
    document.title = 'Welcome | ProtoLearn';
    getCurrentUser()
      .then((u) => {
        if (u) setUser(u);
        else window.location.replace('/admin');
      })
      .catch(() => setError(MESSAGES.offline));
  }, []);

  async function handleLogout() {
    setLeaving(true);
    try {
      await logout();
    } finally {
      window.location.assign('/admin');
    }
  }

  return (
    <main className="pl-login">
      <div className="pl-login__card">
        <div className="pl-login__brand">
          <span className="pl-login__wordmark">
            Proto<span>Learn</span>
          </span>
        </div>

        {error && (
          <p className="pl-login__error" role="alert">
            {error}
          </p>
        )}

        {!user && !error && <p className="pl-home__muted">Loading…</p>}

        {user && (
          <>
            <h1 className="pl-login__title">Welcome, {user.first_name || user.username}</h1>
            <p className="pl-home__muted">
              You are logged in as <strong>{user.username}</strong>.
            </p>
            <button
              type="button"
              className="pl-login__submit pl-home__logout"
              onClick={handleLogout}
              disabled={leaving}
            >
              {leaving ? 'LOGGING OUT…' : 'LOGOUT'}
            </button>
          </>
        )}
      </div>
    </main>
  );
}
