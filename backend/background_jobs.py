"""
Background Jobs for QA Task Manager
Handles periodic Jira sync and maintenance tasks
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import aiosqlite
from pathlib import Path
import json

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "qa_tasks.db"

# Global scheduler instance
scheduler = AsyncIOScheduler()

async def sync_jira_tasks_for_all_users():
    """Sync Jira tasks for all users with Jira mappings"""
    try:
        from jira_client import jira_client
        
        logger.info("Starting periodic Jira sync for all users...")
        
        async with aiosqlite.connect(DB_PATH) as db:
            # Get all users with email (needed for Jira)
            cursor = await db.execute(
                "SELECT id, name, email FROM users WHERE email IS NOT NULL AND email != ''"
            )
            users = await cursor.fetchall()
            
            total_synced = 0
            for user in users:
                user_id, username, email = user
                
                try:
                    # Try to fetch Jira issues
                    issues = await jira_client.get_issues_by_assignee(username)
                    
                    if not issues and email:
                        issues = await jira_client.get_issues_by_assignee(email)
                    
                    if issues:
                        # Update cache
                        for issue in issues:
                            jira_key = issue.get('key')
                            jira_id = issue.get('id')
                            
                            if not jira_key:
                                continue
                            
                            transformed = jira_client.transform_issue(issue)
                            
                            # Check if exists
                            check_cursor = await db.execute(
                                "SELECT id FROM jira_tasks_cache WHERE user_id = ? AND jira_key = ?",
                                (user_id, jira_key)
                            )
                            existing = await check_cursor.fetchone()
                            
                            now = datetime.now(timezone.utc).isoformat()
                            
                            if existing:
                                # Update existing
                                await db.execute(
                                    """UPDATE jira_tasks_cache 
                                       SET summary = ?, description = ?, status = ?, priority = ?, 
                                           assignee = ?, issue_type = ?, jira_url = ?, raw_data = ?, last_synced = ?
                                       WHERE id = ?""",
                                    (
                                        transformed['summary'], transformed['description'], 
                                        transformed['status'], transformed['priority'],
                                        transformed['assignee'], transformed['issue_type'],
                                        transformed['jira_url'], json.dumps(issue), now,
                                        existing[0]
                                    )
                                )
                            else:
                                # Insert new
                                cache_id = f"jira-{jira_key}-{user_id}"
                                await db.execute(
                                    """INSERT INTO jira_tasks_cache 
                                       (id, user_id, jira_key, jira_id, summary, description, status, 
                                        priority, assignee, issue_type, jira_url, raw_data, last_synced, created_at)
                                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                    (
                                        cache_id, user_id, jira_key, jira_id,
                                        transformed['summary'], transformed['description'],
                                        transformed['status'], transformed['priority'],
                                        transformed['assignee'], transformed['issue_type'],
                                        transformed['jira_url'], json.dumps(issue), now, now
                                    )
                                )
                                total_synced += 1
                        
                        await db.commit()
                        logger.info(f"Synced {len(issues)} Jira tasks for user {username}")
                
                except Exception as e:
                    logger.error(f"Error syncing Jira for user {username}: {e}")
                    continue
            
            logger.info(f"Jira sync completed. Total new tasks: {total_synced}")
    
    except Exception as e:
        logger.error(f"Jira sync job failed: {e}")

async def cleanup_old_audit_logs():
    """Archive and clean up old audit logs (90+ days)"""
    try:
        logger.info("Starting audit log cleanup...")
        
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
        
        async with aiosqlite.connect(DB_PATH) as db:
            # Count old logs
            cursor = await db.execute(
                "SELECT COUNT(*) FROM audit_logs WHERE created_at < ?",
                (cutoff_date,)
            )
            count = (await cursor.fetchone())[0]
            
            if count > 0:
                # TODO: Export to archive file before deleting
                # For now, just delete
                await db.execute(
                    "DELETE FROM audit_logs WHERE created_at < ?",
                    (cutoff_date,)
                )
                await db.commit()
                logger.info(f"Cleaned up {count} old audit logs")
            else:
                logger.info("No old audit logs to clean up")
    
    except Exception as e:
        logger.error(f"Audit log cleanup failed: {e}")

async def vacuum_database():
    """Optimize database (weekly)"""
    try:
        logger.info("Starting database optimization...")
        
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("VACUUM")
            await db.execute("ANALYZE")
            await db.commit()
        
        logger.info("Database optimization completed")
    
    except Exception as e:
        logger.error(f"Database optimization failed: {e}")

def start_background_jobs():
    """Start all background jobs"""
    
    # Jira sync every 15 minutes
    scheduler.add_job(
        sync_jira_tasks_for_all_users,
        trigger=IntervalTrigger(minutes=15),
        id='jira_sync',
        name='Periodic Jira synchronization',
        replace_existing=True
    )
    
    # Audit log cleanup daily at 2 AM
    scheduler.add_job(
        cleanup_old_audit_logs,
        trigger='cron',
        hour=2,
        minute=0,
        id='audit_cleanup',
        name='Daily audit log cleanup',
        replace_existing=True
    )
    
    # Database vacuum weekly on Sunday at 3 AM
    scheduler.add_job(
        vacuum_database,
        trigger='cron',
        day_of_week='sun',
        hour=3,
        minute=0,
        id='db_vacuum',
        name='Weekly database optimization',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Background jobs started successfully")

def stop_background_jobs():
    """Stop all background jobs"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background jobs stopped")
