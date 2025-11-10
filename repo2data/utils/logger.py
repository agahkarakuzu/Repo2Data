"""Logging configuration for repo2data with rich formatting."""

import logging
import sys
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

# Custom theme for repo2data
REPO2DATA_THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
})

# Global console instance
console = Console(theme=REPO2DATA_THEME)


class CleanRichHandler(RichHandler):
    """Custom RichHandler with cleaner formatting."""

    def __init__(self, *args, **kwargs):
        """Initialize with sensible defaults for repo2data."""
        kwargs.setdefault("show_time", False)
        kwargs.setdefault("show_path", False)
        kwargs.setdefault("markup", True)
        kwargs.setdefault("rich_tracebacks", True)
        kwargs.setdefault("tracebacks_show_locals", False)
        super().__init__(*args, **kwargs, console=console)


def setup_logger(
    name: str = "repo2data",
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configure logging for the application with rich formatting.

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

    # Rich console handler with clean formatting
    console_handler = CleanRichHandler(level=level)
    console_handler.setLevel(level)

    # No formatter needed - Rich handles it beautifully
    logger.addHandler(console_handler)

    # File handler (optional) - plain format for files
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)

        # Plain formatter for file logs
        file_formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
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
