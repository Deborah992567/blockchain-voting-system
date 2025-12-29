from app.utils.logger import logger as base_logger

logger = base_logger.bind(context="email")


def send_email(to_email: str, subject: str, body: str):
    """Send an email. Currently a stub — logs the attempt and any failures."""
    logger.info("Attempting to send email", to=to_email, subject=subject)
    try:
        # TODO: integrate real email provider
        print(f"Sending email to {to_email}")
        print(subject)
        print(body)
        logger.info("Email sent", to=to_email)
    except Exception:
        logger.exception("Failed to send email", to=to_email, subject=subject)
