from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
import json
import aiosqlite
import io
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum
from contextlib import asynccontextmanager
import asyncio

# Import custom handlers
try:
    from ldaps_handler import ldaps_handler
    LDAPS_AVAILABLE = True
except Exception as e:
    LDAPS_AVAILABLE = False
    logger.warning(f"LDAPS not available: {e}")

try:
    from jira_client import jira_client
    JIRA_AVAILABLE = True
except Exception as e:
    JIRA_AVAILABLE = False
    logger.warning(f"Jira client not available: {e}")

try:
    from report_exporter import report_exporter
    REPORTS_AVAILABLE = True
except Exception as e:
    REPORTS_AVAILABLE = False
    logger.warning(f"Report exporter not available: {e}")

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

# Global SSE connections manager
class NotificationManager:
    def __init__(self):
        self.active_connections: dict[str, List[asyncio.Queue]] = {}
    
    async def connect(self, user_id: str) -> asyncio.Queue:
        """Add a new SSE connection for a user"""
        queue = asyncio.Queue()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(queue)
        logger.info(f"SSE client connected for user {user_id}")
        return queue
    
    def disconnect(self, user_id: str, queue: asyncio.Queue):
        """Remove an SSE connection"""
        if user_id in self.active_connections:
            if queue in self.active_connections[user_id]:
                self.active_connections[user_id].remove(queue)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"SSE client disconnected for user {user_id}")
    
    async def send_notification(self, user_id: str, notification: dict):
        """Send notification to all connected clients of a user"""
        if user_id in self.active_connections:
            for queue in self.active_connections[user_id]:
                await queue.put(notification)
            logger.info(f"Notification sent to {len(self.active_connections[user_id])} clients for user {user_id}")

notification_manager = NotificationManager()

async def init_db():
    """Initialize SQLite database with required tables"""
    DATA_DIR.mkdir(exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Enable WAL mode for better concurrency
        await db.execute('PRAGMA journal_mode=WAL')
        await db.execute('PRAGMA synchronous=NORMAL')
        await db.execute('PRAGMA cache_size=10000')
        
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
                assigned_to TEXT,
                status TEXT NOT NULL,
                priority TEXT NOT NULL,
                due_date TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (assigned_to) REFERENCES users(id)
            )
        ''')
        
        # Add assigned_to column if not exists (for existing databases)
        try:
            await db.execute('ALTER TABLE tasks ADD COLUMN assigned_to TEXT')
        except:
            pass  # Column already exists
        
        # Add email column to users if not exists
        try:
            await db.execute('ALTER TABLE users ADD COLUMN email TEXT')
        except:
            pass  # Column already exists
        
        # Add password_hash column for LDAPS fallback (optional)
        try:
            await db.execute('ALTER TABLE users ADD COLUMN password_hash TEXT')
        except:
            pass  # Column already exists
        
        # Add role column to users
        try:
            await db.execute('ALTER TABLE users ADD COLUMN role TEXT DEFAULT "user"')
        except:
            pass  # Column already exists
        
        # Audit Logs table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT,
                details TEXT,
                ip_address TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Create index for faster audit log queries
        try:
            await db.execute('CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_logs(user_id)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_logs(created_at)')
        except:
            pass
        
        # User Jira Mapping table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_jira_mapping (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                jira_username TEXT,
                jira_email TEXT,
                jira_account_id TEXT,
                last_synced TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Jira Tasks Cache table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS jira_tasks_cache (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                jira_key TEXT NOT NULL,
                jira_id TEXT NOT NULL,
                summary TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL,
                priority TEXT,
                assignee TEXT,
                issue_type TEXT,
                jira_url TEXT,
                raw_data TEXT,
                last_synced TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Create index for Jira cache
        try:
            await db.execute('CREATE INDEX IF NOT EXISTS idx_jira_user_id ON jira_tasks_cache(user_id)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_jira_key ON jira_tasks_cache(jira_key)')
        except:
            pass
        
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

class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"

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
    email: str
    device_id: str

class UserLogin(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
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
    assigned_to: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[str] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    project_id: Optional[str] = None
    assigned_to: Optional[str] = None
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

async def log_audit(
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None
):
    """Log audit trail asynchronously"""
    try:
        audit_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """INSERT INTO audit_logs (id, user_id, action, resource_type, resource_id, details, ip_address, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (audit_id, user_id, action, resource_type, resource_id, details, ip_address, created_at)
            )
            await db.commit()
    except Exception as e:
        logger.error(f"Audit log error: {e}")
        # Don't fail the main operation if audit logging fails

def row_to_dict(row, columns):
    """Convert SQLite row to dictionary"""
    return dict(zip(columns, row))

async def get_db():
    """Get database connection"""
    return await aiosqlite.connect(DB_PATH)

# ============== AUTH ROUTES ==============

@api_router.post("/auth/ldap-login", response_model=UserResponse)
async def ldap_login(user_data: UserLogin):
    """
    LDAPS Authentication endpoint
    Authenticates user against LDAP server, creates/updates local user record
    """
    if not LDAPS_AVAILABLE:
        raise HTTPException(status_code=503, detail="LDAPS authentication not configured")
    
    if not user_data.username or not user_data.password:
        raise HTTPException(status_code=400, detail="Kullanıcı adı ve şifre gerekli")
    
    # Authenticate against LDAPS
    ldap_user_info = ldaps_handler.authenticate_user(user_data.username, user_data.password)
    
    if not ldap_user_info:
        raise HTTPException(status_code=401, detail="Geçersiz kullanıcı adı veya şifre")
    
    # Check/create user in local database
    async with aiosqlite.connect(DB_PATH) as db:
        # Try to find by username or email
        cursor = await db.execute(
            "SELECT id, name, email, device_id, categories, created_at FROM users WHERE name = ? OR email = ?",
            (user_data.username, user_data.email)
        )
        existing = await cursor.fetchone()
        
        if existing:
            # Update last login and email if needed
            await db.execute(
                "UPDATE users SET email = ? WHERE id = ?",
                (user_data.email, existing[0])
            )
            await db.commit()
            
            return UserResponse(
                id=existing[0],
                name=existing[1],
                email=user_data.email,
                device_id=existing[3],
                categories=json.loads(existing[4]),
                created_at=existing[5]
            )
        
        # Create new user from LDAP info
        user_id = str(uuid.uuid4())
        device_id = str(uuid.uuid4())  # Generate device ID for LDAP users
        created_at = datetime.now(timezone.utc).isoformat()
        categories_json = json.dumps(DEFAULT_CATEGORIES)
        
        await db.execute(
            "INSERT INTO users (id, name, email, device_id, categories, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, user_data.username, user_data.email, device_id, categories_json, created_at)
        )
        
        # Create welcome notification
        notif_id = str(uuid.uuid4())
        await db.execute(
            "INSERT INTO notifications (id, user_id, title, message, type, is_read, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (notif_id, user_id, "Hoş Geldiniz!", f"QA Task Manager'a hoş geldiniz, {user_data.username}!", "success", 0, created_at)
        )
        
        await db.commit()
        
        logger.info(f"New LDAP user created: {user_data.username}")
        
        return UserResponse(
            id=user_id,
            name=user_data.username,
            email=user_data.email,
            device_id=device_id,
            categories=DEFAULT_CATEGORIES,
            created_at=created_at
        )

@api_router.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register new user with device_id (fallback for non-LDAP)"""
    if not user_data.name or not user_data.name.strip():
        raise HTTPException(status_code=400, detail="İsim boş olamaz")
    
    if not user_data.device_id:
        raise HTTPException(status_code=400, detail="Cihaz kimliği gerekli")
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if device already registered
        cursor = await db.execute(
            "SELECT id, name, email, device_id, categories, created_at FROM users WHERE device_id = ?",
            (user_data.device_id,)
        )
        existing = await cursor.fetchone()
        
        if existing:
            return UserResponse(
                id=existing[0],
                name=existing[1],
                email=existing[2],
                device_id=existing[3],
                categories=json.loads(existing[4]),
                created_at=existing[5]
            )
        
        # Create new user
        user_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        categories_json = json.dumps(DEFAULT_CATEGORIES)
        
        await db.execute(
            "INSERT INTO users (id, name, email, device_id, categories, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, user_data.name.strip(), user_data.email, user_data.device_id, categories_json, created_at)
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
            email=user_data.email,
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
            "SELECT id, name, email, device_id, categories, created_at FROM users WHERE device_id = ?",
            (device_id,)
        )
        user = await cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="Cihaz kayıtlı değil")
        
        return UserResponse(
            id=user[0],
            name=user[1],
            email=user[2],
            device_id=user[3],
            categories=json.loads(user[4]),
            created_at=user[5]
        )

# ============== USER ROUTES ==============

@api_router.get("/users", response_model=List[dict])
async def get_all_users():
    """Get all registered users for team assignment"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, created_at FROM users ORDER BY name ASC"
        )
        rows = await cursor.fetchall()
        
        return [
            {"id": row[0], "name": row[1], "created_at": row[2]}
            for row in rows
        ]

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
        # Single query with LEFT JOIN to avoid N+1 problem
        cursor = await db.execute(
            """SELECT p.id, p.name, p.description, p.user_id, p.created_at, COUNT(t.id) as task_count
               FROM projects p
               LEFT JOIN tasks t ON p.id = t.project_id
               WHERE p.user_id = ?
               GROUP BY p.id, p.name, p.description, p.user_id, p.created_at""",
            (user_id,)
        )
        rows = await cursor.fetchall()
        
        return [
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "user_id": row[3],
                "created_at": row[4],
                "task_count": row[5]
            }
            for row in rows
        ]

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
            """INSERT INTO tasks (id, title, description, category_id, project_id, user_id, assigned_to, status, priority, due_date, created_at, completed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (task_id, task.title, task.description or "", task.category_id, task.project_id, user_id, 
             task.assigned_to, TaskStatus.BACKLOG.value, task.priority.value, task.due_date, created_at, None)
        )
        
        # Create notification if task is assigned to someone else
        if task.assigned_to and task.assigned_to != user_id:
            # Get assigner name
            cursor = await db.execute("SELECT name FROM users WHERE id = ?", (user_id,))
            assigner = await cursor.fetchone()
            assigner_name = assigner[0] if assigner else "Birisi"
            
            notif_id = str(uuid.uuid4())
            await db.execute(
                "INSERT INTO notifications (id, user_id, title, message, type, is_read, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (notif_id, task.assigned_to, "Yeni Görev Atandı", f"{assigner_name} size bir görev atadı: {task.title}", "info", 0, created_at)
            )
            
            # Send real-time notification via SSE
            await notification_manager.send_notification(task.assigned_to, {
                "id": notif_id,
                "user_id": task.assigned_to,
                "title": "Yeni Görev Atandı",
                "message": f"{assigner_name} size bir görev atadı: {task.title}",
                "type": "info",
                "is_read": False,
                "created_at": created_at
            })
        
        await db.commit()
    
    return {
        "id": task_id,
        "title": task.title,
        "description": task.description or "",
        "category_id": task.category_id,
        "project_id": task.project_id,
        "user_id": user_id,
        "assigned_to": task.assigned_to,
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
    priority: Optional[str] = None,
    assigned_to_me: Optional[bool] = None
):
    # If assigned_to_me is True, show tasks assigned to user (not created by them)
    # Otherwise show tasks created by user OR assigned to them
    if assigned_to_me:
        query = "SELECT id, title, description, category_id, project_id, user_id, assigned_to, status, priority, due_date, created_at, completed_at FROM tasks WHERE assigned_to = ?"
        params = [user_id]
    else:
        query = "SELECT id, title, description, category_id, project_id, user_id, assigned_to, status, priority, due_date, created_at, completed_at FROM tasks WHERE (user_id = ? OR assigned_to = ?)"
        params = [user_id, user_id]
    
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
        
        # Get user names for assigned_to
        user_ids = set()
        for row in rows:
            if row[5]:  # user_id
                user_ids.add(row[5])
            if row[6]:  # assigned_to
                user_ids.add(row[6])
        
        user_map = {}
        if user_ids:
            placeholders = ','.join('?' * len(user_ids))
            cursor = await db.execute(f"SELECT id, name FROM users WHERE id IN ({placeholders})", list(user_ids))
            for u in await cursor.fetchall():
                user_map[u[0]] = u[1]
        
        return [
            {
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "category_id": row[3],
                "project_id": row[4],
                "user_id": row[5],
                "assigned_to": row[6],
                "assigned_to_name": user_map.get(row[6]) if row[6] else None,
                "created_by_name": user_map.get(row[5]) if row[5] else None,
                "status": row[7],
                "priority": row[8],
                "due_date": row[9],
                "created_at": row[10],
                "completed_at": row[11]
            }
            for row in rows
        ]

@api_router.get("/tasks/{task_id}", response_model=dict)
async def get_task(task_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, title, description, category_id, project_id, user_id, assigned_to, status, priority, due_date, created_at, completed_at FROM tasks WHERE id = ?",
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
            "assigned_to": row[6],
            "status": row[7],
            "priority": row[8],
            "due_date": row[9],
            "created_at": row[10],
            "completed_at": row[11]
        }

@api_router.put("/tasks/{task_id}", response_model=dict)
async def update_task(task_id: str, task_update: TaskUpdate, user_id: Optional[str] = None):
    async with aiosqlite.connect(DB_PATH) as db:
        # Get current task to check for assignment changes
        cursor = await db.execute("SELECT id, title, assigned_to FROM tasks WHERE id = ?", (task_id,))
        current_task = await cursor.fetchone()
        if not current_task:
            raise HTTPException(status_code=404, detail="Görev bulunamadı")
        
        old_assigned_to = current_task[2]
        task_title = current_task[1]
        
        updates = []
        params = []
        
        if task_update.title is not None:
            updates.append("title = ?")
            params.append(task_update.title)
            task_title = task_update.title
        if task_update.description is not None:
            updates.append("description = ?")
            params.append(task_update.description)
        if task_update.category_id is not None:
            updates.append("category_id = ?")
            params.append(task_update.category_id)
        if task_update.project_id is not None:
            updates.append("project_id = ?")
            params.append(task_update.project_id)
        if task_update.assigned_to is not None:
            updates.append("assigned_to = ?")
            params.append(task_update.assigned_to if task_update.assigned_to != "none" else None)
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
        
        # Create notification if assigned_to changed
        new_assigned = task_update.assigned_to if task_update.assigned_to != "none" else None
        if task_update.assigned_to is not None and new_assigned != old_assigned_to and new_assigned and user_id:
            # Get assigner name
            cursor = await db.execute("SELECT name FROM users WHERE id = ?", (user_id,))
            assigner = await cursor.fetchone()
            assigner_name = assigner[0] if assigner else "Birisi"
            
            notif_id = str(uuid.uuid4())
            notif_created_at = datetime.now(timezone.utc).isoformat()
            await db.execute(
                "INSERT INTO notifications (id, user_id, title, message, type, is_read, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (notif_id, new_assigned, "Görev Atandı", f"{assigner_name} size bir görev atadı: {task_title}", "info", 0, notif_created_at)
            )
            
            # Send real-time notification via SSE
            await notification_manager.send_notification(new_assigned, {
                "id": notif_id,
                "user_id": new_assigned,
                "title": "Görev Atandı",
                "message": f"{assigner_name} size bir görev atadı: {task_title}",
                "type": "info",
                "is_read": False,
                "created_at": notif_created_at
            })
        await db.commit()
        
        cursor = await db.execute(
            "SELECT id, title, description, category_id, project_id, user_id, assigned_to, status, priority, due_date, created_at, completed_at FROM tasks WHERE id = ?",
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
            "assigned_to": row[6],
            "status": row[7],
            "priority": row[8],
            "due_date": row[9],
            "created_at": row[10],
            "completed_at": row[11]
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
        
        cursor = await db.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status IN (?, ?)", (user_id, TaskStatus.BACKLOG.value, TaskStatus.TODAY_PLANNED.value))
        todo_tasks = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = ?", (user_id, TaskStatus.TODAY_PLANNED.value))
        today_planned_tasks = (await cursor.fetchone())[0]
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
        
        # Today planned - tasks with status "today_planned"
        cursor = await db.execute(
            """SELECT id, title, description, category_id, project_id, status, priority, due_date 
               FROM tasks 
               WHERE user_id = ? AND status = ?
               ORDER BY priority DESC, due_date ASC""",
            (user_id, TaskStatus.TODAY_PLANNED.value)
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

@api_router.get("/notifications/stream")
async def notification_stream(request: Request, user_id: str):
    """Server-Sent Events endpoint for real-time notifications"""
    
    async def event_generator():
        queue = await notification_manager.connect(user_id)
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected', 'message': 'SSE bağlantısı kuruldu'})}\n\n"
            
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                
                try:
                    # Wait for notification with timeout
                    notification = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(notification)}\n\n"
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield f": heartbeat\n\n"
                except Exception as e:
                    logger.error(f"Error in SSE stream: {e}")
                    break
        finally:
            notification_manager.disconnect(user_id, queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# ============== ADMIN ROUTES ==============

@api_router.get("/admin/users", response_model=List[dict])
async def admin_get_all_users():
    """Admin endpoint: Get all users with full details"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, device_id, created_at FROM users ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()
        
        result = []
        for row in rows:
            user_id = row[0]
            # Get task count for each user
            cursor2 = await db.execute(
                "SELECT COUNT(*) FROM tasks WHERE user_id = ?", (user_id,)
            )
            task_count = (await cursor2.fetchone())[0]
            
            result.append({
                "id": user_id,
                "name": row[1],
                "device_id": row[2],
                "created_at": row[3],
                "task_count": task_count
            })
        
        return result

@api_router.post("/admin/users", response_model=UserResponse)
async def admin_create_user(user_data: UserCreate):
    """Admin endpoint: Manually create a new user"""
    if not user_data.name or not user_data.name.strip():
        raise HTTPException(status_code=400, detail="İsim boş olamaz")
    
    if not user_data.device_id:
        raise HTTPException(status_code=400, detail="Cihaz kimliği gerekli")
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if device already exists
        cursor = await db.execute(
            "SELECT id FROM users WHERE device_id = ?", (user_data.device_id,)
        )
        existing = await cursor.fetchone()
        
        if existing:
            raise HTTPException(status_code=400, detail="Bu cihaz kimliği zaten kayıtlı")
        
        # Create new user
        user_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        categories_json = json.dumps(DEFAULT_CATEGORIES)
        
        await db.execute(
            "INSERT INTO users (id, name, device_id, categories, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, user_data.name.strip(), user_data.device_id, categories_json, created_at)
        )
        await db.commit()
        
        return UserResponse(
            id=user_id,
            name=user_data.name.strip(),
            device_id=user_data.device_id,
            categories=DEFAULT_CATEGORIES,
            created_at=created_at
        )

@api_router.put("/admin/users/{user_id}", response_model=UserResponse)
async def admin_update_user(user_id: str, name: str):
    """Admin endpoint: Update user name"""
    if not name or not name.strip():
        raise HTTPException(status_code=400, detail="İsim boş olamaz")
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, device_id, categories, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        user = await cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        await db.execute(
            "UPDATE users SET name = ? WHERE id = ?",
            (name.strip(), user_id)
        )
        await db.commit()
        
        return UserResponse(
            id=user[0],
            name=name.strip(),
            device_id=user[2],
            categories=json.loads(user[3]),
            created_at=user[4]
        )

@api_router.delete("/admin/users/{user_id}")
async def admin_delete_user(user_id: str):
    """Admin endpoint: Delete a user and all their data"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if user exists
        cursor = await db.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        user = await cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        # Delete user's tasks
        await db.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
        
        # Delete user's projects
        await db.execute("DELETE FROM projects WHERE user_id = ?", (user_id,))
        
        # Delete user's notifications
        await db.execute("DELETE FROM notifications WHERE user_id = ?", (user_id,))
        
        # Delete user
        await db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        await db.commit()
        
        return {"message": f"Kullanıcı ve tüm verileri silindi"}

# ============== JIRA INTEGRATION ROUTES ==============

@api_router.get("/jira/issues")
async def get_jira_issues(user_id: str, username: Optional[str] = None, email: Optional[str] = None):
    """Get Jira issues assigned to user"""
    if not JIRA_AVAILABLE:
        raise HTTPException(status_code=503, detail="Jira integration not available")
    
    try:
        # Get user info
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT name, email FROM users WHERE id = ?",
                (user_id,)
            )
            user = await cursor.fetchone()
            
            if not user:
                raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
            
            # Use provided username/email or get from user record
            search_username = username or user[0]
            search_email = email or user[1]
        
        # Try to fetch issues by username first, then email
        issues = await jira_client.get_issues_by_assignee(search_username)
        
        if not issues and search_email:
            issues = await jira_client.get_issues_by_assignee(search_email)
        
        # Transform issues
        transformed_issues = [jira_client.transform_issue(issue) for issue in issues]
        
        return {
            "total": len(transformed_issues),
            "issues": transformed_issues
        }
    
    except Exception as e:
        logger.error(f"Error fetching Jira issues: {e}")
        raise HTTPException(status_code=500, detail=f"Jira issues alınırken hata: {str(e)}")

# ============== REPORT EXPORT ROUTES ==============

@api_router.post("/reports/export")
async def export_report(
    format: str,  # 'pdf', 'excel', 'word'
    user_id: str,
    include_tasks: bool = True,
    include_stats: bool = True
):
    """Export report in specified format"""
    if not REPORTS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Report export not available")
    
    if format not in ['pdf', 'excel', 'word']:
        raise HTTPException(status_code=400, detail="Format must be 'pdf', 'excel', or 'word'")
    
    try:
        # Gather data
        report_data = {}
        
        async with aiosqlite.connect(DB_PATH) as db:
            # Get stats
            if include_stats:
                cursor = await db.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ?", (user_id,))
                total_tasks = (await cursor.fetchone())[0]
                
                cursor = await db.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = ?", (user_id, TaskStatus.COMPLETED.value))
                completed_tasks = (await cursor.fetchone())[0]
                
                cursor = await db.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = ?", (user_id, TaskStatus.IN_PROGRESS.value))
                in_progress_tasks = (await cursor.fetchone())[0]
                
                cursor = await db.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status IN (?, ?)", (user_id, TaskStatus.BACKLOG.value, TaskStatus.TODAY_PLANNED.value))
                todo_tasks = (await cursor.fetchone())[0]
                
                now = datetime.now(timezone.utc).isoformat()
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM tasks WHERE user_id = ? AND due_date < ? AND due_date IS NOT NULL AND status != ?",
                    (user_id, now, TaskStatus.COMPLETED.value)
                )
                overdue_tasks = (await cursor.fetchone())[0]
                
                report_data['stats'] = {
                    'total_tasks': total_tasks,
                    'completed_tasks': completed_tasks,
                    'in_progress_tasks': in_progress_tasks,
                    'todo_tasks': todo_tasks,
                    'overdue_tasks': overdue_tasks,
                    'completion_rate': round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1)
                }
            
            # Get tasks
            if include_tasks:
                cursor = await db.execute(
                    "SELECT id, title, description, category_id, status, priority, created_at, completed_at FROM tasks WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,)
                )
                rows = await cursor.fetchall()
                
                report_data['tasks'] = [
                    {
                        'id': row[0],
                        'title': row[1],
                        'description': row[2],
                        'category_id': row[3],
                        'status': row[4],
                        'priority': row[5],
                        'created_at': row[6],
                        'completed_at': row[7]
                    }
                    for row in rows
                ]
        
        # Generate report
        if format == 'pdf':
            content = report_exporter.generate_pdf_report(report_data)
            media_type = "application/pdf"
            filename = f"qa_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        elif format == 'excel':
            content = report_exporter.generate_excel_report(report_data)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"qa_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        elif format == 'word':
            content = report_exporter.generate_word_report(report_data)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"qa_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        
        # Return file
        return StreamingResponse(
            io.BytesIO(content),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=f"Rapor oluşturulurken hata: {str(e)}")

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
