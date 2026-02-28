import logging
import traceback
from datetime import datetime, timezone
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.tasks.celery_app import celery_app
from app.models.models import Job, Lead

logger = logging.getLogger(__name__)

# Basic synchronous engine and session factory for the Celery worker
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class BaseLeadScraper:
    """
    Placeholder base class for the actual scraper implementation.
    The real scraper will be plugged in later behind this interface.
    """
    def scrape(self, intent: str, lead_count: int, job_id: int):
        # NOTE: Playwright/scraping logic intentionally omitted per requirements.
        raise NotImplementedError("Real scraper logic is not implemented yet.")


@celery_app.task(bind=True, name="app.tasks.generate_leads")
def generate_leads_task(self, job_id: int):
    """
    Celery task that manages the lifecycle of a lead generation job (QUEUED -> PROCESSING -> COMPLETED/FAILED).
    """
    db = SessionLocal()
    try:
        # 1. Fetch Job from DB
        job = db.get(Job, job_id)
        if not job:
            logger.error(f"Job {job_id} not found in database.")
            return

        # 2. Transition job -> PROCESSING
        job.status = "processing"
        job.started_at = datetime.now(timezone.utc)
        job.progress = 0
        db.commit()

        # 3. Call placeholder scraper
        try:
            scraper = BaseLeadScraper()
            scraper.scrape(intent=job.intent, lead_count=job.lead_count, job_id=job.id)

            # If the scraper doesn't raise, we update to 100%
            job.progress = 100
            job.status = "completed"
            
            # (In a real implementation, we might insert the returned Leads here)
            # Insert dummy leads on success:
            # db.add(Lead(job_id=job.id, name="Dummy Lead", confidence=0.9))

        except NotImplementedError as e:
            # Trap the NotImplementedError and fail the job gracefully exactly as requested
            logger.warning(f"Job {job_id} failed intentionally: {str(e)}")
            job.status = "failed"
            job.error_message = str(e)
            
        except Exception as e:
            # Catch all generic exceptions
            logger.error(f"Job {job_id} failed with error: {str(e)}")
            logger.debug(traceback.format_exc())
            job.status = "failed"
            job.error_message = str(e)

        # 4. Set completed_at and persist transitions
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as exc:
        logger.error(f"Critical error in task {self.request.id}: {exc}")
        db.rollback()
        raise exc
    finally:
        db.close()
