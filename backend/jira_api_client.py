"""
Jira/Zephyr Scale API Client - WITH PROXY SUPPORT
Uses subprocess curl for reliable proxy handling
Inherits system environment variables for proxy support
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
    REQUEST_TIMEOUT = 120  # Increased timeout
    CONNECT_TIMEOUT = 30   # Connection timeout
    MAX_RETRIES = 3
    # Proxy settings - can be overridden by env vars
    PROXY_HOST = os.getenv("PROXY_HOST", "10.125.24.215")
    PROXY_PORT = os.getenv("PROXY_PORT", "8080")


class JiraAPIClient:
    """
    HTTP client for Jira/Zephyr Scale API
    Tries both with and without proxy for maximum compatibility
    """
    
    def __init__(self):
        self.config = JiraConfig()
        self.base_url = self.config.BASE_URL
        self.zephyr_path = self.config.ZEPHYR_API_PATH
        self.jira_path = self.config.JIRA_API_PATH
        self.proxy_url = f"http://{self.config.PROXY_HOST}:{self.config.PROXY_PORT}"
        # Check if we should use proxy or not
        self.use_proxy = os.getenv("USE_PROXY", "auto").lower()  # auto, yes, no
        logger.info(f"Jira client initialized. Proxy mode: {self.use_proxy}, Proxy URL: {self.proxy_url}")
    
    def _curl_get(self, url: str, params: dict = None, use_proxy: bool = True) -> Optional[dict]:
        """Execute GET request using curl subprocess"""
        import urllib.parse
        
        # Build URL with properly encoded params
        if params:
            encoded_params = urllib.parse.urlencode(params)
            full_url = f"{url}?{encoded_params}"
        else:
            full_url = url
        
        # Prepare environment
        env = os.environ.copy()
        
        # Build command based on proxy setting
        cmd = [
            "curl", "-s", "-k",  # silent, skip SSL verification
            "--connect-timeout", str(self.config.CONNECT_TIMEOUT),
            "--max-time", str(self.config.REQUEST_TIMEOUT),
            "-H", f"Authorization: {self.config.AUTH_TOKEN}",
            "-H", "Content-Type: application/json",
            "-H", "Accept: application/json",
        ]
        
        if use_proxy:
            cmd.extend(["-x", self.proxy_url])
            env['HTTP_PROXY'] = self.proxy_url
            env['HTTPS_PROXY'] = self.proxy_url
            env['http_proxy'] = self.proxy_url
            env['https_proxy'] = self.proxy_url
        else:
            # Clear proxy env vars for direct connection
            env.pop('HTTP_PROXY', None)
            env.pop('HTTPS_PROXY', None)
            env.pop('http_proxy', None)
            env.pop('https_proxy', None)
        
        cmd.append(full_url)
        
        try:
            proxy_status = f"WITH proxy ({self.proxy_url})" if use_proxy else "WITHOUT proxy (direct)"
            logger.info(f"=== CURL GET {proxy_status} ===")
            logger.info(f"URL: {full_url[:150]}...")
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=self.config.REQUEST_TIMEOUT + 30,
                env=env
            )
            
            logger.info(f"Curl return code: {result.returncode}")
            
            if result.returncode == 0 and result.stdout:
                logger.info(f"Response length: {len(result.stdout)} chars")
                try:
                    data = json.loads(result.stdout)
                    logger.info(f"=== CURL SUCCESS ({proxy_status}) ===")
                    return data
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parse error: {e}")
                    # Check if it's HTML error page
                    if "<html" in result.stdout.lower():
                        logger.error("Received HTML instead of JSON - possible auth or proxy issue")
                    logger.error(f"Raw response (first 500 chars): {result.stdout[:500]}")
            else:
                logger.error(f"=== CURL FAILED ({proxy_status}) ===")
                logger.error(f"Return code: {result.returncode}")
                if result.returncode == 28:
                    logger.error("TIMEOUT: Connection timed out")
                elif result.returncode == 7:
                    logger.error("CONNECTION REFUSED")
                elif result.returncode == 35:
                    logger.error("SSL ERROR")
                elif result.returncode == 6:
                    logger.error("COULD NOT RESOLVE HOST")
                logger.error(f"Stderr: {result.stderr[:300] if result.stderr else 'empty'}")
                
        except subprocess.TimeoutExpired:
            logger.error(f"=== CURL SUBPROCESS TIMEOUT ({proxy_status}) ===")
        except Exception as e:
            logger.error(f"=== CURL EXCEPTION ({proxy_status}) ===: {e}")
        
        return None
    
    def _smart_curl_get(self, url: str, params: dict = None) -> Optional[dict]:
        """Smart GET that tries both proxy and direct connection"""
        if self.use_proxy == "yes":
            return self._curl_get(url, params, use_proxy=True)
        elif self.use_proxy == "no":
            return self._curl_get(url, params, use_proxy=False)
        else:
            # Auto mode: try without proxy first (like friend's axios), then with proxy
            logger.info("Auto mode: Trying direct connection first...")
            result = self._curl_get(url, params, use_proxy=False)
            if result:
                return result
            
            logger.info("Direct connection failed, trying with proxy...")
            return self._curl_get(url, params, use_proxy=True)
    
    def _curl_post(self, url: str, data: dict, use_proxy: bool = True) -> Optional[dict]:
        """Execute POST request using curl subprocess"""
        env = os.environ.copy()
        
        cmd = [
            "curl", "-s", "-k",
            "-X", "POST",
            "--connect-timeout", str(self.config.CONNECT_TIMEOUT),
            "--max-time", str(self.config.REQUEST_TIMEOUT),
            "-H", f"Authorization: {self.config.AUTH_TOKEN}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(data),
        ]
        
        if use_proxy:
            cmd.extend(["-x", self.proxy_url])
            env['HTTP_PROXY'] = self.proxy_url
            env['HTTPS_PROXY'] = self.proxy_url
        
        cmd.append(url)
        
        try:
            proxy_status = "with proxy" if use_proxy else "direct"
            logger.info(f"=== CURL POST ({proxy_status}) ===")
            logger.info(f"URL: {url}")
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=self.config.REQUEST_TIMEOUT + 30,
                env=env
            )
            
            if result.returncode == 0 and result.stdout:
                logger.info(f"=== CURL POST SUCCESS ({proxy_status}) ===")
                return json.loads(result.stdout)
            else:
                logger.error(f"CURL POST failed ({proxy_status}): code={result.returncode}")
        except Exception as e:
            logger.error(f"Curl POST error: {e}")
        
        return None
    
    def _smart_curl_post(self, url: str, data: dict) -> Optional[dict]:
        """Smart POST that tries both methods"""
        if self.use_proxy == "yes":
            return self._curl_post(url, data, use_proxy=True)
        elif self.use_proxy == "no":
            return self._curl_post(url, data, use_proxy=False)
        else:
            result = self._curl_post(url, data, use_proxy=False)
            if result:
                return result
            return self._curl_post(url, data, use_proxy=True)
    
    # ============== ZEPHYR SCALE API ==============
    
    def get_test_run(self, cycle_name: str) -> Dict[str, Any]:
        """Get test run (cycle) details"""
        url = f"{self.base_url}{self.zephyr_path}/testrun/{cycle_name}"
        params = {"fields": "id,key,name,projectId,projectVersionId"}
        
        for attempt in range(self.config.MAX_RETRIES):
            logger.info(f"Zephyr API get_test_run (attempt {attempt + 1}/{self.config.MAX_RETRIES})")
            data = self._smart_curl_get(url, params)
            if data:
                logger.info(f"Got test run: id={data.get('id')}, key={data.get('key')}")
                return data
        
        logger.error(f"Failed to get test run after {self.config.MAX_RETRIES} attempts")
        return {"id": cycle_name, "key": cycle_name, "error": "connection_failed"}
    
    def get_cycle_info(self, cycle_id: str) -> Dict[str, Any]:
        """Get cycle test items"""
        url = f"{self.base_url}{self.zephyr_path}/testrun/{cycle_id}/testrunitems"
        params = {"fields": "id,index,issueCount,$lastTestResult"}
        
        for attempt in range(self.config.MAX_RETRIES):
            data = self._smart_curl_get(url, params)
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
            "maxResults": str(max_results),
            "fields": "key,summary,status,assignee,priority,issuetype,project,created,updated,description"
        }
        
        logger.info("=== JIRA SEARCH ===")
        logger.info(f"JQL: {jql}")
        
        for attempt in range(self.config.MAX_RETRIES):
            logger.info(f"Search attempt {attempt + 1}/{self.config.MAX_RETRIES}")
            data = self._smart_curl_get(url, params)
            if data:
                issues = data.get('issues', [])
                total = data.get('total', 0)
                logger.info(f"=== SEARCH SUCCESS: {len(issues)} issues found (total: {total}) ===")
                return issues
            else:
                logger.warning(f"Search attempt {attempt + 1} returned no data")
        
        logger.error("=== SEARCH FAILED after all retries ===")
        return []
    
    def get_issues_by_assignee(self, username: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Fetch issues assigned to a user - tries multiple formats"""
        logger.info("=== GET ISSUES BY ASSIGNEE ===")
        logger.info(f"Username: {username}")
        
        # Try different JQL formats
        jql_queries = [
            f'assignee = "{username}" ORDER BY updated DESC',
            f'assignee = {username} ORDER BY updated DESC',
            f'assignee ~ "{username}" ORDER BY updated DESC',
        ]
        
        for jql in jql_queries:
            logger.info(f"Trying JQL: {jql}")
            issues = self.search_issues(jql, max_results)
            if issues:
                logger.info(f"Found {len(issues)} issues with JQL: {jql[:50]}...")
                return issues
            logger.info(f"No results for JQL: {jql[:50]}...")
        
        logger.warning("No issues found for any JQL format")
        return []
    
    def add_comment(self, issue_key: str, comment: str) -> bool:
        """Add a comment to an issue"""
        url = f"{self.base_url}{self.jira_path}/issue/{issue_key}/comment"
        result = self._smart_curl_post(url, {"body": comment})
        return result is not None
    
    def link_issues(self, inward_key: str, outward_key: str, link_type: str = "Relates") -> bool:
        """Link two issues together"""
        url = f"{self.base_url}{self.jira_path}/issueLink"
        payload = {
            "type": {"name": link_type},
            "inwardIssue": {"key": inward_key},
            "outwardIssue": {"key": outward_key}
        }
        result = self._smart_curl_post(url, payload)
        return result is not None
    
    def search_users(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Search for users by name/username"""
        logger.info(f"=== SEARCHING USERS: {query} ===")
        
        # Try user search endpoint
        url = f"{self.base_url}{self.jira_path}/user/search"
        params = {
            "username": query,
            "maxResults": max_results
        }
        
        result = self._smart_curl_get(url, params)
        if result and isinstance(result, list):
            logger.info(f"Found {len(result)} users matching '{query}'")
            return result
        
        # Try alternative: user picker
        url2 = f"{self.base_url}{self.jira_path}/user/picker"
        params2 = {
            "query": query,
            "maxResults": max_results
        }
        
        result2 = self._smart_curl_get(url2, params2)
        if result2 and isinstance(result2, dict) and 'users' in result2:
            logger.info(f"Found {len(result2['users'])} users via picker")
            return result2['users']
        
        logger.warning(f"No users found for query: {query}")
        return []
    
    def get_test_case_details(self, test_key: str) -> Dict[str, Any]:
        """Get test case details including custom fields like Test Tipi"""
        logger.info(f"=== GETTING TEST CASE DETAILS: {test_key} ===")
        
        # Zephyr Scale test case endpoint
        url = f"{self.base_url}{self.zephyr_path}/testcase/{test_key}"
        
        result = self._smart_curl_get(url)
        if result:
            logger.info(f"Got test case details for {test_key}")
            return result
        
        # Fallback: Try Jira issue endpoint
        url2 = f"{self.base_url}{self.jira_path}/issue/{test_key}"
        params = {"fields": "summary,customfield_*,status"}
        
        result2 = self._smart_curl_get(url2, params)
        if result2:
            logger.info(f"Got test case from Jira issue for {test_key}")
            return result2
        
        logger.warning(f"Could not get test case details for {test_key}")
        return {}
    
    def get_test_type_from_case(self, test_key: str) -> str:
        """Get the test type (Happy Path, Alternatif, Negatif) from a test case"""
        details = self.get_test_case_details(test_key)
        
        if not details:
            logger.warning(f"No details found for {test_key}")
            return "unknown"
        
        logger.info(f"Test case {test_key} details keys: {list(details.keys())}")
        
        # Check Zephyr Scale customFields array
        custom_fields = details.get("customFields", [])
        logger.info(f"customFields type: {type(custom_fields)}, content: {custom_fields[:3] if isinstance(custom_fields, list) else custom_fields}")
        
        if isinstance(custom_fields, list):
            for cf in custom_fields:
                cf_name = (cf.get("name", "") or "").lower()
                logger.info(f"Checking custom field: {cf_name}")
                if "test tipi" in cf_name or "test type" in cf_name or "tipi" in cf_name:
                    value = cf.get("value", {})
                    logger.info(f"Found test type field! Value: {value}")
                    if isinstance(value, dict):
                        return value.get("name", str(value))
                    return str(value)
        
        # Check customFieldValues (alternative Zephyr format)
        custom_field_values = details.get("customFieldValues", [])
        if isinstance(custom_field_values, list):
            for cfv in custom_field_values:
                cfv_name = (cfv.get("name", "") or "").lower()
                if "test tipi" in cfv_name or "test type" in cfv_name:
                    value = cfv.get("value", {})
                    logger.info(f"Found test type in customFieldValues! Value: {value}")
                    if isinstance(value, dict):
                        return value.get("name", str(value))
                    return str(value)
        
        # Check fields directly (Jira format)
        fields = details.get("fields", {})
        if fields:
            logger.info(f"Checking fields: {list(fields.keys())[:10]}")
            for key, value in fields.items():
                if key.startswith("customfield_") and value:
                    if isinstance(value, dict):
                        val_name = value.get("value", "") or value.get("name", "")
                        if val_name:
                            val_lower = val_name.lower()
                            if "happy" in val_lower or "alternatif" in val_lower or "negatif" in val_lower:
                                logger.info(f"Found test type in {key}: {val_name}")
                                return val_name
        
        logger.warning(f"Could not find test type for {test_key}")
        return "unknown"
        
        # Check Jira custom fields format
        if isinstance(custom_fields, dict):
            for key, value in custom_fields.items():
                if isinstance(value, dict) and value.get("name"):
                    name = value.get("name", "").lower()
                    if "happy" in name:
                        return "Happy Path"
                    elif "alternatif" in name or "alternative" in name:
                        return "Alternatif Senaryo"
                    elif "negatif" in name or "negative" in name:
                        return "Negatif Senaryo"
        
        # Check fields directly
        fields = details.get("fields", {})
        if fields:
            for key, value in fields.items():
                if key.startswith("customfield_") and isinstance(value, dict):
                    val_name = (value.get("value", "") or value.get("name", "") or "").lower()
                    if "happy" in val_name:
                        return "Happy Path"
                    elif "alternatif" in val_name or "alternative" in val_name:
                        return "Alternatif Senaryo"
                    elif "negatif" in val_name or "negative" in val_name:
                        return "Negatif Senaryo"
        
        return "unknown"
    
    async def get_test_types_batch(self, test_keys: List[str]) -> Dict[str, str]:
        """Get test types for multiple test cases"""
        import asyncio
        
        results = {}
        for key in test_keys:
            test_type = self.get_test_type_from_case(key)
            results[key] = test_type
        
        return results
    
    def get_user_task_stats(self, username: str, months: int = 1) -> Dict[str, Any]:
        """Get task statistics for a user"""
        from datetime import datetime, timedelta
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        date_str = start_date.strftime("%Y-%m-%d")
        
        stats = {
            "backlog": 0,
            "in_progress": 0,
            "completed": 0,
            "tasks": []
        }
        
        # JQL for open tasks (backlog + in progress)
        jql_open = f'assignee = "{username}" AND status NOT IN (Done, Closed, Resolved, Cancelled, "İptal Edildi") AND created >= "{date_str}" ORDER BY status ASC'
        
        open_issues = self.search_issues(jql_open, max_results=200)
        
        for issue in open_issues:
            fields = issue.get('fields', {})
            status_name = (fields.get('status', {}).get('name', '') or '').lower()
            
            task_info = {
                "key": issue.get('key', ''),
                "summary": fields.get('summary', ''),
                "status": fields.get('status', {}).get('name', ''),
                "priority": fields.get('priority', {}).get('name', ''),
                "created": fields.get('created', '')[:10] if fields.get('created') else ''
            }
            
            if 'progress' in status_name or 'doing' in status_name or 'development' in status_name:
                stats["in_progress"] += 1
                task_info["category"] = "in_progress"
            else:
                stats["backlog"] += 1
                task_info["category"] = "backlog"
            
            stats["tasks"].append(task_info)
        
        # JQL for completed tasks
        jql_done = f'assignee = "{username}" AND status IN (Done, Closed, Resolved) AND resolved >= "{date_str}" ORDER BY resolved DESC'
        
        done_issues = self.search_issues(jql_done, max_results=200)
        stats["completed"] = len(done_issues)
        
        for issue in done_issues:
            fields = issue.get('fields', {})
            stats["tasks"].append({
                "key": issue.get('key', ''),
                "summary": fields.get('summary', ''),
                "status": fields.get('status', {}).get('name', ''),
                "priority": fields.get('priority', {}).get('name', ''),
                "created": fields.get('created', '')[:10] if fields.get('created') else '',
                "category": "completed"
            })
        
        return stats


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
