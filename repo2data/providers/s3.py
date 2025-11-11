"""AWS S3 provider for downloading datasets."""

import re
import subprocess
from pathlib import Path
from typing import Dict, Any

from repo2data.providers.base import BaseProvider


class S3Provider(BaseProvider):
    """
    Provider for AWS S3 downloads.

    Uses AWS CLI to sync S3 buckets/paths.
    """

    def can_handle(self, source: str) -> bool:
        """
        Check if source is an S3 URL.

        Parameters
        ----------
        source : str
            Source URL

        Returns
        -------
        bool
            True if source starts with s3://
        """
        return bool(re.match(r".*?(s3://).*", source))

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "AWS S3"

    def download(self) -> Path:
        """
        Download data from S3 bucket.

        Returns
        -------
        pathlib.Path
            Path to downloaded data

        Raises
        ------
        FileNotFoundError
            If AWS CLI is not installed
        Exception
            If download fails
        """
        self._ensure_destination_exists()

        self.logger.info(f"Downloading from S3: {self.source}")

        # Check if AWS CLI is available
        try:
            subprocess.run(
                ['aws', '--version'],
                capture_output=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise FileNotFoundError(
                "AWS CLI is not installed. "
                "Install with: pip install awscli"
            )

        # Run aws s3 sync with no-sign-request for public buckets
        try:
            result = subprocess.run(
                [
                    'aws', 's3', 'sync',
                    '--no-sign-request',
                    self.source,
                    str(self.destination)
                ],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                self.logger.error(f"AWS CLI stderr: {result.stderr}")
                raise Exception(
                    f"AWS S3 sync failed with return code {result.returncode}"
                )

            self.logger.info(
                f"Successfully downloaded from S3 to {self.destination}"
            )
            return self.destination

        except Exception as e:
            self.logger.error(f"S3 download failed: {e}")
            raise
