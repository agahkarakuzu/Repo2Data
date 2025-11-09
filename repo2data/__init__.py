"""
Repo2Data - Automated data fetching from various sources with caching.

Supports downloading from:
- HTTP/HTTPS URLs
- Google Drive
- AWS S3
- Datalad/git-annex
- Zenodo
- OSF (Open Science Framework)
- Python library datasets

New API (recommended):
    from repo2data import DatasetManager
    manager = DatasetManager("data_requirement.json")
    paths = manager.install()

Legacy API (deprecated):
    from repo2data import Repo2Data
    repo2data = Repo2Data("data_requirement.json")
    paths = repo2data.install()
"""

__version__ = "2.9.1"

# New API (recommended)
from repo2data.manager import DatasetManager
from repo2data.downloader import DatasetDownloader
from repo2data.config.loader import ConfigLoader
from repo2data.config.validator import ConfigValidator
from repo2data.cache.manager import CacheManager
from repo2data.utils.logger import setup_logger, get_logger

# Legacy API (deprecated, for backwards compatibility)
from repo2data.repo2data import Repo2Data, Repo2DataChild

__all__ = [
    # Version
    '__version__',

    # New API (recommended)
    'DatasetManager',
    'DatasetDownloader',
    'ConfigLoader',
    'ConfigValidator',
    'CacheManager',
    'setup_logger',
    'get_logger',

    # Legacy API (deprecated)
    'Repo2Data',
    'Repo2DataChild',
]
