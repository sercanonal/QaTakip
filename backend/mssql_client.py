"""
MSSQL Client for QA Hub
Port from mssqlClient.js
"""
import pymssql
import logging
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
import time

logger = logging.getLogger(__name__)

# MSSQL Configuration - SHORT timeouts for fast failure
MSSQL_CONFIG = {
    "server": "WIPREDB31.intertech.com.tr",
    "user": "quantra",
    "password": "quantra2",
    "database": "TEST_DATA_MANAGEMENT",
    "timeout": 10,  # Short timeout
    "login_timeout": 5,  # Very short login timeout for fast failure
    "charset": "UTF-8",
    "as_dict": True
}

# Connection pool (simple implementation)
_connection = None

def get_connection():
    """Get or create MSSQL connection"""
    global _connection
    
    if _connection is not None:
        try:
            # Test if connection is alive
            cursor = _connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return _connection
        except Exception:
            close_connection()
    
    try:
        _connection = pymssql.connect(**MSSQL_CONFIG)
        logger.info("MSSQL bağlantısı başarılı!")
        return _connection
    except Exception as e:
        logger.error(f"MSSQL bağlantı hatası: {e}")
        raise

def close_connection():
    """Close MSSQL connection"""
    global _connection
    if _connection is not None:
        try:
            _connection.close()
        except Exception:
            pass
        _connection = None

def query_data(query: str, retries: int = 2) -> List[Dict[str, Any]]:
    """Execute a query and return results as list of dicts"""
    for attempt in range(retries + 1):
        try:
            conn = get_connection()
            cursor = conn.cursor(as_dict=True)
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Query error (attempt {attempt + 1}): {e}")
            close_connection()
            if attempt < retries:
                time.sleep(0.5 * (attempt + 1))
            else:
                raise

# ============== ANALIZ QUERIES ==============

def get_passed_tests(days: int = 1, time: str = "00:00", project_names: List[str] = None) -> List[Dict[str, Any]]:
    """Get passed tests from database"""
    if project_names is None:
        project_names = ["FraudNG.UITests", "Intertech.FraudNG", "Inter.Fraud.UITests"]
    
    time_with_seconds = f"{time}:00"
    project_names_str = ", ".join([f"'{p}'" for p in project_names])
    
    query = f"""
    SELECT DISTINCT ISSUE_ID, TEST_NAME 
    FROM [TEST_DATA_MANAGEMENT].[COR].[TEST_AUTOMATION_FRAMEWORK_SUMMARY_LOG](nolock) 
    WHERE START_TIME >= DATEADD(DAY, -{days}, CAST(CAST(GETDATE() AS DATE) AS DATETIME) + CAST('{time_with_seconds}' AS DATETIME))
    AND PROJECT_NAME IN ({project_names_str})
    AND TEST_STATUS = 'Passed'
    """
    
    results = query_data(query)
    return [{"key": r["ISSUE_ID"], "name": r["TEST_NAME"]} for r in results]

def get_all_tests(days: int = 1, time: str = "00:00", project_names: List[str] = None) -> List[Dict[str, Any]]:
    """Get all tests from database"""
    if project_names is None:
        project_names = ["FraudNG.UITests", "Intertech.FraudNG", "Inter.Fraud.UITests"]
    
    time_with_seconds = f"{time}:00"
    project_names_str = ", ".join([f"'{p}'" for p in project_names])
    
    query = f"""
    SELECT DISTINCT ISSUE_ID, TEST_NAME, PROJECT_NAME 
    FROM [TEST_DATA_MANAGEMENT].[COR].[TEST_AUTOMATION_FRAMEWORK_SUMMARY_LOG](nolock) 
    WHERE START_TIME >= DATEADD(DAY, -{days}, CAST(CAST(GETDATE() AS DATE) AS DATETIME) + CAST('{time_with_seconds}' AS DATETIME))
    AND PROJECT_NAME IN ({project_names_str})
    """
    
    results = query_data(query)
    return [
        {
            "key": r["ISSUE_ID"],
            "name": r["TEST_NAME"],
            "project": r["PROJECT_NAME"],
            "inRegression": False,
            "status": "Fail"
        }
        for r in results
    ]

# ============== API ANALIZ QUERIES ==============

def get_rapor_data(jira_team_id: int, report_date: str) -> List[Dict[str, Any]]:
    """Get report data from MICROSERVICE_ENDPOINTS table"""
    query = f"""
    SELECT * FROM [TEST_DATA_MANAGEMENT].[COR].[MICROSERVICE_ENDPOINTS](nolock) 
    WHERE JIRA_TEAM_ID = {jira_team_id} AND TRAN_UPDATED_DATETIME = '{report_date}'
    """
    
    results = query_data(query)
    return [
        {
            "app": r["PROJECT_NAME"],
            "endpoint": r["PATH"],
            "test": r["IS_USABLE"] == 1,
            "external": r["IS_EXTERNAL"] == 1
        }
        for r in results
    ]

def get_all_api_tests(project_names: List[str], days: int, time: str) -> List[Dict[str, Any]]:
    """Get all API tests from database"""
    time_with_seconds = f"{time}:00"
    project_names_str = ", ".join([f"'{p}'" for p in project_names])
    
    query = f"""
    SELECT DISTINCT TARGET_APP_NAME, ENDPOINT_NAME, TEST_STATUS_DETAIL, ISSUE_ID, TEST_STATUS, TEST_NAME
    FROM [TEST_DATA_MANAGEMENT].[COR].[TEST_AUTOMATION_FRAMEWORK_SUMMARY_LOG](nolock) 
    WHERE PROJECT_NAME IN ({project_names_str}) 
    AND START_TIME >= DATEADD(DAY, -{days}, CAST(CAST(GETDATE() AS DATE) AS DATETIME) + CAST('{time_with_seconds}' AS DATETIME))
    """
    
    results = query_data(query)
    return [
        {
            "key": r["ISSUE_ID"],
            "name": r["TEST_NAME"],
            "app": r["TARGET_APP_NAME"],
            "status": r["TEST_STATUS"],
            "endpoint": r["ENDPOINT_NAME"],
            "detail": r["TEST_STATUS_DETAIL"]
        }
        for r in results
    ]
