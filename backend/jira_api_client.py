"""
Jira REST API Client - Synchronous Implementation
Port from axiosClient.js - uses requests library for reliability
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
    """Jira Configuration"""
    BASE_URL = "https://jira.intertech.com.tr"
    API_PATH = "/rest/api/2"
    # Token: Basic aW50ZWdyYXRpb25fdXNlcjpkMkBDQig1ZA==
    AUTH_TOKEN = os.getenv("JIRA_AUTH_TOKEN", "Basic aW50ZWdyYXRpb25fdXNlcjpkMkBDQig1ZA==")
    REQUEST_TIMEOUT = 60  # Increased timeout
    MAX_RETRIES = 2

class JiraAPIClient:
    """Synchronous HTTP client for Jira REST API"""
    
    def __init__(self):
        self.config = JiraConfig()
        self.base_url = self.config.BASE_URL
        self.api_path = self.config.API_PATH
        self.headers = {
            "Authorization": self.config.AUTH_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        # Create session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.verify = False  # Skip SSL verification for internal server
    
    def search_issues(self, jql: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Execute JQL search and return issues"""
        url = f"{self.base_url}{self.api_path}/search"
        params = {
            "jql": jql,
            "maxResults": max_results,
            "fields": "key,summary,status,assignee,created,updated,priority,issuetype,description,project"
        }
        
        for attempt in range(self.config.MAX_RETRIES):
            try:
                logger.info(f"Jira API request (attempt {attempt + 1}): {url}")
                logger.info(f"JQL: {jql}")
                
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.config.REQUEST_TIMEOUT
                )
                
                logger.info(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    issues = data.get('issues', [])
                    total = data.get('total', 0)
                    logger.info(f"Found {len(issues)} issues out of {total} total")
                    return issues
                elif response.status_code == 401:
                    logger.error("Jira authentication failed")
                    return []
                elif response.status_code == 400:
                    logger.error(f"Invalid JQL: {jql}")
                    return []
                else:
                    logger.error(f"Jira API error: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Jira API timeout (attempt {attempt + 1}/{self.config.MAX_RETRIES})")
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error: {e}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
        
        return []
    
    def get_issues_by_assignee(self, username: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Fetch issues assigned to a user"""
        # Try with quotes first
        jql = f'assignee = "{username}" ORDER BY updated DESC'
        issues = self.search_issues(jql, max_results)
        
        if not issues:
            # Try without quotes
            jql = f'assignee = {username} ORDER BY updated DESC'
            issues = self.search_issues(jql, max_results)
        
        return issues
    
    def get_test_run(self, cycle_key: str) -> Optional[Dict[str, Any]]:
        """Get test run (cycle) details from Jira"""
        # First try to get from Zephyr Scale API
        url = f"{self.base_url}/rest/atm/1.0/testrun/{cycle_key}"
        
        try:
            response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT)
            if response.status_code == 200:
                return response.json()
            
            # Fallback: try Zephyr Squad API
            url = f"{self.base_url}/rest/zapi/latest/cycle"
            params = {"cycleId": cycle_key}
            response = self.session.get(url, params=params, timeout=self.config.REQUEST_TIMEOUT)
            if response.status_code == 200:
                return response.json()
                
        except Exception as e:
            logger.error(f"Error getting test run {cycle_key}: {e}")
        
        return {"id": cycle_key, "key": cycle_key}  # Return basic info if API fails
    
    def get_test_executions(self, cycle_id: str) -> List[Dict[str, Any]]:
        """Get test executions for a cycle"""
        # Try Zephyr Scale API
        url = f"{self.base_url}/rest/atm/1.0/testrun/{cycle_id}/testresults"
        
        try:
            response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Error getting test executions: {e}")
        
        return []
    
    def add_comment(self, issue_key: str, comment: str) -> bool:
        """Add a comment to an issue"""
        url = f"{self.base_url}{self.api_path}/issue/{issue_key}/comment"
        
        try:
            response = self.session.post(
                url,
                json={"body": comment},
                timeout=self.config.REQUEST_TIMEOUT
            )
            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Error adding comment to {issue_key}: {e}")
            return False
    
    def update_issue(self, issue_key: str, fields: Dict[str, Any]) -> bool:
        """Update issue fields"""
        url = f"{self.base_url}{self.api_path}/issue/{issue_key}"
        
        try:
            response = self.session.put(
                url,
                json={"fields": fields},
                timeout=self.config.REQUEST_TIMEOUT
            )
            return response.status_code in [200, 204]
        except Exception as e:
            logger.error(f"Error updating {issue_key}: {e}")
            return False
    
    def link_issues(self, inward_key: str, outward_key: str, link_type: str = "Relates") -> bool:
        """Link two issues together"""
        url = f"{self.base_url}{self.api_path}/issueLink"
        
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
            logger.error(f"Error linking {inward_key} to {outward_key}: {e}")
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
