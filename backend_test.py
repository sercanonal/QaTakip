#!/usr/bin/env python3

import requests
import sys
import json
import uuid
from datetime import datetime, timezone, timedelta

class QATaskManagerTester:
    def __init__(self, base_url="https://interflow.preview.emergentagent.com"):
        self.base_url = base_url
        self.user_id = None
        self.device_id = str(uuid.uuid4())
        self.test_user_name = f"Test User {datetime.now().strftime('%H%M%S')}"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details="", response_data=None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "response_data": response_data
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=data)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            response_data = None
            
            try:
                response_data = response.json()
            except:
                response_data = response.text

            if success:
                self.log_test(name, True, response_data=response_data)
                return True, response_data
            else:
                self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}: {response_data}")
                return False, response_data

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        return self.run_test("Health Check", "GET", "health", 200)

    def test_user_registration(self):
        """Test user registration"""
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={
                "name": self.test_user_name,
                "device_id": self.device_id
            }
        )
        
        if success and response:
            self.user_id = response.get('id')
            return True
        return False

    def test_device_check(self):
        """Test device check endpoint"""
        if not self.device_id:
            return False
        
        return self.run_test(
            "Device Check",
            "GET",
            f"auth/check/{self.device_id}",
            200
        )

    def test_get_user(self):
        """Test get user endpoint"""
        if not self.user_id:
            return False
            
        return self.run_test(
            "Get User",
            "GET",
            f"users/{self.user_id}",
            200
        )

    def test_dashboard_stats(self):
        """Test dashboard stats"""
        if not self.user_id:
            return False
            
        return self.run_test(
            "Dashboard Stats",
            "GET",
            "dashboard/stats",
            200,
            data={"user_id": self.user_id}
        )

    def test_project_crud(self):
        """Test project CRUD operations"""
        if not self.user_id:
            return False

        # Create project
        success, project_data = self.run_test(
            "Create Project",
            "POST",
            "projects",
            200,
            data={
                "name": "Test Project",
                "description": "Test project description",
                "user_id": self.user_id
            }
        )
        
        if not success:
            return False
            
        project_id = project_data.get('id')
        if not project_id:
            self.log_test("Project Creation - Get ID", False, "No project ID returned")
            return False

        # Get projects
        success, _ = self.run_test(
            "Get Projects",
            "GET",
            "projects",
            200,
            data={"user_id": self.user_id}
        )
        
        if not success:
            return False

        # Get single project
        success, _ = self.run_test(
            "Get Single Project",
            "GET",
            f"projects/{project_id}",
            200
        )
        
        if not success:
            return False

        # Update project
        success, _ = self.run_test(
            "Update Project",
            "PUT",
            f"projects/{project_id}",
            200,
            data={
                "name": "Updated Test Project",
                "description": "Updated description"
            }
        )
        
        if not success:
            return False

        # Delete project
        success, _ = self.run_test(
            "Delete Project",
            "DELETE",
            f"projects/{project_id}",
            200
        )
        
        return success

    def test_task_crud(self):
        """Test task CRUD operations"""
        if not self.user_id:
            return False

        # First create a project for the task
        success, project_data = self.run_test(
            "Create Project for Task",
            "POST",
            "projects",
            200,
            data={
                "name": "Task Test Project",
                "description": "Project for task testing",
                "user_id": self.user_id
            }
        )
        
        if not success:
            return False
            
        project_id = project_data.get('id')

        # Create task
        task_data = {
            "title": "Test Task",
            "description": "Test task description",
            "category_id": "api-test",  # Default category
            "project_id": project_id,
            "priority": "medium",
            "due_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "user_id": self.user_id
        }
        
        success, task_response = self.run_test(
            "Create Task",
            "POST",
            "tasks",
            200,
            data=task_data
        )
        
        if not success:
            return False
            
        task_id = task_response.get('id')
        if not task_id:
            self.log_test("Task Creation - Get ID", False, "No task ID returned")
            return False

        # Get tasks
        success, _ = self.run_test(
            "Get Tasks",
            "GET",
            "tasks",
            200,
            data={"user_id": self.user_id}
        )
        
        if not success:
            return False

        # Get single task
        success, _ = self.run_test(
            "Get Single Task",
            "GET",
            f"tasks/{task_id}",
            200
        )
        
        if not success:
            return False

        # Update task status
        success, _ = self.run_test(
            "Update Task Status",
            "PUT",
            f"tasks/{task_id}",
            200,
            data={"status": "in_progress"}
        )
        
        if not success:
            return False

        # Update task details
        success, _ = self.run_test(
            "Update Task Details",
            "PUT",
            f"tasks/{task_id}",
            200,
            data={
                "title": "Updated Test Task",
                "description": "Updated description",
                "priority": "high"
            }
        )
        
        if not success:
            return False

        # Complete task
        success, _ = self.run_test(
            "Complete Task",
            "PUT",
            f"tasks/{task_id}",
            200,
            data={"status": "completed"}
        )
        
        if not success:
            return False

        # Delete task
        success, _ = self.run_test(
            "Delete Task",
            "DELETE",
            f"tasks/{task_id}",
            200
        )
        
        return success

    def test_category_management(self):
        """Test category management"""
        if not self.user_id:
            return False

        # Add category
        success, user_data = self.run_test(
            "Add Category",
            "POST",
            f"users/{self.user_id}/categories",
            200,
            data={
                "id": "test-category",
                "name": "Test Category",
                "color": "#FF5733"
            }
        )
        
        if not success:
            return False

        # Delete category (non-default)
        success, _ = self.run_test(
            "Delete Category",
            "DELETE",
            f"users/{self.user_id}/categories/test-category",
            200
        )
        
        return success

    def test_notifications(self):
        """Test notification endpoints"""
        if not self.user_id:
            return False

        # Get notifications
        success, _ = self.run_test(
            "Get Notifications",
            "GET",
            "notifications",
            200,
            data={"user_id": self.user_id}
        )
        
        return success

    def test_filtered_tasks(self):
        """Test task filtering"""
        if not self.user_id:
            return False

        # Test various filters
        filters = [
            {"status": "todo"},
            {"status": "completed"},
            {"priority": "high"},
            {"category_id": "api-test"}
        ]
        
        all_passed = True
        for filter_params in filters:
            filter_params["user_id"] = self.user_id
            success, _ = self.run_test(
                f"Filter Tasks - {list(filter_params.keys())[0]}",
                "GET",
                "tasks",
                200,
                data=filter_params
            )
            if not success:
                all_passed = False
        
        return all_passed

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting QA Task Manager API Tests (SQLite Backend)")
        print("=" * 60)
        
        # Core functionality tests
        tests = [
            self.test_health_check,
            self.test_user_registration,
            self.test_device_check,
            self.test_get_user,
            self.test_dashboard_stats,
            self.test_project_crud,
            self.test_task_crud,
            self.test_category_management,
            self.test_notifications,
            self.test_filtered_tasks
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_test(f"Exception in {test.__name__}", False, str(e))
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary:")
        print(f"   Total Tests: {self.tests_run}")
        print(f"   Passed: {self.tests_passed}")
        print(f"   Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed")
            return 1

def main():
    tester = QATaskManagerTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())