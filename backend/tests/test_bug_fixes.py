"""
Test file for QA Task Manager Bug Fixes - Iteration 5
Tests for:
1. Admin Panel user list loading - /api/users/roles endpoint with admin_user_id parameter
2. Report export - /api/reports/export endpoint for PDF, Excel, Word formats
3. User login - SERCANO user login and admin role assignment
4. Dashboard display - Dashboard loading after login
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthCheck:
    """Health check endpoint tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "sqlite"


class TestUserRegistrationAndLogin:
    """User registration and login tests"""
    
    def test_sercano_user_gets_admin_role(self):
        """Test that SERCANO user gets admin role on registration"""
        device_id = f"test-device-{uuid.uuid4()}"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "sercano",
            "email": "sercan.onal@intertech.com.tr",
            "device_id": device_id
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "sercano"
        assert data["email"] == "sercan.onal@intertech.com.tr"
        assert data["role"] == "admin"
        assert "id" in data
        assert "categories" in data
        assert len(data["categories"]) == 5  # Default categories
    
    def test_regular_user_gets_user_role(self):
        """Test that regular user gets user role on registration"""
        device_id = f"test-device-{uuid.uuid4()}"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "testuser",
            "email": "test@test.com",
            "device_id": device_id
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "testuser"
        assert data["role"] == "user"
    
    def test_device_check_returns_user(self):
        """Test device check returns existing user"""
        device_id = f"test-device-{uuid.uuid4()}"
        # First register
        reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "checkuser",
            "email": "check@test.com",
            "device_id": device_id
        })
        assert reg_response.status_code == 200
        user_id = reg_response.json()["id"]
        
        # Then check device
        check_response = requests.get(f"{BASE_URL}/api/auth/check/{device_id}")
        assert check_response.status_code == 200
        data = check_response.json()
        assert data["id"] == user_id
        assert data["device_id"] == device_id


class TestAdminPanelUsersRoles:
    """Admin Panel /users/roles endpoint tests"""
    
    @pytest.fixture
    def admin_user(self):
        """Create an admin user for testing"""
        device_id = f"test-admin-{uuid.uuid4()}"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "sercano",
            "email": "sercan.onal@intertech.com.tr",
            "device_id": device_id
        })
        return response.json()
    
    @pytest.fixture
    def regular_user(self):
        """Create a regular user for testing"""
        device_id = f"test-user-{uuid.uuid4()}"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "regularuser",
            "email": "regular@test.com",
            "device_id": device_id
        })
        return response.json()
    
    def test_users_roles_with_admin_user_id(self, admin_user):
        """Test /users/roles endpoint with admin_user_id parameter returns user list"""
        response = requests.get(f"{BASE_URL}/api/users/roles", params={
            "admin_user_id": admin_user["id"]
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Verify response structure
        for user in data:
            assert "id" in user
            assert "name" in user
            assert "email" in user
            assert "role" in user
            assert "created_at" in user
    
    def test_users_roles_without_admin_user_id_fails(self):
        """Test /users/roles endpoint without admin_user_id returns 422"""
        response = requests.get(f"{BASE_URL}/api/users/roles")
        assert response.status_code == 422  # Missing required parameter
    
    def test_users_roles_with_non_admin_user_fails(self, regular_user):
        """Test /users/roles endpoint with non-admin user returns 403"""
        response = requests.get(f"{BASE_URL}/api/users/roles", params={
            "admin_user_id": regular_user["id"]
        })
        assert response.status_code == 403
        data = response.json()
        assert "Admin yetki gerekli" in data["detail"]
    
    def test_users_roles_with_invalid_user_id_fails(self):
        """Test /users/roles endpoint with invalid user_id returns 404"""
        response = requests.get(f"{BASE_URL}/api/users/roles", params={
            "admin_user_id": "invalid-user-id-12345"
        })
        assert response.status_code == 404


class TestReportExport:
    """Report export endpoint tests"""
    
    @pytest.fixture
    def test_user(self):
        """Create a test user for report export"""
        device_id = f"test-report-{uuid.uuid4()}"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "reportuser",
            "email": "report@test.com",
            "device_id": device_id
        })
        return response.json()
    
    def test_export_pdf_format(self, test_user):
        """Test PDF export returns valid response"""
        response = requests.post(f"{BASE_URL}/api/reports/export", json={
            "format": "pdf",
            "user_id": test_user["id"],
            "include_tasks": True,
            "include_stats": True
        })
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        assert len(response.content) > 0
    
    def test_export_excel_format(self, test_user):
        """Test Excel export returns valid response"""
        response = requests.post(f"{BASE_URL}/api/reports/export", json={
            "format": "excel",
            "user_id": test_user["id"],
            "include_tasks": True,
            "include_stats": True
        })
        assert response.status_code == 200
        assert "spreadsheetml" in response.headers.get("content-type", "")
        assert len(response.content) > 0
    
    def test_export_word_format(self, test_user):
        """Test Word export returns valid response"""
        response = requests.post(f"{BASE_URL}/api/reports/export", json={
            "format": "word",
            "user_id": test_user["id"],
            "include_tasks": True,
            "include_stats": True
        })
        assert response.status_code == 200
        assert "wordprocessingml" in response.headers.get("content-type", "")
        assert len(response.content) > 0
    
    def test_export_invalid_format_fails(self, test_user):
        """Test export with invalid format returns 400"""
        response = requests.post(f"{BASE_URL}/api/reports/export", json={
            "format": "invalid",
            "user_id": test_user["id"],
            "include_tasks": True,
            "include_stats": True
        })
        assert response.status_code == 400
        data = response.json()
        assert "Format must be" in data["detail"]
    
    def test_export_without_user_id_fails(self):
        """Test export without user_id returns 422"""
        response = requests.post(f"{BASE_URL}/api/reports/export", json={
            "format": "pdf",
            "include_tasks": True,
            "include_stats": True
        })
        assert response.status_code == 422


class TestDashboardStats:
    """Dashboard statistics endpoint tests"""
    
    @pytest.fixture
    def test_user(self):
        """Create a test user for dashboard tests"""
        device_id = f"test-dashboard-{uuid.uuid4()}"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "dashboarduser",
            "email": "dashboard@test.com",
            "device_id": device_id
        })
        return response.json()
    
    def test_dashboard_stats_returns_data(self, test_user):
        """Test dashboard stats endpoint returns valid data"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", params={
            "user_id": test_user["id"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "total_tasks" in data
        assert "completed_tasks" in data
        assert "in_progress_tasks" in data
        assert "todo_tasks" in data
        assert "overdue_tasks" in data
        assert "completion_rate" in data
    
    def test_dashboard_stats_without_user_id_fails(self):
        """Test dashboard stats without user_id returns 422"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 422


class TestTaskAssignment:
    """Task assignment and user list tests"""
    
    @pytest.fixture
    def test_user(self):
        """Create a test user"""
        device_id = f"test-task-{uuid.uuid4()}"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "taskuser",
            "email": "task@test.com",
            "device_id": device_id
        })
        return response.json()
    
    def test_get_all_users_for_assignment(self):
        """Test /users endpoint returns user list for task assignment"""
        response = requests.get(f"{BASE_URL}/api/users")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Verify response structure
        for user in data:
            assert "id" in user
            assert "name" in user
            assert "created_at" in user
    
    def test_create_task_with_assignment(self, test_user):
        """Test creating a task with assigned_to field"""
        # Create another user to assign to
        device_id = f"test-assignee-{uuid.uuid4()}"
        assignee_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "assignee",
            "email": "assignee@test.com",
            "device_id": device_id
        })
        assignee = assignee_response.json()
        
        # Create task with assignment
        task_response = requests.post(f"{BASE_URL}/api/tasks", params={
            "user_id": test_user["id"]
        }, json={
            "title": "Test Task with Assignment",
            "description": "Testing task assignment",
            "category_id": "api-test",
            "assigned_to": assignee["id"],
            "priority": "medium"
        })
        assert task_response.status_code == 200
        task = task_response.json()
        assert task["assigned_to"] == assignee["id"]
        assert task["title"] == "Test Task with Assignment"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
