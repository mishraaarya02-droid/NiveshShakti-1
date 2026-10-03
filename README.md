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
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r backend/requirements.txt
   npm --prefix frontend ci
   ```
3. For Docker, install Docker Desktop and set url-safe secrets in PowerShell before starting services:
   ```powershell
   $env:POSTGRES_PASSWORD = python -c "import secrets; print(secrets.token_hex(24))"
   $env:JWT_SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(48))"
   docker compose config
   docker compose up --build
   ```
   Compose runs Alembic migrations after PostgreSQL becomes healthy. The frontend is at `http://localhost:5173`; the API is at `http://localhost:8000`.
4. Local backend development may use the configured SQLite fallback when PostgreSQL is unavailable. Set `DATABASE_URL` to PostgreSQL for deployment and run `alembic upgrade head` from `backend/`.
5. Run checks:
   ```powershell
   $env:PYTHONPATH = "backend"
   python -m pytest backend/tests
   npm --prefix frontend run lint
   npm --prefix frontend run build
   ```

Automated claim lookup is intentionally unavailable unless an official source exposes a documented query interface. Source reachability is not evidence about a claim; use the linked official manual route.

## License
MIT – see `LICENSE` for details.
