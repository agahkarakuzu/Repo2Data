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

Usage:
    from repo2data import DatasetManager
    manager = DatasetManager("data_requirement.json")
    paths = manager.install()
"""

__version__ = "2.9.1"

# New API (recommended)
from repo2data.manager import DatasetManager
from repo2data.downloader import DatasetDownloader
from repo2data.config.loader import ConfigLoader
from repo2data.config.validator import ConfigValidator
from repo2data.cache.manager import CacheManager
from repo2data.cache.global_cache import GlobalCacheManager, get_cache_dir
from repo2data.cache.migration import CacheMigrator
from repo2data.utils.logger import setup_logger, get_logger
from repo2data.utils.locator import locate_evidence_data, list_evidence_datasets

__all__ = [
    # Version
    '__version__',

    # New API (recommended)
    'DatasetManager',
    'DatasetDownloader',
    'ConfigLoader',
    'ConfigValidator',
    'CacheManager',
    'GlobalCacheManager',
    'CacheMigrator',
    'get_cache_dir',
    'setup_logger',
    'get_logger',
    'locate_evidence_data',
    'list_evidence_datasets',
]
