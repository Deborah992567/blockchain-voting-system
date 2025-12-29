from loguru import logger
import sys
import os
from datetime import datetime

# Create logs directory if it doesn't exist
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Remove default logger
logger.remove()

# Console logger (INFO+)
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{extra[context]}</cyan> | {message}"
)

# File logger (DEBUG+, daily rotation, keep 7 days)
logger.add(
    f"{LOG_DIR}/backend_{datetime.now().strftime('%Y-%m-%d')}.log",
    rotation="1 day",       # new file every day
    retention="7 days",     # keep last 7 days
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[context]} | {message}"
)
