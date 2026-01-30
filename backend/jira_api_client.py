"""
Jira/Zephyr Scale API Client - WITH PROXY SUPPORT
Uses subprocess curl for reliable proxy handling
"""

import subprocess
import json
import logging
from typing import Optional, Dict, Any, List
import os

logger = logging.getLogger("jira_client")

class JiraConfig:
    BASE_URL = "https://jira.intertech.com.tr"
    ZEPHYR_API_PATH = "/rest/tests/1.0"
    JIRA_API_PATH = "/rest/api/2"
    AUTH_TOKEN = "Basic aW50ZWdyYXRpb25fdXNlcjpkMkBDQig1ZA=="
    REQUEST_TIMEOUT = 60
    MAX_RETRIES = 2
    # Proxy settings
    PROXY_HOST = os.getenv("PROXY_HOST", "10.125.24.215")
    PROXY_PORT = os.getenv("PROXY_PORT", "8080")


class JiraAPIClient:
    """
    HTTP client for Jira/Zephyr Scale API
    Uses curl subprocess for reliable corporate proxy support
    """
    
    def __init__(self):
        self.config = JiraConfig()
        self.base_url = self.config.BASE_URL
        self.zephyr_path = self.config.ZEPHYR_API_PATH
        self.jira_path = self.config.JIRA_API_PATH
        self.proxy_url = f"http://{self.config.PROXY_HOST}:{self.config.PROXY_PORT}"
        logger.info(f"Using proxy: {self.proxy_url}")
    
    def _curl_get(self, url: str, params: dict = None) -> Optional[dict]:
        """Execute GET request using curl subprocess"""
        import urllib.parse
        
        # Build URL with properly encoded params
        if params:
            encoded_params = urllib.parse.urlencode(params)
            full_url = f"{url}?{encoded_params}"
        else:
            full_url = url
        
        cmd = [
            "curl", "-s", "-k",  # silent, insecure (skip SSL)
            "-x", self.proxy_url,  # proxy
            "-H", f"Authorization: {self.config.AUTH_TOKEN}",
            "-H", "Content-Type: application/json",
            "-H", "Accept: application/json",
            "--max-time", str(self.config.REQUEST_TIMEOUT),
            full_url
        ]
        
        try:
            logger.info(f"=== CURL GET REQUEST ===")
            logger.info(f"URL: {full_url[:120]}...")
            logger.info(f"Proxy: {self.proxy_url}")
            logger.info(f"Command: curl -s -k -x {self.proxy_url} ...")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.config.REQUEST_TIMEOUT + 10)
            
            logger.info(f"Curl return code: {result.returncode}")
            
            if result.returncode == 0 and result.stdout:
                logger.info(f"Response length: {len(result.stdout)} chars")
                try:
                    data = json.loads(result.stdout)
                    logger.info(f"=== CURL SUCCESS ===")
                    return data
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parse error: {e}")
                    logger.error(f"Raw response (first 500 chars): {result.stdout[:500]}")
            else:
                logger.error(f"=== CURL FAILED ===")
                logger.error(f"Return code: {result.returncode}")
                logger.error(f"Stdout: {result.stdout[:300] if result.stdout else 'empty'}")
                logger.error(f"Stderr: {result.stderr[:300] if result.stderr else 'empty'}")
                
        except subprocess.TimeoutExpired:
            logger.error("=== CURL TIMEOUT ===")
        except Exception as e:
            logger.error(f"=== CURL EXCEPTION ===: {e}")
        
        return None
    
    def _curl_post(self, url: str, data: dict) -> Optional[dict]:
        """Execute POST request using curl subprocess"""
        cmd = [
            "curl", "-s", "-k",
            "-x", self.proxy_url,
            "-X", "POST",
            "-H", f"Authorization: {self.config.AUTH_TOKEN}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(data),
            "--max-time", str(self.config.REQUEST_TIMEOUT),
            url
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.config.REQUEST_TIMEOUT + 10)
            if result.returncode == 0 and result.stdout:
                return json.loads(result.stdout)
        except Exception as e:
            logger.error(f"Curl POST error: {e}")
        
        return None
    
    # ============== ZEPHYR SCALE API ==============
    
    def get_test_run(self, cycle_name: str) -> Dict[str, Any]:
        """Get test run (cycle) details"""
        url = f"{self.base_url}{self.zephyr_path}/testrun/{cycle_name}"
        params = {"fields": "id,key,name,projectId,projectVersionId"}
        
        for attempt in range(self.config.MAX_RETRIES):
            logger.info(f"Zephyr API (attempt {attempt + 1}): {url}")
            data = self._curl_get(url, params)
            if data:
                logger.info(f"Got test run: id={data.get('id')}, key={data.get('key')}")
                return data
        
        return {"id": cycle_name, "key": cycle_name, "error": "timeout"}
    
    def get_cycle_info(self, cycle_id: str) -> Dict[str, Any]:
        """Get cycle test items"""
        url = f"{self.base_url}{self.zephyr_path}/testrun/{cycle_id}/testrunitems"
        params = {"fields": "id,index,issueCount,$lastTestResult"}
        
        for attempt in range(self.config.MAX_RETRIES):
            data = self._curl_get(url, params)
            if data:
                items = data.get("testRunItems", [])
                logger.info(f"Got {len(items)} test run items")
                return data
        
        return {"testRunItems": []}
    
    def get_test_executions(self, cycle_id: str) -> List[Dict[str, Any]]:
        """Get test executions for a cycle"""
        return self.get_cycle_info(cycle_id).get("testRunItems", [])
    
    # ============== STANDARD JIRA API ==============
    
    def search_issues(self, jql: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Execute JQL search and return issues"""
        url = f"{self.base_url}{self.jira_path}/search"
        params = {
            "jql": jql,
            "maxResults": max_results,
            "fields": "key,summary,status,assignee,priority,issuetype,project,created,updated"
        }
        
        for attempt in range(self.config.MAX_RETRIES):
            logger.info(f"Jira search (attempt {attempt + 1}): {jql[:50]}...")
            data = self._curl_get(url, params)
            if data:
                issues = data.get('issues', [])
                logger.info(f"Found {len(issues)} issues")
                return issues
        
        return []
    
    def get_issues_by_assignee(self, username: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Fetch issues assigned to a user"""
        # URL encode the JQL
        import urllib.parse
        jql = f'assignee = "{username}" ORDER BY updated DESC'
        return self.search_issues(jql, max_results)
    
    def add_comment(self, issue_key: str, comment: str) -> bool:
        """Add a comment to an issue"""
        url = f"{self.base_url}{self.jira_path}/issue/{issue_key}/comment"
        result = self._curl_post(url, {"body": comment})
        return result is not None
    
    def link_issues(self, inward_key: str, outward_key: str, link_type: str = "Relates") -> bool:
        """Link two issues together"""
        url = f"{self.base_url}{self.jira_path}/issueLink"
        payload = {
            "type": {"name": link_type},
            "inwardIssue": {"key": inward_key},
            "outwardIssue": {"key": outward_key}
        }
        result = self._curl_post(url, payload)
        return result is not None


# Create singleton instance
jira_api_client = JiraAPIClient()


def format_issue(issue: Dict[str, Any]) -> Dict[str, Any]:
    """Format Jira issue for frontend display"""
    fields = issue.get('fields', {})
    return {
        "key": issue.get('key'),
        "summary": fields.get('summary', ''),
        "description": fields.get('description', ''),
        "status": fields.get('status', {}).get('name', 'Unknown') if fields.get('status') else 'Unknown',
        "priority": fields.get('priority', {}).get('name', 'Medium') if fields.get('priority') else 'Medium',
        "assignee": fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned',
        "created": fields.get('created', ''),
        "updated": fields.get('updated', ''),
        "project": fields.get('project', {}).get('key', '') if fields.get('project') else '',
        "issuetype": fields.get('issuetype', {}).get('name', '') if fields.get('issuetype') else '',
        "jira_url": f"https://jira.intertech.com.tr/browse/{issue.get('key')}"
    }
