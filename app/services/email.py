from datetime import datetime, timedelta
from app.utils.logger import logger as base_logger
from app.database.session import SessionLocal
from app.models.email_job import EmailJob
from app.config import settings

logger = base_logger.bind(context="email")


def enqueue_email(to_email: str, subject: str, body: str, max_attempts: int | None = None):
    """Create an EmailJob to be processed by the retry worker."""
    db = SessionLocal()
    try:
        job = EmailJob(
            to_email=to_email,
            subject=subject,
            body=body,
            max_attempts=max_attempts or settings.EMAIL_RETRY_MAX_ATTEMPTS,
            status="pending",
            next_attempt_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        logger.info("Enqueued email", job_id=job.id, to=to_email)
        return job
    except Exception:
        logger.exception("Failed to enqueue email", to=to_email)
        raise
    finally:
        db.close()


def _send_via_sendgrid(to_email: str, subject: str, body: str):
    """Attempt to send an email via SendGrid. Raises on failure."""
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
    except Exception as e:
        logger.exception("SendGrid library not available")
        raise

    if not settings.SENDGRID_API_KEY:
        logger.error("SENDGRID_API_KEY not configured")
        raise RuntimeError("SendGrid not configured")

    message = Mail(from_email=settings.EMAIL_FROM, to_emails=to_email, subject=subject, html_content=body)
    client = SendGridAPIClient(settings.SENDGRID_API_KEY)
    resp = client.send(message)
    if resp.status_code >= 400:
        logger.error("SendGrid send failed", status_code=resp.status_code, body=resp.body)
        raise RuntimeError(f"SendGrid error: {resp.status_code}")


def process_pending_emails(limit: int = 50):
    db = SessionLocal()
    now = datetime.utcnow()
    try:
        jobs = db.query(EmailJob).filter(EmailJob.status == "pending", EmailJob.next_attempt_at <= now).order_by(EmailJob.created_at).limit(limit).all()
        logger.info("Processing pending emails", count=len(jobs))
        for j in jobs:
            try:
                _send_via_sendgrid(j.to_email, j.subject, j.body)
                j.status = "sent"
                j.attempts = (j.attempts or 0) + 1
                j.last_error = None
                j.next_attempt_at = None
                db.commit()
                logger.info("Email sent", job_id=j.id, to=j.to_email)
            except Exception as exc:
                j.attempts = (j.attempts or 0) + 1
                j.last_error = str(exc)
                if j.attempts >= (j.max_attempts or settings.EMAIL_RETRY_MAX_ATTEMPTS):
                    j.status = "failed"
                    j.next_attempt_at = None
                    logger.warning("Email job failed permanently", job_id=j.id, attempts=j.attempts)
                else:
                    # exponential backoff
                    delay = settings.EMAIL_RETRY_BASE_DELAY_SECONDS * (2 ** (j.attempts - 1))
                    j.next_attempt_at = datetime.utcnow() + timedelta(seconds=delay)
                    logger.info("Email job scheduled for retry", job_id=j.id, next_attempt_at=str(j.next_attempt_at))
                db.commit()
    except Exception:
        logger.exception("Processing pending emails failed")
    finally:
        db.close()


def send_email(to_email: str, subject: str, body: str):
    """Public API kept for backward compatibility: enqueue email for sending."""
    return enqueue_email(to_email, subject, body)
