"""Cache migration utilities for moving from local to global cache."""

import json
from pathlib import Path
from typing import List, Tuple, Optional
import logging

from repo2data.cache.global_cache import GlobalCacheManager

logger = logging.getLogger(__name__)


class CacheMigrator:
    """
    Migrates cache files from local storage to global cache database.

    Handles migration from the old local cache system (repo2data_cache.json
    files stored in data directories) to the new global SQLite cache.
    """

    LOCAL_CACHE_FILENAME = "repo2data_cache.json"

    def __init__(self, global_cache: GlobalCacheManager):
        """
        Initialize CacheMigrator.

        Parameters
        ----------
        global_cache : GlobalCacheManager
            Global cache manager to migrate to
        """
        self.global_cache = global_cache
        self.logger = logger

    def find_local_caches(self, search_paths: List[Path]) -> List[Path]:
        """
        Find all local cache files in given search paths.

        Parameters
        ----------
        search_paths : list of pathlib.Path
            Directories to search for local cache files

        Returns
        -------
        list of pathlib.Path
            Paths to all local cache files found
        """
        cache_files = []

        for search_path in search_paths:
            if not search_path.exists():
                continue

            try:
                # Search recursively for cache files
                for cache_file in search_path.rglob(self.LOCAL_CACHE_FILENAME):
                    if cache_file.is_file():
                        cache_files.append(cache_file)

                # Also search for download_key prefixed caches
                for cache_file in search_path.rglob("*_repo2data_cache_record.json"):
                    if cache_file.is_file():
                        cache_files.append(cache_file)

            except (PermissionError, OSError) as e:
                self.logger.warning(f"Error searching {search_path}: {e}")
                continue

        self.logger.debug(f"Found {len(cache_files)} local cache files")
        return cache_files

    def migrate_local_cache(
        self,
        cache_file: Path,
        remove_after: bool = False
    ) -> bool:
        """
        Migrate a single local cache file to global cache.

        Parameters
        ----------
        cache_file : pathlib.Path
            Path to local cache file
        remove_after : bool
            If True, remove local cache file after successful migration

        Returns
        -------
        bool
            True if migration successful
        """
        try:
            # Read local cache file
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # Extract information
            config = cache_data.get('config', {})
            timestamp = cache_data.get('timestamp')
            metadata = cache_data.get('metadata', {})
            cache_version = cache_data.get('cache_version', '2.0')

            # Determine destination path (parent directory of cache file)
            destination = cache_file.parent

            # Extract download_key if present in filename
            download_key = None
            filename = cache_file.name
            if filename != self.LOCAL_CACHE_FILENAME:
                # Extract from filename like "dataset1_repo2data_cache.json"
                download_key = filename.replace(f"_{self.LOCAL_CACHE_FILENAME}", "")

            # Validate we have required fields
            if not config or 'src' not in config:
                self.logger.warning(
                    f"Invalid cache file {cache_file}: missing config or src"
                )
                return False

            # Check if already migrated
            if self.global_cache.is_cached(config, destination, download_key):
                self.logger.debug(
                    f"Already migrated: {cache_file}"
                )
                if remove_after:
                    cache_file.unlink()
                return True

            # Save to global cache
            self.global_cache.save_cache(
                config=config,
                destination=destination,
                download_key=download_key,
                metadata=metadata
            )

            self.logger.info(
                f"Migrated: {cache_file} -> global cache"
            )

            # Remove local cache file if requested
            if remove_after:
                cache_file.unlink()
                self.logger.debug(f"Removed local cache file: {cache_file}")

            return True

        except (json.JSONDecodeError, KeyError, IOError) as e:
            self.logger.error(f"Error migrating {cache_file}: {e}")
            return False

    def migrate_all(
        self,
        search_paths: List[Path],
        remove_after: bool = False
    ) -> Tuple[int, int]:
        """
        Migrate all local cache files to global cache.

        Parameters
        ----------
        search_paths : list of pathlib.Path
            Directories to search for local cache files
        remove_after : bool
            If True, remove local cache files after successful migration

        Returns
        -------
        tuple of (int, int)
            (number_migrated, number_failed)
        """
        cache_files = self.find_local_caches(search_paths)

        if not cache_files:
            self.logger.info("No local cache files found to migrate")
            return (0, 0)

        migrated = 0
        failed = 0

        for cache_file in cache_files:
            if self.migrate_local_cache(cache_file, remove_after):
                migrated += 1
            else:
                failed += 1

        self.logger.info(
            f"Migration complete: {migrated} migrated, {failed} failed"
        )

        return (migrated, failed)

    def auto_migrate(
        self,
        config_path: Optional[str] = None,
        remove_after: bool = False
    ) -> Tuple[int, int]:
        """
        Automatically migrate local caches found near config file or in common locations.

        Parameters
        ----------
        config_path : str, optional
            Path to configuration file (searches nearby directories)
        remove_after : bool
            If True, remove local cache files after migration

        Returns
        -------
        tuple of (int, int)
            (number_migrated, number_failed)
        """
        search_paths = []

        # If config path provided, search relative to it
        if config_path:
            config_dir = Path(config_path).parent.resolve()
            search_paths.append(config_dir)

            # Also search common relative paths
            search_paths.append(config_dir / 'data')
            search_paths.append(config_dir / '..' / 'data')

        # Search current directory and ./data
        search_paths.append(Path.cwd())
        search_paths.append(Path.cwd() / 'data')

        # Remove duplicates and non-existent paths
        search_paths = [p.resolve() for p in search_paths if p.exists()]
        search_paths = list(dict.fromkeys(search_paths))  # Remove duplicates

        self.logger.info(f"Auto-migrating caches from {len(search_paths)} locations")

        return self.migrate_all(search_paths, remove_after)
