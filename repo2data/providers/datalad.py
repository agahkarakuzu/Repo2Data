"""Datalad provider for git-annex datasets."""

import re
import subprocess
from pathlib import Path
from typing import Dict, Any

from repo2data.providers.base import BaseProvider


class DataladProvider(BaseProvider):
    """
    Provider for Datalad/git-annex datasets.

    Uses datalad to clone and install git-annex repositories.
    """

    def can_handle(self, source: str) -> bool:
        """
        Check if source is a git repository URL.

        Parameters
        ----------
        source : str
            Source URL

        Returns
        -------
        bool
            True if source ends with .git
        """
        return bool(re.match(r".*?\.git$", source))

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "Datalad"

    def download(self) -> Path:
        """
        Clone and install Datalad dataset.

        Returns
        -------
        pathlib.Path
            Path to installed dataset

        Raises
        ------
        FileNotFoundError
            If datalad is not installed
        Exception
            If installation fails
        """
        self.logger.info(f"Installing Datalad dataset: {self.source}")

        # Check if datalad is available
        try:
            subprocess.run(
                ['datalad', '--version'],
                capture_output=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise FileNotFoundError(
                "datalad is not installed. "
                "Install instructions: https://www.datalad.org/get_datalad.html"
            )

        # Run datalad install
        try:
            result = subprocess.run(
                [
                    'datalad', 'install',
                    str(self.destination),
                    '-s', self.source
                ],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                self.logger.error(f"datalad stderr: {result.stderr}")
                raise Exception(
                    f"datalad install failed with return code "
                    f"{result.returncode}"
                )

            self.logger.info(
                f"Successfully installed Datalad dataset to {self.destination}"
            )
            return self.destination

        except Exception as e:
            self.logger.error(f"Datalad installation failed: {e}")
            raise
