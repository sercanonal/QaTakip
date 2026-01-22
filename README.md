# QA Task Manager - Intertech

Professional task management for QA engineers.

**No MongoDB required. No system dependencies. Just Python and Node.js.**

## Features

- Device-based authentication (no passwords)
- Task management with priorities and deadlines
- Project organization
- Smart "Today Focus" dashboard
- Calendar view
- Progress reports

## Requirements

- **Node.js** ≥ 18
- **Python** ≥ 3.10

**That's it.** No MongoDB, no brew, no sudo, no system installs.

---

## Quick Start

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn server:app --reload --port 8001
```

### Frontend

```bash
cd frontend
npm install
npm start
```

---

## How It Works

- **Database**: SQLite (file-based, created automatically in `backend/data/`)
- **No external services required**
- Data persists in `backend/data/qa_tasks.db`

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/auth/register` | Register user |
| GET | `/api/auth/check/{device_id}` | Check device |
| GET | `/api/dashboard/stats` | Dashboard stats |
| GET/POST | `/api/tasks` | Tasks |
| GET/POST | `/api/projects` | Projects |

---

## Project Structure

```
├── backend/
│   ├── server.py          # FastAPI + SQLite
│   ├── requirements.txt   # Python dependencies
│   └── data/              # SQLite database (auto-created)
│       └── qa_tasks.db
│
├── frontend/
│   ├── src/
│   └── package.json
│
└── README.md
```

---

© 2025 Intertech
