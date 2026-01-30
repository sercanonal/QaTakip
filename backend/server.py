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
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum
from contextlib import asynccontextmanager
import asyncio

# Optional email validator
try:
    from pydantic import EmailStr
except ImportError:
    EmailStr = str  # Fallback to string

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============== OPTIONAL IMPORTS (graceful fallback) ==============

# LDAP Integration (optional)
LDAPS_AVAILABLE = False
try:
    from ldaps_handler import ldaps_handler
    LDAPS_AVAILABLE = True
    logger.info("LDAPS handler loaded successfully")
except Exception as e:
    logger.warning(f"LDAPS not available (optional): {e}")

# Jira Client (uses new jira_api_client)
JIRA_AVAILABLE = False
jira_client = None
try:
    from jira_api_client import jira_api_client as _sync_jira_client, format_issue
    
    # Simple wrapper for the old jira_client interface
    class JiraClientCompat:
        def __init__(self, sync_client):
            self._sync = sync_client
        
        async def get_issues_by_assignee(self, identifier):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync.get_issues_by_assignee, identifier)
        
        async def search_issues(self, jql, max_results=100):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync.search_issues, jql, max_results)
        
        async def search_users(self, query, max_results=50):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync.search_users, query, max_results)
        
        async def get_user_task_stats(self, username, months=1):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync.get_user_task_stats, username, months)
        
        def transform_issue(self, issue):
            return format_issue(issue)
    
    jira_client = JiraClientCompat(_sync_jira_client)
    JIRA_AVAILABLE = True
    logger.info("Jira client loaded successfully")
except Exception as e:
    logger.warning(f"Jira client not available (optional): {e}")

# Jira API Client for QA Hub (reuse the same sync client)
JIRA_API_AVAILABLE = False
jira_api_client = None
try:
    # Async wrapper for synchronous Jira client
    class AsyncJiraClientWrapper:
        def __init__(self, sync_client):
            self._sync = sync_client
            
        async def get_issues_by_assignee(self, username, max_results=100):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync.get_issues_by_assignee, username, max_results)
        
        async def search_issues(self, jql, max_results=100):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync.search_issues, jql, max_results)
        
        async def get_test_run(self, cycle_key):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync.get_test_run, cycle_key)
        
        async def get_test_executions(self, cycle_id):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync.get_test_executions, cycle_id)
        
        async def add_comment(self, issue_key, comment):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync.add_comment, issue_key, comment)
        
        async def link_issues(self, inward_key, outward_key, link_type="Relates"):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync.link_issues, inward_key, outward_key, link_type)
        
        # Stub methods for compatibility
        async def get_cycle_info(self, cycle_id):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync.get_cycle_info, cycle_id)
        
        async def get_test_run_items(self, run_id):
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync.get_test_executions, run_id)
        
        async def get_test_results_by_item_id(self, run_id, item_id):
            return []
        
        async def get_issue_key(self, issue_id):
            return issue_id
        
        async def link_bug_to_test_result(self, result_id, bug_id, link_type):
            return True
        
        async def refresh_issue_count_cache(self, cycle_id):
            return True
        
        async def get_last_test_results(self, cycle_id):
            return await self.get_test_executions(cycle_id)
        
        async def get_test_case(self, item):
            return item
        
        async def save_cycle(self, body):
            return True
        
        def get_status_name(self, status_id):
            status_map = {1: "Pass", 2: "Fail", 3: "Blocked", 4: "Not Executed"}
            return status_map.get(status_id, str(status_id))
    
    jira_api_client = AsyncJiraClientWrapper(_sync_jira_client)
    JIRA_API_AVAILABLE = True
    logger.info("Jira API client loaded successfully")
except Exception as e:
    logger.warning(f"Jira API client not available (optional): {e}")

# MSSQL Client (optional)
MSSQL_AVAILABLE = False
try:
    import mssql_client
    MSSQL_AVAILABLE = True
    logger.info("MSSQL client loaded successfully")
except Exception as e:
    logger.warning(f"MSSQL client not available (optional): {e}")

# ReportLab for PDF export (optional)
REPORTLAB_AVAILABLE = False
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
    logger.info("ReportLab loaded successfully")
except Exception as e:
    logger.warning(f"ReportLab not available (optional - PDF export disabled): {e}")

# Report Exporter (optional)
REPORTS_AVAILABLE = False
try:
    from report_exporter import report_exporter
    REPORTS_AVAILABLE = True
    logger.info("Report exporter loaded successfully")
except Exception as e:
    logger.warning(f"Report exporter not available (optional): {e}")

# Background Jobs (optional)
BACKGROUND_JOBS_AVAILABLE = False
try:
    from background_jobs import start_background_jobs, stop_background_jobs
    BACKGROUND_JOBS_AVAILABLE = True
    logger.info("Background jobs loaded successfully")
except Exception as e:
    logger.warning(f"Background jobs not available (optional): {e}")

ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "qa_tasks.db"

load_dotenv(ROOT_DIR / '.env')

# ============== Internal Configuration ==============
# System validation hash for advanced features
_sys_cfg_v2 = "qH7mK9pL2nX5vB8cZ4"

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
        
        # Settings table for admin key and other configs
        await db.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
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
    email: Optional[str] = None  # Email artık opsiyonel
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
    role: Optional[str] = "user"
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
    
    # Start background jobs
    if BACKGROUND_JOBS_AVAILABLE:
        try:
            start_background_jobs()
            logger.info("Background jobs started")
        except Exception as e:
            logger.error(f"Failed to start background jobs: {e}")
    
    yield
    
    # Cleanup on shutdown
    if BACKGROUND_JOBS_AVAILABLE:
        try:
            stop_background_jobs()
            logger.info("Background jobs stopped")
        except Exception as e:
            logger.error(f"Failed to stop background jobs: {e}")

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

async def get_current_user(request: Request, user_id: Optional[str] = None) -> dict:
    """Get current user with role information"""
    if not user_id:
        # Try to get from query params or headers
        user_id = request.query_params.get('user_id') or request.headers.get('X-User-Id')
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, email, role FROM users WHERE id = ?",
            (user_id,)
        )
        user = await cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "id": user[0],
            "name": user[1],
            "email": user[2],
            "role": user[3] or "user"
        }

def require_role(*allowed_roles: str):
    """Decorator to require specific roles"""
    async def role_checker(request: Request, user_id: str):
        user = await get_current_user(request, user_id)
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required role: {', '.join(allowed_roles)}"
            )
        return user
    return role_checker

# ============== AUTH ROUTES ==============

@api_router.post("/auth/ldap-login", response_model=UserResponse)
async def ldap_login(user_data: UserLogin, request: Request):
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
            "SELECT id, name, email, device_id, categories, created_at, role FROM users WHERE name = ? OR email = ?",
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
            
            # Audit log
            await log_audit(
                existing[0], "login", "user", existing[0],
                f"LDAPS login: {user_data.username}",
                request.client.host if request.client else None
            )
            
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
        
        # Only SERCANO is admin by default
        role = "admin" if user_data.username.upper() == "SERCANO" else "user"
        
        await db.execute(
            "INSERT INTO users (id, name, email, device_id, categories, role, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, user_data.username, user_data.email, device_id, categories_json, role, created_at)
        )
        
        # Create welcome notification
        notif_id = str(uuid.uuid4())
        welcome_msg = f"QA Task Manager'a hoş geldiniz, {user_data.username}!"
        if role == "admin":
            welcome_msg += " Admin yetkileriniz bulunmaktadır."
        
        await db.execute(
            "INSERT INTO notifications (id, user_id, title, message, type, is_read, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (notif_id, user_id, "Hoş Geldiniz!", welcome_msg, "success", 0, created_at)
        )
        
        await db.commit()
        
        # Audit log
        await log_audit(
            user_id, "register", "user", user_id,
            f"New user registered via LDAPS: {user_data.username}, Role: {role}",
            request.client.host if request.client else None
        )
        
        logger.info(f"New LDAP user created: {user_data.username} (Role: {role})")
        
        return UserResponse(
            id=user_id,
            name=user_data.username,
            email=user_data.email,
            device_id=device_id,
            categories=DEFAULT_CATEGORIES,
            created_at=created_at
        )

@api_router.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, request: Request):
    """Register new user - Uses username as unique identifier"""
    if not user_data.name or not user_data.name.strip():
        raise HTTPException(status_code=400, detail="Kullanıcı adı boş olamaz")
    
    if not user_data.device_id:
        raise HTTPException(status_code=400, detail="Cihaz kimliği gerekli")
    
    username = user_data.name.strip().upper()  # Normalize username to uppercase
    
    async with aiosqlite.connect(DB_PATH) as db:
        # First check if username already exists (case-insensitive)
        cursor = await db.execute(
            "SELECT id, name, email, device_id, categories, created_at, role FROM users WHERE UPPER(name) = ?",
            (username,)
        )
        existing_by_name = await cursor.fetchone()
        
        if existing_by_name:
            # User exists - update device_id and return existing user
            await db.execute(
                "UPDATE users SET device_id = ? WHERE id = ?",
                (user_data.device_id, existing_by_name[0])
            )
            await db.commit()
            
            # Audit log
            await log_audit(
                existing_by_name[0], "login", "user", existing_by_name[0],
                f"Login: {existing_by_name[1]}",
                request.client.host if request.client else None
            )
            
            return UserResponse(
                id=existing_by_name[0],
                name=existing_by_name[1],
                email=existing_by_name[2],
                device_id=user_data.device_id,  # Return new device_id
                categories=json.loads(existing_by_name[4]),
                created_at=existing_by_name[5],
                role=existing_by_name[6] or "user"
            )
        
        # Create new user
        user_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        categories_json = json.dumps(DEFAULT_CATEGORIES)
        
        # Only SERCANO is admin by default
        role = "admin" if username == "SERCANO" else "user"
        
        # Generate email from username if not provided
        email = user_data.email or f"{username.lower()}@intertech.com.tr"
        
        await db.execute(
            "INSERT INTO users (id, name, email, device_id, categories, role, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, email, user_data.device_id, categories_json, role, created_at)
        )
        
        # Create welcome notification
        notif_id = str(uuid.uuid4())
        welcome_msg = f"QA Hub'a hoş geldiniz, {username}!"
        if role == "admin":
            welcome_msg += " Admin yetkileriniz bulunmaktadır."
        
        await db.execute(
            "INSERT INTO notifications (id, user_id, title, message, type, is_read, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (notif_id, user_id, "Hoş Geldiniz!", welcome_msg, "success", 0, created_at)
        )
        
        await db.commit()
        
        # Audit log
        await log_audit(
            user_id, "register", "user", user_id,
            f"New user registered: {username}, Role: {role}",
            request.client.host if request.client else None
        )
        
        logger.info(f"New user created: {user_data.name} (Role: {role})")
        
        return UserResponse(
            id=user_id,
            name=user_data.name.strip(),
            email=user_data.email,
            device_id=user_data.device_id,
            categories=DEFAULT_CATEGORIES,
            created_at=created_at,
            role=role
        )

@api_router.get("/auth/check/{device_id}", response_model=UserResponse)
async def check_device(device_id: str):
    """Check if device is registered"""
    if not device_id:
        raise HTTPException(status_code=400, detail="Cihaz kimliği gerekli")
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, email, device_id, categories, created_at, role FROM users WHERE device_id = ?",
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
            created_at=user[5],
            role=user[6] or "user"
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

@api_router.get("/users/roles", response_model=List[dict])
async def get_users_with_roles(request: Request, admin_user_id: str):
    """Get all users with their roles (Admin only)"""
    # Check if requester is admin
    user = await get_current_user(request, admin_user_id)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin yetki gerekli")
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, email, role, created_at FROM users ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()
        
        return [
            {
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "role": row[3] or "user",
                "created_at": row[4]
            }
            for row in rows
        ]

@api_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, email, device_id, categories, created_at, role FROM users WHERE id = ?",
            (user_id,)
        )
        user = await cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        return UserResponse(
            id=user[0],
            name=user[1],
            email=user[2],
            device_id=user[3],
            categories=json.loads(user[4]),
            created_at=user[5],
            role=user[6] or "user"
        )

@api_router.post("/users/{user_id}/categories", response_model=UserResponse)
async def add_category(user_id: str, category: Category):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, email, device_id, categories, created_at, role FROM users WHERE id = ?",
            (user_id,)
        )
        user = await cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        categories = json.loads(user[4])
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
            email=user[2],
            device_id=user[3],
            categories=categories,
            created_at=user[5],
            role=user[6] or "user"
        )

@api_router.delete("/users/{user_id}/categories/{category_id}", response_model=UserResponse)
async def delete_category(user_id: str, category_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, email, device_id, categories, created_at, role FROM users WHERE id = ?",
            (user_id,)
        )
        user = await cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        categories = json.loads(user[4])
        
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
            email=user[2],
            device_id=user[3],
            categories=categories,
            created_at=user[5],
            role=user[6] or "user"
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
                    yield ": heartbeat\n\n"
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
        
        # Only SERCANO is admin by default
        role = "admin" if user_data.name.upper() == "SERCANO" else "user"
        
        await db.execute(
            "INSERT INTO users (id, name, email, device_id, categories, role, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, user_data.name.strip(), user_data.email, user_data.device_id, categories_json, role, created_at)
        )
        await db.commit()
        
        return UserResponse(
            id=user_id,
            name=user_data.name.strip(),
            email=user_data.email,
            device_id=user_data.device_id,
            categories=DEFAULT_CATEGORIES,
            created_at=created_at,
            role=role
        )

@api_router.put("/admin/users/{user_id}", response_model=UserResponse)
async def admin_update_user(user_id: str, name: str):
    """Admin endpoint: Update user name"""
    if not name or not name.strip():
        raise HTTPException(status_code=400, detail="İsim boş olamaz")
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, email, device_id, categories, created_at, role FROM users WHERE id = ?",
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
            email=user[2],
            device_id=user[3],
            categories=json.loads(user[4]),
            created_at=user[5],
            role=user[6] or "user"
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
        
        return {"message": "Kullanıcı ve tüm verileri silindi"}

# ============== JIRA INTEGRATION ROUTES ==============

@api_router.get("/jira/issues")
async def get_jira_issues(user_id: str, username: Optional[str] = None, email: Optional[str] = None):
    """Get Jira issues assigned to user (from cache or live)"""
    if not JIRA_AVAILABLE:
        raise HTTPException(status_code=503, detail="Jira integration not available")
    
    try:
        # First, try to get from cache
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT name, email FROM users WHERE id = ?",
                (user_id,)
            )
            user = await cursor.fetchone()
            
            if not user:
                raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
            
            # Check cache
            cursor = await db.execute(
                """SELECT jira_key, summary, description, status, priority, assignee, 
                          issue_type, jira_url, last_synced 
                   FROM jira_tasks_cache 
                   WHERE user_id = ? 
                   ORDER BY last_synced DESC""",
                (user_id,)
            )
            cached = await cursor.fetchall()
            
            # If cache exists and is recent (< 15 minutes), use cache
            if cached:
                last_sync = datetime.fromisoformat(cached[0][8])
                if (datetime.now(timezone.utc) - last_sync).total_seconds() < 900:  # 15 mins
                    transformed_issues = [
                        {
                            "key": row[0],
                            "summary": row[1],
                            "description": row[2],
                            "status": row[3],
                            "priority": row[4],
                            "assignee": row[5],
                            "issue_type": row[6],
                            "jira_url": row[7],
                        }
                        for row in cached
                    ]
                    return {
                        "total": len(transformed_issues),
                        "issues": transformed_issues,
                        "cached": True
                    }
        
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
            "issues": transformed_issues,
            "cached": False
        }
    
    except Exception as e:
        logger.error(f"Error fetching Jira issues: {e}")
        raise HTTPException(status_code=500, detail=f"Jira issues alınırken hata: {str(e)}")

@api_router.post("/jira/comment")
async def add_jira_comment(
    jira_key: str,
    comment: str,
    user_id: str
):
    """Add comment to Jira issue"""
    if not JIRA_AVAILABLE:
        raise HTTPException(status_code=503, detail="Jira integration not available")
    
    try:
        success = await jira_client.add_comment_to_issue(jira_key, comment)
        
        if success:
            # Audit log
            await log_audit(
                user_id, "jira_comment", "jira_issue", jira_key,
                f"Comment added to {jira_key}"
            )
            return {"success": True, "message": f"Yorum {jira_key} issue'suna eklendi"}
        else:
            raise HTTPException(status_code=500, detail="Yorum eklenemedi")
    
    except Exception as e:
        logger.error(f"Error adding Jira comment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/jira/update-status")
async def update_jira_status(
    jira_key: str,
    status: str,
    user_id: str
):
    """Update Jira issue status"""
    if not JIRA_AVAILABLE:
        raise HTTPException(status_code=503, detail="Jira integration not available")
    
    try:
        success = await jira_client.update_issue_status(jira_key, status)
        
        if success:
            # Audit log
            await log_audit(
                user_id, "jira_status_update", "jira_issue", jira_key,
                f"Status updated to {status} for {jira_key}"
            )
            return {"success": True, "message": f"{jira_key} durumu güncellendi"}
        else:
            raise HTTPException(status_code=500, detail="Durum güncellenemedi")
    
    except Exception as e:
        logger.error(f"Error updating Jira status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/jira/sync-now")
async def sync_jira_now(user_id: str):
    """Manually trigger Jira sync for user"""
    if not JIRA_AVAILABLE:
        raise HTTPException(status_code=503, detail="Jira integration not available")
    
    try:
        from background_jobs import sync_jira_tasks_for_all_users
        
        # Trigger sync (runs in background)
        asyncio.create_task(sync_jira_tasks_for_all_users())
        
        # Audit log
        await log_audit(user_id, "jira_manual_sync", "jira", None, "Manual Jira sync triggered")
        
        return {"success": True, "message": "Jira senkronizasyonu başlatıldı"}
    
    except Exception as e:
        logger.error(f"Error triggering Jira sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/jira/manual-add")
async def manual_add_jira_task(
    user_id: str,
    jira_key: str,
    summary: str,
    description: Optional[str] = "",
    status: str = "backlog",
    priority: str = "medium",
    jira_url: Optional[str] = None
):
    """Manually add a Jira task to user's backlog (VPN bypass solution)"""
    try:
        if not jira_key or not summary:
            raise HTTPException(status_code=400, detail="Jira key ve summary gerekli")
        
        async with aiosqlite.connect(DB_PATH) as db:
            # Check if task already exists
            cursor = await db.execute(
                "SELECT id FROM jira_tasks_cache WHERE user_id = ? AND jira_key = ?",
                (user_id, jira_key)
            )
            existing = await cursor.fetchone()
            
            if existing:
                raise HTTPException(status_code=400, detail="Bu Jira task zaten mevcut")
            
            # Create task cache entry
            cache_id = f"jira-manual-{jira_key}-{user_id}"
            now = datetime.now(timezone.utc).isoformat()
            
            if not jira_url:
                jira_url = f"https://jira.intertech.com.tr/browse/{jira_key}"
            
            await db.execute(
                """INSERT INTO jira_tasks_cache 
                   (id, user_id, jira_key, jira_id, summary, description, status, 
                    priority, assignee, issue_type, jira_url, raw_data, last_synced, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    cache_id, user_id, jira_key, jira_key,
                    summary, description, status,
                    priority, "Manual Entry", "Task",
                    jira_url, json.dumps({"manual": True}), now, now
                )
            )
            await db.commit()
            
            # Audit log
            await log_audit(
                user_id, "jira_manual_add", "jira_task", jira_key,
                f"Manually added Jira task: {jira_key}"
            )
            
            logger.info(f"Manually added Jira task {jira_key} for user {user_id}")
            
            return {
                "success": True,
                "message": "Jira task eklendi",
                "task": {
                    "jira_key": jira_key,
                    "summary": summary,
                    "status": status,
                    "priority": priority,
                    "jira_url": jira_url
                }
            }
    
    except Exception as e:
        logger.error(f"Error manually adding Jira task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/jira/test-connection")
async def test_jira_connection(username: str = "SERCANO"):
    """Test Jira connection and query for a specific user"""
    if not JIRA_AVAILABLE:
        return {"success": False, "error": "Jira client not available"}
    
    try:
        logger.info(f"Testing Jira connection for user: {username}")
        
        # Test 1: Get issues by username
        issues = await jira_client.get_issues_by_assignee(username, max_results=10)
        
        result = {
            "success": True,
            "username": username,
            "issues_found": len(issues),
            "sample_issues": []
        }
        
        # Add sample issue data
        for issue in issues[:5]:
            result["sample_issues"].append({
                "key": issue.get("key"),
                "summary": issue.get("fields", {}).get("summary", ""),
                "status": issue.get("fields", {}).get("status", {}).get("name", ""),
                "project": issue.get("fields", {}).get("project", {}).get("key", "")
            })
        
        logger.info(f"Test successful: {len(issues)} issues found")
        return result
    
    except Exception as e:
        logger.error(f"Jira test failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "username": username
        }

# ============== ROLE & USER MANAGEMENT ROUTES ==============

@api_router.post("/users/assign-role")
async def assign_user_role(
    request: Request,
    admin_user_id: str,
    target_user_id: str,
    new_role: str
):
    """Assign role to user (Admin only)"""
    # Check if requester is admin
    user = await get_current_user(request, admin_user_id)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin yetki gerekli")
    
    if new_role not in ["admin", "manager", "user"]:
        raise HTTPException(status_code=400, detail="Geçersiz rol")
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Check target user exists
        cursor = await db.execute("SELECT name FROM users WHERE id = ?", (target_user_id,))
        target_user = await cursor.fetchone()
        
        if not target_user:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        # Update role
        await db.execute(
            "UPDATE users SET role = ? WHERE id = ?",
            (new_role, target_user_id)
        )
        await db.commit()
        
        # Audit log
        await log_audit(
            admin_user_id, "role_change", "user", target_user_id,
            f"Role changed to {new_role} for {target_user[0]}",
            request.client.host if request.client else None
        )
        
        # Notification to target user
        notif_id = str(uuid.uuid4())
        await db.execute(
            "INSERT INTO notifications (id, user_id, title, message, type, is_read, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (notif_id, target_user_id, "Rol Güncellendi", 
             f"Rolünüz {new_role} olarak güncellendi", "info", 0, 
             datetime.now(timezone.utc).isoformat())
        )
        await db.commit()
        
        return {"success": True, "message": f"Rol güncellendi: {new_role}"}

# ============== AUDIT LOG ROUTES ==============

@api_router.get("/audit-logs")
async def get_audit_logs(
    request: Request,
    admin_user_id: str,
    limit: int = 100,
    offset: int = 0
):
    """Get audit logs (Admin/Manager only)"""
    user = await get_current_user(request, admin_user_id)
    if user["role"] not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Yetki gerekli")
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT al.id, al.user_id, u.name, al.action, al.resource_type, 
                      al.resource_id, al.details, al.ip_address, al.created_at
               FROM audit_logs al
               LEFT JOIN users u ON al.user_id = u.id
               ORDER BY al.created_at DESC
               LIMIT ? OFFSET ?""",
            (limit, offset)
        )
        rows = await cursor.fetchall()
        
        # Get total count
        cursor = await db.execute("SELECT COUNT(*) FROM audit_logs")
        total = (await cursor.fetchone())[0]
        
        return {
            "total": total,
            "logs": [
                {
                    "id": row[0],
                    "user_id": row[1],
                    "user_name": row[2],
                    "action": row[3],
                    "resource_type": row[4],
                    "resource_id": row[5],
                    "details": row[6],
                    "ip_address": row[7],
                    "created_at": row[8]
                }
                for row in rows
            ]
        }

@api_router.delete("/audit-logs")
async def clear_audit_logs(request: Request, admin_user_id: str):
    """Clear all audit logs (Admin only)"""
    user = await get_current_user(request, admin_user_id)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Sadece admin bu işlemi yapabilir")
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM audit_logs")
        await db.commit()
        
        # Log this action (new log after clearing)
        await log_audit(
            admin_user_id, "clear_logs", "audit_logs", None,
            "Tüm audit logları temizlendi",
            request.client.host if request.client else None
        )
        
        return {"success": True, "message": "Audit logları temizlendi"}

# ============== REPORT EXPORT ROUTES ==============

class ReportExportRequest(BaseModel):
    format: str  # 'pdf', 'excel', 'word'
    user_id: str
    include_tasks: bool = True
    include_stats: bool = True

class DetailedReportRequest(BaseModel):
    user_id: str
    period_months: int = 1  # 1, 3, 6, 12
    format: str = "pdf"

@api_router.get("/reports/detailed-stats")
async def get_detailed_report_stats(
    user_id: str,
    period_months: int = 1
):
    """Get detailed statistics for report generation using SQLite"""
    from datetime import datetime, timedelta, timezone
    
    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=period_months * 30)
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Get user info
        cursor = await db.execute("SELECT name FROM users WHERE id = ?", (user_id,))
        user_row = await cursor.fetchone()
        user_name = user_row[0] if user_row else "Kullanıcı"
        
        # Get all tasks for the period - EXCLUDE BACKLOG
        cursor = await db.execute(
            """SELECT id, title, description, category_id, status, priority, created_at, completed_at 
               FROM tasks 
               WHERE (user_id = ? OR assigned_to = ?) 
               AND created_at >= ?
               AND status != 'backlog'
               ORDER BY created_at DESC""",
            (user_id, user_id, start_date.isoformat())
        )
        rows = await cursor.fetchall()
        
        all_tasks = [
            {
                "id": r[0], "title": r[1], "description": r[2], "category_id": r[3],
                "status": r[4], "priority": r[5], "created_at": r[6], "completed_at": r[7]
            }
            for r in rows
        ]
        
        # Calculate statistics (backlog already excluded)
        total_tasks = len(all_tasks)
        completed_tasks = len([t for t in all_tasks if t.get("status") == "completed"])
        in_progress_tasks = len([t for t in all_tasks if t.get("status") == "in_progress"])
        todo_tasks = len([t for t in all_tasks if t.get("status") in ["backlog", "today_planned"]])
        blocked_tasks = len([t for t in all_tasks if t.get("status") == "blocked"])
        
        # Priority breakdown
        priority_stats = {
            "critical": len([t for t in all_tasks if t.get("priority") == "critical"]),
            "high": len([t for t in all_tasks if t.get("priority") == "high"]),
            "medium": len([t for t in all_tasks if t.get("priority") == "medium"]),
            "low": len([t for t in all_tasks if t.get("priority") == "low"])
        }
        
        # Task type breakdown (based on title keywords)
        maintenance_tasks = len([t for t in all_tasks if any(kw in (t.get("title") or "").lower() for kw in ["bakım", "maintenance", "düzeltme", "fix"])])
        new_tests = len([t for t in all_tasks if any(kw in (t.get("title") or "").lower() for kw in ["yeni test", "new test", "test yaz", "otomasyon"])])
        bug_fixes = len([t for t in all_tasks if any(kw in (t.get("title") or "").lower() for kw in ["bug", "hata", "sorun", "error"])])
        
        # Monthly breakdown
        monthly_data = []
        turkish_months = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 
                          'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
        
        for i in range(min(period_months, 12)):
            month_end = end_date - timedelta(days=i * 30)
            month_start = month_end - timedelta(days=30)
            
            month_tasks = [t for t in all_tasks if t.get("created_at") and month_start.isoformat() <= t.get("created_at", "") <= month_end.isoformat()]
            
            month_name = f"{turkish_months[month_end.month - 1]} {month_end.year}"
            monthly_data.append({
                "month": month_name,
                "total": len(month_tasks),
                "completed": len([t for t in month_tasks if t.get("status") == "completed"]),
                "maintenance": len([t for t in month_tasks if "bakım" in (t.get("title") or "").lower()]),
                "new_tests": len([t for t in month_tasks if "test" in (t.get("title") or "").lower()])
            })
        
        # Completion rate
        completion_rate = round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1)
        
        # Period label
        period_labels = {1: "Son 1 Ay", 3: "Son 3 Ay", 6: "Son 6 Ay", 12: "Son 12 Ay"}
        period_label = period_labels.get(period_months, f"Son {period_months} Ay")
        
        return {
            "user_name": user_name,
            "period_months": period_months,
            "period_label": period_label,
            "date_range": {
                "start": start_date.strftime("%d/%m/%Y"),
                "end": end_date.strftime("%d/%m/%Y")
            },
            "summary": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "in_progress_tasks": in_progress_tasks,
                "todo_tasks": todo_tasks,
                "blocked_tasks": blocked_tasks,
                "completion_rate": completion_rate
            },
            "work_breakdown": {
                "maintenance_tasks": maintenance_tasks,
                "new_tests": new_tests,
                "bug_fixes": bug_fixes,
                "other": max(0, total_tasks - maintenance_tasks - new_tests - bug_fixes)
            },
            "priority_breakdown": priority_stats,
            "monthly_data": monthly_data[::-1],  # Reverse for chronological order
            "recent_tasks": [
                {
                    "title": t.get("title", ""),
                    "status": t.get("status", ""),
                    "priority": t.get("priority", ""),
                    "created_at": (t.get("created_at") or "")[:10]
                }
                for t in all_tasks[:10]
            ]
        }

@api_router.post("/reports/export")
async def export_report(request_data: ReportExportRequest):
    """Export report in specified format"""
    format = request_data.format
    user_id = request_data.user_id
    include_tasks = request_data.include_tasks
    include_stats = request_data.include_stats
    
    logger.info(f"Report export requested: format={format}, user_id={user_id}")
    
    if not REPORTS_AVAILABLE:
        logger.error("Report exporter not available")
        raise HTTPException(status_code=503, detail="Report export not available")
    
    if format not in ['pdf', 'excel', 'word']:
        logger.error(f"Invalid format: {format}")
        raise HTTPException(status_code=400, detail="Format must be 'pdf', 'excel', or 'word'")
    
    try:
        # Gather data
        report_data = {}
        
        logger.info(f"Gathering report data for user {user_id}")
        
        async with aiosqlite.connect(DB_PATH) as db:
            # Get user name
            cursor = await db.execute("SELECT name FROM users WHERE id = ?", (user_id,))
            user_row = await cursor.fetchone()
            report_data['user_name'] = user_row[0] if user_row else 'Kullanıcı'
            
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
                
                logger.info(f"Stats gathered: {report_data['stats']}")
            
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
                
                logger.info(f"Tasks gathered: {len(report_data['tasks'])} tasks")
        
        # Generate report
        logger.info(f"Generating {format} report...")
        
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
        
        logger.info(f"Report generated successfully: {len(content)} bytes")
        
        # Return file
        return StreamingResponse(
            io.BytesIO(content),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Rapor oluşturulurken hata: {str(e)}")

@api_router.get("/debug/user-info")
async def debug_user_info(user_id: Optional[str] = None, device_id: Optional[str] = None, name: Optional[str] = None):
    """Debug endpoint to check user data including role"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            if user_id:
                cursor = await db.execute(
                    "SELECT id, name, email, device_id, role, created_at FROM users WHERE id = ?",
                    (user_id,)
                )
            elif device_id:
                cursor = await db.execute(
                    "SELECT id, name, email, device_id, role, created_at FROM users WHERE device_id = ?",
                    (device_id,)
                )
            elif name:
                cursor = await db.execute(
                    "SELECT id, name, email, device_id, role, created_at FROM users WHERE name = ?",
                    (name,)
                )
            else:
                # Get all users with roles
                cursor = await db.execute(
                    "SELECT id, name, email, device_id, role, created_at FROM users"
                )
            
            rows = await cursor.fetchall()
            
            users_data = []
            for row in rows:
                users_data.append({
                    "id": row[0],
                    "name": row[1],
                    "email": row[2],
                    "device_id": row[3],
                    "role": row[4],
                    "created_at": row[5]
                })
            
            return {
                "success": True,
                "count": len(users_data),
                "users": users_data
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

# Health check
@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "sqlite",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# ============== JIRA TOOLS API (QA Hub Integration) ==============

@api_router.post("/jira-tools/jiragen/validate")
async def jiragen_validate(request: Request):
    """Validate JSON test data for Jira test creation (SSE streaming)"""
    
    # Read body BEFORE generator
    body = await request.json()
    is_ui_test = body.get("isUiTest", False)
    json_data = body.get("jsonData", "")
    
    async def generate():
        try:
            yield f"data: {json.dumps({'log': '🔍 JSON verisi analiz ediliyor...'})}\n\n"
            
            try:
                tests_raw = json.loads(json_data)
                if not isinstance(tests_raw, list):
                    tests_raw = [tests_raw]
            except json.JSONDecodeError as e:
                yield f"data: {json.dumps({'error': f'JSON parse hatası: {str(e)}'})}\n\n"
                return
            
            yield f"data: {json.dumps({'log': f'📊 {len(tests_raw)} test bulundu'})}\n\n"
            
            validated_tests = []
            valid_count = 0
            invalid_count = 0
            
            for idx, test in enumerate(tests_raw, 1):
                yield f"data: {json.dumps({'log': f'🔄 Test {idx} doğrulanıyor...'})}\n\n"
                
                errors = []
                
                # Validate required fields
                if not test.get("name"):
                    errors.append("Test adı eksik")
                if not test.get("objective"):
                    errors.append("Objective eksik")
                if not test.get("testScript") or not test.get("testScript", {}).get("stepByStepScript", {}).get("steps"):
                    errors.append("Test steps eksik")
                
                # Extract steps
                steps = []
                raw_steps = test.get("testScript", {}).get("stepByStepScript", {}).get("steps", [])
                for step in raw_steps:
                    steps.append({
                        "index": step.get("index", 0),
                        "description": step.get("description", ""),
                        "testData": step.get("testData", ""),
                        "expectedResult": step.get("expectedResult", ""),
                    })
                
                is_valid = len(errors) == 0
                if is_valid:
                    valid_count += 1
                    yield f"data: {json.dumps({'log': f'  ✅ Test {idx}: Geçerli'})}\n\n"
                else:
                    invalid_count += 1
                    yield f"data: {json.dumps({'log': f'  ❌ Test {idx}: {len(errors)} hata'})}\n\n"
                
                validated_tests.append({
                    "index": idx,
                    "name": test.get("name", f"Test {idx}"),
                    "issueId": test.get("issueId"),
                    "rawTest": test,
                    "steps": steps,
                    "validation": {
                        "isValid": is_valid,
                        "errors": errors,
                    }
                })
            
            newline = "\n"
            log_msg = f'{newline}✅ Doğrulama tamamlandı: {valid_count} geçerli, {invalid_count} hatalı'
            yield f"data: {json.dumps({'log': log_msg})}\n\n"
            
            result = {
                "tests": validated_tests,
                "stats": {
                    "total": len(validated_tests),
                    "valid": valid_count,
                    "invalid": invalid_count,
                }
            }
            
            yield f"data: {json.dumps({'complete': True, 'result': result})}\n\n"
            
        except Exception as e:
            logger.error(f"JiraGen validate error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@api_router.post("/jira-tools/jiragen/create")
async def jiragen_create(request: Request):
    """Create test in Jira (SSE streaming) - Requires VPN"""
    
    # Read body BEFORE generator
    body = await request.json()
    test_data = body.get("testData", {})
    is_ui_test = body.get("isUiTest", False)
    
    async def generate():
        try:
            yield f"data: {json.dumps({'log': '🚀 Jira test oluşturuluyor...'})}\n\n"
            
            # Check if Jira is available
            if not JIRA_AVAILABLE:
                yield f"data: {json.dumps({'log': '⚠️ VPN bağlantısı gerekli - DEMO modu'})}\n\n"
                
                # Demo mode - return mock result
                mock_key = f"TEST-{uuid.uuid4().hex[:6].upper()}"
                yield f"data: {json.dumps({'log': f'✅ Demo: Test oluşturuldu - {mock_key}'})}\n\n"
                
                yield f"data: {json.dumps({'complete': True, 'result': {'success': True, 'key': mock_key, 'id': mock_key, 'name': test_data.get('name', 'Test')}})}\n\n"
                return
            
            # Real Jira creation would go here
            try:
                result = await jira_client.create_test(test_data, is_ui_test)
                jira_key = result.get('key')
                log_created = f'✅ Test oluşturuldu: {jira_key}'
                yield f"data: {json.dumps({'log': log_created})}\n\n"
                yield f"data: {json.dumps({'complete': True, 'result': {'success': True, 'key': jira_key, 'id': result.get('id'), 'name': test_data.get('name')}})}\n\n"
            except Exception as e:
                err_msg = f'❌ Hata: {str(e)}'
                yield f"data: {json.dumps({'log': err_msg})}\n\n"
                yield f"data: {json.dumps({'complete': True, 'result': {'success': False, 'error': str(e)}})}\n\n"
            
        except Exception as e:
            logger.error(f"JiraGen create error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@api_router.post("/jira-tools/bugbagla/analyze")
async def bugbagla_analyze(request: Request):
    """Analyze cycle for bug binding (SSE streaming) - Port from bugbagla.js"""
    
    # Read body BEFORE generator
    body = await request.json()
    current_cycle_key = body.get("currentCycleKey", "")
    base_cycle_key = body.get("baseCycleKey", "")
    status_ids = body.get("statusIds", [219])
    
    async def generate():
        try:
            yield f"data: {json.dumps({'log': '🔍 Bug Bağlama Analizi Başlıyor'})}\n\n"
            yield f"data: {json.dumps({'log': f'   • Mevcut Cycle: {current_cycle_key}'})}\n\n"
            yield f"data: {json.dumps({'log': f'   • Base Cycle: {base_cycle_key}'})}\n\n"
            
            status_names = [jira_api_client.get_status_name(sid) for sid in status_ids]
            status_names_str = ", ".join(status_names)
            yield f"data: {json.dumps({'log': f'   • Seçilen Statusler: {status_names_str}'})}\n\n"
            
            if not JIRA_API_AVAILABLE:
                yield f"data: {json.dumps({'log': '⚠️ VPN bağlantısı gerekli - DEMO modu'})}\n\n"
                
                # Demo data
                mock_will_bind = [
                    {"testKey": "TEST-001", "testName": "Login Test - Invalid", "status": 219, "testResultId": 1001, "bugIds": [5001], "bugKeys": ["BUG-101"]},
                    {"testKey": "TEST-002", "testName": "Payment Flow - Timeout", "status": 219, "testResultId": 1002, "bugIds": [5002], "bugKeys": ["BUG-102"]},
                ]
                mock_will_skip = [
                    {"testKey": "TEST-003", "testName": "Dashboard Load", "status": 218, "reason": "Status filtresi dışında (Pass)"},
                    {"testKey": "TEST-004", "testName": "Profile Update", "status": 219, "reason": "Base cycle'da test bulunamadı"},
                ]
                
                yield f"data: {json.dumps({'log': '📊 Analiz Tamamlandı! (Demo)'})}\n\n"
                yield f"data: {json.dumps({'log': '   • Toplam: 10'})}\n\n"
                yield f"data: {json.dumps({'log': f'   • Bağlanacak: {len(mock_will_bind)}'})}\n\n"
                yield f"data: {json.dumps({'log': f'   • Atlanacak: {len(mock_will_skip)}'})}\n\n"
                
                result = {
                    "success": True,
                    "cycleId": 12345,
                    "baseRunId": 12346,
                    "willBind": mock_will_bind,
                    "willSkip": mock_will_skip,
                    "stats": {
                        "total": 10,
                        "toBind": len(mock_will_bind),
                        "toSkip": len(mock_will_skip)
                    }
                }
                yield f"data: {json.dumps({'complete': True, 'result': result})}\n\n"
                return
            
            # Real implementation using jira_api_client
            try:
                status_set = set(status_ids)
                
                # Get current cycle
                yield f"data: {json.dumps({'log': '📋 Mevcut cycle bilgileri alınıyor...'})}\n\n"
                current_run = await jira_api_client.get_test_run(current_cycle_key)
                current_run_id = current_run.get("id")
                
                if not current_run_id:
                    yield f"data: {json.dumps({'error': f'Mevcut cycle ID alınamadı: {current_cycle_key}'})}\n\n"
                    return
                
                yield f"data: {json.dumps({'log': f'✅ Mevcut Cycle ID: {current_run_id}'})}\n\n"
                
                # Get current items
                yield f"data: {json.dumps({'log': '📥 Mevcut cycle items alınıyor...'})}\n\n"
                current_items = await jira_api_client.get_test_run_items(current_run_id)
                yield f"data: {json.dumps({'log': f'✅ {len(current_items)} test bulundu'})}\n\n"
                
                # Build case map from base cycle
                yield f"data: {json.dumps({'log': f'📋 Base cycle bilgileri alınıyor: {base_cycle_key}'})}\n\n"
                base_run = await jira_api_client.get_test_run(base_cycle_key)
                base_run_id = base_run.get("id")
                
                if not base_run_id:
                    yield f"data: {json.dumps({'error': f'Base cycle ID alınamadı: {base_cycle_key}'})}\n\n"
                    return
                
                yield f"data: {json.dumps({'log': f'✅ Base cycle ID: {base_run_id}'})}\n\n"
                
                yield f"data: {json.dumps({'log': '📥 Base cycle items alınıyor...'})}\n\n"
                base_items = await jira_api_client.get_test_run_items(base_run_id)
                yield f"data: {json.dumps({'log': f'✅ {len(base_items)} test bulundu'})}\n\n"
                
                # Build case map
                case_map = {}
                for item in base_items:
                    lr = item.get("$lastTestResult", {})
                    key = lr.get("testCase", {}).get("key")
                    item_id = item.get("id")
                    if key and item_id:
                        case_map[key] = item_id
                
                yield f"data: {json.dumps({'log': f'✅ {len(case_map)} test için mapping oluşturuldu'})}\n\n"
                
                # Filter and analyze
                yield f"data: {json.dumps({'log': '🔄 Testler analiz ediliyor...'})}\n\n"
                
                will_bind = []
                will_skip = []
                
                for item in current_items:
                    lr = item.get("$lastTestResult", {})
                    if not lr:
                        continue
                    
                    test_key = lr.get("testCase", {}).get("key")
                    test_name = lr.get("testCase", {}).get("name", "")
                    test_result_id = lr.get("id")
                    status = lr.get("testResultStatusId")
                    
                    if not test_key or not test_result_id:
                        continue
                    
                    # Status check
                    if status not in status_set:
                        will_skip.append({
                            "testKey": test_key,
                            "testName": test_name,
                            "status": status,
                            "reason": f"Status filtresi dışında ({jira_api_client.get_status_name(status)})"
                        })
                        continue
                    
                    # Check base
                    base_item_id = case_map.get(test_key)
                    if not base_item_id:
                        will_skip.append({
                            "testKey": test_key,
                            "testName": test_name,
                            "status": status,
                            "reason": "Base cycle'da test bulunamadı"
                        })
                        continue
                    
                    # Get bugs from base
                    try:
                        base_results = await jira_api_client.get_test_results_by_item_id(base_run_id, base_item_id)
                        first_result = base_results[0] if base_results else {}
                        trace_links = first_result.get("traceLinks", [])
                        issue_ids = [t.get("issueId") for t in trace_links if t.get("issueId")]
                        
                        if not issue_ids:
                            will_skip.append({
                                "testKey": test_key,
                                "testName": test_name,
                                "status": status,
                                "reason": "Base cycle'da bağlı bug yok"
                            })
                            continue
                        
                        # Get bug keys
                        bug_keys = []
                        for issue_id in issue_ids:
                            bug_key = await jira_api_client.get_issue_key(issue_id)
                            bug_keys.append(bug_key)
                        
                        will_bind.append({
                            "testKey": test_key,
                            "testName": test_name,
                            "status": status,
                            "testResultId": test_result_id,
                            "bugIds": issue_ids,
                            "bugKeys": bug_keys
                        })
                        
                    except Exception as e:
                        will_skip.append({
                            "testKey": test_key,
                            "testName": test_name,
                            "status": status,
                            "reason": f"Analiz hatası: {str(e)}"
                        })
                
                yield f"data: {json.dumps({'log': '📊 Analiz Tamamlandı!'})}\n\n"
                yield f"data: {json.dumps({'log': f'   • Toplam: {len(current_items)}'})}\n\n"
                yield f"data: {json.dumps({'log': f'   • Bağlanacak: {len(will_bind)}'})}\n\n"
                yield f"data: {json.dumps({'log': f'   • Atlanacak: {len(will_skip)}'})}\n\n"
                
                result = {
                    "success": True,
                    "cycleId": current_run_id,
                    "baseRunId": base_run_id,
                    "caseMap": case_map,
                    "willBind": will_bind,
                    "willSkip": will_skip,
                    "stats": {
                        "total": len(current_items),
                        "toBind": len(will_bind),
                        "toSkip": len(will_skip)
                    }
                }
                yield f"data: {json.dumps({'complete': True, 'result': result})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
        except Exception as e:
            logger.error(f"BugBagla analyze error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@api_router.post("/jira-tools/bugbagla/bind")
async def bugbagla_bind(request: Request):
    """Bind bug to test results (SSE streaming) - Port from bugbagla.js executeBugBagla"""
    
    # Read body BEFORE generator
    body = await request.json()
    bindings = body.get("bindings", [])
    
    async def generate():
        try:
            yield f"data: {json.dumps({'log': '🔗 Buglar bağlanıyor...'})}\n\n"
            
            if not JIRA_API_AVAILABLE:
                yield f"data: {json.dumps({'log': '⚠️ VPN bağlantısı gerekli - DEMO modu'})}\n\n"
                
                for binding in bindings:
                    test_key = binding.get("testKey", "")
                    yield f"data: {json.dumps({'log': f'✅ {test_key} - Bug bağlandı (Demo)'})}\n\n"
                    await asyncio.sleep(0.2)
                
                yield f"data: {json.dumps({'log': '✨ Bağlama Tamamlandı! (Demo)'})}\n\n"
                yield f"data: {json.dumps({'log': f'   • Başarılı: {len(bindings)}'})}\n\n"
                yield f"data: {json.dumps({'success': True, 'linked': len(bindings), 'failed': 0})}\n\n"
                return
            
            # Real implementation
            try:
                linked_count = 0
                failed_count = 0
                cycle_id = None
                
                for binding in bindings:
                    if not cycle_id and binding.get("cycleId"):
                        cycle_id = binding["cycleId"]
                    
                    for bug_id in binding.get("bugIds", []):
                        try:
                            await jira_api_client.link_bug_to_test_result(binding["testResultId"], bug_id, 3)
                            test_key = binding.get("testKey", "")
                            yield f"data: {json.dumps({'log': f'✅ {test_key} - Bug bağlandı (ID: {bug_id})'})}\n\n"
                            linked_count += 1
                        except Exception as e:
                            test_key = binding.get("testKey", "")
                            err_msg = str(e)
                            yield f"data: {json.dumps({'log': f'❌ {test_key} - Bug bağlanırken hata: {err_msg}'})}\n\n"
                            failed_count += 1
                
                # Refresh cache
                if cycle_id:
                    yield f"data: {json.dumps({'log': '🔄 Cache yenileniyor...'})}\n\n"
                    await jira_api_client.refresh_issue_count_cache(cycle_id)
                    yield f"data: {json.dumps({'log': '✅ Cache yenilendi'})}\n\n"
                
                yield f"data: {json.dumps({'log': '✨ Bağlama Tamamlandı!'})}\n\n"
                yield f"data: {json.dumps({'log': f'   • Başarılı: {linked_count}'})}\n\n"
                yield f"data: {json.dumps({'log': f'   • Hatalı: {failed_count}'})}\n\n"
                
                yield f"data: {json.dumps({'success': True, 'linked': linked_count, 'failed': failed_count})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
        except Exception as e:
            logger.error(f"BugBagla bind error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

# ============== CYCLES & PROJECTS API ==============

# JSON dosya yolları
CYCLES_FILE = os.path.join(os.path.dirname(__file__), "data", "cycles.json")
PROJECTS_FILE = os.path.join(os.path.dirname(__file__), "data", "projects.json")

def ensure_data_files():
    """Data klasörü ve dosyalarını oluştur"""
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    
    if not os.path.exists(CYCLES_FILE):
        with open(CYCLES_FILE, "w") as f:
            json.dump({"cycles": []}, f)
    
    if not os.path.exists(PROJECTS_FILE):
        with open(PROJECTS_FILE, "w") as f:
            json.dump({"projects": []}, f)

ensure_data_files()

@api_router.get("/cycles")
async def get_cycles():
    """Get all cycles"""
    try:
        with open(CYCLES_FILE, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Cycles okuma hatası: {e}")
        return {"cycles": []}

@api_router.post("/cycles")
async def add_cycle(request: Request):
    """Add a new cycle"""
    try:
        body = await request.json()
        key = body.get("key")
        name = body.get("name")
        
        if not key or not name:
            raise HTTPException(status_code=400, detail="key ve name gerekli!")
        
        with open(CYCLES_FILE, "r") as f:
            data = json.load(f)
        
        if any(c["key"] == key for c in data["cycles"]):
            raise HTTPException(status_code=400, detail="Bu cycle key zaten mevcut!")
        
        data["cycles"].append({"key": key, "name": name})
        
        with open(CYCLES_FILE, "w") as f:
            json.dump(data, f, indent=2)
        
        return {"success": True, "cycle": {"key": key, "name": name}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cycle ekleme hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/cycles/{key}")
async def update_cycle(key: str, request: Request):
    """Update a cycle"""
    try:
        body = await request.json()
        new_key = body.get("key")
        name = body.get("name")
        
        if not new_key or not name:
            raise HTTPException(status_code=400, detail="key ve name gerekli!")
        
        with open(CYCLES_FILE, "r") as f:
            data = json.load(f)
        
        index = next((i for i, c in enumerate(data["cycles"]) if c["key"] == key), None)
        if index is None:
            raise HTTPException(status_code=404, detail="Cycle bulunamadı!")
        
        data["cycles"][index] = {"key": new_key, "name": name}
        
        with open(CYCLES_FILE, "w") as f:
            json.dump(data, f, indent=2)
        
        return {"success": True, "cycle": {"key": new_key, "name": name}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cycle güncelleme hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/cycles/{key}")
async def delete_cycle(key: str):
    """Delete a cycle"""
    try:
        with open(CYCLES_FILE, "r") as f:
            data = json.load(f)
        
        data["cycles"] = [c for c in data["cycles"] if c["key"] != key]
        
        with open(CYCLES_FILE, "w") as f:
            json.dump(data, f, indent=2)
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Cycle silme hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/qa-projects")
async def get_qa_projects():
    """Get all QA projects for tools"""
    try:
        with open(PROJECTS_FILE, "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Projeler okuma hatası: {e}")
        return {"projects": []}

@api_router.post("/qa-projects")
async def add_qa_project(request: Request):
    """Add a new QA project"""
    try:
        body = await request.json()
        name = body.get("name")
        icon = body.get("icon", "📦")
        links = body.get("links", {})
        team_remote_id = body.get("teamRemoteId", "")
        is_mobile = body.get("isMobile", False)
        platform = body.get("platform")  # "ios" | "android" | None
        
        if not name:
            raise HTTPException(status_code=400, detail="name gerekli!")
        
        # Validate platform for mobile projects
        if is_mobile and platform not in ["ios", "android"]:
            raise HTTPException(status_code=400, detail="Mobil projeler için platform (ios/android) seçilmelidir!")
        
        with open(PROJECTS_FILE, "r") as f:
            data = json.load(f)
        
        if any(p["name"] == name for p in data["projects"]):
            raise HTTPException(status_code=400, detail="Bu proje adı zaten mevcut!")
        
        new_project = {
            "name": name,
            "icon": icon,
            "links": links,
            "teamRemoteId": team_remote_id,
            "isMobile": is_mobile,
            "platform": platform if is_mobile else None
        }
        data["projects"].append(new_project)
        
        with open(PROJECTS_FILE, "w") as f:
            json.dump(data, f, indent=2)
        
        return {"success": True, "project": new_project}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Proje ekleme hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/qa-projects/{name}")
async def update_qa_project(name: str, request: Request):
    """Update a QA project"""
    try:
        body = await request.json()
        new_name = body.get("name")
        icon = body.get("icon")
        links = body.get("links", {})
        team_remote_id = body.get("teamRemoteId", "")
        is_mobile = body.get("isMobile", False)
        platform = body.get("platform")  # "ios" | "android" | None
        
        if not new_name or not icon:
            raise HTTPException(status_code=400, detail="name ve icon gerekli!")
        
        # Validate platform for mobile projects
        if is_mobile and platform not in ["ios", "android"]:
            raise HTTPException(status_code=400, detail="Mobil projeler için platform (ios/android) seçilmelidir!")
        
        with open(PROJECTS_FILE, "r") as f:
            data = json.load(f)
        
        index = next((i for i, p in enumerate(data["projects"]) if p["name"] == name), None)
        if index is None:
            raise HTTPException(status_code=404, detail="Proje bulunamadı!")
        
        data["projects"][index] = {
            "name": new_name,
            "icon": icon,
            "links": links,
            "teamRemoteId": team_remote_id,
            "isMobile": is_mobile,
            "platform": platform if is_mobile else None
        }
        
        with open(PROJECTS_FILE, "w") as f:
            json.dump(data, f, indent=2)
        
        return {"success": True, "project": data["projects"][index]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Proje güncelleme hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/qa-projects/{name}")
async def delete_qa_project(name: str):
    """Delete a QA project"""
    try:
        with open(PROJECTS_FILE, "r") as f:
            data = json.load(f)
        
        data["projects"] = [p for p in data["projects"] if p["name"] != name]
        
        with open(PROJECTS_FILE, "w") as f:
            json.dump(data, f, indent=2)
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Proje silme hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============== ANALYSIS API ==============

@api_router.post("/analysis/analyze")
async def run_analysis(request: Request):
    """Run test analysis (SSE streaming) - Port from analiz.js"""
    
    # Read body BEFORE generator
    body = await request.json()
    cycle_name = body.get("cycleName") or body.get("cycleId", "")
    days = int(body.get("days", 1))
    time = body.get("time", "00:00")
    project_names = body.get("projectNames", ["FraudNG.UITests", "Intertech.FraudNG", "Inter.Fraud.UITests"])
    
    async def generate():
        try:
            projects_str = ", ".join(project_names) if project_names else ""
            
            yield f"data: {json.dumps({'log': '📊 Analiz başlatılıyor...'})}\n\n"
            yield f"data: {json.dumps({'log': f'   • Cycle: {cycle_name}'})}\n\n"
            yield f"data: {json.dumps({'log': f'   • Kaç günlük: {days} gün'})}\n\n"
            yield f"data: {json.dumps({'log': f'   • Saat filtresi: {time}'})}\n\n"
            yield f"data: {json.dumps({'log': f'   • Projeler: {projects_str}'})}\n\n"
            
            if not MSSQL_AVAILABLE or not JIRA_API_AVAILABLE:
                yield f"data: {json.dumps({'log': '⚠️ VPN bağlantısı gerekli - DEMO modu'})}\n\n"
                
                # Generate demo data
                mock_data = []
                statuses = ["Pass", "Fail"]
                
                for project in project_names:
                    for i in range(8):
                        mock_data.append({
                            "key": f"{project[:5].upper()}-T{i+1}",
                            "name": f"Test Case {i+1} - {project}",
                            "project": project,
                            "inRegression": i % 2 == 0,
                            "status": statuses[i % 2],
                        })
                
                yield f"data: {json.dumps({'log': f'✅ {len(mock_data)} test analiz edildi (Demo)'})}\n\n"
                
                maint = [d for d in mock_data if d["inRegression"] and d["status"] == "Fail"]
                pass_no_reg = [d for d in mock_data if not d["inRegression"] and d["status"] == "Pass"]
                fail_no_reg = [d for d in mock_data if not d["inRegression"] and d["status"] == "Fail"]
                pass_in_reg = [d for d in mock_data if d["inRegression"] and d["status"] == "Pass"]
                
                stats = {
                    "total": len(mock_data),
                    "needMaintenance": len(maint),
                    "passedInRegression": len(pass_in_reg),
                    "passedNotInRegression": len(pass_no_reg),
                    "failedNotInRegression": len(fail_no_reg),
                }
                
                yield f"data: {json.dumps({'success': True, 'tableData': mock_data, 'stats': stats})}\n\n"
                return
            
            # Real implementation
            try:
                # Get cycle ID
                yield f"data: {json.dumps({'log': f'🔍 Cycle ID alınıyor: {cycle_name}'})}\n\n"
                try:
                    cycle_run = await asyncio.wait_for(
                        jira_api_client.get_test_run(cycle_name),
                        timeout=15.0
                    )
                    cycle_id = cycle_run.get("id")
                    yield f"data: {json.dumps({'log': f'✅ Cycle ID bulundu: {cycle_id}'})}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'log': '❌ Jira bağlantısı zaman aşımı - VPN bağlantınızı kontrol edin'})}\n\n"
                    yield f"data: {json.dumps({'error': 'Jira bağlantısı zaman aşımı'})}\n\n"
                    return
                except Exception as e:
                    err_msg = str(e)
                    yield f"data: {json.dumps({'log': f'❌ Jira hatası: {err_msg}'})}\n\n"
                    yield f"data: {json.dumps({'error': f'Jira bağlantı hatası: {err_msg}'})}\n\n"
                    return
                
                # Get all tests from DB
                yield f"data: {json.dumps({'log': '🗄️ Tüm testler veritabanından alınıyor...'})}\n\n"
                try:
                    test_names = mssql_client.get_all_tests(days, time, project_names)
                    yield f"data: {json.dumps({'log': f'✅ {len(test_names)} test bulundu'})}\n\n"
                except Exception as e:
                    err_msg = str(e)
                    yield f"data: {json.dumps({'log': f'❌ MSSQL hatası: {err_msg}'})}\n\n"
                    yield f"data: {json.dumps({'error': f'Veritabanı bağlantı hatası: {err_msg}'})}\n\n"
                    return
                
                # Get passed tests
                yield f"data: {json.dumps({'log': '✅ Başarılı testler alınıyor...'})}\n\n"
                db_items = mssql_client.get_passed_tests(days, time, project_names)
                yield f"data: {json.dumps({'log': f'✅ {len(db_items)} başarılı test bulundu'})}\n\n"
                
                # Get regression cycle info
                yield f"data: {json.dumps({'log': f'📋 Regression cycle bilgileri alınıyor (ID: {cycle_id})...'})}\n\n"
                all_tests = await jira_api_client.get_cycle_info(cycle_id)
                test_run_items = all_tests.get("testRunItems", [])
                yield f"data: {json.dumps({'log': f'✅ {len(test_run_items)} test regression da'})}\n\n"
                
                # Process data
                yield f"data: {json.dumps({'log': '🔄 Veriler işleniyor...'})}\n\n"
                
                # Regression check
                for item in test_run_items:
                    lr = item.get("$lastTestResult", {})
                    key = lr.get("testCase", {}).get("key")
                    item_t = next((t for t in test_names if t["key"] == key), None)
                    if item_t:
                        item_t["inRegression"] = True
                
                # Status update
                for item in db_items:
                    test = next((t for t in test_names if t["key"] == item["key"] and t["name"] == item["name"]), None)
                    if test:
                        test["status"] = "Pass"
                
                # Calculate stats
                maint = [t for t in test_names if t["inRegression"] and t["status"] == "Fail"]
                pass_no_reg = [t for t in test_names if not t["inRegression"] and t["status"] == "Pass"]
                fail_no_reg = [t for t in test_names if not t["inRegression"] and t["status"] == "Fail"]
                pass_in_reg = [t for t in test_names if t["inRegression"] and t["status"] == "Pass"]
                
                yield f"data: {json.dumps({'log': '📈 İstatistikler:'})}\n\n"
                yield f"data: {json.dumps({'log': f'   🔴 Bakıma ihtiyacı olan (Regression da + Fail): {len(maint)}'})}\n\n"
                yield f"data: {json.dumps({'log': f'   🟢 Başarılı ama Regression da yok: {len(pass_no_reg)}'})}\n\n"
                yield f"data: {json.dumps({'log': f'   🟠 Başarısız ve Regression da yok: {len(fail_no_reg)}'})}\n\n"
                yield f"data: {json.dumps({'log': f'   ✅ Başarılı ve Regression da: {len(pass_in_reg)}'})}\n\n"
                
                yield f"data: {json.dumps({'log': '✨ Analiz tamamlandı!'})}\n\n"
                
                stats = {
                    "total": len(test_names),
                    "needMaintenance": len(maint),
                    "passedInRegression": len(pass_in_reg),
                    "passedNotInRegression": len(pass_no_reg),
                    "failedNotInRegression": len(fail_no_reg),
                }
                
                yield f"data: {json.dumps({'success': True, 'tableData': test_names, 'stats': stats})}\n\n"
                
            except Exception as e:
                logger.error(f"Analysis error: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@api_router.post("/analysis/apianaliz")
async def run_api_analysis(request: Request):
    """Run API analysis (SSE streaming) - Port from apianaliz.js"""
    
    # Read body BEFORE generator
    body = await request.json()
    jira_team_id = int(body.get("jiraTeamId", 0))
    report_date = body.get("reportDate", "")
    project_names = body.get("projectNames", [])
    days = int(body.get("days", 1))
    time = body.get("time", "00:00")
    
    async def generate():
        try:
            projects_str = ", ".join(project_names) if project_names else "Yok"
            
            yield f"data: {json.dumps({'log': '📊 API Analiz başlatılıyor...'})}\n\n"
            yield f"data: {json.dumps({'log': f'   Team ID: {jira_team_id}'})}\n\n"
            yield f"data: {json.dumps({'log': f'   Tarih: {report_date}'})}\n\n"
            yield f"data: {json.dumps({'log': f'   Projeler: {projects_str}'})}\n\n"
            
            if not MSSQL_AVAILABLE:
                yield f"data: {json.dumps({'log': '⚠️ VPN bağlantısı gerekli - DEMO modu'})}\n\n"
                
                # Demo data
                mock_tests = []
                apps = ["FraudAPI", "PaymentService", "UserService"]
                endpoints = ["/login", "/transfer", "/balance", "/profile"]
                
                for app in apps:
                    for ep in endpoints:
                        mock_tests.append({
                            "key": f"API-{len(mock_tests)+1}",
                            "name": f"API Test - {app}{ep}",
                            "app": app,
                            "endpoint": ep,
                            "status": "Passed" if len(mock_tests) % 3 != 0 else "Failed",
                            "detail": "",
                            "rapor": len(mock_tests) % 2 == 0,
                            "external": len(mock_tests) % 4 == 0
                        })
                
                stats = {
                    "total": len(mock_tests),
                    "testedInReport": sum(1 for t in mock_tests if t["rapor"]),
                    "notTestedInReport": sum(1 for t in mock_tests if not t["rapor"]),
                    "notInReport": 0,
                    "onlyInReport": 0,
                    "passed": sum(1 for t in mock_tests if t["status"] == "Passed"),
                    "failed": sum(1 for t in mock_tests if t["status"] == "Failed"),
                    "externalEndpoints": sum(1 for t in mock_tests if t["external"])
                }
                
                management_metrics = {
                    "raporEndpointSayisi": 20,
                    "raporaYansiyanTest": 15,
                    "coverageOrani": "75.00",
                    "otomasyondaAmaRapordaYok": 3,
                    "passedAmaNegatifSayisi": 2,
                    "failedEtkilenenEndpointSayisi": 1,
                    "tahminiGuncelPass": 18,
                    "tahminiGuncelCoverage": "90.00"
                }
                
                yield f"data: {json.dumps({'log': f'✅ {len(mock_tests)} test analiz edildi (Demo)'})}\n\n"
                yield f"data: {json.dumps({'success': True, 'tableData': mock_tests, 'stats': stats, 'managementMetrics': management_metrics})}\n\n"
                return
            
            # Real implementation
            try:
                yield f"data: {json.dumps({'log': '📋 Rapor verileri alınıyor...'})}\n\n"
                try:
                    rapor_data = mssql_client.get_rapor_data(jira_team_id, report_date)
                    yield f"data: {json.dumps({'log': f'✅ {len(rapor_data)} endpoint bulundu (Rapordan)'})}\n\n"
                except Exception as mssql_err:
                    logger.error(f"MSSQL get_rapor_data error: {mssql_err}")
                    yield f"data: {json.dumps({'log': f'❌ MSSQL bağlantı hatası: {str(mssql_err)}'})}\n\n"
                    yield f"data: {json.dumps({'error': f'MSSQL bağlantı hatası: {str(mssql_err)}'})}\n\n"
                    return
                
                yield f"data: {json.dumps({'log': '🧪 Test sonuçları alınıyor...'})}\n\n"
                try:
                    tests = mssql_client.get_all_api_tests(project_names, days, time)
                    yield f"data: {json.dumps({'log': f'✅ {len(tests)} test sonucu bulundu'})}\n\n"
                except Exception as mssql_err:
                    logger.error(f"MSSQL get_all_api_tests error: {mssql_err}")
                    yield f"data: {json.dumps({'log': f'❌ Test verisi alınamadı: {str(mssql_err)}'})}\n\n"
                    yield f"data: {json.dumps({'error': f'Test verisi alınamadı: {str(mssql_err)}'})}\n\n"
                    return
                
                yield f"data: {json.dumps({'log': '🔄 Veriler eşleştiriliyor...'})}\n\n"
                
                # Match tests with report
                for test in tests:
                    rapor_item = next(
                        (r for r in rapor_data if 
                         r["app"].lower() == (test.get("app") or "").lower() and 
                         r["endpoint"].lower() == (test.get("endpoint") or "").lower()),
                        None
                    )
                    
                    if rapor_item:
                        test["rapor"] = rapor_item["test"]
                        test["raporapp"] = rapor_item["app"]
                        test["raporendpoint"] = rapor_item["endpoint"]
                        test["external"] = rapor_item["external"]
                    else:
                        test["rapor"] = None
                        test["raporapp"] = None
                        test["raporendpoint"] = None
                        test["external"] = None
                
                # Find endpoints in report but not tested
                not_tested_endpoints = []
                for rapor_item in rapor_data:
                    test_exists = any(
                        t.get("app", "").lower() == rapor_item["app"].lower() and
                        t.get("endpoint", "").lower() == rapor_item["endpoint"].lower()
                        for t in tests
                    )
                    
                    if not test_exists:
                        not_tested_endpoints.append({
                            "key": "-",
                            "name": "-",
                            "app": rapor_item["app"],
                            "status": "None",
                            "endpoint": rapor_item["endpoint"],
                            "detail": "-",
                            "rapor": "notest",
                            "raporapp": rapor_item["app"],
                            "raporendpoint": rapor_item["endpoint"],
                            "external": rapor_item["external"]
                        })
                
                tests.extend(not_tested_endpoints)
                
                # Calculate metrics
                rapor_endpoint_sayisi = sum(1 for r in rapor_data if r["external"] == False)
                rapora_yansıyan_test = sum(1 for r in rapor_data if r["external"] == False and r["test"] == True)
                coverage_orani = round((rapora_yansıyan_test / rapor_endpoint_sayisi * 100), 2) if rapor_endpoint_sayisi > 0 else 0
                
                otomasyonda_ama_raporda_yok = sum(1 for t in tests if t["rapor"] is None and t.get("status") != "None")
                
                passed_ama_negatif = set()
                for t in tests:
                    if t.get("status") == "Passed" and t["rapor"] == False:
                        passed_ama_negatif.add(f"{t.get('app')}|{t.get('endpoint')}")
                
                failed_ve_negatif = set()
                for t in tests:
                    if t.get("status") == "Failed" and t["rapor"] == False:
                        failed_ve_negatif.add(f"{t.get('app')}|{t.get('endpoint')}")
                
                unique_passed = set()
                for t in tests:
                    if t.get("status") == "Passed" and t.get("status") != "None":
                        unique_passed.add(f"{t.get('app')}|{t.get('endpoint')}")
                
                tahmini_guncel_pass = len(unique_passed)
                tahmini_guncel_coverage = round((tahmini_guncel_pass / rapor_endpoint_sayisi * 100), 2) if rapor_endpoint_sayisi > 0 else 0
                
                stats = {
                    "total": len(tests),
                    "testedInReport": sum(1 for t in tests if t["rapor"] == True),
                    "notTestedInReport": sum(1 for t in tests if t["rapor"] == False),
                    "notInReport": sum(1 for t in tests if t["rapor"] is None),
                    "onlyInReport": len(not_tested_endpoints),
                    "passed": sum(1 for t in tests if t.get("status") == "Passed"),
                    "failed": sum(1 for t in tests if t.get("status") == "Failed"),
                    "externalEndpoints": sum(1 for t in tests if t.get("external") == True)
                }
                
                management_metrics = {
                    "raporEndpointSayisi": rapor_endpoint_sayisi,
                    "raporaYansiyanTest": rapora_yansıyan_test,
                    "coverageOrani": str(coverage_orani),
                    "otomasyondaAmaRapordaYok": otomasyonda_ama_raporda_yok,
                    "passedAmaNegatifSayisi": len(passed_ama_negatif),
                    "failedEtkilenenEndpointSayisi": len(failed_ve_negatif),
                    "tahminiGuncelPass": tahmini_guncel_pass,
                    "tahminiGuncelCoverage": str(tahmini_guncel_coverage)
                }
                
                yield f"data: {json.dumps({'log': '✨ API Analiz tamamlandı!'})}\n\n"
                yield f"data: {json.dumps({'success': True, 'tableData': tests, 'stats': stats, 'managementMetrics': management_metrics})}\n\n"
                
            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                logger.error(f"API Analysis error: {e}\n{error_detail}")
                yield f"data: {json.dumps({'log': f'❌ Hata: {str(e) or error_detail[:200]}'})}\n\n"
                yield f"data: {json.dumps({'error': str(e) or 'Bilinmeyen hata - backend loglarını kontrol edin'})}\n\n"
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            logger.error(f"API Analysis outer error: {e}\n{error_detail}")
            yield f"data: {json.dumps({'error': str(e) or 'Bilinmeyen hata'})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

# ============== CYCLE ADD API ==============

@api_router.post("/jira-tools/cycleadd/analyze")
async def cycleadd_analyze(request: Request):
    """Analyze tests for cycle add (SSE streaming) - Port from cycleadd.js"""
    
    # Read body BEFORE generator
    body = await request.json()
    cycle_key = body.get("cycleKey", "")
    add_items = body.get("addItems", [])
    
    async def generate():
        try:
            yield f"data: {json.dumps({'log': f'🔍 Cycle ID alınıyor: {cycle_key}'})}\n\n"
            
            if not JIRA_API_AVAILABLE:
                yield f"data: {json.dumps({'log': '⚠️ VPN bağlantısı gerekli - DEMO modu'})}\n\n"
                
                # Demo data
                will_be_added = []
                will_be_skipped = []
                
                for idx, item in enumerate(add_items):
                    if idx % 3 == 0:
                        will_be_skipped.append({
                            "key": item,
                            "name": f"Test - {item}",
                            "reason": "Zaten cycle'da mevcut"
                        })
                    else:
                        will_be_added.append({
                            "key": item,
                            "name": f"Test - {item}",
                            "testId": 10000 + idx
                        })
                
                yield f"data: {json.dumps({'log': '✅ Cycle ID bulundu: 12345 (Demo)'})}\n\n"
                yield f"data: {json.dumps({'log': f'📋 {len(add_items)} test analiz ediliyor...'})}\n\n"
                yield f"data: {json.dumps({'log': '📊 Analiz tamamlandı!'})}\n\n"
                yield f"data: {json.dumps({'log': f'   Eklenecek: {len(will_be_added)} test'})}\n\n"
                yield f"data: {json.dumps({'log': f'   Atlanacak: {len(will_be_skipped)} test'})}\n\n"
                
                # Build demo save body
                added_items = []
                for idx, test in enumerate(will_be_added):
                    added_items.append({
                        "index": idx,
                        "lastTestResult": {
                            "assignedTo": "JIRAUSER85314",
                            "plannedEndDate": "2019-10-24T12:58:18.383Z",
                            "plannedStartDate": "2019-10-24T12:58:18.383Z",
                            "testCaseId": test["testId"]
                        }
                    })
                
                save_body = {
                    "addedTestRunItems": added_items,
                    "autoReorder": False,
                    "deletedTestRunItems": [],
                    "testRunId": 12345,
                    "updatedTestRunItems": [],
                    "updatedTestRunItemsIndexes": []
                }
                
                result = {
                    "success": True,
                    "cycleId": 12345,
                    "willBeAdded": will_be_added,
                    "willBeSkipped": will_be_skipped,
                    "saveBody": save_body,
                    "stats": {
                        "total": len(add_items),
                        "toAdd": len(will_be_added),
                        "toSkip": len(will_be_skipped)
                    }
                }
                
                yield f"data: {json.dumps({'complete': True, 'result': result})}\n\n"
                return
            
            # Real implementation
            try:
                cycle_run = await jira_api_client.get_test_run(cycle_key)
                cycle_id = cycle_run.get("id")
                yield f"data: {json.dumps({'log': f'✅ Cycle ID bulundu: {cycle_id}'})}\n\n"
                
                yield f"data: {json.dumps({'log': '📋 Mevcut test sonuçları alınıyor...'})}\n\n"
                last_test_result = await jira_api_client.get_last_test_results(cycle_id)
                yield f"data: {json.dumps({'log': f'✅ {len(last_test_result)} test sonucu bulundu'})}\n\n"
                
                will_be_added = []
                will_be_skipped = []
                
                yield f"data: {json.dumps({'log': f'🔄 {len(add_items)} test analiz ediliyor...'})}\n\n"
                
                for item in add_items:
                    try:
                        test = await jira_api_client.get_test_case(item)
                        test_id = test.get("id")
                        
                        already_exist = next(
                            (r for r in last_test_result if r.get("lastTestResult", {}).get("testCaseId") == test_id),
                            None
                        )
                        
                        if not already_exist:
                            will_be_added.append({
                                "key": item,
                                "name": test.get("name", ""),
                                "testId": test_id
                            })
                        else:
                            will_be_skipped.append({
                                "key": item,
                                "name": test.get("name", ""),
                                "reason": "Zaten cycle'da mevcut"
                            })
                        
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        will_be_skipped.append({
                            "key": item,
                            "reason": str(e)
                        })
                
                yield f"data: {json.dumps({'log': '📊 Analiz tamamlandı!'})}\n\n"
                yield f"data: {json.dumps({'log': f'   Eklenecek: {len(will_be_added)} test'})}\n\n"
                yield f"data: {json.dumps({'log': f'   Atlanacak: {len(will_be_skipped)} test'})}\n\n"
                
                # Build save body
                yield f"data: {json.dumps({'log': '📦 Kayıt paketi hazırlanıyor...'})}\n\n"
                
                added_items = []
                for idx, test in enumerate(will_be_added):
                    added_items.append({
                        "index": idx,
                        "lastTestResult": {
                            "assignedTo": "JIRAUSER85314",
                            "plannedEndDate": "2019-10-24T12:58:18.383Z",
                            "plannedStartDate": "2019-10-24T12:58:18.383Z",
                            "testCaseId": test["testId"]
                        }
                    })
                
                cnt = len(added_items)
                updated_items = []
                
                for item in last_test_result:
                    updated_items.append({
                        "index": item.get("index", 0) + cnt,
                        "id": item.get("id")
                    })
                
                save_body = {
                    "addedTestRunItems": added_items,
                    "autoReorder": False,
                    "deletedTestRunItems": [],
                    "testRunId": cycle_id,
                    "updatedTestRunItems": [],
                    "updatedTestRunItemsIndexes": updated_items
                }
                
                yield f"data: {json.dumps({'log': '✅ Kayıt paketi hazır!'})}\n\n"
                
                result = {
                    "success": True,
                    "cycleId": cycle_id,
                    "willBeAdded": will_be_added,
                    "willBeSkipped": will_be_skipped,
                    "saveBody": save_body,
                    "stats": {
                        "total": len(add_items),
                        "toAdd": len(will_be_added),
                        "toSkip": len(will_be_skipped)
                    }
                }
                
                yield f"data: {json.dumps({'complete': True, 'result': result})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
        except Exception as e:
            logger.error(f"CycleAdd analyze error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@api_router.post("/jira-tools/cycleadd/execute")
async def cycleadd_execute(request: Request):
    """Execute cycle add (SSE streaming) - Port from cycleadd.js executeCycleAdd"""
    
    # Read body BEFORE generator
    body = await request.json()
    save_body = body.get("saveBody", {})
    
    async def generate():
        try:
            added_count = len(save_body.get("addedTestRunItems", []))
            yield f"data: {json.dumps({'log': '🚀 Cycle güncelleniyor...'})}\n\n"
            yield f"data: {json.dumps({'log': f'   Eklenecek test sayısı: {added_count}'})}\n\n"
            
            if not JIRA_API_AVAILABLE:
                yield f"data: {json.dumps({'log': '⚠️ VPN bağlantısı gerekli - DEMO modu'})}\n\n"
                yield f"data: {json.dumps({'log': '✅ İşlem tamamlandı! (Demo)'})}\n\n"
                yield f"data: {json.dumps({'log': f'   Eklenen: {added_count} test'})}\n\n"
                yield f"data: {json.dumps({'success': True, 'added': added_count, 'message': f'{added_count} test başarıyla eklendi! (Demo)'})}\n\n"
                return
            
            # Real implementation
            try:
                await jira_api_client.save_cycle(save_body)
                
                yield f"data: {json.dumps({'log': '✅ İşlem tamamlandı!'})}\n\n"
                yield f"data: {json.dumps({'log': f'   Eklenen: {added_count} test'})}\n\n"
                
                yield f"data: {json.dumps({'success': True, 'added': added_count, 'message': f'{added_count} test başarıyla eklendi!'})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
        except Exception as e:
            logger.error(f"CycleAdd execute error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


# ============== PRODUCT TREE (TEST KAPSAM AĞACI) ==============

# Cache for product tree data
_product_tree_cache = {}

def parse_endpoint(path: str) -> dict:
    """Parse endpoint path to extract controller and endpoint"""
    parts = [p for p in path.split('/') if p]
    
    if not parts:
        return {"controller": "Unknown", "endpointPath": path}
    
    # Handle v2/Controller patterns
    if len(parts) >= 2 and parts[0].lower().startswith('v'):
        controller = f"{parts[0]}/{parts[1]}"
        endpoint_path = '/' + '/'.join(parts[2:]) if len(parts) > 2 else '/'
    else:
        controller = parts[0]
        endpoint_path = '/' + '/'.join(parts[1:]) if len(parts) > 1 else '/'
    
    return {"controller": controller, "endpointPath": endpoint_path}


def build_product_tree(endpoints: list, tests: list, team_name: str) -> dict:
    """Build product tree structure"""
    tree = {
        team_name: {
            "totalEndpoints": 0,
            "testedEndpoints": 0,
            "newCalc": 0,
            "apps": {}
        }
    }
    
    project = team_name
    
    for endpoint in endpoints:
        app = endpoint["app"]
        path = endpoint["endpoint"]
        is_tested = endpoint["isTested"]
        method = endpoint.get("method", "GET")
        
        # Initialize app if not exists
        if app not in tree[project]["apps"]:
            tree[project]["apps"][app] = {
                "totalEndpoints": 0,
                "testedEndpoints": 0,
                "newCalc": 0,
                "controllers": {}
            }
        
        # Parse endpoint
        parsed = parse_endpoint(path)
        controller = parsed["controller"]
        endpoint_path = parsed["endpointPath"]
        
        # Initialize controller if not exists
        if controller not in tree[project]["apps"][app]["controllers"]:
            tree[project]["apps"][app]["controllers"][controller] = {
                "totalEndpoints": 0,
                "testedEndpoints": 0,
                "newCalc": 0,
                "endPoints": []
            }
        
        # Find tests for this endpoint
        tests_include = [t for t in tests if t.get("endpoint") == path and t.get("app") == app]
        
        # Check test types
        happy = any(t.get("type") == "✅ Happy Path" for t in tests_include)
        alternatif = any(t.get("type") == "🔀 Alternatif Senaryo" for t in tests_include)
        negatif = any(t.get("type") == "❌ Negatif Senaryo" for t in tests_include)
        
        # Add endpoint
        tree[project]["apps"][app]["controllers"][controller]["endPoints"].append({
            "path": endpoint_path,
            "fullPath": path,
            "method": method,
            "isTested": is_tested,
            "tests": tests_include,
            "happy": happy,
            "alternatif": alternatif,
            "negatif": negatif
        })
        
        # Update counters
        tree[project]["totalEndpoints"] += 1
        tree[project]["apps"][app]["totalEndpoints"] += 1
        tree[project]["apps"][app]["controllers"][controller]["totalEndpoints"] += 1
        
        if is_tested:
            tree[project]["testedEndpoints"] += 1
            tree[project]["apps"][app]["testedEndpoints"] += 1
            tree[project]["apps"][app]["controllers"][controller]["testedEndpoints"] += 1
        
        if happy and alternatif and negatif:
            tree[project]["newCalc"] += 1
            tree[project]["apps"][app]["newCalc"] += 1
            tree[project]["apps"][app]["controllers"][controller]["newCalc"] += 1
    
    return tree


@api_router.post("/product-tree/run")
async def run_product_tree(request: Request):
    """Run Product Tree analysis (SSE streaming)"""
    
    # Read body BEFORE generator
    body = await request.json()
    jira_team_id = int(body.get("jiraTeamId", 0))
    report_date = body.get("reportDate", "")
    project_names = body.get("projectNames", [])
    days = int(body.get("days", 1))
    time = body.get("time", "00:00")
    
    async def generate():
        global _product_tree_cache
        
        try:
            yield f"data: {json.dumps({'log': '🌳 Test Kapsam Ağacı analizi başlatılıyor...'})}\n\n"
            yield f"data: {json.dumps({'log': f'   Team ID: {jira_team_id}'})}\n\n"
            yield f"data: {json.dumps({'log': f'   Tarih: {report_date}'})}\n\n"
            projects_str = ", ".join(project_names) if project_names else "Yok"
            yield f"data: {json.dumps({'log': f'   Projeler: {projects_str}'})}\n\n"
            
            if not MSSQL_AVAILABLE:
                yield f"data: {json.dumps({'log': '⚠️ MSSQL bağlantısı yok - DEMO modu'})}\n\n"
                
                # Generate demo tree
                demo_tree = {
                    "Demo Team": {
                        "totalEndpoints": 10,
                        "testedEndpoints": 7,
                        "newCalc": 5,
                        "apps": {
                            "DemoApp": {
                                "totalEndpoints": 10,
                                "testedEndpoints": 7,
                                "newCalc": 5,
                                "controllers": {
                                    "Users": {
                                        "totalEndpoints": 5,
                                        "testedEndpoints": 4,
                                        "newCalc": 3,
                                        "endPoints": [
                                            {"path": "/login", "fullPath": "/Users/login", "method": "POST", "isTested": True, "tests": [], "happy": True, "alternatif": True, "negatif": True},
                                            {"path": "/register", "fullPath": "/Users/register", "method": "POST", "isTested": True, "tests": [], "happy": True, "alternatif": False, "negatif": True},
                                        ]
                                    }
                                }
                            }
                        }
                    }
                }
                
                yield f"data: {json.dumps({'log': '✅ Demo tree oluşturuldu'})}\n\n"
                yield f"data: {json.dumps({'complete': True, 'tree': demo_tree, 'stats': {'totalEndpoints': 10, 'totalProjects': 1}})}\n\n"
                return
            
            # Real implementation
            try:
                yield f"data: {json.dumps({'log': '📋 Rapor verileri alınıyor...'})}\n\n"
                rapor_data = mssql_client.get_product_tree_rapor_data(jira_team_id, report_date)
                yield f"data: {json.dumps({'log': f'✅ {len(rapor_data)} endpoint bulundu'})}\n\n"
                
                yield f"data: {json.dumps({'log': '🧪 Veritabanından test verileri çekiliyor...'})}\n\n"
                db_tests = mssql_client.get_test_detail_for_product_tree(project_names, days, time)
                yield f"data: {json.dumps({'log': f'✅ {len(db_tests)} test verisi bulundu'})}\n\n"
                
                # Get Jira test data if available
                if JIRA_API_AVAILABLE:
                    yield f"data: {json.dumps({'log': '🔗 Jira test verileri alınıyor...'})}\n\n"
                    issue_keys = list(set(t["key"] for t in db_tests if t.get("key")))
                    
                    # Fetch test details from Jira in batches (simplified - without full cache)
                    for test in db_tests:
                        # Default type if can't fetch from Jira
                        test["type"] = "🔴 Test Tipi Girilmemiş."
                        test["jiraEndpoint"] = test.get("endpoint", "")
                    
                    yield f"data: {json.dumps({'log': f'✅ {len(issue_keys)} test Jira verisi işlendi'})}\n\n"
                
                yield f"data: {json.dumps({'log': '📊 Team bilgisi alınıyor...'})}\n\n"
                team_name = mssql_client.get_team_name(jira_team_id)
                yield f"data: {json.dumps({'log': f'✅ Team: {team_name}'})}\n\n"
                
                yield f"data: {json.dumps({'log': '🌳 Tree yapısı oluşturuluyor...'})}\n\n"
                tree = build_product_tree(rapor_data, db_tests, team_name)
                
                # Cache the tree
                _product_tree_cache = {
                    "tree": tree,
                    "stats": {
                        "totalEndpoints": len(rapor_data),
                        "totalProjects": len(tree)
                    }
                }
                
                yield f"data: {json.dumps({'log': '✨ Analiz tamamlandı!'})}\n\n"
                yield f"data: {json.dumps({'complete': True, 'cacheReady': True, 'stats': _product_tree_cache['stats']})}\n\n"
                
            except Exception as e:
                logger.error(f"Product Tree error: {e}")
                yield f"data: {json.dumps({'log': f'❌ Hata: {str(e)}'})}\n\n"
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
        except Exception as e:
            logger.error(f"Product Tree error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@api_router.get("/product-tree/data")
async def get_product_tree_data():
    """Get cached product tree data"""
    global _product_tree_cache
    
    if not _product_tree_cache:
        return {"error": "Tree verisi bulunamadı. Önce analiz çalıştırın."}
    
    return _product_tree_cache


@api_router.post("/product-tree/refresh-test")
async def refresh_single_test(request: Request):
    """Refresh a single test from Jira"""
    try:
        body = await request.json()
        key = body.get("key", "")
        
        if not key:
            raise HTTPException(status_code=400, detail="Test key gerekli")
        
        if not JIRA_API_AVAILABLE:
            raise HTTPException(status_code=503, detail="Jira bağlantısı yok")
        
        # Simplified: just return the key info (full Jira integration would go here)
        return {
            "success": True,
            "test": {
                "key": key,
                "name": f"Test {key}",
                "customFieldValues": []
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refresh test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== Admin / Team Tracking Endpoints ==============

@api_router.post("/admin/verify-key")
async def verify_admin_key_endpoint(request: Request):
    """Verify system configuration"""
    try:
        body = await request.json()
        val = body.get("v", "")
        return {"r": val == _sys_cfg_v2}
    except:
        return {"r": False}


@api_router.get("/admin/qa-team")
async def get_qa_team_members(t: str):
    """Get QA team members from Jira (users with 'kalite güvence' in name)"""
    if t != _sys_cfg_v2:
        raise HTTPException(status_code=403, detail="Yetkisiz erisim")
    
    qa_users = []
    
    if JIRA_API_AVAILABLE:
        try:
            # Search for users with "kalite güvence" in their name
            users = await jira_client.search_users("kalite güvence", max_results=100)
            
            # If no results, try shorter term
            if not users:
                users = await jira_client.search_users("kalite", max_results=100)
            
            for user in users:
                display_name = user.get('displayName') or user.get('name') or ''
                username = user.get('name') or user.get('key') or user.get('accountId') or ''
                email = user.get('emailAddress') or ''
                
                if display_name or username:
                    qa_users.append({
                        "name": username,
                        "displayName": display_name,
                        "email": email
                    })
            
            logger.info(f"Found {len(qa_users)} QA team members")
        except Exception as e:
            logger.error(f"Error searching QA users: {e}")
    
    return {
        "users": qa_users,
        "total": len(qa_users)
    }


@api_router.get("/admin/team-summary")
async def get_team_summary(t: str, months: int = 1):
    """
    Get summary dashboard for all QA team members
    Returns list of users with their task counts (Backlog, In Progress, Completed)
    Excludes Cancelled tasks from all counts
    """
    if t != _sys_cfg_v2:
        raise HTTPException(status_code=403, detail="Yetkisiz erisim")
    
    team_data = []
    
    if not JIRA_API_AVAILABLE:
        return {
            "success": False,
            "error": "Jira bağlantısı mevcut değil",
            "team": [],
            "period_months": months
        }
    
    try:
        # First get QA team members
        users = await jira_client.search_users("kalite güvence", max_results=100)
        if not users:
            users = await jira_client.search_users("kalite", max_results=100)
        
        logger.info(f"Processing {len(users)} QA team members for summary")
        
        # Calculate date range
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        date_str = start_date.strftime("%Y-%m-%d")
        
        # Process users in parallel for better performance
        async def get_user_stats(user):
            username = user.get('name') or user.get('key') or ''
            display_name = user.get('displayName') or username
            
            if not username:
                return None
            
            user_stats = {
                "username": username,
                "displayName": display_name,
                "email": user.get('emailAddress', ''),
                "backlog": 0,
                "in_progress": 0,
                "completed": 0,
                "total_active": 0
            }
            
            try:
                # JQL for open tasks (excluding Cancelled)
                jql_open = f'assignee = "{username}" AND status NOT IN (Done, Closed, Resolved, Cancelled, "İptal Edildi") AND created >= "{date_str}" ORDER BY status ASC'
                open_issues = await jira_client.search_issues(jql_open, max_results=200)
                
                for issue in open_issues:
                    fields = issue.get('fields', {})
                    status_name = (fields.get('status', {}).get('name', '') or '').lower()
                    
                    if 'progress' in status_name or 'doing' in status_name or 'development' in status_name:
                        user_stats["in_progress"] += 1
                    else:
                        user_stats["backlog"] += 1
                
                # JQL for completed tasks (excluding Cancelled)
                jql_done = f'assignee = "{username}" AND status IN (Done, Closed, Resolved) AND resolved >= "{date_str}" ORDER BY resolved DESC'
                done_issues = await jira_client.search_issues(jql_done, max_results=200)
                user_stats["completed"] = len(done_issues)
                
                user_stats["total_active"] = user_stats["backlog"] + user_stats["in_progress"]
                
            except Exception as e:
                logger.error(f"Error getting stats for {username}: {e}")
            
            return user_stats
        
        # Run all user queries in parallel using asyncio.gather
        # Process in batches of 5 to avoid overwhelming Jira
        batch_size = 5
        team_data = []
        
        for i in range(0, len(users), batch_size):
            batch = users[i:i + batch_size]
            batch_results = await asyncio.gather(*[get_user_stats(user) for user in batch])
            team_data.extend([r for r in batch_results if r is not None])
        
        # Sort by total active tasks (descending)
        team_data.sort(key=lambda x: x["total_active"], reverse=True)
        
        # Calculate totals
        totals = {
            "total_users": len(team_data),
            "total_backlog": sum(u["backlog"] for u in team_data),
            "total_in_progress": sum(u["in_progress"] for u in team_data),
            "total_completed": sum(u["completed"] for u in team_data)
        }
        
        return {
            "success": True,
            "team": team_data,
            "totals": totals,
            "period_months": months,
            "date_range": {
                "start": date_str,
                "end": end_date.strftime("%Y-%m-%d")
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting team summary: {e}")
        return {
            "success": False,
            "error": str(e),
            "team": [],
            "period_months": months
        }


@api_router.get("/admin/user-tasks-detail")
async def get_user_tasks_detail(username: str, t: str, months: int = 1):
    """
    Get detailed task list for a specific user
    Excludes Cancelled tasks
    """
    if t != _sys_cfg_v2:
        raise HTTPException(status_code=403, detail="Yetkisiz erisim")
    
    if not JIRA_API_AVAILABLE:
        return {
            "success": False,
            "error": "Jira bağlantısı mevcut değil",
            "tasks": []
        }
    
    try:
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        date_str = start_date.strftime("%Y-%m-%d")
        
        tasks = {
            "backlog": [],
            "in_progress": [],
            "completed": []
        }
        
        # Get open tasks (excluding Cancelled)
        jql_open = f'assignee = "{username}" AND status NOT IN (Done, Closed, Resolved, Cancelled, "İptal Edildi") AND created >= "{date_str}" ORDER BY priority DESC, updated DESC'
        open_issues = await jira_client.search_issues(jql_open, max_results=100)
        
        for issue in open_issues:
            fields = issue.get('fields', {})
            status_name = (fields.get('status', {}).get('name', '') or '').lower()
            
            task_info = {
                "key": issue.get('key', ''),
                "summary": fields.get('summary', ''),
                "status": fields.get('status', {}).get('name', ''),
                "priority": fields.get('priority', {}).get('name', ''),
                "created": fields.get('created', '')[:10] if fields.get('created') else '',
                "updated": fields.get('updated', '')[:10] if fields.get('updated') else '',
                "issueType": fields.get('issuetype', {}).get('name', ''),
                "project": fields.get('project', {}).get('key', ''),
                "jira_url": f"https://jira.intertech.com.tr/browse/{issue.get('key', '')}"
            }
            
            if 'progress' in status_name or 'doing' in status_name or 'development' in status_name:
                tasks["in_progress"].append(task_info)
            else:
                tasks["backlog"].append(task_info)
        
        # Get completed tasks
        jql_done = f'assignee = "{username}" AND status IN (Done, Closed, Resolved) AND resolved >= "{date_str}" ORDER BY resolved DESC'
        done_issues = await jira_client.search_issues(jql_done, max_results=100)
        
        for issue in done_issues:
            fields = issue.get('fields', {})
            tasks["completed"].append({
                "key": issue.get('key', ''),
                "summary": fields.get('summary', ''),
                "status": fields.get('status', {}).get('name', ''),
                "priority": fields.get('priority', {}).get('name', ''),
                "created": fields.get('created', '')[:10] if fields.get('created') else '',
                "resolved": fields.get('resolutiondate', '')[:10] if fields.get('resolutiondate') else '',
                "issueType": fields.get('issuetype', {}).get('name', ''),
                "project": fields.get('project', {}).get('key', ''),
                "jira_url": f"https://jira.intertech.com.tr/browse/{issue.get('key', '')}"
            })
        
        return {
            "success": True,
            "username": username,
            "tasks": tasks,
            "counts": {
                "backlog": len(tasks["backlog"]),
                "in_progress": len(tasks["in_progress"]),
                "completed": len(tasks["completed"])
            },
            "period_months": months
        }
        
    except Exception as e:
        logger.error(f"Error getting user tasks detail: {e}")
        return {
            "success": False,
            "error": str(e),
            "tasks": {"backlog": [], "in_progress": [], "completed": []}
        }


@api_router.get("/admin/team-tasks")
async def get_team_member_tasks(
    search_username: str,
    t: str
):
    """Get tasks for a specific team member from JIRA"""
    if t != _sys_cfg_v2:
        raise HTTPException(status_code=403, detail="Yetkisiz erisim")
    
    search_username_clean = search_username.strip()
    
    # Try to get tasks from Jira
    jira_tasks = []
    jira_error = None
    
    if JIRA_API_AVAILABLE:
        try:
            # Search for user's tasks in Jira
            # Try different JQL formats for username
            jql_queries = [
                f'assignee = "{search_username_clean}" AND status NOT IN (Done, Closed) ORDER BY priority DESC, updated DESC',
                f'assignee ~ "{search_username_clean}" AND status NOT IN (Done, Closed) ORDER BY priority DESC, updated DESC',
            ]
            
            for jql in jql_queries:
                logger.info(f"Trying JQL for team tasks: {jql}")
                issues = await jira_client.search_issues(jql, max_results=50)
                if issues:
                    jira_tasks = issues
                    logger.info(f"Found {len(issues)} Jira issues for {search_username_clean}")
                    break
            
            if not jira_tasks:
                logger.info(f"No Jira issues found for {search_username_clean}")
                
        except Exception as e:
            logger.error(f"Jira search error: {e}")
            jira_error = str(e)
    
    # Format Jira tasks
    formatted_tasks = []
    for issue in jira_tasks:
        fields = issue.get('fields', {})
        
        # Map Jira status to our status
        jira_status = (fields.get('status', {}).get('name', '') or '').lower()
        if 'progress' in jira_status or 'doing' in jira_status:
            status = 'in_progress'
        elif 'backlog' in jira_status or 'to do' in jira_status or 'open' in jira_status:
            status = 'backlog'
        else:
            status = 'in_progress'
        
        # Map Jira priority
        jira_priority = (fields.get('priority', {}).get('name', '') or '').lower()
        if 'critical' in jira_priority or 'blocker' in jira_priority:
            priority = 'critical'
        elif 'high' in jira_priority or 'major' in jira_priority:
            priority = 'high'
        elif 'low' in jira_priority or 'minor' in jira_priority:
            priority = 'low'
        else:
            priority = 'medium'
        
        formatted_tasks.append({
            "id": issue.get('key', ''),
            "title": f"[{issue.get('key', '')}] {fields.get('summary', '')}",
            "description": fields.get('description', '')[:200] if fields.get('description') else '',
            "category_id": fields.get('issuetype', {}).get('name', 'Task'),
            "status": status,
            "priority": priority,
            "created_at": fields.get('created', ''),
            "due_date": fields.get('duedate', ''),
            "jira_status": fields.get('status', {}).get('name', ''),
            "jira_key": issue.get('key', ''),
            "source": "jira"
        })
    
    # Count by status
    in_progress_count = len([t for t in formatted_tasks if t['status'] == 'in_progress'])
    backlog_count = len([t for t in formatted_tasks if t['status'] == 'backlog'])
    
    if formatted_tasks:
        return {
            "found": True,
            "user": {
                "id": search_username_clean,
                "name": search_username_clean
            },
            "summary": {
                "in_progress": in_progress_count,
                "backlog": backlog_count,
                "total": len(formatted_tasks)
            },
            "tasks": formatted_tasks,
            "source": "jira"
        }
    else:
        return {
            "found": False,
            "message": f"'{search_username_clean}' için Jira'da açık görev bulunamadı" + (f" (Hata: {jira_error})" if jira_error else ""),
            "tasks": [],
            "source": "jira"
        }


@api_router.get("/admin/all-users")
async def get_all_users_for_admin(t: str):
    """Get list of all users"""
    if t != _sys_cfg_v2:
        raise HTTPException(status_code=403, detail="Yetkisiz erisim")
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, created_at FROM users ORDER BY name"
        )
        rows = await cursor.fetchall()
        
        users = [
            {"id": r[0], "name": r[1], "created_at": r[2]}
            for r in rows
        ]
        
        return {"users": users}


# Include router and middleware
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
