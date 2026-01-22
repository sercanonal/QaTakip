from fastapi import FastAPI, APIRouter, HTTPException, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="QA Task Manager - Intertech")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
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

# Models
class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(BaseModel):
    email: EmailStr

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    categories: List[dict] = Field(default_factory=lambda: DEFAULT_CATEGORIES.copy())

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
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

class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    user_id: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    task_count: int = 0

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

class Task(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    category_id: str
    project_id: Optional[str] = None
    user_id: str
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None

class NotificationBase(BaseModel):
    title: str
    message: str
    type: str = "info"

class Notification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    message: str
    type: str = "info"
    is_read: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# Helper function to get user from email header
async def get_current_user(email: str) -> dict:
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    return user

# Auth Routes
@api_router.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    # Validate Intertech email
    if not user_data.email.endswith("@intertech.com.tr"):
        raise HTTPException(status_code=400, detail="Sadece @intertech.com.tr uzantılı e-postalar kabul edilir")
    
    # Check if user exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı")
    
    # Extract name from email
    name = user_data.email.split("@")[0].replace(".", " ").title()
    
    user = User(email=user_data.email, name=name)
    user_dict = user.model_dump()
    
    await db.users.insert_one(user_dict)
    
    # Create welcome notification
    notification = Notification(
        user_id=user.id,
        title="Hoş Geldiniz!",
        message=f"QA Task Manager'a hoş geldiniz, {name}!",
        type="success"
    )
    await db.notifications.insert_one(notification.model_dump())
    
    return UserResponse(**user_dict)

@api_router.post("/auth/login", response_model=UserResponse)
async def login(user_data: UserCreate):
    # Validate Intertech email
    if not user_data.email.endswith("@intertech.com.tr"):
        raise HTTPException(status_code=400, detail="Sadece @intertech.com.tr uzantılı e-postalar kabul edilir")
    
    user = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı. Lütfen önce kayıt olun.")
    
    return UserResponse(**user)

# User Routes
@api_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    return UserResponse(**user)

@api_router.post("/users/{user_id}/categories", response_model=UserResponse)
async def add_category(user_id: str, category: Category):
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    category_dict = category.model_dump()
    category_dict["is_default"] = False
    
    await db.users.update_one(
        {"id": user_id},
        {"$push": {"categories": category_dict}}
    )
    
    updated_user = await db.users.find_one({"id": user_id}, {"_id": 0})
    return UserResponse(**updated_user)

@api_router.delete("/users/{user_id}/categories/{category_id}", response_model=UserResponse)
async def delete_category(user_id: str, category_id: str):
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    
    # Check if category is default
    for cat in user.get("categories", []):
        if cat["id"] == category_id and cat.get("is_default"):
            raise HTTPException(status_code=400, detail="Varsayılan kategoriler silinemez")
    
    await db.users.update_one(
        {"id": user_id},
        {"$pull": {"categories": {"id": category_id}}}
    )
    
    updated_user = await db.users.find_one({"id": user_id}, {"_id": 0})
    return UserResponse(**updated_user)

# Project Routes
@api_router.post("/projects", response_model=dict)
async def create_project(project: ProjectBase, user_id: str):
    project_obj = Project(
        name=project.name,
        description=project.description or "",
        user_id=user_id
    )
    project_dict = project_obj.model_dump()
    
    await db.projects.insert_one(project_dict)
    # Return clean dict without MongoDB ObjectId
    return {k: v for k, v in project_dict.items() if k != "_id"}

@api_router.get("/projects", response_model=List[dict])
async def get_projects(user_id: str):
    projects = await db.projects.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    
    # Update task counts
    for project in projects:
        task_count = await db.tasks.count_documents({"project_id": project["id"]})
        project["task_count"] = task_count
    
    return projects

@api_router.get("/projects/{project_id}", response_model=dict)
async def get_project(project_id: str):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Proje bulunamadı")
    return project

@api_router.put("/projects/{project_id}", response_model=dict)
async def update_project(project_id: str, project: ProjectBase):
    result = await db.projects.update_one(
        {"id": project_id},
        {"$set": {"name": project.name, "description": project.description}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Proje bulunamadı")
    
    updated = await db.projects.find_one({"id": project_id}, {"_id": 0})
    return updated

@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    # Delete all tasks in project
    await db.tasks.delete_many({"project_id": project_id})
    
    result = await db.projects.delete_one({"id": project_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Proje bulunamadı")
    
    return {"message": "Proje silindi"}

# Task Routes
@api_router.post("/tasks", response_model=dict)
async def create_task(task: TaskCreate, user_id: str):
    task_obj = Task(
        title=task.title,
        description=task.description or "",
        category_id=task.category_id,
        project_id=task.project_id,
        user_id=user_id,
        priority=task.priority,
        due_date=task.due_date
    )
    task_dict = task_obj.model_dump()
    
    await db.tasks.insert_one(task_dict)
    # Return clean dict without MongoDB ObjectId
    return {k: v for k, v in task_dict.items() if k != "_id"}

@api_router.get("/tasks", response_model=List[dict])
async def get_tasks(
    user_id: str,
    status: Optional[str] = None,
    category_id: Optional[str] = None,
    project_id: Optional[str] = None,
    priority: Optional[str] = None
):
    query = {"user_id": user_id}
    
    if status:
        query["status"] = status
    if category_id:
        query["category_id"] = category_id
    if project_id:
        query["project_id"] = project_id
    if priority:
        query["priority"] = priority
    
    tasks = await db.tasks.find(query, {"_id": 0}).to_list(1000)
    return tasks

@api_router.get("/tasks/{task_id}", response_model=dict)
async def get_task(task_id: str):
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Görev bulunamadı")
    return task

@api_router.put("/tasks/{task_id}", response_model=dict)
async def update_task(task_id: str, task_update: TaskUpdate):
    update_data = {k: v for k, v in task_update.model_dump().items() if v is not None}
    
    # If status is being set to completed, add completed_at
    if update_data.get("status") == TaskStatus.COMPLETED:
        update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
    elif update_data.get("status") and update_data.get("status") != TaskStatus.COMPLETED:
        update_data["completed_at"] = None
    
    if not update_data:
        raise HTTPException(status_code=400, detail="Güncellenecek alan bulunamadı")
    
    result = await db.tasks.update_one(
        {"id": task_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Görev bulunamadı")
    
    updated = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    return updated

@api_router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    result = await db.tasks.delete_one({"id": task_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Görev bulunamadı")
    return {"message": "Görev silindi"}

# Dashboard Stats
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(user_id: str):
    total_tasks = await db.tasks.count_documents({"user_id": user_id})
    completed_tasks = await db.tasks.count_documents({"user_id": user_id, "status": TaskStatus.COMPLETED})
    in_progress_tasks = await db.tasks.count_documents({"user_id": user_id, "status": TaskStatus.IN_PROGRESS})
    todo_tasks = await db.tasks.count_documents({"user_id": user_id, "status": TaskStatus.TODO})
    
    # Tasks by category
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$category_id", "count": {"$sum": 1}}}
    ]
    category_stats = await db.tasks.aggregate(pipeline).to_list(100)
    
    # Tasks by priority
    priority_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$priority", "count": {"$sum": 1}}}
    ]
    priority_stats = await db.tasks.aggregate(priority_pipeline).to_list(100)
    
    # Recent tasks
    recent_tasks = await db.tasks.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    # Overdue tasks (due_date < now and status != completed)
    now = datetime.now(timezone.utc).isoformat()
    overdue_tasks = await db.tasks.count_documents({
        "user_id": user_id,
        "due_date": {"$lt": now, "$ne": None},
        "status": {"$ne": TaskStatus.COMPLETED}
    })
    
    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "in_progress_tasks": in_progress_tasks,
        "todo_tasks": todo_tasks,
        "overdue_tasks": overdue_tasks,
        "completion_rate": round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1),
        "category_stats": {stat["_id"]: stat["count"] for stat in category_stats},
        "priority_stats": {stat["_id"]: stat["count"] for stat in priority_stats},
        "recent_tasks": recent_tasks
    }

# Notification Routes
@api_router.get("/notifications", response_model=List[dict])
async def get_notifications(user_id: str):
    notifications = await db.notifications.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return notifications

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    result = await db.notifications.update_one(
        {"id": notification_id},
        {"$set": {"is_read": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Bildirim bulunamadı")
    return {"message": "Bildirim okundu olarak işaretlendi"}

@api_router.put("/notifications/read-all")
async def mark_all_notifications_read(user_id: str):
    await db.notifications.update_many(
        {"user_id": user_id, "is_read": False},
        {"$set": {"is_read": True}}
    )
    return {"message": "Tüm bildirimler okundu olarak işaretlendi"}

@api_router.delete("/notifications/{notification_id}")
async def delete_notification(notification_id: str):
    result = await db.notifications.delete_one({"id": notification_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Bildirim bulunamadı")
    return {"message": "Bildirim silindi"}

# Health check
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
