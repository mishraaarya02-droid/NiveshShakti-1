# NiveshShakti

**Tagline:** "Before You Trust It, Verify It."

A public-good tool that helps Indian retail investors examine financial claims, see deterministic wording cues, and find official routes for manual verification. An unavailable source is not a safety result.

## Tech Stack
- **Frontend:** React, TypeScript, Vite, Tailwind CSS
- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy
- **Database:** PostgreSQL (managed via Alembic migrations)
- **Auth:** Secure password hashing, JWT
- **Other services:** Tesseract OCR, Whisper speech-to-text, conservative official-source adapters

## Repository Layout
```
NiveshShakti/
├─ frontend/                # React app
├─ backend/                 # FastAPI service
│   ├─ app/
│   │   ├─ api/             # Auth, analysis, grievance routes
│   │   ├─ core/            # Config and security
│   │   ├─ services/        # Analysis, source, OCR, and speech providers
│   │   ├─ models.py        # SQLAlchemy models
│   │   ├─ schemas.py       # Pydantic schemas
│   │   └─ main.py
│   ├─ alembic/             # Database migrations
│   └─ tests/               # Backend regression and provider tests
├─ docker-compose.yml
├─ README.md
└─ .gitignore
```

## Development
1. Install Python 3.11+, Node.js 22+, and (for local multimodal use) Tesseract with English/Hindi data plus FFmpeg. Whisper also requires PyTorch; model weights are downloaded by Whisper when first used.
2. Install dependencies:
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   npm --prefix frontend ci
   ```
   On Windows, activate the virtual environment with `.\.venv\Scripts\Activate.ps1`.
   To run the backend test suite, install `backend/requirements-dev.txt` instead of `backend/requirements.txt`.
3. Start the local SQLite backend from `backend/`. A fresh database must be migrated before the first request:
   ```sh
   cd backend
   alembic upgrade head
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   In a second terminal, start the frontend from the repository root:
   ```sh
   npm --prefix frontend run dev
   ```
   Vite proxies API requests to `http://localhost:8000` by default; set `VITE_BACKEND_PROXY_TARGET` to override it. Backend settings load an optional `.env` file from the backend's current working directory and can also be set through environment variables. Set a private `JWT_SECRET_KEY` in `backend/.env` to keep local login tokens valid across backend restarts; without it, a fresh development key is generated at each startup. Never commit `.env`.
4. For Docker, install Docker Desktop and set url-safe secrets in PowerShell before starting services:
   ```powershell
   $env:POSTGRES_PASSWORD = python -c "import secrets; print(secrets.token_hex(24))"
   $env:JWT_SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(48))"
   docker compose config
   docker compose up --build
   ```
   Compose runs Alembic migrations after PostgreSQL becomes healthy. The frontend is at `http://localhost:5173`; the API is at `http://localhost:8000`.
5. Run checks:
   ```powershell
   $env:PYTHONPATH = "backend"
   python -m pytest backend/tests
   npm --prefix frontend run lint
   npm --prefix frontend run build
   ```

Automated claim lookup is intentionally unavailable unless an official source exposes a documented query interface. URL analysis checks only the submitted URL text and does not fetch the destination page or verify domain ownership, reputation, or safety. Source reachability is not evidence about a claim; use the linked official manual route.

## License
MIT – see `LICENSE` for details.
