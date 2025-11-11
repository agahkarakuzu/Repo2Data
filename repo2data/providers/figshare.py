"""Figshare provider for downloading datasets via DOI or article ID."""

import re
import json
from pathlib import Path
from typing import Dict, Any
from urllib.parse import urlparse
import requests

from repo2data.providers.base import BaseProvider
from repo2data.utils.download import download_with_progress, check_disk_space
from repo2data.utils.logger import console


class FigshareProvider(BaseProvider):
    """
    Provider for Figshare downloads.

    Supports:
    - Figshare DOIs: doi:10.6084/m9.figshare.XXXXXX
    - Figshare URLs: https://figshare.com/articles/...
    - Direct article IDs: figshare://XXXXXX

    Uses the Figshare API v2 to fetch metadata and download files.
    """

    FIGSHARE_API_BASE = "https://api.figshare.com/v2"

    def can_handle(self, source: str) -> bool:
        """
        Check if source is a Figshare DOI, URL, or article ID.

        Parameters
        ----------
        source : str
            Source DOI, URL, or article ID

        Returns
        -------
        bool
            True if source matches Figshare pattern
        """
        # Check for Figshare DOI
        if re.search(r"10\.6084/m9\.figshare\.\d+", source):
            return True

        # Check for Figshare URL
        if "figshare.com" in source.lower():
            return True

        # Check for figshare:// protocol
        if source.startswith("figshare://"):
            return True

        return False

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "Figshare"

    def _extract_article_id(self, source: str) -> str:
        """
        Extract Figshare article ID from various source formats.

        Parameters
        ----------
        source : str
            Source string (DOI, URL, or article ID)

        Returns
        -------
        str
            Article ID

        Raises
        ------
        ValueError
            If article ID cannot be extracted
        """
        # Extract from DOI
        doi_match = re.search(r"10\.6084/m9\.figshare\.(\d+)", source)
        if doi_match:
            return doi_match.group(1)

        # Extract from URL - handles various URL formats
        # Examples:
        # - https://figshare.com/articles/dataset/Title/7778845
        # - https://figshare.com/articles/Title/7778845
        # Match the last numeric segment in the path
        url_match = re.search(r"figshare\.com/articles/.*/(\d+)", source)
        if url_match:
            return url_match.group(1)

        # Extract from figshare:// protocol
        if source.startswith("figshare://"):
            return source.replace("figshare://", "")

        # Try as direct article ID
        if source.isdigit():
            return source

        raise ValueError(f"Could not extract Figshare article ID from: {source}")

    def _get_article_metadata(self, article_id: str) -> Dict[str, Any]:
        """
        Fetch article metadata from Figshare API.

        Parameters
        ----------
        article_id : str
            Figshare article ID

        Returns
        -------
        dict
            Article metadata

        Raises
        ------
        Exception
            If API request fails
        """
        url = f"{self.FIGSHARE_API_BASE}/articles/{article_id}"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch Figshare metadata: {e}")

    def download(self) -> Path:
        """
        Download dataset from Figshare.

        Returns
        -------
        pathlib.Path
            Path to downloaded data

        Raises
        ------
        Exception
            If download fails
        """
        self._ensure_destination_exists()

        # Extract article ID
        try:
            article_id = self._extract_article_id(self.source)
        except ValueError as e:
            raise ValueError(f"Invalid Figshare source: {e}")

        self.logger.info(f"Fetching Figshare article {article_id}")

        # Get article metadata
        metadata = self._get_article_metadata(article_id)

        title = metadata.get("title", "Unknown")
        files = metadata.get("files", [])

        if not files:
            raise ValueError(f"No files found in Figshare article {article_id}")

        console.print(f"  [cyan]Figshare:[/cyan] {title}")
        console.print(f"  [dim]Files: {len(files)}[/dim]")

        # Download all files
        for idx, file_info in enumerate(files, 1):
            file_name = file_info.get("name", f"file_{idx}")
            file_url = file_info.get("download_url")
            file_size = file_info.get("size", 0)

            if not file_url:
                self.logger.warning(f"No download URL for file: {file_name}")
                continue

            file_path = self.destination / file_name

            console.print(f"  [cyan]({idx}/{len(files)})[/cyan] {file_name}")

            # Check disk space
            if file_size > 0:
                try:
                    check_disk_space(self.destination, file_size)
                except OSError as e:
                    raise OSError(f"Insufficient disk space for {file_name}: {e}")

            # Download file
            try:
                response = requests.get(file_url, stream=True, timeout=60)
                response.raise_for_status()

                # Get actual size from headers if not in metadata
                total_size = file_size
                if not total_size:
                    total_size = int(response.headers.get('content-length', 0))

                # Download with progress
                with open(file_path, 'wb') as f:
                    downloaded = download_with_progress(
                        response.iter_content,
                        f,
                        total_size=total_size if total_size > 0 else None,
                        description=f"  Downloading {file_name}"
                    )

                console.print(f"  [green]✓[/green] Downloaded {file_name}")

            except requests.RequestException as e:
                raise Exception(f"Failed to download {file_name}: {e}")

        self.logger.info(f"Successfully downloaded {len(files)} file(s) from Figshare")
        return self.destination
