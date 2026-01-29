"""
Jira REST API Client
Handles communication with Intertech Jira instance
"""

import httpx
import logging
from typing import Optional, Dict, Any, List
import os

logger = logging.getLogger(__name__)

class JiraConfig:
    """Jira Configuration"""
    BASE_URL = "https://jira.intertech.com.tr"
    API_PATH = "/rest/api/2"  # Using API v2 for broader compatibility
    # Token from user: Basic aW50ZWdyYXRpb25fdXNlcjpkMkBDQig1ZA==
    AUTH_TOKEN = os.getenv("JIRA_AUTH_TOKEN", "Basic aW50ZWdyYXRpb25fdXNlcjpkMkBDQig1ZA==")

class JiraClient:
    """HTTP client for Jira REST API communication"""
    
    def __init__(self):
        self.config = JiraConfig()
        self.base_url = self.config.BASE_URL
        self.api_path = self.config.API_PATH
        self.headers = {
            "Authorization": self.config.AUTH_TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    
    async def get_issues_by_assignee(
        self, 
        assignee_identifier: str,  # Can be username or email
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Fetch issues assigned to a specific user by username or email
        """
        # Try with username first, then email
        jql_username = f'assignee = {assignee_identifier} ORDER BY updated DESC'
        jql_email = f'assignee = "{assignee_identifier}" ORDER BY updated DESC'
        
        # Try username first
        issues = await self._search_issues(jql_username, max_results)
        
        # If no results and looks like email, try email search
        if not issues and '@' in assignee_identifier:
            issues = await self._search_issues(jql_email, max_results)
        
        return issues
    
    async def _search_issues(self, jql: str, max_results: int) -> List[Dict[str, Any]]:
        """Execute JQL search"""
        try:
            async with httpx.AsyncClient(verify=False) as client:  # Note: verify=False for self-signed certs
                response = await client.get(
                    f"{self.base_url}{self.api_path}/search",
                    headers=self.headers,
                    params={
                        "jql": jql,
                        "maxResults": max_results,
                        "fields": "key,summary,status,assignee,created,updated,priority,issuetype,description"
                    },
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    issues = data.get('issues', [])
                    logger.info(f"Fetched {len(issues)} issues from Jira")
                    return issues
                elif response.status_code == 401:
                    logger.error("Jira authentication failed - check API token")
                    return []
                elif response.status_code == 400:
                    logger.warning(f"Invalid JQL query: {jql}")
                    return []
                else:
                    logger.error(f"Jira API error: {response.status_code}")
                    return []
        
        except httpx.TimeoutException:
            logger.error("Timeout communicating with Jira API")
            return []
        except Exception as e:
            logger.error(f"Jira request error: {e}")
            return []
    
    async def get_user_by_identifier(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Find Jira user by username or email"""
        try:
            async with httpx.AsyncClient(verify=False) as client:
                # Try searching by email or username
                response = await client.get(
                    f"{self.base_url}{self.api_path}/user/search",
                    headers=self.headers,
                    params={"username": identifier} if '@' not in identifier else {"query": identifier},
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    users = response.json()
                    if users:
                        return users[0]
                
                return None
        
        except Exception as e:
            logger.error(f"Error fetching Jira user: {e}")
            return None
    
    async def add_comment_to_issue(self, issue_key: str, comment_text: str) -> bool:
        """Add a comment to a Jira issue"""
        try:
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.post(
                    f"{self.base_url}{self.api_path}/issue/{issue_key}/comment",
                    headers=self.headers,
                    json={"body": comment_text},
                    timeout=30.0,
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"Comment added to {issue_key}")
                    return True
                else:
                    logger.error(f"Failed to add comment: {response.status_code}")
                    return False
        
        except Exception as e:
            logger.error(f"Error adding comment: {e}")
            return False
    
    async def update_issue_status(self, issue_key: str, status_name: str) -> bool:
        """Update Jira issue status (transition)"""
        try:
            async with httpx.AsyncClient(verify=False) as client:
                # Get available transitions
                trans_response = await client.get(
                    f"{self.base_url}{self.api_path}/issue/{issue_key}/transitions",
                    headers=self.headers,
                    timeout=30.0,
                )
                
                if trans_response.status_code != 200:
                    logger.error(f"Failed to get transitions: {trans_response.status_code}")
                    return False
                
                transitions = trans_response.json().get('transitions', [])
                
                # Find matching transition
                # Map our statuses to Jira statuses
                status_mapping = {
                    'in_progress': ['In Progress', 'Start Progress', 'In Development'],
                    'completed': ['Done', 'Resolved', 'Closed'],
                    'blocked': ['Blocked', 'On Hold'],
                    'backlog': ['To Do', 'Open', 'Backlog'],
                    'today_planned': ['To Do', 'Selected for Development']
                }
                
                target_statuses = status_mapping.get(status_name, [status_name])
                transition_id = None
                
                for transition in transitions:
                    if transition['to']['name'] in target_statuses:
                        transition_id = transition['id']
                        break
                
                if not transition_id:
                    logger.warning(f"No transition found for status {status_name}")
                    return False
                
                # Execute transition
                response = await client.post(
                    f"{self.base_url}{self.api_path}/issue/{issue_key}/transitions",
                    headers=self.headers,
                    json={"transition": {"id": transition_id}},
                    timeout=30.0,
                )
                
                if response.status_code in [200, 204]:
                    logger.info(f"Status updated for {issue_key}")
                    return True
                else:
                    logger.error(f"Failed to update status: {response.status_code}")
                    return False
        
        except Exception as e:
            logger.error(f"Error updating status: {e}")
            return False
    
    def transform_issue(self, raw_issue: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw Jira issue to application format"""
        fields = raw_issue.get("fields", {})
        
        return {
            "key": raw_issue.get("key"),
            "jira_id": raw_issue.get("id"),
            "summary": fields.get("summary", ""),
            "description": fields.get("description", ""),
            "status": fields.get("status", {}).get("name", "Unknown"),
            "status_category": fields.get("status", {}).get("statusCategory", {}).get("name", ""),
            "priority": fields.get("priority", {}).get("name", "Medium"),
            "issue_type": fields.get("issuetype", {}).get("name", "Task"),
            "assignee": fields.get("assignee", {}).get("displayName", "Unassigned") if fields.get("assignee") else "Unassigned",
            "assignee_email": fields.get("assignee", {}).get("emailAddress", "") if fields.get("assignee") else "",
            "created": fields.get("created", ""),
            "updated": fields.get("updated", ""),
            "jira_url": f"{self.base_url}/browse/{raw_issue.get('key')}",
        }


# Global Jira client instance
jira_client = JiraClient()
