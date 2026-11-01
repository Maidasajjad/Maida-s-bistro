# 🍽️ Maida's Bistro

A restaurant website built with **Python + Streamlit**: menu with PKR prices, live stock status, online ordering, table booking, and a password-protected admin dashboard. Data is stored permanently in SQLite.

## Features
- Cream / brown / beige / gold design, responsive on phones
- Menu by category with images (URL or emoji), descriptions, PKR prices, search
- **Automatic stock status**: `Available` → `Low Stock` → `Out of Stock` (calculated from quantity; orders reduce stock, cancelled orders restore it)
- Customer table booking with automatic table assignment and double-booking prevention
- Admin dashboard: dishes, prices, stock, orders, reservations
- Secure by design: no default password, constant-time password check, login lockout, parameterised SQL, HTML escaping, input validation

## Project structure
```
app.py                  Homepage
pages/menu.py           Menu + ordering
pages/reservations.py   Table booking
pages/admin.py          Admin dashboard
database/db.py          SQLite database layer
utils.py                Shared helpers
assets/style.css        Theme styling
.streamlit/config.toml  Theme/server config
```

## Run locally
1. Install Python 3.10+ from python.org.
2. Open a terminal in this folder and run:
   ```bash
   python -m venv .venv
   # Windows:  .venv\Scripts\activate      Mac/Linux:  source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env        # Windows: copy .env.example .env
   ```
3. Edit `.env` and set a strong `ADMIN_PASSWORD` (12+ characters).
4. Start the app: `streamlit run app.py`
5. Open http://localhost:8501. The **Staff Login** page is the admin dashboard.

The database file is created automatically in `data/` with sample menu items and 8 tables.

## Deploy on GitHub + Streamlit Community Cloud
1. Create a GitHub repository and push this folder (`.env` and the database are git-ignored):
   ```bash
   git init && git add . && git commit -m "Maida's Bistro"
   git branch -M main
   git remote add origin https://github.com/YOUR-USER/maidas-bistro.git
   git push -u origin main
   ```
2. Go to https://share.streamlit.io → **New app** → pick the repo, branch `main`, main file `app.py`.
3. Open **Advanced settings → Secrets** and paste:
   ```toml
   ADMIN_PASSWORD = "your-long-random-password"
   ```
4. Click **Deploy**.

### ⚠️ Important: permanent storage on Streamlit Cloud
Community Cloud's file system is **not guaranteed to persist** across reboots/redeployments, so a SQLite file there can be reset. For a real restaurant, either host on a VPS/Docker with a persistent volume, or swap `database/db.py` to a hosted database (e.g. Supabase/Neon PostgreSQL). All SQL is isolated in `database/db.py` to make this easy. Locally, data persists permanently.

## Customising
- Restaurant address/phone/hours: edit `app.py`, `utils.py`.
- Colours: `assets/style.css` and `.streamlit/config.toml`.
- Time slots and tables: `TIME_SLOTS` and seed list in `database/db.py`.
- Dish photos: in Admin → Menu & Prices, paste an `https://` image URL.

## Security notes
- Never commit `.env` or `secrets.toml`.
- Admin login lockout is per browser session; for high-security needs, put the app behind additional authentication (e.g. a reverse proxy).
- Back up `data/maidas_bistro.db` regularly.
