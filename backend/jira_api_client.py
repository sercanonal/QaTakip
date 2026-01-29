"""
Jira API Client for QA Hub
Port from axiosClient.js
"""
import httpx
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Jira API Configuration
JIRA_BASE_URL = "https://jira.intertech.com.tr"
JIRA_API_URL = f"{JIRA_BASE_URL}/rest/tests/1.0/"
JIRA_AUTH_TOKEN = "Basic aW50ZWdyYXRpb25fdXNlcjpkMkBDQig1ZA=="

# HTTP client with timeout settings
def get_client():
    return httpx.AsyncClient(
        base_url=JIRA_API_URL,
        headers={
            "Authorization": JIRA_AUTH_TOKEN,
            "Content-Type": "application/json"
        },
        timeout=httpx.Timeout(30.0, connect=10.0),
        verify=False  # VPN arkasında SSL sorunları için
    )

# ============== TEST RUN OPERATIONS ==============

async def get_test_run(cycle_key: str) -> Dict[str, Any]:
    """Get test run info by cycle key"""
    fields = "id,key,name,projectId,projectVersionId,environmentId,plannedStartDate,plannedEndDate,iteration(name),executionTime,estimatedTime"
    
    async with get_client() as client:
        response = await client.get(f"testrun/{cycle_key}", params={"fields": fields})
        response.raise_for_status()
        return response.json()

async def get_test_run_items(testrun_id: int) -> List[Dict[str, Any]]:
    """Get test run items"""
    fields = "id,index,issueCount,$lastTestResult"
    
    async with get_client() as client:
        response = await client.get(f"testrun/{testrun_id}/testrunitems", params={"fields": fields})
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list):
            return data
        return data.get("testRunItems", [])

async def get_last_test_results(testrun_id: int) -> List[Dict[str, Any]]:
    """Get last test results for a test run"""
    async with get_client() as client:
        response = await client.get(f"testrun/{testrun_id}/testrunitems/lasttestresults")
        response.raise_for_status()
        return response.json()

async def get_test_results_by_item_id(testrun_id: int, item_id: int) -> List[Dict[str, Any]]:
    """Get test results for a specific item"""
    fields = "id,testResultStatusId,automated,estimatedTime,customFieldValues,executionTime,executionDate,plannedStartDate,plannedEndDate,actualStartDate,actualEndDate,environmentId,jiraVersionId,sprintId,comment,userKey,assignedTo,testScriptResults(id,testResultStatusId,executionDate,comment,index,description,expectedResult,testData,traceLinks,attachments,sourceScriptType,parameterSetId,customFieldValues,stepAttachmentsMapping),traceLinks,attachments"
    
    async with get_client() as client:
        response = await client.get(
            f"testrun/{testrun_id}/testresults",
            params={"fields": fields, "itemId": item_id}
        )
        response.raise_for_status()
        return response.json() or []

async def get_test_case(test_key: str) -> Dict[str, Any]:
    """Get test case details by key"""
    fields = "id,projectId,archived,key,name,objective,majorVersion,latestVersion,precondition,folder(id,fullName),status,priority,estimatedTime,averageTime,componentId,owner,labels,customFieldValues,testScript(id,text,steps(index,reflectRef,description,text,expectedResult,testData,attachments,customFieldValues,id,stepParameters(id,testCaseParameterId,value),testCase(projectId,id,key,name,archived,majorVersion,latestVersion,parameters(id,name,defaultValue,index)))),testData,parameters(id,name,defaultValue,index),paramType"
    
    async with get_client() as client:
        response = await client.get(f"testcase/{test_key}", params={"fields": fields})
        response.raise_for_status()
        return response.json()

async def get_cycle_info(cycle_id: int) -> Dict[str, Any]:
    """Get cycle info with test run items"""
    fields = "id,index,issueCount,$lastTestResult"
    
    async with get_client() as client:
        response = await client.get(f"testrun/{cycle_id}/testrunitems", params={"fields": fields})
        response.raise_for_status()
        data = response.json()
        
        # Return in expected format
        if isinstance(data, list):
            return {"testRunItems": data}
        return data

# ============== BUG OPERATIONS ==============

async def link_bug_to_test_result(test_result_id: int, issue_id: int, type_id: int = 3):
    """Link a bug to a test result"""
    payload = [{"testResultId": test_result_id, "issueId": issue_id, "typeId": type_id}]
    
    async with get_client() as client:
        response = await client.post("tracelink/testresult/bulk/create", json=payload)
        response.raise_for_status()
        return response.json() if response.content else None

async def refresh_issue_count_cache(testrun_id: int):
    """Refresh issue count cache for a test run"""
    payload = {"id": testrun_id}
    
    async with get_client() as client:
        try:
            response = await client.post(f"testrun/{testrun_id}/refreshissuecountcache", json=payload)
            response.raise_for_status()
        except Exception as e:
            logger.warning(f"Cache refresh failed (non-critical): {e}")

async def get_issue_key(issue_id: int) -> str:
    """Get issue key from issue ID"""
    try:
        async with httpx.AsyncClient(
            base_url=JIRA_BASE_URL,
            headers={
                "Authorization": JIRA_AUTH_TOKEN,
                "Content-Type": "application/json"
            },
            timeout=httpx.Timeout(15.0),
            verify=False
        ) as client:
            response = await client.get(f"/rest/api/2/issue/{issue_id}")
            response.raise_for_status()
            return response.json().get("key", f"ID:{issue_id}")
    except Exception:
        return f"ID:{issue_id}"

# ============== CYCLE OPERATIONS ==============

async def save_cycle(body: Dict[str, Any]) -> Dict[str, Any]:
    """Save/update cycle items"""
    async with get_client() as client:
        response = await client.put("testrunitem/bulk/save", json=body)
        response.raise_for_status()
        return response.json() if response.content else {}

# ============== STATUS INFO ==============

STATUS_INFO = {
    216: {"name": "Not Executed", "color": "#cfcfc4"},
    217: {"name": "In Progress", "color": "#f0ad4e"},
    218: {"name": "Pass", "color": "#3abb4b"},
    219: {"name": "Fail", "color": "#df2f36"},
    220: {"name": "Blocked", "color": "#4b88e7"},
    5116: {"name": "Pass(Manuel)", "color": "#38761d"}
}

def get_status_name(status_id: int) -> str:
    """Get status name from ID"""
    return STATUS_INFO.get(status_id, {}).get("name", str(status_id))
