#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backwards compatibility layer for Repo2Data.

This module provides the legacy Repo2Data and Repo2DataChild classes
that wrap the new DatasetManager and DatasetDownloader classes.

DEPRECATED: Use DatasetManager and DatasetDownloader directly.
These classes are provided for backwards compatibility only.

Created on Fri Dec 21 11:55:12 2018
@author: ltetrel

Refactored: Major architectural improvements
"""

import warnings
from typing import Optional, Dict, Any, List

# Import new architecture
from repo2data.manager import DatasetManager
from repo2data.downloader import DatasetDownloader


class Repo2Data:
    """
    DEPRECATED: Use DatasetManager instead.

    Backwards compatibility wrapper for the legacy Repo2Data class.
    Delegates to DatasetManager for actual functionality.
    """

    def __init__(
        self,
        data_requirement: Optional[str] = None,
        server: bool = False
    ):
        """
        Initialize the Repo2Data class.

        DEPRECATED: Use DatasetManager instead.

        Parameters
        ----------
        data_requirement : str, optional
            Path to the data requirement file or GitHub repository
        server : bool
            Whether to force output directory (default: False)
        """
        warnings.warn(
            "Repo2Data class is deprecated. Use DatasetManager instead. "
            "The old API will be removed in a future version.",
            DeprecationWarning,
            stacklevel=2
        )

        # Initialize internal state for compatibility
        self._data_requirement_path = data_requirement
        self._use_server = server
        self._server_dst_folder = "./data"

        # Create new DatasetManager instance
        self._manager = DatasetManager(
            requirement_path=data_requirement,
            server_mode=server,
            server_destination=self._server_dst_folder
        )

        # Load requirements to populate _data_requirement_file
        try:
            self._data_requirement_file = self._manager.load_requirements()
        except Exception:
            # If loading fails, let it fail during install()
            self._data_requirement_file = None

    def set_server_dst_folder(self, directory: str) -> None:
        """
        Set the server destination folder.

        Parameters
        ----------
        directory : str
            Destination directory path
        """
        self._server_dst_folder = directory
        self._manager.server_destination = directory

    def load_data_requirement(self, data_requirement: Optional[str]) -> None:
        """
        Load data requirement file.

        Parameters
        ----------
        data_requirement : str, optional
            Path to requirement file or GitHub URL
        """
        if data_requirement is not None:
            self._data_requirement_path = data_requirement
            self._manager = DatasetManager(
                requirement_path=data_requirement,
                server_mode=self._use_server,
                server_destination=self._server_dst_folder
            )
            try:
                self._data_requirement_file = self._manager.load_requirements()
            except Exception:
                self._data_requirement_file = None

    def install(self) -> List[str]:
        """
        Install the dataset(s) by launching child process(es).

        Returns
        -------
        list of str
            List of path(s) to the installed data directory(ies)
        """
        return self._manager.install()


class Repo2DataChild:
    """
    DEPRECATED: Use DatasetDownloader instead.

    Backwards compatibility wrapper for the legacy Repo2DataChild class.
    Delegates to DatasetDownloader for actual functionality.
    """

    def __init__(
        self,
        data_requirement_file: Optional[Dict[str, Any]] = None,
        use_server: bool = False,
        data_requirement_path: Optional[str] = None,
        download_key: Optional[str] = None,
        server_dst_folder: Optional[str] = None
    ):
        """
        Initialize the Repo2DataChild class.

        DEPRECATED: Use DatasetDownloader instead.

        Parameters
        ----------
        data_requirement_file : dict, optional
            Un-nested requirement in dict format
        use_server : bool
            Whether to force output directory (default: False)
        data_requirement_path : str, optional
            Path to the requirement file
        download_key : str, optional
            Download key for multi-download configs
        server_dst_folder : str, optional
            Server destination folder
        """
        warnings.warn(
            "Repo2DataChild class is deprecated. "
            "Use DatasetDownloader instead. "
            "The old API will be removed in a future version.",
            DeprecationWarning,
            stacklevel=2
        )

        # Store parameters for compatibility
        self._data_requirement_file = data_requirement_file or {}
        self._use_server = use_server
        self._data_requirement_path = data_requirement_path
        self._download_key = download_key
        self._server_dst_folder = server_dst_folder or "./data"

        # Create new DatasetDownloader instance
        if data_requirement_file:
            self._downloader = DatasetDownloader(
                config=data_requirement_file,
                server_mode=use_server,
                server_destination=self._server_dst_folder,
                requirement_path=data_requirement_path,
                download_key=download_key
            )
            self._dst_path = str(self._downloader.destination)
        else:
            self._downloader = None
            self._dst_path = None

        # Cache record name for compatibility
        if download_key:
            self._cache_record = f"{download_key}_repo2data_cache_record.json"
        else:
            self._cache_record = "repo2data_cache_record.json"

    def load_data_requirement(self, data_requirement_file: Dict[str, Any]) -> None:
        """
        Load the dict data requirement file.

        Parameters
        ----------
        data_requirement_file : dict
            Requirement configuration
        """
        if data_requirement_file:
            self._data_requirement_file = data_requirement_file
            self._downloader = DatasetDownloader(
                config=data_requirement_file,
                server_mode=self._use_server,
                server_destination=self._server_dst_folder,
                requirement_path=self._data_requirement_path,
                download_key=self._download_key
            )
            self._dst_path = str(self._downloader.destination)

    def install(self) -> str:
        """
        Install the dataset.

        Returns
        -------
        str
            Path to the installed data directory
        """
        if self._downloader is None:
            raise ValueError("No data requirement loaded")

        return self._downloader.download()


# For backwards compatibility, keep these at module level
__all__ = ['Repo2Data', 'Repo2DataChild']
