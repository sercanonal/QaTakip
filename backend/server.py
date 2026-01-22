from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
import json
import aiosqlite
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum
from contextlib import asynccontextmanager

ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "qa_tasks.db"

load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============== SQLite Database Setup ==============

async def init_db():
    """Initialize SQLite database with required tables"""
    DATA_DIR.mkdir(exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Users table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                device_id TEXT UNIQUE NOT NULL,
                categories TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Tasks table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                category_id TEXT NOT NULL,
                project_id TEXT,
                user_id TEXT NOT NULL,
                status TEXT NOT NULL,
                priority TEXT NOT NULL,
                due_date TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Projects table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Notifications table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                type TEXT NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        await db.commit()
    
    logger.info(f"SQLite database initialized at {DB_PATH}")

# ============== Enums ==============

class TaskStatus(str, Enum):
    BACKLOG = "backlog"  # Eski "todo" - Backlog
    TODAY_PLANNED = "today_planned"  # Bugün Başlamayı Planlıyorum
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Default categories
DEFAULT_CATEGORIES = [
    {"id": "api-test", "name": "API Testi", "color": "#3B82F6", "is_default": True},
    {"id": "ui-test", "name": "UI Testi", "color": "#10B981", "is_default": True},
    {"id": "regression", "name": "Regresyon", "color": "#F59E0B", "is_default": True},
    {"id": "bug-tracking", "name": "Bug Tracking", "color": "#EF4444", "is_default": True},
    {"id": "documentation", "name": "Test Dokümantasyonu", "color": "#8B5CF6", "is_default": True},
]

# ============== Models ==============

class UserCreate(BaseModel):
    name: str
    device_id: str

class UserResponse(BaseModel):
    id: str
    name: str
    device_id: str
    created_at: str
    categories: List[dict]

class Category(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    color: str = "#3B82F6"
    is_default: bool = False

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = ""

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = ""
    category_id: str
    project_id: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[str] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    project_id: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[str] = None

# ============== App Setup ==============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    await init_db()
    logger.info("QA Task Manager started - Using SQLite (no MongoDB required)")
    yield

app = FastAPI(title="QA Task Manager - Intertech", lifespan=lifespan)
api_router = APIRouter(prefix="/api")

# ============== Helper Functions ==============

def row_to_dict(row, columns):
    """Convert SQLite row to dictionary"""
    return dict(zip(columns, row))

async def get_db():
    """Get database connection"""
    return await aiosqlite.connect(DB_PATH)

# ============== AUTH ROUTES ==============

@api_router.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register new user with device_id"""
    if not user_data.name or not user_data.name.strip():
        raise HTTPException(status_code=400, detail="İsim boş olamaz")
    
    if not user_data.device_id:
        raise HTTPException(status_code=400, detail="Cihaz kimliği gerekli")
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if device already registered
        cursor = await db.execute(
            "SELECT id, name, device_id, categories, created_at FROM users WHERE device_id = ?",
            (user_data.device_id,)
        )
        existing = await cursor.fetchone()
        
        if existing:
            return UserResponse(
                id=existing[0],
                name=existing[1],
                device_id=existing[2],
                categories=json.loads(existing[3]),
                created_at=existing[4]
            )
        
        # Create new user
        user_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        categories_json = json.dumps(DEFAULT_CATEGORIES)
        
        await db.execute(
            "INSERT INTO users (id, name, device_id, categories, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, user_data.name.strip(), user_data.device_id, categories_json, created_at)
        )
        
        # Create welcome notification
        notif_id = str(uuid.uuid4())
        await db.execute(
            "INSERT INTO notifications (id, user_id, title, message, type, is_read, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (notif_id, user_id, "Hoş Geldiniz!", f"QA Task Manager'a hoş geldiniz, {user_data.name.strip()}!", "success", 0, created_at)
        )
        
        await db.commit()
        
        return UserResponse(
            id=user_id,
            name=user_data.name.strip(),
            device_id=user_data.device_id,
            categories=DEFAULT_CATEGORIES,
            created_at=created_at
        )

@api_router.get("/auth/check/{device_id}", response_model=UserResponse)
async def check_device(device_id: str):
    """Check if device is registered"""
    if not device_id:
        raise HTTPException(status_code=400, detail="Cihaz kimliği gerekli")
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, device_id, categories, created_at FROM users WHERE device_id = ?",
            (device_id,)
        )
        user = await cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="Cihaz kayıtlı değil")
        
        return UserResponse(
            id=user[0],
            name=user[1],
            device_id=user[2],
            categories=json.loads(user[3]),
            created_at=user[4]
        )

# ============== USER ROUTES ==============

@api_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, device_id, categories, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        user = await cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        return UserResponse(
            id=user[0],
            name=user[1],
            device_id=user[2],
            categories=json.loads(user[3]),
            created_at=user[4]
        )

@api_router.post("/users/{user_id}/categories", response_model=UserResponse)
async def add_category(user_id: str, category: Category):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, device_id, categories, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        user = await cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        categories = json.loads(user[3])
        new_cat = {"id": category.id, "name": category.name, "color": category.color, "is_default": False}
        categories.append(new_cat)
        
        await db.execute(
            "UPDATE users SET categories = ? WHERE id = ?",
            (json.dumps(categories), user_id)
        )
        await db.commit()
        
        return UserResponse(
            id=user[0],
            name=user[1],
            device_id=user[2],
            categories=categories,
            created_at=user[4]
        )

@api_router.delete("/users/{user_id}/categories/{category_id}", response_model=UserResponse)
async def delete_category(user_id: str, category_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, device_id, categories, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        user = await cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        categories = json.loads(user[3])
        
        for cat in categories:
            if cat["id"] == category_id and cat.get("is_default"):
                raise HTTPException(status_code=400, detail="Varsayılan kategoriler silinemez")
        
        categories = [c for c in categories if c["id"] != category_id]
        
        await db.execute(
            "UPDATE users SET categories = ? WHERE id = ?",
            (json.dumps(categories), user_id)
        )
        await db.commit()
        
        return UserResponse(
            id=user[0],
            name=user[1],
            device_id=user[2],
            categories=categories,
            created_at=user[4]
        )

# ============== PROJECT ROUTES ==============

@api_router.post("/projects", response_model=dict)
async def create_project(project: ProjectBase, user_id: str):
    project_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO projects (id, name, description, user_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (project_id, project.name, project.description or "", user_id, created_at)
        )
        await db.commit()
    
    return {
        "id": project_id,
        "name": project.name,
        "description": project.description or "",
        "user_id": user_id,
        "created_at": created_at,
        "task_count": 0
    }

@api_router.get("/projects", response_model=List[dict])
async def get_projects(user_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, description, user_id, created_at FROM projects WHERE user_id = ?",
            (user_id,)
        )
        rows = await cursor.fetchall()
        
        projects = []
        for row in rows:
            # Count tasks for this project
            task_cursor = await db.execute(
                "SELECT COUNT(*) FROM tasks WHERE project_id = ?",
                (row[0],)
            )
            task_count = (await task_cursor.fetchone())[0]
            
            projects.append({
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "user_id": row[3],
                "created_at": row[4],
                "task_count": task_count
            })
        
        return projects

@api_router.get("/projects/{project_id}", response_model=dict)
async def get_project(project_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, description, user_id, created_at FROM projects WHERE id = ?",
            (project_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Proje bulunamadı")
        
        return {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "user_id": row[3],
            "created_at": row[4]
        }

@api_router.put("/projects/{project_id}", response_model=dict)
async def update_project(project_id: str, project: ProjectBase):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id FROM projects WHERE id = ?",
            (project_id,)
        )
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Proje bulunamadı")
        
        await db.execute(
            "UPDATE projects SET name = ?, description = ? WHERE id = ?",
            (project.name, project.description, project_id)
        )
        await db.commit()
        
        cursor = await db.execute(
            "SELECT id, name, description, user_id, created_at FROM projects WHERE id = ?",
            (project_id,)
        )
        row = await cursor.fetchone()
        
        return {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "user_id": row[3],
            "created_at": row[4]
        }

@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM tasks WHERE project_id = ?", (project_id,))
        result = await db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        await db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Proje bulunamadı")
        
        return {"message": "Proje silindi"}

# ============== TASK ROUTES ==============

@api_router.post("/tasks", response_model=dict)
async def create_task(task: TaskCreate, user_id: str):
    task_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO tasks (id, title, description, category_id, project_id, user_id, status, priority, due_date, created_at, completed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (task_id, task.title, task.description or "", task.category_id, task.project_id, user_id, 
             TaskStatus.BACKLOG.value, task.priority.value, task.due_date, created_at, None)
        )
        await db.commit()
    
    return {
        "id": task_id,
        "title": task.title,
        "description": task.description or "",
        "category_id": task.category_id,
        "project_id": task.project_id,
        "user_id": user_id,
        "status": TaskStatus.BACKLOG.value,
        "priority": task.priority.value,
        "due_date": task.due_date,
        "created_at": created_at,
        "completed_at": None
    }

@api_router.get("/tasks", response_model=List[dict])
async def get_tasks(
    user_id: str,
    status: Optional[str] = None,
    category_id: Optional[str] = None,
    project_id: Optional[str] = None,
    priority: Optional[str] = None
):
    query = "SELECT id, title, description, category_id, project_id, user_id, status, priority, due_date, created_at, completed_at FROM tasks WHERE user_id = ?"
    params = [user_id]
    
    if status:
        query += " AND status = ?"
        params.append(status)
    if category_id:
        query += " AND category_id = ?"
        params.append(category_id)
    if project_id:
        query += " AND project_id = ?"
        params.append(project_id)
    if priority:
        query += " AND priority = ?"
        params.append(priority)
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        
        return [
            {
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "category_id": row[3],
                "project_id": row[4],
                "user_id": row[5],
                "status": row[6],
                "priority": row[7],
                "due_date": row[8],
                "created_at": row[9],
                "completed_at": row[10]
            }
            for row in rows
        ]

@api_router.get("/tasks/{task_id}", response_model=dict)
async def get_task(task_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, title, description, category_id, project_id, user_id, status, priority, due_date, created_at, completed_at FROM tasks WHERE id = ?",
            (task_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Görev bulunamadı")
        
        return {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "category_id": row[3],
            "project_id": row[4],
            "user_id": row[5],
            "status": row[6],
            "priority": row[7],
            "due_date": row[8],
            "created_at": row[9],
            "completed_at": row[10]
        }

@api_router.put("/tasks/{task_id}", response_model=dict)
async def update_task(task_id: str, task_update: TaskUpdate):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
        if not await cursor.fetchone():
            raise HTTPException(status_code=404, detail="Görev bulunamadı")
        
        updates = []
        params = []
        
        if task_update.title is not None:
            updates.append("title = ?")
            params.append(task_update.title)
        if task_update.description is not None:
            updates.append("description = ?")
            params.append(task_update.description)
        if task_update.category_id is not None:
            updates.append("category_id = ?")
            params.append(task_update.category_id)
        if task_update.project_id is not None:
            updates.append("project_id = ?")
            params.append(task_update.project_id)
        if task_update.priority is not None:
            updates.append("priority = ?")
            params.append(task_update.priority.value)
        if task_update.status is not None:
            updates.append("status = ?")
            params.append(task_update.status.value)
            if task_update.status == TaskStatus.COMPLETED:
                updates.append("completed_at = ?")
                params.append(datetime.now(timezone.utc).isoformat())
            else:
                updates.append("completed_at = ?")
                params.append(None)
        if task_update.due_date is not None:
            updates.append("due_date = ?")
            params.append(task_update.due_date)
        
        if not updates:
            raise HTTPException(status_code=400, detail="Güncellenecek alan bulunamadı")
        
        params.append(task_id)
        await db.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?", params)
        await db.commit()
        
        cursor = await db.execute(
            "SELECT id, title, description, category_id, project_id, user_id, status, priority, due_date, created_at, completed_at FROM tasks WHERE id = ?",
            (task_id,)
        )
        row = await cursor.fetchone()
        
        return {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "category_id": row[3],
            "project_id": row[4],
            "user_id": row[5],
            "status": row[6],
            "priority": row[7],
            "due_date": row[8],
            "created_at": row[9],
            "completed_at": row[10]
        }

@api_router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        await db.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Görev bulunamadı")
        
        return {"message": "Görev silindi"}

# ============== DASHBOARD STATS ==============

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(user_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        # Counts
        cursor = await db.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ?", (user_id,))
        total_tasks = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = ?", (user_id, TaskStatus.COMPLETED.value))
        completed_tasks = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = ?", (user_id, TaskStatus.IN_PROGRESS.value))
        in_progress_tasks = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = ?", (user_id, TaskStatus.TODO.value))
        todo_tasks = (await cursor.fetchone())[0]
        
        # Category stats
        cursor = await db.execute(
            "SELECT category_id, COUNT(*) FROM tasks WHERE user_id = ? GROUP BY category_id",
            (user_id,)
        )
        category_rows = await cursor.fetchall()
        category_stats = {row[0]: row[1] for row in category_rows}
        
        # Priority stats
        cursor = await db.execute(
            "SELECT priority, COUNT(*) FROM tasks WHERE user_id = ? GROUP BY priority",
            (user_id,)
        )
        priority_rows = await cursor.fetchall()
        priority_stats = {row[0]: row[1] for row in priority_rows}
        
        # Recent tasks
        cursor = await db.execute(
            "SELECT id, title, description, category_id, project_id, user_id, status, priority, due_date, created_at, completed_at FROM tasks WHERE user_id = ? ORDER BY created_at DESC LIMIT 5",
            (user_id,)
        )
        recent_rows = await cursor.fetchall()
        recent_tasks = [
            {
                "id": row[0], "title": row[1], "description": row[2], "category_id": row[3],
                "project_id": row[4], "user_id": row[5], "status": row[6], "priority": row[7],
                "due_date": row[8], "created_at": row[9], "completed_at": row[10]
            }
            for row in recent_rows
        ]
        
        # Overdue tasks
        now = datetime.now(timezone.utc).isoformat()
        cursor = await db.execute(
            "SELECT COUNT(*) FROM tasks WHERE user_id = ? AND due_date < ? AND due_date IS NOT NULL AND status != ?",
            (user_id, now, TaskStatus.COMPLETED.value)
        )
        overdue_tasks = (await cursor.fetchone())[0]
        
        # Today Focus
        cursor = await db.execute(
            "SELECT id, title, description, category_id, project_id, user_id, status, priority, due_date, created_at, completed_at FROM tasks WHERE user_id = ? AND status != ?",
            (user_id, TaskStatus.COMPLETED.value)
        )
        active_rows = await cursor.fetchall()
        
        now_dt = datetime.now(timezone.utc)
        focus_tasks = []
        
        for row in active_rows:
            task = {
                "id": row[0], "title": row[1], "description": row[2], "category_id": row[3],
                "project_id": row[4], "user_id": row[5], "status": row[6], "priority": row[7],
                "due_date": row[8], "created_at": row[9], "completed_at": row[10]
            }
            
            risk_score = 0
            urgency_score = 0
            labels = []
            
            priority_weights = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            risk_score += priority_weights.get(task.get("priority", "medium"), 2)
            
            if task.get("due_date"):
                try:
                    due_dt = datetime.fromisoformat(task["due_date"].replace("Z", "+00:00"))
                    days_until = (due_dt - now_dt).days
                    
                    if days_until < 0:
                        overdue_days = abs(days_until)
                        risk_score += min(overdue_days, 5) + 3
                        urgency_score = 10
                        labels.append(f"{overdue_days} gün gecikmiş")
                    elif days_until == 0:
                        risk_score += 3
                        urgency_score = 8
                        labels.append("Bugün son gün")
                    elif days_until == 1:
                        risk_score += 2
                        urgency_score = 6
                        labels.append("Yarın bitiyor")
                    elif days_until <= 3:
                        risk_score += 1
                        urgency_score = 4
                        labels.append(f"{days_until} gün kaldı")
                except:
                    pass
            
            if task.get("priority") in ["critical", "high"] and not labels:
                labels.append("Yüksek öncelik")
            
            task["risk_score"] = risk_score
            task["urgency_score"] = urgency_score
            task["focus_labels"] = labels
            
            if risk_score >= 4 or urgency_score >= 4:
                focus_tasks.append(task)
        
        focus_tasks.sort(key=lambda x: (x["urgency_score"], x["risk_score"]), reverse=True)
        
        overdue_list = [t for t in focus_tasks if any("gecikmiş" in l for l in t.get("focus_labels", []))]
        critical_today = [t for t in focus_tasks if "Bugün son gün" in t.get("focus_labels", [])]
        high_priority = [t for t in active_rows if t[7] in ["critical", "high"]]
        
        today_summary = []
        if overdue_list:
            today_summary.append(f"{len(overdue_list)} görev gecikmiş durumda")
        if critical_today:
            today_summary.append(f"{len(critical_today)} görevin bugün son günü")
        if len(high_priority) > 0 and not overdue_list and not critical_today:
            today_summary.append(f"{len(high_priority)} yüksek öncelikli görev bekliyor")
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "todo_tasks": todo_tasks,
            "overdue_tasks": overdue_tasks,
            "completion_rate": round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1),
            "category_stats": category_stats,
            "priority_stats": priority_stats,
            "recent_tasks": recent_tasks,
            "today_focus": {
                "tasks": focus_tasks[:5],
                "summary": today_summary,
                "total_attention_needed": len(focus_tasks)
            }
        }

# ============== NOTIFICATION ROUTES ==============

@api_router.get("/daily-summary")
async def get_daily_summary(user_id: str, target_date: Optional[str] = None):
    """Get daily summary for standup meetings - yesterday completed + today's work
    
    Args:
        user_id: User ID
        target_date: Target date in ISO format (YYYY-MM-DD). Defaults to today.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        # Parse target date or use today
        if target_date:
            try:
                target_dt = datetime.fromisoformat(target_date.replace("Z", "+00:00"))
                if target_dt.tzinfo is None:
                    target_dt = target_dt.replace(tzinfo=timezone.utc)
            except:
                target_dt = datetime.now(timezone.utc)
        else:
            target_dt = datetime.now(timezone.utc)
        
        today_start = target_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)
        
        # Yesterday completed tasks (completed_at between yesterday 00:00 and today 00:00)
        cursor = await db.execute(
            """SELECT id, title, description, category_id, project_id, status, priority, completed_at 
               FROM tasks 
               WHERE user_id = ? AND status = ? AND completed_at >= ? AND completed_at < ?
               ORDER BY completed_at DESC""",
            (user_id, TaskStatus.COMPLETED.value, yesterday_start.isoformat(), today_start.isoformat())
        )
        yesterday_rows = await cursor.fetchall()
        yesterday_completed = [
            {"id": r[0], "title": r[1], "description": r[2], "category_id": r[3], 
             "project_id": r[4], "status": r[5], "priority": r[6], "completed_at": r[7]}
            for r in yesterday_rows
        ]
        
        # Today's work - in_progress tasks
        cursor = await db.execute(
            """SELECT id, title, description, category_id, project_id, status, priority, due_date 
               FROM tasks 
               WHERE user_id = ? AND status = ?
               ORDER BY priority DESC""",
            (user_id, TaskStatus.IN_PROGRESS.value)
        )
        in_progress_rows = await cursor.fetchall()
        today_in_progress = [
            {"id": r[0], "title": r[1], "description": r[2], "category_id": r[3], 
             "project_id": r[4], "status": r[5], "priority": r[6], "due_date": r[7]}
            for r in in_progress_rows
        ]
        
        # Blocked tasks
        cursor = await db.execute(
            """SELECT id, title, description, category_id, project_id, status, priority, due_date 
               FROM tasks 
               WHERE user_id = ? AND status = ?
               ORDER BY priority DESC""",
            (user_id, TaskStatus.BLOCKED.value)
        )
        blocked_rows = await cursor.fetchall()
        blocked_tasks = [
            {"id": r[0], "title": r[1], "description": r[2], "category_id": r[3], 
             "project_id": r[4], "status": r[5], "priority": r[6], "due_date": r[7]}
            for r in blocked_rows
        ]
        
        # Today planned (todo with high priority or due on target date)
        today_end = today_start + timedelta(days=1)
        cursor = await db.execute(
            """SELECT id, title, description, category_id, project_id, status, priority, due_date 
               FROM tasks 
               WHERE user_id = ? AND status = ? AND (priority IN ('high', 'critical') OR (due_date >= ? AND due_date < ?))
               ORDER BY priority DESC, due_date ASC""",
            (user_id, TaskStatus.TODO.value, today_start.isoformat(), today_end.isoformat())
        )
        planned_rows = await cursor.fetchall()
        today_planned = [
            {"id": r[0], "title": r[1], "description": r[2], "category_id": r[3], 
             "project_id": r[4], "status": r[5], "priority": r[6], "due_date": r[7]}
            for r in planned_rows
        ]
        
        # Get project names
        cursor = await db.execute("SELECT id, name FROM projects WHERE user_id = ?", (user_id,))
        project_rows = await cursor.fetchall()
        project_map = {r[0]: r[1] for r in project_rows}
        
        # Add project names to tasks
        for task_list in [yesterday_completed, today_in_progress, blocked_tasks, today_planned]:
            for task in task_list:
                task["project_name"] = project_map.get(task.get("project_id"), None)
        
        return {
            "target_date": today_start.isoformat(),
            "yesterday_completed": yesterday_completed,
            "today_in_progress": today_in_progress,
            "blocked_tasks": blocked_tasks,
            "today_planned": today_planned,
            "summary": {
                "yesterday_count": len(yesterday_completed),
                "in_progress_count": len(today_in_progress),
                "blocked_count": len(blocked_tasks),
                "planned_count": len(today_planned)
            }
        }

@api_router.get("/notifications", response_model=List[dict])
async def get_notifications(user_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, user_id, title, message, type, is_read, created_at FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 50",
            (user_id,)
        )
        rows = await cursor.fetchall()
        
        return [
            {
                "id": row[0], "user_id": row[1], "title": row[2], "message": row[3],
                "type": row[4], "is_read": bool(row[5]), "created_at": row[6]
            }
            for row in rows
        ]

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
        await db.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Bildirim bulunamadı")
        
        return {"message": "Bildirim okundu olarak işaretlendi"}

@api_router.put("/notifications/read-all")
async def mark_all_notifications_read(user_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0", (user_id,))
        await db.commit()
        return {"message": "Tüm bildirimler okundu olarak işaretlendi"}

@api_router.delete("/notifications/{notification_id}")
async def delete_notification(notification_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM notifications WHERE id = ?", (notification_id,))
        await db.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Bildirim bulunamadı")
        
        return {"message": "Bildirim silindi"}

# Health check
@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "sqlite",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# Include router and middleware
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
