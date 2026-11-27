"""Background scheduler for periodic data synchronization using APScheduler.
"""

import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.core.db import async_session_maker, RecordModel
from app.connectors import (
    get_gmail_connector,
    get_calendar_connector,
    get_tasks_connector,
    get_drive_connector,
)
from app.services.briefing import generate_daily_briefing
from app.core.config import settings
from sqlalchemy import select, delete

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

# In-memory storage for demo credentials (in production, store in DB)
demo_credentials = {
    "access_token": "",
    "refresh_token": "",
}

async def sync_all_sources():
    """Sync data from all Google Workspace sources."""
    logger.info("Starting scheduled sync at %s", datetime.now())
    
    connectors = [
        get_gmail_connector(demo_credentials),
        get_calendar_connector(demo_credentials),
        get_tasks_connector(demo_credentials),
        get_drive_connector(demo_credentials),
    ]
    
    all_records = []
    
    for connector in connectors:
        try:
            records = await connector.fetch()
            all_records.extend(records)
            logger.info("Fetched %d records from %s", len(records), connector.name)
        except Exception as e:
            logger.error("Error fetching from %s: %s", connector.name, e)
    
    # Save to database
    if all_records:
        async with async_session_maker() as session:
            # Clear old records for demo (in production, use upsert)
            await session.execute(delete(RecordModel))
            
            for record in all_records:
                db_record = RecordModel(**record)
                session.add(db_record)
            
            await session.commit()
            logger.info("Saved %d records to database", len(all_records))
            
            # Generate AI briefing
            try:
                briefing = await generate_daily_briefing(all_records)
                logger.info("AI Briefing generated: %s...", briefing[:100])
            except Exception as e:
                logger.error("Error generating briefing: %s", e)
    
    logger.info("Sync completed at %s", datetime.now())

def start_scheduler():
    """Start the background scheduler."""
    # Run sync every 15 minutes
    scheduler.add_job(
        sync_all_sources,
        IntervalTrigger(minutes=15),
        id="sync_job",
        replace_existing=True,
        next_run_time=datetime.now()  # Run immediately on startup
    )
    scheduler.start()
    logger.info("Scheduler started - sync runs every 15 minutes")

def stop_scheduler():
    """Stop the background scheduler."""
    scheduler.shutdown()
    logger.info("Scheduler stopped")