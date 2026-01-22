# QA Task Manager - Intertech

Professional task management application for QA engineers.

## Features

- Device-based authentication (no passwords)
- Task management with priorities and deadlines
- Project organization
- Smart "Today Focus" dashboard
- Calendar view
- Progress reports
- Custom categories

## Requirements

- **Node.js** ≥ 18
- **Python** 3.10 or 3.11
- **MongoDB** running locally

---

## Quick Start

### Backend

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn server:app --reload --port 8001
```

Backend: `http://localhost:8001`

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm start
```

Frontend: `http://localhost:3000`

---

## Environment Variables

### Backend (`backend/.env`)

```
MONGO_URL=mongodb://127.0.0.1:27017
DB_NAME=qa_task_manager
```

### Frontend (`frontend/.env`)

```
REACT_APP_API_URL=http://localhost:8001
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register user |
| GET | `/api/auth/check/{device_id}` | Check device |
| GET | `/api/dashboard/stats` | Dashboard stats |
| GET/POST | `/api/tasks` | Tasks |
| GET/POST | `/api/projects` | Projects |
| GET | `/api/health` | Health check |

---

## Troubleshooting

### MongoDB Connection
```bash
# macOS
brew services start mongodb-community

# Ubuntu
sudo systemctl start mongod
```

### Port Conflict
```bash
lsof -ti:8001 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

---

© 2025 Intertech
