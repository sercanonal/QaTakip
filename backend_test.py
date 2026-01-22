import requests
import sys
import json
from datetime import datetime, timezone

class IntertechQAAPITester:
    def __init__(self, base_url="https://interflow.preview.emergentagent.com"):
        self.base_url = base_url
        self.test_email = "sercan.onal@intertech.com.tr"
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Add user_id as query param for endpoints that need it
        if params:
            url += "?" + "&".join([f"{k}={v}" for k, v in params.items()])

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            
            if success:
                self.log_test(name, True)
                try:
                    return response.json() if response.content else {}
                except:
                    return {}
            else:
                error_msg = f"Expected {expected_status}, got {response.status_code}"
                try:
                    error_detail = response.json().get('detail', '')
                    if error_detail:
                        error_msg += f" - {error_detail}"
                except:
                    pass
                self.log_test(name, False, error_msg)
                return {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return {}

    def test_health_check(self):
        """Test health endpoint"""
        return self.run_test("Health Check", "GET", "health", 200)

    def test_register_user(self):
        """Test user registration"""
        response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={"email": self.test_email}
        )
        if response and 'id' in response:
            self.user_id = response['id']
            print(f"   User ID: {self.user_id}")
            return True
        return False

    def test_login_user(self):
        """Test user login"""
        response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={"email": self.test_email}
        )
        if response and 'id' in response:
            if not self.user_id:
                self.user_id = response['id']
            return True
        return False

    def test_get_user(self):
        """Test get user by ID"""
        if not self.user_id:
            self.log_test("Get User", False, "No user ID available")
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
            self.log_test("Dashboard Stats", False, "No user ID available")
            return False
        
        return self.run_test(
            "Dashboard Stats",
            "GET",
            "dashboard/stats",
            200,
            params={"user_id": self.user_id}
        )

    def test_create_project(self):
        """Test project creation"""
        if not self.user_id:
            self.log_test("Create Project", False, "No user ID available")
            return False
        
        response = self.run_test(
            "Create Project",
            "POST",
            "projects",
            200,
            data={
                "name": "Test Projesi",
                "description": "Test için oluşturulan proje"
            },
            params={"user_id": self.user_id}
        )
        if response and 'id' in response:
            self.project_id = response['id']
            return True
        return False

    def test_get_projects(self):
        """Test get projects"""
        if not self.user_id:
            self.log_test("Get Projects", False, "No user ID available")
            return False
        
        return self.run_test(
            "Get Projects",
            "GET",
            "projects",
            200,
            params={"user_id": self.user_id}
        )

    def test_create_task(self):
        """Test task creation"""
        if not self.user_id:
            self.log_test("Create Task", False, "No user ID available")
            return False
        
        response = self.run_test(
            "Create Task",
            "POST",
            "tasks",
            200,
            data={
                "title": "Test Görevi",
                "description": "Test için oluşturulan görev",
                "category_id": "api-test",
                "priority": "high",
                "due_date": datetime.now(timezone.utc).isoformat()
            },
            params={"user_id": self.user_id}
        )
        if response and 'id' in response:
            self.task_id = response['id']
            return True
        return False

    def test_get_tasks(self):
        """Test get tasks"""
        if not self.user_id:
            self.log_test("Get Tasks", False, "No user ID available")
            return False
        
        return self.run_test(
            "Get Tasks",
            "GET",
            "tasks",
            200,
            params={"user_id": self.user_id}
        )

    def test_update_task_status(self):
        """Test task status update"""
        if not hasattr(self, 'task_id') or not self.task_id:
            self.log_test("Update Task Status", False, "No task ID available")
            return False
        
        return self.run_test(
            "Update Task Status",
            "PUT",
            f"tasks/{self.task_id}",
            200,
            data={"status": "in_progress"}
        )

    def test_add_category(self):
        """Test adding custom category"""
        if not self.user_id:
            self.log_test("Add Category", False, "No user ID available")
            return False
        
        return self.run_test(
            "Add Category",
            "POST",
            f"users/{self.user_id}/categories",
            200,
            data={
                "id": "custom-test",
                "name": "Özel Test Kategorisi",
                "color": "#FF5722"
            }
        )

    def test_get_notifications(self):
        """Test get notifications"""
        if not self.user_id:
            self.log_test("Get Notifications", False, "No user ID available")
            return False
        
        return self.run_test(
            "Get Notifications",
            "GET",
            "notifications",
            200,
            params={"user_id": self.user_id}
        )

    def test_invalid_email_registration(self):
        """Test registration with invalid email"""
        return self.run_test(
            "Invalid Email Registration",
            "POST",
            "auth/register",
            400,
            data={"email": "test@gmail.com"}
        )

    def test_invalid_email_login(self):
        """Test login with invalid email"""
        return self.run_test(
            "Invalid Email Login",
            "POST",
            "auth/login",
            400,
            data={"email": "test@gmail.com"}
        )

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Intertech QA API Tests...")
        print(f"📧 Test Email: {self.test_email}")
        print(f"🌐 Base URL: {self.base_url}")
        
        # Health check first
        self.test_health_check()
        
        # Test invalid emails first
        self.test_invalid_email_registration()
        self.test_invalid_email_login()
        
        # Auth tests
        if not self.test_register_user():
            # If registration fails, try login (user might already exist)
            if not self.test_login_user():
                print("❌ Cannot proceed without valid user authentication")
                return False
        
        # User tests
        self.test_get_user()
        
        # Dashboard tests
        self.test_dashboard_stats()
        
        # Project tests
        self.test_create_project()
        self.test_get_projects()
        
        # Task tests
        self.test_create_task()
        self.test_get_tasks()
        self.test_update_task_status()
        
        # Category tests
        self.test_add_category()
        
        # Notification tests
        self.test_get_notifications()
        
        return True

    def print_summary(self):
        """Print test summary"""
        print(f"\n📊 Test Summary:")
        print(f"   Total Tests: {self.tests_run}")
        print(f"   Passed: {self.tests_passed}")
        print(f"   Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Print failed tests
        failed_tests = [t for t in self.test_results if not t['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = IntertechQAAPITester()
    
    success = tester.run_all_tests()
    all_passed = tester.print_summary()
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())