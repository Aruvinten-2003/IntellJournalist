# Intell Journalist

AI-powered world news interface using FastAPI, MongoDB, and plain HTML/CSS/JavaScript.

## Included

- MongoDB-backed users, bookmarks, articles, conversations, and messages
- JWT registration, login, profile, logout, and password-reset endpoints
- News listing, filtering, source links, and bookmarks
- OpenAI-grounded news chat with a deterministic fallback
- Responsive login, sign-up, forgot-password, and dashboard pages
- Pydantic request/response schemas under `backend/schemas`

## Start MongoDB

Run a local MongoDB server on `mongodb://127.0.0.1:27017`, or use a MongoDB Atlas connection string.

Copy `.env.example` to `.env`, then set the MongoDB URL and a private JWT secret. The `.env` file is ignored by Git.

## Install and start

Run these commands from the project directory:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 5500 --reload
```

Open:

- Website: `http://127.0.0.1:5500`
- API documentation: `http://127.0.0.1:5500/api/docs`
- Health check: `http://127.0.0.1:5500/api/health`

FastAPI serves the frontend and API together, so a separate `http.server` command is not required.

## Development behavior

If MongoDB is unavailable and `DATABASE_REQUIRED=false`, public news and chat still use the bundled grounded demo reports. Persistent accounts, server bookmarks, and saved conversations require MongoDB.

If the OpenAI key is not loaded, chat uses the local extractive summarizer. Credentials must remain in the ignored `.env` file and must never be added to frontend JavaScript.
