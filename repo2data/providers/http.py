"""HTTP/HTTPS provider for downloading files."""

import re
import time
from pathlib import Path
from typing import Dict, Any, Optional
import requests

from repo2data.providers.base import BaseProvider
from repo2data.utils.download import (
    download_with_progress,
    check_disk_space,
    verify_checksum,
    compute_checksum
)
from repo2data.utils.logger import console


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
        Download file from HTTP/HTTPS URL with progress tracking and verification.

        Returns
        -------
        pathlib.Path
            Path to downloaded file

        Raises
        ------
        Exception
            If download fails after all retries
        OSError
            If insufficient disk space
        ValueError
            If checksum verification fails
        """
        self._ensure_destination_exists()

        url = self.source
        self.logger.debug(f"Downloading from {url}")

        # Get checksum from config if provided
        expected_checksum = self.config.get("checksum")
        checksum_algorithm = self.config.get("checksum_algorithm", "sha256")

        for retry in range(self.max_retries):
            try:
                response = requests.get(url, stream=True, timeout=30)

                if response.status_code == 200:
                    # Get filename and file size
                    filename = self._extract_filename(url, response)
                    filepath = self.destination / filename
                    tmp_filepath = filepath.with_suffix(filepath.suffix + '.tmp')

                    total_size = int(response.headers.get('content-length', 0))

                    # Check disk space before downloading
                    if total_size > 0:
                        try:
                            check_disk_space(self.destination, total_size)
                        except OSError as e:
                            console.print(f"  [red]✗[/red] {str(e)}")
                            raise

                    # Download with progress bar
                    try:
                        with open(tmp_filepath, 'wb') as f:
                            downloaded = download_with_progress(
                                response.iter_content,
                                f,
                                total_size=total_size if total_size > 0 else None,
                                description=f"  Downloading {filename}"
                            )

                        # Verify checksum if provided
                        if expected_checksum:
                            console.print(f"  [cyan]Verifying checksum ({checksum_algorithm})...[/cyan]")
                            try:
                                verify_checksum(tmp_filepath, expected_checksum, checksum_algorithm)
                                console.print(f"  [green]✓[/green] Checksum verified")
                            except ValueError as e:
                                # Clean up failed download
                                tmp_filepath.unlink(missing_ok=True)
                                raise

                        # Atomic move: tmp -> final
                        tmp_filepath.rename(filepath)

                        self.logger.debug(f"Downloaded to {filepath}")
                        return filepath

                    except Exception as e:
                        # Clean up temp file on any error
                        tmp_filepath.unlink(missing_ok=True)
                        raise

                elif response.status_code == 404:
                    raise Exception(
                        f"File not found (404): {url}\n"
                        f"Please check the URL is correct."
                    )
                elif response.status_code == 403:
                    raise Exception(
                        f"Access forbidden (403): {url}\n"
                        f"You may not have permission to access this resource."
                    )
                else:
                    self.logger.warning(
                        f"Attempt {retry + 1}/{self.max_retries} - "
                        f"HTTP {response.status_code}: {response.reason}"
                    )

            except requests.Timeout:
                self.logger.warning(
                    f"Attempt {retry + 1}/{self.max_retries} - "
                    f"Timeout after 30 seconds"
                )
            except requests.ConnectionError as e:
                self.logger.warning(
                    f"Attempt {retry + 1}/{self.max_retries} - "
                    f"Connection error: {e}"
                )
            except requests.RequestException as e:
                self.logger.warning(
                    f"Attempt {retry + 1}/{self.max_retries} - "
                    f"Request error: {e}"
                )

            # Retry with exponential backoff
            if retry < self.max_retries - 1:
                delay = self.retry_delay * (2 ** retry)  # Exponential backoff
                self.logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)

        raise Exception(
            f"Failed to download from {url} after {self.max_retries} attempts.\n"
            f"Please check your internet connection and try again."
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
