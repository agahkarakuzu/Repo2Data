"""Google Drive provider for downloading files."""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Any

from repo2data.providers.base import BaseProvider


class GoogleDriveProvider(BaseProvider):
    """
    Provider for Google Drive downloads.

    Uses gdown utility to download files from Google Drive.
    """

    def can_handle(self, source: str) -> bool:
        """
        Check if source is a Google Drive URL.

        Parameters
        ----------
        source : str
            Source URL

        Returns
        -------
        bool
            True if source is a Google Drive URL
        """
        return bool(re.match(r".*?(drive\.google\.com).*", source))

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "Google Drive"

    def download(self) -> Path:
        """
        Download file from Google Drive.

        Returns
        -------
        pathlib.Path
            Path to destination directory

        Raises
        ------
        FileNotFoundError
            If gdown is not installed
        Exception
            If download fails
        """
        self._ensure_destination_exists()

        self.logger.info(
            f"Downloading from Google Drive: {self.source}"
        )

        # Check if gdown is available
        try:
            subprocess.run(
                ['gdown', '--version'],
                capture_output=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise FileNotFoundError(
                "gdown is not installed. Install with: pip install gdown"
            )

        # gdown doesn't support output directory, so we need to change cwd
        original_cwd = os.getcwd()

        try:
            os.chdir(self.destination)

            # Run gdown
            result = subprocess.run(
                ['gdown', self.source],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                self.logger.error(f"gdown stderr: {result.stderr}")
                raise Exception(
                    f"gdown failed with return code {result.returncode}"
                )

            self.logger.info(f"Successfully downloaded to {self.destination}")
            return self.destination

        finally:
            os.chdir(original_cwd)
