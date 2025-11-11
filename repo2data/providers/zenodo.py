"""Zenodo provider for downloading datasets via DOI."""

import re
import subprocess
from pathlib import Path
from typing import Dict, Any

from repo2data.providers.base import BaseProvider


class ZenodoProvider(BaseProvider):
    """
    Provider for Zenodo downloads.

    Uses zenodo_get to download datasets by DOI.
    """

    def can_handle(self, source: str) -> bool:
        """
        Check if source is a Zenodo DOI.

        Parameters
        ----------
        source : str
            Source DOI or URL

        Returns
        -------
        bool
            True if source matches Zenodo DOI pattern
        """
        return bool(re.match(r".*?(10\.\d{4}/zenodo).*", source))

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "Zenodo"

    def download(self) -> Path:
        """
        Download dataset from Zenodo.

        Returns
        -------
        pathlib.Path
            Path to downloaded data

        Raises
        ------
        FileNotFoundError
            If zenodo_get is not installed
        Exception
            If download fails
        """
        self._ensure_destination_exists()

        self.logger.info(f"Downloading from Zenodo: {self.source}")

        # Check if zenodo_get is available
        try:
            subprocess.run(
                ['zenodo_get', '--version'],
                capture_output=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise FileNotFoundError(
                "zenodo_get is not installed. "
                "Install with: pip install zenodo-get"
            )

        # Run zenodo_get
        try:
            result = subprocess.run(
                [
                    'zenodo_get',
                    '-o', str(self.destination),
                    self.source
                ],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                self.logger.error(f"zenodo_get stderr: {result.stderr}")
                raise Exception(
                    f"zenodo_get failed with return code {result.returncode}"
                )

            self.logger.info(
                f"Successfully downloaded from Zenodo to {self.destination}"
            )
            return self.destination

        except Exception as e:
            self.logger.error(f"Zenodo download failed: {e}")
            raise
