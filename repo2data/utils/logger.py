"""Logging configuration for repo2data."""

import logging
import sys
from typing import Optional


def setup_logger(
    name: str = "repo2data",
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configure logging for the application.

    Parameters
    ----------
    name : str
        Name of the logger (default: "repo2data")
    level : int
        Logging level (default: logging.INFO)
    log_file : str, optional
        Path to log file. If None, only console logging is enabled

    Returns
    -------
    logging.Logger
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "repo2data") -> logging.Logger:
    """
    Get a logger instance. If not configured, sets up default configuration.

    Parameters
    ----------
    name : str
        Name of the logger (default: "repo2data")

    Returns
    -------
    logging.Logger
        Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        setup_logger(name)
    return logger
