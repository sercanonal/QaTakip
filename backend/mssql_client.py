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

# MSSQL Configuration - Increased timeouts for VPN/corporate network
MSSQL_CONFIG = {
    "server": "WIPREDB31.intertech.com.tr",
    "user": "quantra",
    "password": "quantra2",
    "database": "TEST_DATA_MANAGEMENT",
    "timeout": 60,  # Increased timeout for slow network
    "login_timeout": 30,  # Increased login timeout
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

# ============== HELPER FUNCTIONS ==============

def format_date_for_sql(date_str: str) -> str:
    """Convert GG/AA/YYYY format to YYYY-MM-DD for SQL Server"""
    # If already in YYYY-MM-DD format, return as is
    if '-' in date_str and len(date_str) == 10:
        return date_str
    
    # Parse GG/AA/YYYY format
    parts = date_str.split('/')
    if len(parts) != 3:
        raise ValueError(f'Tarih formatı hatalı! GG/AA/YYYY olmalı (örn: 10/12/2025). Girilen: {date_str}')
    
    day = parts[0].zfill(2)
    month = parts[1].zfill(2)
    year = parts[2]
    
    return f"{year}-{month}-{day}"

# ============== API ANALIZ QUERIES ==============

def get_rapor_data(jira_team_id: int, report_date: str) -> List[Dict[str, Any]]:
    """Get report data from MICROSERVICE_ENDPOINTS table"""
    sql_date = format_date_for_sql(report_date)
    
    query = f"""
    SELECT * FROM [TEST_DATA_MANAGEMENT].[COR].[MICROSERVICE_ENDPOINTS](nolock) 
    WHERE JIRA_TEAM_ID = {jira_team_id} AND TRAN_UPDATED_DATETIME = '{sql_date}'
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

# ============== PRODUCT TREE QUERIES ==============

def get_team_name(jira_team_id: int) -> str:
    """Get team name from JIRA_TEAM table"""
    query = f"""
    SELECT JIRA_TEAM_NAME FROM [TEST_DATA_MANAGEMENT].[TEAM].[JIRA_TEAM](nolock) 
    WHERE JIRA_TEAM_ID = {jira_team_id}
    """
    results = query_data(query)
    if results:
        return results[0]["JIRA_TEAM_NAME"]
    return f"Team-{jira_team_id}"

def get_product_tree_rapor_data(jira_team_id: int, report_date: str) -> List[Dict[str, Any]]:
    """Get endpoint data for product tree analysis"""
    sql_date = format_date_for_sql(report_date)
    
    query = f"""
    SELECT * FROM [TEST_DATA_MANAGEMENT].[COR].[MICROSERVICE_ENDPOINTS](nolock) 
    WHERE JIRA_TEAM_ID = {jira_team_id} AND TRAN_UPDATED_DATETIME = '{sql_date}' AND IS_EXTERNAL = 0
    """
    
    results = query_data(query)
    return [
        {
            "app": r["PROJECT_NAME"],
            "endpoint": r["PATH"],
            "isTested": r["IS_USABLE"] == 1,
            "method": r.get("HTTP_METHOD", "GET")
        }
        for r in results
    ]

def get_test_detail_for_product_tree(project_names: List[str], days: int, time: str) -> List[Dict[str, Any]]:
    """Get test details for product tree - aggregates by endpoint"""
    time_with_seconds = f"{time}:00"
    project_names_str = ", ".join([f"'{p}'" for p in project_names])
    
    query = f"""
    SELECT 
        TARGET_APP_NAME, 
        ENDPOINT_NAME, 
        ISSUE_ID, 
        CASE 
            WHEN MAX(CASE WHEN TEST_STATUS = 'PASSED' THEN 1 ELSE 0 END) = 1 THEN 'PASSED'
            ELSE 'FAILED'
        END as TEST_STATUS,
        TEST_NAME
    FROM [TEST_DATA_MANAGEMENT].[COR].[TEST_AUTOMATION_FRAMEWORK_SUMMARY_LOG](nolock) 
    WHERE PROJECT_NAME IN ({project_names_str}) 
    AND START_TIME >= DATEADD(DAY, -{days}, CAST(CAST(GETDATE() AS DATE) AS DATETIME) + CAST('{time_with_seconds}' AS DATETIME))
    GROUP BY TARGET_APP_NAME, ENDPOINT_NAME, ISSUE_ID, TEST_NAME
    """
    
    results = query_data(query)
    return [
        {
            "key": r["ISSUE_ID"],
            "name": r["TEST_NAME"],
            "app": r["TARGET_APP_NAME"],
            "status": r["TEST_STATUS"],
            "endpoint": r["ENDPOINT_NAME"]
        }
        for r in results
    ]
