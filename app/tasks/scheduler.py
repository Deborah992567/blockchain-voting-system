from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from app.utils.logger import logger as base_logger
from app.auths.otp import cleanup_expired_otps
from app.database.session import SessionLocal

logger = base_logger.bind(context="scheduler")


def _cleanup_job():
    logger.info("Running scheduled cleanup job", time=str(datetime.utcnow()))
    db = SessionLocal()
    try:
        cleanup_expired_otps(db)
    except Exception:
        logger.exception("Cleanup job failed")
    finally:
        db.close()


def start_scheduler(app):
    scheduler = BackgroundScheduler()
    # run every hour
    scheduler.add_job(_cleanup_job, 'interval', hours=1, id='cleanup_otps')
    scheduler.start()
    app.state.scheduler = scheduler
    logger.info("Scheduler started")


def stop_scheduler(app):
    scheduler = getattr(app.state, 'scheduler', None)
    if scheduler:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
