"""
QA Task Manager - Backend API Tests
Tests for: Auth, Tasks, Projects, Notifications, Daily Summary
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test user data
TEST_DEVICE_ID = f"test_device_{uuid.uuid4().hex[:8]}"
TEST_USER_NAME = f"TEST_User_{uuid.uuid4().hex[:6]}"


class TestHealthCheck:
    """Health check endpoint tests"""
    
    def test_health_endpoint(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "sqlite"
        assert "timestamp" in data
        print(f"✓ Health check passed: {data}")


class TestAuthEndpoints:
    """Authentication endpoint tests - device-based auth"""
    
    @pytest.fixture(scope="class")
    def registered_user(self):
        """Register a test user and return user data"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": TEST_USER_NAME,
            "device_id": TEST_DEVICE_ID
        })
        assert response.status_code == 200
        return response.json()
    
    def test_register_new_user(self, registered_user):
        """Test user registration with device_id"""
        assert "id" in registered_user
        assert registered_user["name"] == TEST_USER_NAME
        assert registered_user["device_id"] == TEST_DEVICE_ID
        assert "categories" in registered_user
        assert len(registered_user["categories"]) == 5  # Default categories
        print(f"✓ User registered: {registered_user['name']}")
    
    def test_register_same_device_returns_existing_user(self, registered_user):
        """Test that registering same device returns existing user"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Different Name",
            "device_id": TEST_DEVICE_ID
        })
        assert response.status_code == 200
        data = response.json()
        # Should return existing user, not create new
        assert data["id"] == registered_user["id"]
        assert data["name"] == TEST_USER_NAME  # Original name preserved
        print("✓ Same device returns existing user")
    
    def test_check_device_registered(self, registered_user):
        """Test /api/auth/check/{device_id} for registered device"""
        response = requests.get(f"{BASE_URL}/api/auth/check/{TEST_DEVICE_ID}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == registered_user["id"]
        assert data["name"] == TEST_USER_NAME
        print("✓ Device check returns correct user")
    
    def test_check_device_not_registered(self):
        """Test /api/auth/check/{device_id} for unregistered device"""
        fake_device = f"fake_device_{uuid.uuid4().hex}"
        response = requests.get(f"{BASE_URL}/api/auth/check/{fake_device}")
        assert response.status_code == 404
        print("✓ Unregistered device returns 404")
    
    def test_register_empty_name_fails(self):
        """Test registration with empty name fails"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "",
            "device_id": f"test_{uuid.uuid4().hex}"
        })
        assert response.status_code == 400
        print("✓ Empty name registration rejected")


class TestTaskEndpoints:
    """Task CRUD endpoint tests"""
    
    @pytest.fixture(scope="class")
    def test_user(self):
        """Create a test user for task tests"""
        device_id = f"task_test_device_{uuid.uuid4().hex[:8]}"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": f"TEST_TaskUser_{uuid.uuid4().hex[:6]}",
            "device_id": device_id
        })
        return response.json()
    
    @pytest.fixture(scope="class")
    def created_task(self, test_user):
        """Create a task for testing"""
        response = requests.post(f"{BASE_URL}/api/tasks?user_id={test_user['id']}", json={
            "title": "TEST_Task_API_Test",
            "description": "Test task description",
            "category_id": "api-test",
            "priority": "high"
        })
        assert response.status_code == 200
        return response.json()
    
    def test_create_task(self, created_task, test_user):
        """Test task creation"""
        assert "id" in created_task
        assert created_task["title"] == "TEST_Task_API_Test"
        assert created_task["status"] == "todo"
        assert created_task["priority"] == "high"
        assert created_task["user_id"] == test_user["id"]
        print(f"✓ Task created: {created_task['id']}")
    
    def test_get_tasks(self, test_user, created_task):
        """Test getting all tasks for user"""
        response = requests.get(f"{BASE_URL}/api/tasks?user_id={test_user['id']}")
        assert response.status_code == 200
        tasks = response.json()
        assert isinstance(tasks, list)
        assert len(tasks) >= 1
        task_ids = [t["id"] for t in tasks]
        assert created_task["id"] in task_ids
        print(f"✓ Got {len(tasks)} tasks")
    
    def test_get_single_task(self, created_task):
        """Test getting a single task by ID"""
        response = requests.get(f"{BASE_URL}/api/tasks/{created_task['id']}")
        assert response.status_code == 200
        task = response.json()
        assert task["id"] == created_task["id"]
        assert task["title"] == "TEST_Task_API_Test"
        print("✓ Single task retrieved")
    
    def test_update_task_status(self, created_task):
        """Test updating task status - critical for Kanban drag & drop"""
        response = requests.put(f"{BASE_URL}/api/tasks/{created_task['id']}", json={
            "status": "in_progress"
        })
        assert response.status_code == 200
        task = response.json()
        assert task["status"] == "in_progress"
        print("✓ Task status updated to in_progress")
        
        # Update to completed
        response = requests.put(f"{BASE_URL}/api/tasks/{created_task['id']}", json={
            "status": "completed"
        })
        assert response.status_code == 200
        task = response.json()
        assert task["status"] == "completed"
        assert task["completed_at"] is not None
        print("✓ Task status updated to completed with completed_at timestamp")
    
    def test_update_task_priority(self, created_task):
        """Test updating task priority"""
        response = requests.put(f"{BASE_URL}/api/tasks/{created_task['id']}", json={
            "priority": "critical"
        })
        assert response.status_code == 200
        task = response.json()
        assert task["priority"] == "critical"
        print("✓ Task priority updated")
    
    def test_filter_tasks_by_status(self, test_user):
        """Test filtering tasks by status"""
        response = requests.get(f"{BASE_URL}/api/tasks?user_id={test_user['id']}&status=completed")
        assert response.status_code == 200
        tasks = response.json()
        for task in tasks:
            assert task["status"] == "completed"
        print(f"✓ Filtered {len(tasks)} completed tasks")
    
    def test_delete_task(self, test_user):
        """Test task deletion"""
        # Create a task to delete
        create_response = requests.post(f"{BASE_URL}/api/tasks?user_id={test_user['id']}", json={
            "title": "TEST_Task_To_Delete",
            "category_id": "api-test",
            "priority": "low"
        })
        task_id = create_response.json()["id"]
        
        # Delete it
        delete_response = requests.delete(f"{BASE_URL}/api/tasks/{task_id}")
        assert delete_response.status_code == 200
        
        # Verify it's gone
        get_response = requests.get(f"{BASE_URL}/api/tasks/{task_id}")
        assert get_response.status_code == 404
        print("✓ Task deleted and verified")


class TestNotificationEndpoints:
    """Notification system endpoint tests"""
    
    @pytest.fixture(scope="class")
    def test_user(self):
        """Create a test user for notification tests"""
        device_id = f"notif_test_device_{uuid.uuid4().hex[:8]}"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": f"TEST_NotifUser_{uuid.uuid4().hex[:6]}",
            "device_id": device_id
        })
        return response.json()
    
    def test_get_notifications(self, test_user):
        """Test /api/notifications endpoint"""
        response = requests.get(f"{BASE_URL}/api/notifications?user_id={test_user['id']}")
        assert response.status_code == 200
        notifications = response.json()
        assert isinstance(notifications, list)
        # New user should have welcome notification
        assert len(notifications) >= 1
        welcome_notif = notifications[0]
        assert "Hoş Geldiniz" in welcome_notif["title"]
        assert welcome_notif["type"] == "success"
        assert welcome_notif["is_read"] == False
        print(f"✓ Got {len(notifications)} notifications, welcome notification present")
    
    def test_mark_notification_read(self, test_user):
        """Test marking notification as read"""
        # Get notifications
        response = requests.get(f"{BASE_URL}/api/notifications?user_id={test_user['id']}")
        notifications = response.json()
        notif_id = notifications[0]["id"]
        
        # Mark as read
        response = requests.put(f"{BASE_URL}/api/notifications/{notif_id}/read")
        assert response.status_code == 200
        
        # Verify it's marked as read
        response = requests.get(f"{BASE_URL}/api/notifications?user_id={test_user['id']}")
        notifications = response.json()
        marked_notif = next(n for n in notifications if n["id"] == notif_id)
        assert marked_notif["is_read"] == True
        print("✓ Notification marked as read")
    
    def test_mark_all_notifications_read(self, test_user):
        """Test marking all notifications as read"""
        response = requests.put(f"{BASE_URL}/api/notifications/read-all?user_id={test_user['id']}")
        assert response.status_code == 200
        
        # Verify all are read
        response = requests.get(f"{BASE_URL}/api/notifications?user_id={test_user['id']}")
        notifications = response.json()
        for notif in notifications:
            assert notif["is_read"] == True
        print("✓ All notifications marked as read")


class TestDailySummaryEndpoint:
    """Daily Summary endpoint tests - for standup meetings"""
    
    @pytest.fixture(scope="class")
    def test_user_with_tasks(self):
        """Create a test user with various task statuses"""
        device_id = f"daily_test_device_{uuid.uuid4().hex[:8]}"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": f"TEST_DailyUser_{uuid.uuid4().hex[:6]}",
            "device_id": device_id
        })
        user = response.json()
        
        # Create tasks with different statuses
        # In Progress task
        requests.post(f"{BASE_URL}/api/tasks?user_id={user['id']}", json={
            "title": "TEST_InProgress_Task",
            "category_id": "api-test",
            "priority": "high"
        })
        task_resp = requests.get(f"{BASE_URL}/api/tasks?user_id={user['id']}")
        task_id = task_resp.json()[0]["id"]
        requests.put(f"{BASE_URL}/api/tasks/{task_id}", json={"status": "in_progress"})
        
        # Blocked task
        blocked_resp = requests.post(f"{BASE_URL}/api/tasks?user_id={user['id']}", json={
            "title": "TEST_Blocked_Task",
            "category_id": "bug-tracking",
            "priority": "critical"
        })
        blocked_id = blocked_resp.json()["id"]
        requests.put(f"{BASE_URL}/api/tasks/{blocked_id}", json={"status": "blocked"})
        
        # Todo task with high priority (should appear in today_planned)
        requests.post(f"{BASE_URL}/api/tasks?user_id={user['id']}", json={
            "title": "TEST_HighPriority_Todo",
            "category_id": "ui-test",
            "priority": "high"
        })
        
        return user
    
    def test_daily_summary_endpoint(self, test_user_with_tasks):
        """Test /api/daily-summary endpoint structure"""
        response = requests.get(f"{BASE_URL}/api/daily-summary?user_id={test_user_with_tasks['id']}")
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "yesterday_completed" in data
        assert "today_in_progress" in data
        assert "blocked_tasks" in data
        assert "today_planned" in data
        assert "summary" in data
        
        # Check summary counts
        assert "yesterday_count" in data["summary"]
        assert "in_progress_count" in data["summary"]
        assert "blocked_count" in data["summary"]
        assert "planned_count" in data["summary"]
        
        print(f"✓ Daily summary structure correct")
        print(f"  - Yesterday completed: {data['summary']['yesterday_count']}")
        print(f"  - In progress: {data['summary']['in_progress_count']}")
        print(f"  - Blocked: {data['summary']['blocked_count']}")
        print(f"  - Planned: {data['summary']['planned_count']}")
    
    def test_daily_summary_in_progress_tasks(self, test_user_with_tasks):
        """Test that in_progress tasks appear in daily summary"""
        response = requests.get(f"{BASE_URL}/api/daily-summary?user_id={test_user_with_tasks['id']}")
        data = response.json()
        
        assert len(data["today_in_progress"]) >= 1
        in_progress_titles = [t["title"] for t in data["today_in_progress"]]
        assert "TEST_InProgress_Task" in in_progress_titles
        print("✓ In-progress tasks appear in daily summary")
    
    def test_daily_summary_blocked_tasks(self, test_user_with_tasks):
        """Test that blocked tasks appear in daily summary"""
        response = requests.get(f"{BASE_URL}/api/daily-summary?user_id={test_user_with_tasks['id']}")
        data = response.json()
        
        assert len(data["blocked_tasks"]) >= 1
        blocked_titles = [t["title"] for t in data["blocked_tasks"]]
        assert "TEST_Blocked_Task" in blocked_titles
        print("✓ Blocked tasks appear in daily summary")
    
    def test_daily_summary_planned_tasks(self, test_user_with_tasks):
        """Test that high priority todo tasks appear in today_planned"""
        response = requests.get(f"{BASE_URL}/api/daily-summary?user_id={test_user_with_tasks['id']}")
        data = response.json()
        
        assert len(data["today_planned"]) >= 1
        planned_titles = [t["title"] for t in data["today_planned"]]
        assert "TEST_HighPriority_Todo" in planned_titles
        print("✓ High priority todo tasks appear in today_planned")


class TestProjectEndpoints:
    """Project CRUD endpoint tests"""
    
    @pytest.fixture(scope="class")
    def test_user(self):
        """Create a test user for project tests"""
        device_id = f"proj_test_device_{uuid.uuid4().hex[:8]}"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": f"TEST_ProjUser_{uuid.uuid4().hex[:6]}",
            "device_id": device_id
        })
        return response.json()
    
    @pytest.fixture(scope="class")
    def created_project(self, test_user):
        """Create a project for testing"""
        response = requests.post(f"{BASE_URL}/api/projects?user_id={test_user['id']}", json={
            "name": "TEST_Project_API",
            "description": "Test project description"
        })
        assert response.status_code == 200
        return response.json()
    
    def test_create_project(self, created_project, test_user):
        """Test project creation"""
        assert "id" in created_project
        assert created_project["name"] == "TEST_Project_API"
        assert created_project["user_id"] == test_user["id"]
        print(f"✓ Project created: {created_project['id']}")
    
    def test_get_projects(self, test_user, created_project):
        """Test getting all projects for user"""
        response = requests.get(f"{BASE_URL}/api/projects?user_id={test_user['id']}")
        assert response.status_code == 200
        projects = response.json()
        assert isinstance(projects, list)
        assert len(projects) >= 1
        project_ids = [p["id"] for p in projects]
        assert created_project["id"] in project_ids
        print(f"✓ Got {len(projects)} projects")
    
    def test_update_project(self, created_project):
        """Test project update"""
        response = requests.put(f"{BASE_URL}/api/projects/{created_project['id']}", json={
            "name": "TEST_Project_Updated",
            "description": "Updated description"
        })
        assert response.status_code == 200
        project = response.json()
        assert project["name"] == "TEST_Project_Updated"
        print("✓ Project updated")


class TestDashboardStats:
    """Dashboard statistics endpoint tests"""
    
    @pytest.fixture(scope="class")
    def test_user(self):
        """Create a test user for dashboard tests"""
        device_id = f"dash_test_device_{uuid.uuid4().hex[:8]}"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": f"TEST_DashUser_{uuid.uuid4().hex[:6]}",
            "device_id": device_id
        })
        return response.json()
    
    def test_dashboard_stats_structure(self, test_user):
        """Test /api/dashboard/stats endpoint structure"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats?user_id={test_user['id']}")
        assert response.status_code == 200
        data = response.json()
        
        # Check all required fields
        assert "total_tasks" in data
        assert "completed_tasks" in data
        assert "in_progress_tasks" in data
        assert "todo_tasks" in data
        assert "overdue_tasks" in data
        assert "completion_rate" in data
        assert "category_stats" in data
        assert "priority_stats" in data
        assert "recent_tasks" in data
        assert "today_focus" in data
        
        print(f"✓ Dashboard stats structure correct")
        print(f"  - Total tasks: {data['total_tasks']}")
        print(f"  - Completion rate: {data['completion_rate']}%")


class TestCategoryManagement:
    """Category management endpoint tests"""
    
    @pytest.fixture(scope="class")
    def test_user(self):
        """Create a test user for category tests"""
        device_id = f"cat_test_device_{uuid.uuid4().hex[:8]}"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": f"TEST_CatUser_{uuid.uuid4().hex[:6]}",
            "device_id": device_id
        })
        return response.json()
    
    def test_default_categories_exist(self, test_user):
        """Test that default categories are created for new user"""
        assert len(test_user["categories"]) == 5
        category_ids = [c["id"] for c in test_user["categories"]]
        assert "api-test" in category_ids
        assert "ui-test" in category_ids
        assert "regression" in category_ids
        assert "bug-tracking" in category_ids
        assert "documentation" in category_ids
        print("✓ Default categories exist")
    
    def test_add_custom_category(self, test_user):
        """Test adding a custom category"""
        response = requests.post(f"{BASE_URL}/api/users/{test_user['id']}/categories", json={
            "id": "custom-test-cat",
            "name": "TEST_Custom_Category",
            "color": "#FF5733"
        })
        assert response.status_code == 200
        user = response.json()
        category_ids = [c["id"] for c in user["categories"]]
        assert "custom-test-cat" in category_ids
        print("✓ Custom category added")
    
    def test_delete_custom_category(self, test_user):
        """Test deleting a custom category"""
        # First add a category to delete
        requests.post(f"{BASE_URL}/api/users/{test_user['id']}/categories", json={
            "id": "to-delete-cat",
            "name": "TEST_To_Delete",
            "color": "#000000"
        })
        
        # Delete it
        response = requests.delete(f"{BASE_URL}/api/users/{test_user['id']}/categories/to-delete-cat")
        assert response.status_code == 200
        user = response.json()
        category_ids = [c["id"] for c in user["categories"]]
        assert "to-delete-cat" not in category_ids
        print("✓ Custom category deleted")
    
    def test_cannot_delete_default_category(self, test_user):
        """Test that default categories cannot be deleted"""
        response = requests.delete(f"{BASE_URL}/api/users/{test_user['id']}/categories/api-test")
        assert response.status_code == 400
        print("✓ Default category deletion blocked")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
