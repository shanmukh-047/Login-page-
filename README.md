# ProtoLearn login (`/admin`)

This adds a ProtoLearn-branded login page at `/admin`. The accounts behind it are created by admins only. There is no signup, registration, or demo page.

```
logic cred/
├── frontend/   React (Vite) login page. Only adds the /admin route.
└── backend/    Django: session login API + account management in Django admin at /manage/
```

## How it works

1. An admin signs in at `/manage/`, opens **Users → Add user**, and sets a username and initial password. Django hashes the password and rejects duplicate usernames.
2. The admin gives those credentials to the student or customer.
3. The user opens `/admin` and enters them. React sends the credentials to `POST /api/auth/login/`, which uses CSRF protection.
4. Django's `authenticate()` checks the password hash. Inactive accounts are refused. On success, `login()` sets an HttpOnly session cookie.
5. The user is sent to their destination:
   - The **Home page after login** set on their account, if there is one.
   - Otherwise `PROTOLEARN_DEFAULT_REDIRECT`, which defaults to `/login` (the student welcome page).
   - Staff go to `/manage/` instead of the default.

Admins can do the following in `/manage/`:

- **Deactivate an account:** untick **Active**.
- **Reset a password:** use the **Reset password** link on the user's page.

### Who can manage accounts

- **Superusers** can do everything.
- **Account managers** are staff users in the auto-created *Account managers* group. They can create, edit, deactivate and reset student/customer accounts. They cannot see or edit staff/superuser accounts, cannot grant staff or superuser rights, and cannot delete accounts.
- **Students/customers** have no access to `/manage/`.

### API (no registration endpoint exists)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/auth/csrf/` | Sets the CSRF cookie |
| POST | `/api/auth/login/` | `{username, password}` → `{user, redirect}`. Returns 401 `Invalid username or password.` on failure. |
| POST | `/api/auth/logout/` | Ends the session |
| GET | `/api/auth/me/` | Current user or 401 |

Responses never include password hashes or permissions.

## Run locally

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export DJANGO_DEBUG=true                               # Windows: set DJANGO_DEBUG=true
python manage.py migrate
python manage.py createsuperuser                       # you choose the credentials
python manage.py runserver 127.0.0.1:8000

# Frontend (second terminal)
cd frontend
npm install
npm run dev                                            # open http://localhost:5173/admin
```

Vite forwards `/api`, `/manage` and `/static` to Django, so you can also reach the account admin at `http://localhost:5173/manage/`.

Run the backend tests with `DJANGO_DEBUG=true python manage.py test accounts`.

## Merging into the existing ProtoLearn site

- **Frontend:** copy these into the site's React project:
  - `src/pages/LoginPage.jsx`
  - `src/pages/LoginPage.css`
  - `src/lib/auth.js`

  Then add one route to the existing router: `<Route path="/admin" element={<LoginPage />} />`. Leave the other routes alone. Put the real logo at `public/protolearn-logo.png`; until then a "ProtoLearn" wordmark is shown.
- **Brand match:** the colors are CSS variables at the top of `LoginPage.css`. They are set to a standard blue (`#2563eb`) with the Inter font. Swap in the live site's exact hex values and font if they differ.
- **Backend:** if ProtoLearn already has a Django project, don't run this one separately. Copy the `accounts` app into it, add it to `INSTALLED_APPS`, include `accounts.urls` at `api/auth/`, and run `migrate`. Its existing `User` table, hashing and sessions are reused. If its Django admin is already at `/admin/`, move it (for example to `manage/`) so it doesn't clash with the React page. Otherwise, keep the React route somewhere else and tell me.

## Production checklist (remaining configuration)

1. Set the environment variables from `backend/.env.example`. `DJANGO_SECRET_KEY` is required; the app refuses to start without it when not in debug.
2. Point `DB_*` at the existing production database. SQLite is only for local use.
3. Serve React and Django on the **same domain** so the session and CSRF cookies work. Example nginx:
   ```nginx
   location /api/     { proxy_pass http://127.0.0.1:8000; proxy_set_header Host $host; proxy_set_header X-Forwarded-Proto $scheme; }
   location /manage/  { proxy_pass http://127.0.0.1:8000; proxy_set_header Host $host; proxy_set_header X-Forwarded-Proto $scheme; }
   location /static/  { alias /path/to/backend/staticfiles/; }
   location /         { root /path/to/frontend/dist; try_files $uri /index.html; }
   ```
   Run `python manage.py collectstatic` and serve Django with gunicorn (or similar), not `runserver`.
4. HTTPS is required. Secure cookies are on whenever `DJANGO_DEBUG` is false.
5. Recommended: add login rate limiting, such as `django-axes`, to slow down password guessing.
6. If the site is currently a static Bolt.new deploy with no server, you'll need a host that can run Django, for example a VPS, Render or Railway.
