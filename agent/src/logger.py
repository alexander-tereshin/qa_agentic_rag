import logging
import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


def setup_logging() -> logging.Logger:
    """Set up the application"s logging configuration."""
    Path("logs").mkdir(exist_ok=True)

    logger = logging.getLogger(__name__)
    log_level = getattr(logging, os.environ["LOG_LEVEL"])
    logger.setLevel(log_level)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler("logs/sql_agent.log", mode="w")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    logger.addHandler(file_handler)

    return logger
