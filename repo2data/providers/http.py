"""HTTP/HTTPS provider for downloading files."""

import re
import time
from pathlib import Path
from typing import Dict, Any
import requests

from repo2data.providers.base import BaseProvider


class HTTPProvider(BaseProvider):
    """
    Provider for HTTP/HTTPS downloads.

    Downloads files from generic HTTP/HTTPS URLs using the requests library.
    """

    def __init__(self, config: Dict[str, Any], destination: Path):
        """
        Initialize HTTP provider.

        Parameters
        ----------
        config : dict
            Configuration containing 'src' URL
        destination : pathlib.Path
            Destination directory
        """
        super().__init__(config, destination)
        self.max_retries = 3
        self.retry_delay = 5  # seconds

    def can_handle(self, source: str) -> bool:
        """
        Check if source is an HTTP/HTTPS URL.

        Excludes specialized providers (git, Google Drive, OSF).

        Parameters
        ----------
        source : str
            Source URL

        Returns
        -------
        bool
            True if this is a generic HTTP/HTTPS URL
        """
        # Check for HTTP/HTTPS
        is_http = bool(
            re.match(r".*?(https?://).*", source)
        )

        if not is_http:
            return False

        # Exclude specialized providers
        is_git = bool(re.match(r".*?\.git$", source))
        is_gdrive = bool(re.match(r".*?(drive\.google\.com).*", source))
        is_osf = bool(re.match(r".*?(https://osf\.io).*", source))

        return not (is_git or is_gdrive or is_osf)

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "HTTP"

    def download(self) -> Path:
        """
        Download file from HTTP/HTTPS URL.

        Returns
        -------
        pathlib.Path
            Path to downloaded file

        Raises
        ------
        Exception
            If download fails after all retries
        """
        self._ensure_destination_exists()

        url = self.source
        self.logger.info(f"Downloading from {url}")

        for retry in range(self.max_retries):
            try:
                response = requests.get(url, stream=True, timeout=30)

                if response.status_code == 200:
                    # Get filename from URL
                    filename = self._extract_filename(url, response)
                    filepath = self.destination / filename

                    # Download the file
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0

                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)

                    if total_size > 0:
                        self.logger.info(
                            f"Downloaded {downloaded / (1024*1024):.2f} MB "
                            f"to {filepath}"
                        )
                    else:
                        self.logger.info(f"Downloaded to {filepath}")

                    return filepath

                else:
                    self.logger.warning(
                        f"Attempt {retry + 1}/{self.max_retries} - "
                        f"Status code: {response.status_code}"
                    )

            except requests.RequestException as e:
                self.logger.warning(
                    f"Attempt {retry + 1}/{self.max_retries} - "
                    f"Error: {e}"
                )

            # Retry with delay
            if retry < self.max_retries - 1:
                self.logger.info(f"Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)

        raise Exception(
            f"Failed to download {url} after {self.max_retries} attempts"
        )

    def _extract_filename(
        self,
        url: str,
        response: requests.Response
    ) -> str:
        """
        Extract filename from URL or response headers.

        Parameters
        ----------
        url : str
            Download URL
        response : requests.Response
            HTTP response object

        Returns
        -------
        str
            Extracted filename
        """
        # Try to get from Content-Disposition header
        if 'Content-Disposition' in response.headers:
            import re
            match = re.search(
                r'filename="?([^"]+)"?',
                response.headers['Content-Disposition']
            )
            if match:
                return match.group(1)

        # Fall back to URL
        filename = url.split('/')[-1].split('?')[0]

        # If no filename in URL, use a default
        if not filename or '.' not in filename:
            # Try to guess extension from content-type
            content_type = response.headers.get('Content-Type', '')
            ext_map = {
                'application/zip': '.zip',
                'application/x-tar': '.tar',
                'application/gzip': '.tar.gz',
                'application/x-gzip': '.tar.gz',
            }
            ext = ext_map.get(content_type, '.bin')
            filename = f"download{ext}"

        return filename
