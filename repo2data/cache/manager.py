"""Cache management for downloaded datasets."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging
import os

from repo2data.cache.global_cache import GlobalCacheManager

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages download caching with content-based validation.

    Now uses the global cache system by default, with optional fallback
    to local cache for backward compatibility.

    Uses hash-based caching to determine if data needs to be re-downloaded.
    Only critical fields (src, projectName, version) affect cache validation.
    """

    CACHE_FILENAME = "repo2data_cache.json"
    CRITICAL_FIELDS = ["src", "projectName", "version"]

    def __init__(
        self,
        cache_dir: Path,
        download_key: Optional[str] = None,
        use_global_cache: bool = True
    ):
        """
        Initialize CacheManager.

        Parameters
        ----------
        cache_dir : pathlib.Path
            Directory where data is stored (used as destination)
        download_key : str, optional
            Key for multi-download configurations
        use_global_cache : bool
            If True, use global cache system (default: True)
            Can be disabled via REPO2DATA_USE_LOCAL_CACHE env var
        """
        self.cache_dir = Path(cache_dir)
        self.download_key = download_key

        # Check environment variable to override global cache
        use_local = os.environ.get('REPO2DATA_USE_LOCAL_CACHE', '').lower() in ('1', 'true', 'yes')
        self.use_global_cache = use_global_cache and not use_local

        # Initialize global cache manager if enabled
        if self.use_global_cache:
            self.global_cache = GlobalCacheManager()
        else:
            self.global_cache = None

        # Keep local cache file path for backward compatibility
        if download_key:
            self.cache_filename = f"{download_key}_{self.CACHE_FILENAME}"
        else:
            self.cache_filename = self.CACHE_FILENAME

        self.cache_file = self.cache_dir / self.cache_filename
        self.logger = logger

    def compute_cache_key(self, config: Dict[str, Any]) -> str:
        """
        Compute hash from critical configuration fields.

        Only fields that affect the actual data content are included
        in the hash. This allows cosmetic config changes without
        invalidating the cache.

        Parameters
        ----------
        config : dict
            Configuration dictionary

        Returns
        -------
        str
            SHA256 hash of critical fields
        """
        # Extract only critical fields
        critical_config = {}
        for field in self.CRITICAL_FIELDS:
            if field in config:
                critical_config[field] = config[field]

        # Create deterministic JSON string
        config_str = json.dumps(critical_config, sort_keys=True)

        # Compute hash
        hash_obj = hashlib.sha256(config_str.encode('utf-8'))
        cache_key = hash_obj.hexdigest()

        self.logger.debug(f"Computed cache key: {cache_key[:16]}...")
        return cache_key

    def is_cached(self, config: Dict[str, Any]) -> bool:
        """
        Check if data is already cached.

        Parameters
        ----------
        config : dict
            Current configuration

        Returns
        -------
        bool
            True if cached and valid
        """
        # Use global cache if enabled
        if self.use_global_cache and self.global_cache:
            return self.global_cache.is_cached(
                config,
                self.cache_dir,
                self.download_key
            )

        # Fall back to local cache
        if not self.cache_file.exists():
            self.logger.debug("No cache file found")
            return False

        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)

            # Compare cache keys
            current_key = self.compute_cache_key(config)
            cached_key = cached_data.get("cache_key")

            if current_key == cached_key:
                cached_time = cached_data.get("timestamp", "unknown")
                self.logger.info(
                    f"Cache hit! Data cached at {cached_time}"
                )
                return True
            else:
                self.logger.debug(
                    "Cache key mismatch - data needs to be re-downloaded"
                )
                return False

        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"Invalid cache file: {e}")
            return False

    def save_cache(
        self,
        config: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Save cache record with metadata.

        Parameters
        ----------
        config : dict
            Configuration that was used for download
        metadata : dict, optional
            Additional metadata to store (e.g., file sizes, checksums)
        """
        # Use global cache if enabled
        if self.use_global_cache and self.global_cache:
            self.global_cache.save_cache(
                config,
                self.cache_dir,
                self.download_key,
                metadata
            )
            return

        # Fall back to local cache
        cache_key = self.compute_cache_key(config)

        cache_data = {
            "cache_key": cache_key,
            "config": config,
            "timestamp": datetime.now().isoformat(),
            "cache_version": "2.0",  # For future compatibility
            "metadata": metadata or {}
        }

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Write cache file
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2)

        self.logger.info(f"Cache saved to {self.cache_file}")

    def invalidate_cache(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Delete cache to force re-download.

        Parameters
        ----------
        config : dict, optional
            Configuration to invalidate (required for global cache)
        """
        # Use global cache if enabled
        if self.use_global_cache and self.global_cache and config:
            self.global_cache.invalidate_cache(config)
            return

        # Fall back to local cache
        if self.cache_file.exists():
            self.cache_file.unlink()
            self.logger.info(f"Cache invalidated: {self.cache_file}")
        else:
            self.logger.warning("No cache file to invalidate")

    def get_cache_info(self, config: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Get cached information without validation.

        Parameters
        ----------
        config : dict, optional
            Configuration to look up (required for global cache)

        Returns
        -------
        dict or None
            Cached data if available, None otherwise
        """
        # Use global cache if enabled
        if self.use_global_cache and self.global_cache and config:
            return self.global_cache.get_cache_info(config)

        # Fall back to local cache
        if not self.cache_file.exists():
            return None

        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Error reading cache: {e}")
            return None

    def __repr__(self) -> str:
        """String representation of CacheManager."""
        status = "exists" if self.cache_file.exists() else "not found"
        return (
            f"CacheManager("
            f"cache_dir={self.cache_dir}, "
            f"cache_file={self.cache_filename}, "
            f"status={status})"
        )
