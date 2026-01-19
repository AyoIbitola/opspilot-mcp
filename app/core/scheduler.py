from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.workflow import run_discovery_cycle
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def start_scheduler():
    # Run every 24 hours
    scheduler.add_job(run_discovery_cycle, 'interval', hours=24, id='daily_discovery')
    scheduler.start()
    logger.info("Scheduler started. Job 'daily_discovery' registered for every 24h.")
