"""Base class for data providers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any
import logging


class BaseProvider(ABC):
    """
    Abstract base class for all data providers.

    Each provider handles downloading data from a specific source type
    (e.g., HTTP, S3, Google Drive, etc.).
    """

    def __init__(self, config: Dict[str, Any], destination: Path):
        """
        Initialize the provider.

        Parameters
        ----------
        config : dict
            Configuration dictionary containing 'src' and other parameters
        destination : pathlib.Path
            Destination directory for downloaded data
        """
        self.config = config
        self.destination = Path(destination)
        self.source = config.get("src", "")
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def can_handle(self, source: str) -> bool:
        """
        Check if this provider can handle the given source.

        Parameters
        ----------
        source : str
            Source URL or command string

        Returns
        -------
        bool
            True if this provider can handle the source
        """
        pass

    @abstractmethod
    def download(self) -> Path:
        """
        Download data from source to destination.

        Returns
        -------
        pathlib.Path
            Path to downloaded content (file or directory)

        Raises
        ------
        Exception
            If download fails
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Get the name of this provider.

        Returns
        -------
        str
            Provider name (e.g., "HTTP", "S3", "Google Drive")
        """
        pass

    def _ensure_destination_exists(self) -> None:
        """Create destination directory if it doesn't exist."""
        self.destination.mkdir(parents=True, exist_ok=True)
        self.logger.debug(f"Destination directory: {self.destination}")

    def __repr__(self) -> str:
        """String representation of the provider."""
        return (
            f"{self.__class__.__name__}("
            f"source={self.source}, "
            f"destination={self.destination})"
        )
