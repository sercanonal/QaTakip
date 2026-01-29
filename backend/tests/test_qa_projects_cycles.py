"""
Test QA Projects and Cycles API endpoints
Tests for dynamic project/cycle management feature
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://testcenter-1.preview.emergentagent.com').rstrip('/')

class TestQAProjectsAPI:
    """QA Projects CRUD API tests"""
    
    def test_get_qa_projects(self):
        """GET /api/qa-projects - should return projects list"""
        response = requests.get(f"{BASE_URL}/api/qa-projects")
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        assert isinstance(data["projects"], list)
        print(f"✓ GET /api/qa-projects returned {len(data['projects'])} projects")
    
    def test_add_qa_project(self):
        """POST /api/qa-projects - should add new project"""
        unique_name = f"TEST_Project_{uuid.uuid4().hex[:8]}"
        payload = {
            "name": unique_name,
            "icon": "🧪"
        }
        response = requests.post(f"{BASE_URL}/api/qa-projects", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert data.get("project", {}).get("name") == unique_name
        assert data.get("project", {}).get("icon") == "🧪"
        print(f"✓ POST /api/qa-projects created project: {unique_name}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/qa-projects/{unique_name}")
    
    def test_add_duplicate_project_fails(self):
        """POST /api/qa-projects - should fail for duplicate name"""
        unique_name = f"TEST_Dup_{uuid.uuid4().hex[:8]}"
        payload = {"name": unique_name, "icon": "📦"}
        
        # Create first
        response1 = requests.post(f"{BASE_URL}/api/qa-projects", json=payload)
        assert response1.status_code == 200
        
        # Try duplicate
        response2 = requests.post(f"{BASE_URL}/api/qa-projects", json=payload)
        assert response2.status_code == 400
        assert "zaten mevcut" in response2.json().get("detail", "")
        print(f"✓ Duplicate project correctly rejected")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/qa-projects/{unique_name}")
    
    def test_add_project_without_name_fails(self):
        """POST /api/qa-projects - should fail without name"""
        payload = {"icon": "📦"}
        response = requests.post(f"{BASE_URL}/api/qa-projects", json=payload)
        assert response.status_code == 400
        assert "name gerekli" in response.json().get("detail", "")
        print(f"✓ Project without name correctly rejected")
    
    def test_update_qa_project(self):
        """PUT /api/qa-projects/{name} - should update project"""
        unique_name = f"TEST_Update_{uuid.uuid4().hex[:8]}"
        
        # Create project
        requests.post(f"{BASE_URL}/api/qa-projects", json={"name": unique_name, "icon": "📦"})
        
        # Update project
        new_name = f"TEST_Updated_{uuid.uuid4().hex[:8]}"
        update_payload = {"name": new_name, "icon": "🚀"}
        response = requests.put(f"{BASE_URL}/api/qa-projects/{unique_name}", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert data.get("project", {}).get("name") == new_name
        assert data.get("project", {}).get("icon") == "🚀"
        print(f"✓ PUT /api/qa-projects updated project: {unique_name} -> {new_name}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/qa-projects/{new_name}")
    
    def test_delete_qa_project(self):
        """DELETE /api/qa-projects/{name} - should delete project"""
        unique_name = f"TEST_Delete_{uuid.uuid4().hex[:8]}"
        
        # Create project
        requests.post(f"{BASE_URL}/api/qa-projects", json={"name": unique_name, "icon": "📦"})
        
        # Delete project
        response = requests.delete(f"{BASE_URL}/api/qa-projects/{unique_name}")
        assert response.status_code == 200
        assert response.json().get("success") == True
        print(f"✓ DELETE /api/qa-projects deleted project: {unique_name}")
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/qa-projects")
        projects = get_response.json().get("projects", [])
        assert not any(p["name"] == unique_name for p in projects)
        print(f"✓ Project deletion verified")


class TestCyclesAPI:
    """Cycles CRUD API tests"""
    
    def test_get_cycles(self):
        """GET /api/cycles - should return cycles list"""
        response = requests.get(f"{BASE_URL}/api/cycles")
        assert response.status_code == 200
        data = response.json()
        assert "cycles" in data
        assert isinstance(data["cycles"], list)
        print(f"✓ GET /api/cycles returned {len(data['cycles'])} cycles")
    
    def test_add_cycle(self):
        """POST /api/cycles - should add new cycle"""
        unique_key = f"TEST-C{uuid.uuid4().hex[:6]}"
        payload = {
            "key": unique_key,
            "name": "Test Cycle Sprint"
        }
        response = requests.post(f"{BASE_URL}/api/cycles", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert data.get("cycle", {}).get("key") == unique_key
        assert data.get("cycle", {}).get("name") == "Test Cycle Sprint"
        print(f"✓ POST /api/cycles created cycle: {unique_key}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/cycles/{unique_key}")
    
    def test_add_duplicate_cycle_fails(self):
        """POST /api/cycles - should fail for duplicate key"""
        unique_key = f"TEST-DUP{uuid.uuid4().hex[:4]}"
        payload = {"key": unique_key, "name": "Duplicate Test"}
        
        # Create first
        response1 = requests.post(f"{BASE_URL}/api/cycles", json=payload)
        assert response1.status_code == 200
        
        # Try duplicate
        response2 = requests.post(f"{BASE_URL}/api/cycles", json=payload)
        assert response2.status_code == 400
        assert "zaten mevcut" in response2.json().get("detail", "")
        print(f"✓ Duplicate cycle correctly rejected")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/cycles/{unique_key}")
    
    def test_add_cycle_without_key_fails(self):
        """POST /api/cycles - should fail without key"""
        payload = {"name": "No Key Cycle"}
        response = requests.post(f"{BASE_URL}/api/cycles", json=payload)
        assert response.status_code == 400
        assert "key ve name gerekli" in response.json().get("detail", "")
        print(f"✓ Cycle without key correctly rejected")
    
    def test_add_cycle_without_name_fails(self):
        """POST /api/cycles - should fail without name"""
        payload = {"key": "TEST-NONAME"}
        response = requests.post(f"{BASE_URL}/api/cycles", json=payload)
        assert response.status_code == 400
        assert "key ve name gerekli" in response.json().get("detail", "")
        print(f"✓ Cycle without name correctly rejected")
    
    def test_update_cycle(self):
        """PUT /api/cycles/{key} - should update cycle"""
        unique_key = f"TEST-UPD{uuid.uuid4().hex[:4]}"
        
        # Create cycle
        requests.post(f"{BASE_URL}/api/cycles", json={"key": unique_key, "name": "Original Name"})
        
        # Update cycle
        new_key = f"TEST-NEW{uuid.uuid4().hex[:4]}"
        update_payload = {"key": new_key, "name": "Updated Name"}
        response = requests.put(f"{BASE_URL}/api/cycles/{unique_key}", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert data.get("cycle", {}).get("key") == new_key
        assert data.get("cycle", {}).get("name") == "Updated Name"
        print(f"✓ PUT /api/cycles updated cycle: {unique_key} -> {new_key}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/cycles/{new_key}")
    
    def test_delete_cycle(self):
        """DELETE /api/cycles/{key} - should delete cycle"""
        unique_key = f"TEST-DEL{uuid.uuid4().hex[:4]}"
        
        # Create cycle
        requests.post(f"{BASE_URL}/api/cycles", json={"key": unique_key, "name": "To Delete"})
        
        # Delete cycle
        response = requests.delete(f"{BASE_URL}/api/cycles/{unique_key}")
        assert response.status_code == 200
        assert response.json().get("success") == True
        print(f"✓ DELETE /api/cycles deleted cycle: {unique_key}")
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/cycles")
        cycles = get_response.json().get("cycles", [])
        assert not any(c["key"] == unique_key for c in cycles)
        print(f"✓ Cycle deletion verified")


class TestDataPersistence:
    """Test that data persists correctly in JSON files"""
    
    def test_project_persists_after_creation(self):
        """Verify project data persists after creation"""
        unique_name = f"TEST_Persist_{uuid.uuid4().hex[:8]}"
        
        # Create project
        requests.post(f"{BASE_URL}/api/qa-projects", json={"name": unique_name, "icon": "💾"})
        
        # Verify in GET response
        response = requests.get(f"{BASE_URL}/api/qa-projects")
        projects = response.json().get("projects", [])
        found = next((p for p in projects if p["name"] == unique_name), None)
        assert found is not None
        assert found["icon"] == "💾"
        print(f"✓ Project {unique_name} persisted correctly")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/qa-projects/{unique_name}")
    
    def test_cycle_persists_after_creation(self):
        """Verify cycle data persists after creation"""
        unique_key = f"TEST-PER{uuid.uuid4().hex[:4]}"
        
        # Create cycle
        requests.post(f"{BASE_URL}/api/cycles", json={"key": unique_key, "name": "Persist Test"})
        
        # Verify in GET response
        response = requests.get(f"{BASE_URL}/api/cycles")
        cycles = response.json().get("cycles", [])
        found = next((c for c in cycles if c["key"] == unique_key), None)
        assert found is not None
        assert found["name"] == "Persist Test"
        print(f"✓ Cycle {unique_key} persisted correctly")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/cycles/{unique_key}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
