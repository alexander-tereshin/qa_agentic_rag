import logging

from resume_parser.config.config import settings


def setup_logging() -> logging.Logger:
    """Set up the application"s logging configuration."""
    logger = logging.getLogger(__name__)
    log_level = getattr(logging, settings.log_level)
    logger.setLevel(log_level)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)
    return logger
