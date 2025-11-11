"""Dataset downloader for executing individual downloads."""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from repo2data.cache.manager import CacheManager
from repo2data.utils.decompressor import Decompressor
from repo2data.utils.logger import get_logger, console

# Import provider registry
from repo2data.providers import registry

# Import all providers to register them
from repo2data.providers.http import HTTPProvider
from repo2data.providers.gdrive import GoogleDriveProvider
from repo2data.providers.datalad import DataladProvider
from repo2data.providers.s3 import S3Provider
from repo2data.providers.zenodo import ZenodoProvider
from repo2data.providers.osf import OSFProvider
from repo2data.providers.library import LibraryProvider

logger = logging.getLogger(__name__)


# Register all providers
# Order matters: more specific providers should be registered last
# (they are checked in reverse order)
registry.register(HTTPProvider)
registry.register(DataladProvider)
registry.register(GoogleDriveProvider)
registry.register(S3Provider)
registry.register(ZenodoProvider)
registry.register(OSFProvider)
registry.register(LibraryProvider)


class DatasetDownloader:
    """
    Handles downloading a single dataset.

    Coordinates provider selection, caching, downloading, and decompression.
    Replaces the old Repo2DataChild class.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        server_mode: bool = False,
        server_destination: str = "./data",
        requirement_path: Optional[str] = None,
        download_key: Optional[str] = None
    ):
        """
        Initialize DatasetDownloader.

        Parameters
        ----------
        config : dict
            Download configuration containing 'src', 'projectName', etc.
        server_mode : bool
            If True, force destination to server_destination
        server_destination : str
            Destination directory when in server mode
        requirement_path : str, optional
            Path to requirement file (for dataLayout resolution)
        download_key : str, optional
            Key for multi-download configurations
        """
        self.config = config
        self.server_mode = server_mode
        self.server_destination = server_destination
        self.requirement_path = requirement_path
        self.download_key = download_key
        self.logger = get_logger(__name__)

        # Compute destination path
        self.destination = self._compute_destination()

        # Initialize cache manager and decompressor
        self.cache_manager = CacheManager(self.destination, download_key)
        self.decompressor = Decompressor(self.destination)

    def _compute_destination(self) -> Path:
        """
        Compute destination path based on configuration.

        Returns
        -------
        pathlib.Path
            Destination directory path

        Raises
        ------
        ValueError
            If projectName is missing from config
        """
        if "projectName" not in self.config:
            raise ValueError("Configuration missing 'projectName' field")

        project_name = self.config["projectName"]

        # Server mode: force destination
        if self.server_mode:
            return Path(self.server_destination) / project_name

        # Check for special data layouts
        if "dataLayout" in self.config and self.requirement_path:
            if os.path.exists(self.requirement_path):
                data_layout = self.config["dataLayout"]

                if data_layout == "neurolibre":
                    # Neurolibre layout: ../data relative to requirement file
                    req_dir = os.path.dirname(self.requirement_path)
                    return Path(os.path.realpath(
                        os.path.join(req_dir, "..", "data")
                    )) / project_name

        # Default: use dst from config
        if "dst" in self.config:
            dst_path = Path(self.config["dst"])

            # If dst is relative, resolve it relative to the config file location
            if not dst_path.is_absolute() and self.requirement_path:
                # Get directory containing the config file
                config_dir = Path(self.requirement_path).parent
                # Resolve dst relative to config file location
                dst_path = (config_dir / dst_path).resolve()

            return dst_path / project_name

        # Fallback: current directory
        return Path("./data") / project_name

    def download(self) -> str:
        """
        Execute the download with caching and decompression.

        Returns
        -------
        str
            Path to downloaded dataset

        Raises
        ------
        ValueError
            If no provider can handle the source
        Exception
            If download fails
        """
        self.logger.debug(f"Destination: {self.destination}")

        # Check cache
        if self.cache_manager.is_cached(self.config):
            console.print(f"  [green]✓[/green] Using cached data")
            return str(self.destination)

        # Ensure destination exists
        self.destination.mkdir(parents=True, exist_ok=True)

        # Get appropriate provider
        source = self.config.get("src", "")
        if not source:
            raise ValueError("Configuration missing 'src' field")

        try:
            provider = registry.get_provider(
                source,
                self.config,
                self.destination
            )
        except ValueError as e:
            self.logger.error(f"No provider found: {e}")
            raise

        # Download
        self.logger.debug(f"Using {provider.provider_name} provider")
        try:
            downloaded_path = provider.download()
            self.logger.debug(f"Download completed: {downloaded_path}")
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            raise

        # Decompress archives
        try:
            decompressed = self.decompressor.decompress_all()
            if decompressed:
                self.logger.debug(
                    f"Decompressed {len(decompressed)} archive(s)"
                )
        except Exception as e:
            self.logger.warning(f"Decompression warning: {e}")
            # Don't fail the download if decompression fails

        # Save cache
        try:
            cache_path = self.cache_manager.save_cache(self.config)
            console.print(f"  [green]✓[/green] Cache saved")
        except Exception as e:
            self.logger.warning(f"Failed to save cache: {e}")
            # Don't fail the download if cache save fails

        return str(self.destination)

    def get_provider_name(self) -> str:
        """
        Get the name of the provider that would handle this download.

        Returns
        -------
        str
            Provider name

        Raises
        ------
        ValueError
            If no provider can handle the source
        """
        source = self.config.get("src", "")
        provider = registry.get_provider(
            source,
            self.config,
            self.destination
        )
        return provider.provider_name

    def is_cached(self) -> bool:
        """
        Check if this download is cached.

        Returns
        -------
        bool
            True if cached
        """
        return self.cache_manager.is_cached(self.config)

    def invalidate_cache(self) -> None:
        """Invalidate cache to force re-download."""
        self.cache_manager.invalidate_cache()

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"DatasetDownloader("
            f"project={self.config.get('projectName', 'unknown')}, "
            f"destination={self.destination})"
        )
