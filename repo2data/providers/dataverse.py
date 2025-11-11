"""Dataverse provider for downloading datasets via DOI or dataset URL."""

import re
import json
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs
import requests

from repo2data.providers.base import BaseProvider
from repo2data.utils.download import download_with_progress, check_disk_space
from repo2data.utils.logger import console


class DataverseProvider(BaseProvider):
    """
    Provider for Dataverse downloads.

    Supports:
    - Dataverse DOIs: doi:10.7910/DVN/XXXXXX
    - Dataverse URLs: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:...
    - Direct dataset URLs with persistentId parameter
    - dataverse:// protocol with server and DOI

    Uses the Dataverse API to fetch metadata and download files.
    """

    # Common Dataverse installations
    KNOWN_DATAVERSE_HOSTS = [
        "dataverse.harvard.edu",
        "dataverse.nl",
        "data.aussda.at",
        "dataverse.no",
        "dataverse.unc.edu",
        "archive.data.jhu.edu",
        "dataverse.lib.umanitoba.ca",
    ]

    def can_handle(self, source: str) -> bool:
        """
        Check if source is a Dataverse URL or DOI.

        Parameters
        ----------
        source : str
            Source URL or DOI

        Returns
        -------
        bool
            True if source matches Dataverse pattern
        """
        # Check for dataverse:// protocol
        if source.startswith("dataverse://"):
            return True

        # Check for known Dataverse hosts in URL
        try:
            parsed = urlparse(source)
            if any(host in parsed.netloc for host in self.KNOWN_DATAVERSE_HOSTS):
                return True
        except:
            pass

        # Check for Dataverse DOI pattern (common pattern, not exhaustive)
        if re.search(r"10\.\d+/DVN/\w+", source):
            return True

        # Check for persistentId parameter in URL
        if "persistentId=" in source and "dataverse" in source.lower():
            return True

        return False

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "Dataverse"

    def _parse_source(self, source: str) -> tuple[str, str]:
        """
        Parse source to extract Dataverse server and persistent ID.

        Parameters
        ----------
        source : str
            Source string

        Returns
        -------
        tuple of (str, str)
            (server_url, persistent_id)

        Raises
        ------
        ValueError
            If source cannot be parsed
        """
        # Handle dataverse:// protocol
        # Format: dataverse://server.edu/doi:10.7910/DVN/XXXXXX
        if source.startswith("dataverse://"):
            parts = source.replace("dataverse://", "").split("/", 1)
            if len(parts) == 2:
                server = f"https://{parts[0]}"
                persistent_id = parts[1]
                return server, persistent_id

        # Check if it's a DOI (before trying to parse as URL)
        # This handles both "doi:10.XXX" and "10.XXX" formats
        doi_match = re.search(r"(?:doi:)?(10\.\d+/\S+)", source)
        if doi_match and not source.startswith("http"):
            doi = doi_match.group(1)
            if not doi.startswith("doi:"):
                doi = f"doi:{doi}"
            # Default to Harvard Dataverse
            return "https://dataverse.harvard.edu", doi

        # Handle full URLs
        try:
            parsed = urlparse(source)

            # Extract server
            server = f"{parsed.scheme}://{parsed.netloc}"

            # Extract persistent ID from query parameters
            if "persistentId=" in source:
                query_params = parse_qs(parsed.query)
                persistent_id = query_params.get("persistentId", [None])[0]
                if persistent_id:
                    return server, persistent_id

            # Try to extract DOI from path or query
            doi_match = re.search(r"(doi:10\.\d+/\S+)", source)
            if doi_match:
                persistent_id = doi_match.group(1)
                # If valid server found, return it
                if server and server != "://" and not server.startswith("doi://"):
                    return server, persistent_id

        except Exception as e:
            self.logger.debug(f"Failed to parse as URL: {e}")

        raise ValueError(f"Could not parse Dataverse source: {source}")

    def _get_dataset_metadata(self, server: str, persistent_id: str) -> Dict[str, Any]:
        """
        Fetch dataset metadata from Dataverse API.

        Parameters
        ----------
        server : str
            Dataverse server URL
        persistent_id : str
            Dataset persistent identifier (DOI)

        Returns
        -------
        dict
            Dataset metadata

        Raises
        ------
        Exception
            If API request fails
        """
        url = f"{server}/api/datasets/:persistentId"
        params = {"persistentId": persistent_id}

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(
                f"Failed to fetch Dataverse metadata from {server}: {e}\n"
                f"Make sure the DOI is correct and the server is accessible."
            )

    def download(self) -> Path:
        """
        Download dataset from Dataverse.

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

        # Parse source
        try:
            server, persistent_id = self._parse_source(self.source)
        except ValueError as e:
            raise ValueError(f"Invalid Dataverse source: {e}")

        self.logger.info(f"Fetching Dataverse dataset: {persistent_id} from {server}")

        # Get dataset metadata
        try:
            metadata = self._get_dataset_metadata(server, persistent_id)
        except Exception as e:
            raise Exception(f"Failed to access Dataverse: {e}")

        # Extract dataset information
        data = metadata.get("data", {})
        latest_version = data.get("latestVersion", {})
        title = latest_version.get("metadataBlocks", {}).get("citation", {}).get(
            "fields", []
        )

        # Try to get title from metadata
        dataset_title = "Unknown Dataset"
        for field in title if isinstance(title, list) else []:
            if field.get("typeName") == "title":
                dataset_title = field.get("value", "Unknown Dataset")
                break

        files = latest_version.get("files", [])

        if not files:
            raise ValueError(f"No files found in Dataverse dataset {persistent_id}")

        console.print(f"  [cyan]Dataverse:[/cyan] {dataset_title}")
        console.print(f"  [cyan]Server:[/cyan] {server}")
        console.print(f"  [dim]Files: {len(files)}[/dim]")

        # Download all files
        for idx, file_info in enumerate(files, 1):
            file_metadata = file_info.get("dataFile", {})
            file_name = file_metadata.get("filename", f"file_{idx}")
            file_id = file_metadata.get("id")
            file_size = file_metadata.get("filesize", 0)

            if not file_id:
                self.logger.warning(f"No file ID for: {file_name}")
                continue

            file_path = self.destination / file_name

            console.print(f"  [cyan]({idx}/{len(files)})[/cyan] {file_name}")

            # Check disk space
            if file_size > 0:
                try:
                    check_disk_space(self.destination, file_size)
                except OSError as e:
                    raise OSError(f"Insufficient disk space for {file_name}: {e}")

            # Download file using Dataverse API
            download_url = f"{server}/api/access/datafile/{file_id}"

            try:
                response = requests.get(download_url, stream=True, timeout=60)
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

        self.logger.info(
            f"Successfully downloaded {len(files)} file(s) from Dataverse"
        )
        return self.destination
