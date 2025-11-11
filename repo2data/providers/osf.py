"""OSF (Open Science Framework) provider for downloading datasets."""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Any, List

from repo2data.providers.base import BaseProvider


class OSFProvider(BaseProvider):
    """
    Provider for Open Science Framework (OSF) downloads.

    Uses osfclient to download files from OSF projects.
    """

    def can_handle(self, source: str) -> bool:
        """
        Check if source is an OSF URL.

        Parameters
        ----------
        source : str
            Source URL

        Returns
        -------
        bool
            True if source is an OSF URL
        """
        return bool(re.match(r".*?(https://osf\.io).*", source))

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "OSF"

    def download(self) -> Path:
        """
        Download files from OSF project.

        Returns
        -------
        pathlib.Path
            Path to downloaded data

        Raises
        ------
        FileNotFoundError
            If osfclient is not installed
        ValueError
            If project ID cannot be extracted
        Exception
            If download fails
        """
        self._ensure_destination_exists()

        self.logger.info(f"Downloading from OSF: {self.source}")

        # Check if osf CLI is available
        try:
            subprocess.run(
                ['osf', '--version'],
                capture_output=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise FileNotFoundError(
                "osfclient is not installed. "
                "Install with: pip install osfclient"
            )

        # Extract project ID from URL
        match = re.match(r"https://osf\.io/(.{5})", self.source)
        if not match:
            raise ValueError(
                f"Cannot extract OSF project ID from URL: {self.source}"
            )

        project_id = match.group(1)
        self.logger.debug(f"OSF project ID: {project_id}")

        # Check if specific files are requested
        remote_filepaths = self.config.get("remote_filepath")

        try:
            if not remote_filepaths:
                # Clone entire project
                result = subprocess.run(
                    [
                        'osf',
                        '--project', project_id,
                        'clone',
                        str(self.destination)
                    ],
                    capture_output=True,
                    text=True,
                    check=False
                )
            else:
                # Download specific files
                if not isinstance(remote_filepaths, list):
                    remote_filepaths = [remote_filepaths]

                result = None
                for remote_filepath in remote_filepaths:
                    self.logger.info(f"Fetching file: {remote_filepath}")

                    local_path = self.destination / remote_filepath
                    local_path.parent.mkdir(parents=True, exist_ok=True)

                    result = subprocess.run(
                        [
                            'osf',
                            '--project', project_id,
                            'fetch',
                            '-f', remote_filepath,
                            str(local_path)
                        ],
                        capture_output=True,
                        text=True,
                        check=False
                    )

                    if result.returncode != 0:
                        self.logger.error(f"osf stderr: {result.stderr}")
                        raise Exception(
                            f"OSF fetch failed for {remote_filepath}"
                        )

            if result and result.returncode != 0:
                self.logger.error(f"osf stderr: {result.stderr}")
                raise Exception(
                    f"OSF command failed with return code {result.returncode}"
                )

            self.logger.info(
                f"Successfully downloaded from OSF to {self.destination}"
            )
            return self.destination

        except Exception as e:
            self.logger.error(f"OSF download failed: {e}")
            raise
