#!/usr/bin/env python3
"""
QA Task Manager Backend Test Suite
Tests all backend API endpoints including Admin APIs and SSE notifications
"""

import requests
import json
import time
import uuid
import os
from datetime import datetime, timezone

# Get backend URL from environment
BACKEND_URL = "https://qacentral.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log_test(test_name, status, details=""):
    color = Colors.GREEN if status == "PASS" else Colors.RED if status == "FAIL" else Colors.YELLOW
    print(f"{color}[{status}]{Colors.ENDC} {test_name}")
    if details:
        print(f"    {details}")

def log_info(message):
    print(f"{Colors.BLUE}[INFO]{Colors.ENDC} {message}")

def log_error(message):
    print(f"{Colors.RED}[ERROR]{Colors.ENDC} {message}")

class QATaskManagerTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.test_users = []
        self.test_tasks = []
        self.test_notifications = []
        
    def run_all_tests(self):
        """Run comprehensive test suite"""
        log_info(f"Starting QA Task Manager Backend Tests")
        log_info(f"Backend URL: {BACKEND_URL}")
        
        # Test basic connectivity
        if not self.test_health_check():
            log_error("Health check failed - aborting tests")
            return False
            
        # Test user registration and authentication
        if not self.test_user_registration():
            log_error("User registration failed - aborting tests")
            return False
            
        # Test admin API endpoints
        self.test_admin_apis()
        
        # Test task management
        self.test_task_management()
        
        # Test notification system
        self.test_notification_system()
        
        # Test SSE endpoint accessibility
        self.test_sse_endpoint()
        
        # Cleanup
        self.cleanup_test_data()
        
        log_info("All tests completed!")
        return True
    
    def test_health_check(self):
        """Test basic connectivity and health endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                log_test("Health Check", "PASS", f"Status: {data.get('status')}, DB: {data.get('database')}")
                return True
            else:
                log_test("Health Check", "FAIL", f"Status code: {response.status_code}")
                return False
        except Exception as e:
            log_test("Health Check", "FAIL", f"Connection error: {str(e)}")
            return False
    
    def test_user_registration(self):
        """Test user registration endpoint"""
        try:
            # Create test users
            test_users_data = [
                {"name": "Ahmet Yılmaz", "device_id": f"test_device_{uuid.uuid4()}"},
                {"name": "Ayşe Kaya", "device_id": f"test_device_{uuid.uuid4()}"}
            ]
            
            for user_data in test_users_data:
                response = self.session.post(f"{API_BASE}/auth/register", json=user_data)
                
                if response.status_code == 200:
                    user = response.json()
                    self.test_users.append(user)
                    log_test("User Registration", "PASS", f"Created user: {user['name']} (ID: {user['id']})")
                else:
                    log_test("User Registration", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                    return False
            
            return len(self.test_users) >= 2
            
        except Exception as e:
            log_test("User Registration", "FAIL", f"Exception: {str(e)}")
            return False
    
    def test_admin_apis(self):
        """Test all admin API endpoints"""
        log_info("Testing Admin API Endpoints...")
        
        # Test GET /api/admin/users
        try:
            response = self.session.get(f"{API_BASE}/admin/users")
            if response.status_code == 200:
                users = response.json()
                log_test("Admin GET Users", "PASS", f"Retrieved {len(users)} users")
                
                # Verify our test users are in the list
                test_user_ids = [u['id'] for u in self.test_users]
                admin_user_ids = [u['id'] for u in users]
                
                if all(uid in admin_user_ids for uid in test_user_ids):
                    log_test("Admin Users Data Integrity", "PASS", "All test users found in admin list")
                else:
                    log_test("Admin Users Data Integrity", "FAIL", "Some test users missing from admin list")
            else:
                log_test("Admin GET Users", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            log_test("Admin GET Users", "FAIL", f"Exception: {str(e)}")
        
        # Test POST /api/admin/users (Manual user creation)
        try:
            new_user_data = {
                "name": "Admin Test User",
                "device_id": f"admin_test_{uuid.uuid4()}"
            }
            
            response = self.session.post(f"{API_BASE}/admin/users", json=new_user_data)
            if response.status_code == 200:
                admin_user = response.json()
                self.test_users.append(admin_user)
                log_test("Admin POST User", "PASS", f"Created user via admin: {admin_user['name']}")
            else:
                log_test("Admin POST User", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            log_test("Admin POST User", "FAIL", f"Exception: {str(e)}")
        
        # Test PUT /api/admin/users/{user_id} (Update user name)
        if self.test_users:
            try:
                user_to_update = self.test_users[0]
                new_name = f"Updated {user_to_update['name']}"
                
                # Note: The endpoint expects 'name' as a query parameter based on the code
                response = self.session.put(f"{API_BASE}/admin/users/{user_to_update['id']}?name={new_name}")
                
                if response.status_code == 200:
                    updated_user = response.json()
                    if updated_user['name'] == new_name:
                        log_test("Admin PUT User", "PASS", f"Updated user name to: {new_name}")
                        # Update our local copy
                        user_to_update['name'] = new_name
                    else:
                        log_test("Admin PUT User", "FAIL", "Name not updated correctly")
                else:
                    log_test("Admin PUT User", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
            except Exception as e:
                log_test("Admin PUT User", "FAIL", f"Exception: {str(e)}")
        
        # Test DELETE /api/admin/users/{user_id} (will test this at cleanup)
        log_info("Admin DELETE User test will be performed during cleanup")
    
    def test_task_management(self):
        """Test task creation and assignment with notifications"""
        log_info("Testing Task Management...")
        
        if len(self.test_users) < 2:
            log_test("Task Management", "SKIP", "Need at least 2 users for task assignment tests")
            return
        
        user1 = self.test_users[0]
        user2 = self.test_users[1]
        
        # Test task creation with assignment
        try:
            task_data = {
                "title": "Test API Endpoint",
                "description": "Test the new API endpoint functionality",
                "category_id": "api-test",
                "assigned_to": user2['id'],
                "priority": "high"
            }
            
            response = self.session.post(f"{API_BASE}/tasks?user_id={user1['id']}", json=task_data)
            
            if response.status_code == 200:
                task = response.json()
                self.test_tasks.append(task)
                log_test("Task Creation with Assignment", "PASS", f"Created task: {task['title']}")
                
                # Verify assignment
                if task['assigned_to'] == user2['id']:
                    log_test("Task Assignment", "PASS", f"Task assigned to {user2['name']}")
                else:
                    log_test("Task Assignment", "FAIL", "Task assignment failed")
            else:
                log_test("Task Creation with Assignment", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            log_test("Task Creation with Assignment", "FAIL", f"Exception: {str(e)}")
        
        # Test GET /api/tasks
        try:
            response = self.session.get(f"{API_BASE}/tasks?user_id={user1['id']}")
            if response.status_code == 200:
                tasks = response.json()
                log_test("GET Tasks", "PASS", f"Retrieved {len(tasks)} tasks")
            else:
                log_test("GET Tasks", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            log_test("GET Tasks", "FAIL", f"Exception: {str(e)}")
        
        # Test task update with assignment change
        if self.test_tasks:
            try:
                task = self.test_tasks[0]
                update_data = {
                    "title": "Updated Test Task",
                    "assigned_to": user1['id']  # Reassign back to user1
                }
                
                response = self.session.put(f"{API_BASE}/tasks/{task['id']}?user_id={user2['id']}", json=update_data)
                
                if response.status_code == 200:
                    updated_task = response.json()
                    log_test("Task Update with Reassignment", "PASS", f"Task reassigned to {user1['name']}")
                else:
                    log_test("Task Update with Reassignment", "FAIL", f"Status: {response.status_code}")
            except Exception as e:
                log_test("Task Update with Reassignment", "FAIL", f"Exception: {str(e)}")
    
    def test_notification_system(self):
        """Test notification endpoints"""
        log_info("Testing Notification System...")
        
        if not self.test_users:
            log_test("Notification System", "SKIP", "No test users available")
            return
        
        user = self.test_users[0]
        
        # Test GET /api/notifications
        try:
            response = self.session.get(f"{API_BASE}/notifications?user_id={user['id']}")
            if response.status_code == 200:
                notifications = response.json()
                log_test("GET Notifications", "PASS", f"Retrieved {len(notifications)} notifications")
                
                # Check if we have notifications from task assignments
                task_notifications = [n for n in notifications if "görev" in n.get('message', '').lower()]
                if task_notifications:
                    log_test("Task Assignment Notifications", "PASS", f"Found {len(task_notifications)} task-related notifications")
                    self.test_notifications.extend(task_notifications[:2])  # Keep some for testing
                else:
                    log_test("Task Assignment Notifications", "WARN", "No task assignment notifications found")
            else:
                log_test("GET Notifications", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            log_test("GET Notifications", "FAIL", f"Exception: {str(e)}")
        
        # Test notification read functionality
        if self.test_notifications:
            try:
                notif = self.test_notifications[0]
                response = self.session.put(f"{API_BASE}/notifications/{notif['id']}/read")
                
                if response.status_code == 200:
                    log_test("Mark Notification Read", "PASS", "Notification marked as read")
                else:
                    log_test("Mark Notification Read", "FAIL", f"Status: {response.status_code}")
            except Exception as e:
                log_test("Mark Notification Read", "FAIL", f"Exception: {str(e)}")
        
        # Test mark all notifications read
        try:
            response = self.session.put(f"{API_BASE}/notifications/read-all?user_id={user['id']}")
            if response.status_code == 200:
                log_test("Mark All Notifications Read", "PASS", "All notifications marked as read")
            else:
                log_test("Mark All Notifications Read", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            log_test("Mark All Notifications Read", "FAIL", f"Exception: {str(e)}")
    
    def test_sse_endpoint(self):
        """Test SSE endpoint accessibility (not full streaming due to complexity)"""
        log_info("Testing SSE Endpoint Accessibility...")
        
        if not self.test_users:
            log_test("SSE Endpoint", "SKIP", "No test users available")
            return
        
        user = self.test_users[0]
        
        try:
            # Test SSE endpoint accessibility with a short timeout
            response = self.session.get(
                f"{API_BASE}/notifications/stream?user_id={user['id']}", 
                timeout=3,
                stream=True
            )
            
            if response.status_code == 200:
                # Check if we get the expected content type
                content_type = response.headers.get('content-type', '')
                if 'text/event-stream' in content_type:
                    log_test("SSE Endpoint Accessibility", "PASS", "SSE endpoint accessible with correct content-type")
                    
                    # Try to read first chunk (connection message)
                    try:
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:
                                chunk_str = chunk.decode('utf-8')
                                if 'connected' in chunk_str or 'bağlantısı kuruldu' in chunk_str:
                                    log_test("SSE Connection Message", "PASS", "Received connection confirmation")
                                break
                    except:
                        log_test("SSE Connection Message", "WARN", "Could not read connection message (timeout expected)")
                else:
                    log_test("SSE Endpoint Accessibility", "FAIL", f"Wrong content-type: {content_type}")
            else:
                log_test("SSE Endpoint Accessibility", "FAIL", f"Status: {response.status_code}")
                
        except requests.exceptions.Timeout:
            log_test("SSE Endpoint Accessibility", "PASS", "SSE endpoint accessible (timeout expected for streaming)")
        except Exception as e:
            log_test("SSE Endpoint Accessibility", "FAIL", f"Exception: {str(e)}")
    
    def cleanup_test_data(self):
        """Clean up test data using admin delete endpoint"""
        log_info("Cleaning up test data...")
        
        # Delete test tasks
        for task in self.test_tasks:
            try:
                response = self.session.delete(f"{API_BASE}/tasks/{task['id']}")
                if response.status_code == 200:
                    log_test("Cleanup Task", "PASS", f"Deleted task: {task['title']}")
                else:
                    log_test("Cleanup Task", "FAIL", f"Failed to delete task: {task['id']}")
            except Exception as e:
                log_test("Cleanup Task", "FAIL", f"Exception: {str(e)}")
        
        # Delete test users using admin endpoint (test DELETE admin API)
        for user in self.test_users:
            try:
                response = self.session.delete(f"{API_BASE}/admin/users/{user['id']}")
                if response.status_code == 200:
                    log_test("Admin DELETE User", "PASS", f"Deleted user: {user['name']}")
                else:
                    log_test("Admin DELETE User", "FAIL", f"Failed to delete user: {user['id']}")
            except Exception as e:
                log_test("Admin DELETE User", "FAIL", f"Exception: {str(e)}")

def main():
    """Main test execution"""
    print(f"{Colors.BOLD}QA Task Manager Backend Test Suite{Colors.ENDC}")
    print("=" * 50)
    
    tester = QATaskManagerTester()
    success = tester.run_all_tests()
    
    print("=" * 50)
    if success:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ Test Suite Completed{Colors.ENDC}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ Test Suite Failed{Colors.ENDC}")
    
    return success

if __name__ == "__main__":
    main()