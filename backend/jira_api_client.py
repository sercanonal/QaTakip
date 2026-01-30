"""
Jira/Zephyr Scale API Client - Port from axiosClient.js
Uses Zephyr Scale (TM4J) API: /rest/tests/1.0/
WITH PROXY SUPPORT
"""

import requests
import logging
from typing import Optional, Dict, Any, List
import os
import urllib3

# Disable SSL warnings for internal Jira server
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger("jira_client")

class JiraConfig:
    """Jira/Zephyr Configuration - Port from axiosClient.js"""
    BASE_URL = "https://jira.intertech.com.tr"
    # Zephyr Scale API path (NOT standard Jira API)
    ZEPHYR_API_PATH = "/rest/tests/1.0"
    # Standard Jira API for issue operations
    JIRA_API_PATH = "/rest/api/2"
    # Token: Basic aW50ZWdyYXRpb25fdXNlcjpkMkBDQig1ZA==
    AUTH_TOKEN = os.getenv("JIRA_AUTH_TOKEN", "Basic aW50ZWdyYXRpb25fdXNlcjpkMkBDQig1ZA==")
    REQUEST_TIMEOUT = 60
    MAX_RETRIES = 2
    # PROXY SETTINGS - Corporate network proxy
    PROXY_HOST = os.getenv("PROXY_HOST", "10.125.24.215")
    PROXY_PORT = os.getenv("PROXY_PORT", "8080")


class JiraAPIClient:
    """
    HTTP client for Jira/Zephyr Scale API
    Port from axiosClient.js
    WITH PROXY SUPPORT
    """
    
    def __init__(self):
        self.config = JiraConfig()
        self.base_url = self.config.BASE_URL
        self.zephyr_path = self.config.ZEPHYR_API_PATH
        self.jira_path = self.config.JIRA_API_PATH
        self.headers = {
            "Authorization": self.config.AUTH_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        # PROXY CONFIGURATION
        proxy_url = f"http://{self.config.PROXY_HOST}:{self.config.PROXY_PORT}"
        self.proxies = {
            "http": proxy_url,
            "https": proxy_url,
        }
        logger.info(f"Using proxy: {proxy_url}")
        
        # Create session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(self.proxies)
        self.session.verify = False  # Skip SSL verification for internal server
    
    # ============== ZEPHYR SCALE API (Test Management) ==============
    
    def get_test_run(self, cycle_name: str) -> Dict[str, Any]:
        """
        Get test run (cycle) details - Port from getCycleIdFromName
        URL: /rest/tests/1.0/testrun/{cycleName}
        """
        url = f"{self.base_url}{self.zephyr_path}/testrun/{cycle_name}"
        params = {
            "fields": "id,key,name,projectId,projectVersionId,environmentId,plannedStartDate,plannedEndDate,iteration(name),executionTime,estimatedTime"
        }
        
        for attempt in range(self.config.MAX_RETRIES):
            try:
                logger.info(f"Zephyr API request (attempt {attempt + 1}): {url}")
                
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.config.REQUEST_TIMEOUT
                )
                
                logger.info(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Got test run: id={data.get('id')}, key={data.get('key')}")
                    return data
                elif response.status_code == 404:
                    logger.error(f"Test run not found: {cycle_name}")
                    return {"id": cycle_name, "key": cycle_name, "error": "not_found"}
                else:
                    logger.error(f"Zephyr API error: {response.status_code} - {response.text[:200]}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Zephyr API timeout (attempt {attempt + 1}/{self.config.MAX_RETRIES})")
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error: {e}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
        
        return {"id": cycle_name, "key": cycle_name, "error": "timeout"}
    
    def get_cycle_info(self, cycle_id: str) -> Dict[str, Any]:
        """
        Get cycle test items - Port from getCycleInfo
        URL: /rest/tests/1.0/testrun/{cycleId}/testrunitems
        """
        url = f"{self.base_url}{self.zephyr_path}/testrun/{cycle_id}/testrunitems"
        params = {
            "fields": "id,index,issueCount,$lastTestResult"
        }
        
        for attempt in range(self.config.MAX_RETRIES):
            try:
                logger.info(f"Getting cycle info: {url}")
                
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.config.REQUEST_TIMEOUT
                )
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("testRunItems", [])
                    logger.info(f"Got {len(items)} test run items")
                    return data
                else:
                    logger.error(f"Error getting cycle info: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout getting cycle info (attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"Error: {e}")
        
        return {"testRunItems": []}
    
    def get_test_executions(self, cycle_id: str) -> List[Dict[str, Any]]:
        """Get test executions for a cycle"""
        data = self.get_cycle_info(cycle_id)
        return data.get("testRunItems", [])
    
    # ============== STANDARD JIRA API (Issues) ==============
    
    def search_issues(self, jql: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Execute JQL search and return issues"""
        url = f"{self.base_url}{self.jira_path}/search"
        params = {
            "jql": jql,
            "maxResults": max_results,
            "fields": "key,summary,status,assignee,created,updated,priority,issuetype,description,project"
        }
        
        for attempt in range(self.config.MAX_RETRIES):
            try:
                logger.info(f"Jira search (attempt {attempt + 1}): {jql[:50]}...")
                
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.config.REQUEST_TIMEOUT
                )
                
                logger.info(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    issues = data.get('issues', [])
                    logger.info(f"Found {len(issues)} issues")
                    return issues
                elif response.status_code == 401:
                    logger.error("Jira authentication failed")
                    return []
                else:
                    logger.error(f"Jira API error: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Jira search timeout (attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"Error: {e}")
        
        return []
    
    def get_issues_by_assignee(self, username: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Fetch issues assigned to a user"""
        jql = f'assignee = "{username}" ORDER BY updated DESC'
        issues = self.search_issues(jql, max_results)
        
        if not issues:
            # Try without quotes
            jql = f'assignee = {username} ORDER BY updated DESC'
            issues = self.search_issues(jql, max_results)
        
        return issues
    
    def add_comment(self, issue_key: str, comment: str) -> bool:
        """Add a comment to an issue"""
        url = f"{self.base_url}{self.jira_path}/issue/{issue_key}/comment"
        
        try:
            response = self.session.post(
                url,
                json={"body": comment},
                timeout=self.config.REQUEST_TIMEOUT
            )
            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Error adding comment: {e}")
            return False
    
    def link_issues(self, inward_key: str, outward_key: str, link_type: str = "Relates") -> bool:
        """Link two issues together"""
        url = f"{self.base_url}{self.jira_path}/issueLink"
        
        payload = {
            "type": {"name": link_type},
            "inwardIssue": {"key": inward_key},
            "outwardIssue": {"key": outward_key}
        }
        
        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=self.config.REQUEST_TIMEOUT
            )
            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Error linking issues: {e}")
            return False


# Create singleton instance
jira_api_client = JiraAPIClient()


# Helper function for formatted issue output
def format_issue(issue: Dict[str, Any]) -> Dict[str, Any]:
    """Format Jira issue for frontend display"""
    fields = issue.get('fields', {})
    
    return {
        "key": issue.get('key'),
        "summary": fields.get('summary', ''),
        "description": fields.get('description', ''),
        "status": fields.get('status', {}).get('name', 'Unknown'),
        "priority": fields.get('priority', {}).get('name', 'Medium'),
        "assignee": fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned',
        "created": fields.get('created', ''),
        "updated": fields.get('updated', ''),
        "project": fields.get('project', {}).get('key', ''),
        "issuetype": fields.get('issuetype', {}).get('name', ''),
        "jira_url": f"https://jira.intertech.com.tr/browse/{issue.get('key')}"
    }
