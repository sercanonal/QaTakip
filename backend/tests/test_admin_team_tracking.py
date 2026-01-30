"""
Backend tests for Admin Team Tracking Dashboard endpoints
Tests: /api/admin/verify-key, /api/admin/team-summary, /api/admin/user-tasks-detail

Note: Jira API requires VPN access which is not available in test environment.
Tests verify endpoint structure, auth validation, and error handling.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
ADMIN_KEY = "qH7mK9pL2nX5vB8cZ4"
TEST_USERNAME = "SERCANO"


class TestAdminVerifyKey:
    """Tests for /api/admin/verify-key endpoint"""
    
    def test_verify_key_valid(self):
        """Test valid admin key verification"""
        response = requests.post(
            f"{BASE_URL}/api/admin/verify-key",
            json={"v": ADMIN_KEY}
        )
        assert response.status_code == 200
        data = response.json()
        assert "r" in data
        assert data["r"] == True
        print(f"✓ Valid key verification: {data}")
    
    def test_verify_key_invalid(self):
        """Test invalid admin key rejection"""
        response = requests.post(
            f"{BASE_URL}/api/admin/verify-key",
            json={"v": "wrong_key_12345"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "r" in data
        assert data["r"] == False
        print(f"✓ Invalid key rejected: {data}")
    
    def test_verify_key_empty(self):
        """Test empty key rejection"""
        response = requests.post(
            f"{BASE_URL}/api/admin/verify-key",
            json={"v": ""}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["r"] == False
        print(f"✓ Empty key rejected: {data}")
    
    def test_verify_key_missing_field(self):
        """Test missing v field"""
        response = requests.post(
            f"{BASE_URL}/api/admin/verify-key",
            json={}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["r"] == False
        print(f"✓ Missing field handled: {data}")


class TestAdminTeamSummary:
    """Tests for /api/admin/team-summary endpoint"""
    
    def test_team_summary_unauthorized(self):
        """Test unauthorized access with wrong key"""
        response = requests.get(
            f"{BASE_URL}/api/admin/team-summary",
            params={"t": "wrong_key", "months": 1}
        )
        assert response.status_code == 403
        print(f"✓ Unauthorized access blocked (403)")
    
    def test_team_summary_valid_key(self):
        """Test team summary with valid key - returns structure even if Jira unavailable"""
        response = requests.get(
            f"{BASE_URL}/api/admin/team-summary",
            params={"t": ADMIN_KEY, "months": 1}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "success" in data
        assert "team" in data
        assert "period_months" in data
        
        # If Jira is unavailable, success will be False with error message
        # If Jira is available, success will be True with team data
        if data["success"]:
            assert "totals" in data
            assert "date_range" in data
            assert isinstance(data["team"], list)
            print(f"✓ Team summary returned with {len(data['team'])} members")
        else:
            # Jira unavailable - expected in test environment
            assert "error" in data
            print(f"✓ Team summary structure valid (Jira unavailable: {data.get('error', 'timeout')})")
    
    def test_team_summary_period_params(self):
        """Test different period parameters (1, 3, 6, 12 months)"""
        for months in [1, 3, 6, 12]:
            response = requests.get(
                f"{BASE_URL}/api/admin/team-summary",
                params={"t": ADMIN_KEY, "months": months}
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get("period_months") == months
            print(f"✓ Period {months} months accepted")
    
    def test_team_summary_response_structure(self):
        """Verify complete response structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/team-summary",
            params={"t": ADMIN_KEY, "months": 1}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Required fields
        required_fields = ["success", "team", "period_months"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # If success, check totals structure
        if data["success"] and data.get("totals"):
            totals = data["totals"]
            assert "total_users" in totals
            assert "total_backlog" in totals
            assert "total_in_progress" in totals
            assert "total_completed" in totals
            print(f"✓ Totals structure valid: {totals}")
        
        print(f"✓ Response structure valid")


class TestAdminUserTasksDetail:
    """Tests for /api/admin/user-tasks-detail endpoint"""
    
    def test_user_tasks_unauthorized(self):
        """Test unauthorized access with wrong key"""
        response = requests.get(
            f"{BASE_URL}/api/admin/user-tasks-detail",
            params={"username": TEST_USERNAME, "t": "wrong_key", "months": 1}
        )
        assert response.status_code == 403
        print(f"✓ Unauthorized access blocked (403)")
    
    def test_user_tasks_valid_key(self):
        """Test user tasks detail with valid key"""
        response = requests.get(
            f"{BASE_URL}/api/admin/user-tasks-detail",
            params={"username": TEST_USERNAME, "t": ADMIN_KEY, "months": 1}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "success" in data
        assert "tasks" in data
        
        if data["success"]:
            assert "counts" in data
            assert "username" in data
            tasks = data["tasks"]
            assert "backlog" in tasks
            assert "in_progress" in tasks
            assert "completed" in tasks
            print(f"✓ User tasks returned: backlog={data['counts'].get('backlog', 0)}, in_progress={data['counts'].get('in_progress', 0)}, completed={data['counts'].get('completed', 0)}")
        else:
            # Jira unavailable - expected in test environment
            print(f"✓ User tasks structure valid (Jira unavailable: {data.get('error', 'timeout')})")
    
    def test_user_tasks_response_structure(self):
        """Verify complete response structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/user-tasks-detail",
            params={"username": TEST_USERNAME, "t": ADMIN_KEY, "months": 1}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Required fields
        assert "success" in data
        assert "tasks" in data
        
        # Tasks structure
        tasks = data["tasks"]
        assert isinstance(tasks, dict)
        assert "backlog" in tasks
        assert "in_progress" in tasks
        assert "completed" in tasks
        
        # Each should be a list
        assert isinstance(tasks["backlog"], list)
        assert isinstance(tasks["in_progress"], list)
        assert isinstance(tasks["completed"], list)
        
        print(f"✓ User tasks response structure valid")
    
    def test_user_tasks_period_params(self):
        """Test different period parameters"""
        for months in [1, 3, 6, 12]:
            response = requests.get(
                f"{BASE_URL}/api/admin/user-tasks-detail",
                params={"username": TEST_USERNAME, "t": ADMIN_KEY, "months": months}
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get("period_months") == months
            print(f"✓ Period {months} months accepted for user tasks")


class TestAdminQATeam:
    """Tests for /api/admin/qa-team endpoint"""
    
    def test_qa_team_unauthorized(self):
        """Test unauthorized access"""
        response = requests.get(
            f"{BASE_URL}/api/admin/qa-team",
            params={"t": "wrong_key"}
        )
        assert response.status_code == 403
        print(f"✓ Unauthorized access blocked (403)")
    
    def test_qa_team_valid_key(self):
        """Test QA team endpoint with valid key"""
        response = requests.get(
            f"{BASE_URL}/api/admin/qa-team",
            params={"t": ADMIN_KEY}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "users" in data
        assert "total" in data
        assert isinstance(data["users"], list)
        assert isinstance(data["total"], int)
        
        print(f"✓ QA team endpoint returned {data['total']} users")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
