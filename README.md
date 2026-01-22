# QA Task Manager - Intertech

Professional task management application for QA engineers and Intertech employees.

## Features

- **Device-based Authentication** - No passwords, unique per device
- **Task Management** - Create, edit, delete tasks with priorities and deadlines
- **Project Organization** - Group tasks by projects
- **Smart Dashboard** - "Today Focus" highlights urgent and overdue tasks
- **Calendar View** - Visualize tasks by date
- **Reports** - Progress analytics and statistics
- **Custom Categories** - Default QA categories + custom ones

## Tech Stack

- **Backend**: FastAPI + MongoDB
- **Frontend**: React 18 + Tailwind CSS + Shadcn/UI
- **Database**: MongoDB

## Requirements

- Node.js >= 18
- Python >= 3.10
- MongoDB running locally (default: `localhost:27017`)

---

## Local Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd qa-task-manager
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env if needed (defaults work for local development)

# Start server
uvicorn server:app --reload --port 8001
```

Backend will be available at `http://localhost:8001`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
# or
yarn install

# Setup environment variables
cp .env.example .env
# Edit .env if needed (defaults work for local development)

# Start development server
npm start
# or
yarn start
```

Frontend will be available at `http://localhost:3000`

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGO_URL` | MongoDB connection string | `mongodb://localhost:27017` |
| `DB_NAME` | Database name | `qa_task_manager` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |

### Frontend (`frontend/.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `REACT_APP_BACKEND_URL` | Backend API URL | `http://localhost:8001` |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register with name + device_id |
| GET | `/api/auth/check/{device_id}` | Check if device registered |
| GET | `/api/dashboard/stats` | Get dashboard statistics |
| GET/POST | `/api/tasks` | List/Create tasks |
| PUT/DELETE | `/api/tasks/{id}` | Update/Delete task |
| GET/POST | `/api/projects` | List/Create projects |
| PUT/DELETE | `/api/projects/{id}` | Update/Delete project |
| GET | `/api/health` | Health check |

---

## Project Structure

```
├── backend/
│   ├── server.py          # FastAPI application
│   ├── requirements.txt   # Python dependencies
│   ├── .env.example       # Environment template
│   └── .env               # Local environment (git-ignored)
│
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── context/       # Auth context
│   │   ├── lib/           # API client, utilities
│   │   └── pages/         # Page components
│   ├── package.json       # Node dependencies
│   ├── .env.example       # Environment template
│   └── .env               # Local environment (git-ignored)
│
└── README.md
```

---

## Default Task Categories

- API Testi (Blue)
- UI Testi (Green)
- Regresyon (Orange)
- Bug Tracking (Red)
- Test Dokümantasyonu (Purple)

Users can add custom categories via Settings.

---

## Troubleshooting

### MongoDB Connection Error
Ensure MongoDB is running:
```bash
# macOS (Homebrew)
brew services start mongodb-community

# Ubuntu
sudo systemctl start mongod
```

### Port Already in Use
```bash
# Kill process on port 8001 (backend)
lsof -ti:8001 | xargs kill -9

# Kill process on port 3000 (frontend)
lsof -ti:3000 | xargs kill -9
```

### Clear Frontend Cache
```bash
cd frontend
rm -rf node_modules/.cache
npm start
```

---

## License

Internal use - Intertech © 2025
