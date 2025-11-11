"""Global cache manager using SQLite for centralized cache storage."""

import hashlib
import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)


def get_cache_dir() -> Path:
    """
    Get the global cache directory following XDG Base Directory standard.

    Returns
    -------
    pathlib.Path
        Path to global cache directory (~/.cache/repo2data/)
    """
    # Use XDG_CACHE_HOME if set, otherwise ~/.cache
    import os
    xdg_cache = os.environ.get('XDG_CACHE_HOME')
    if xdg_cache:
        cache_home = Path(xdg_cache)
    else:
        cache_home = Path.home() / '.cache'

    return cache_home / 'repo2data'


class GlobalCacheManager:
    """
    Manages a global cache database for all repo2data downloads.

    Uses SQLite to store cache metadata centrally in ~/.cache/repo2data/
    instead of storing cache files in each data directory.

    Benefits:
    - Centralized cache management
    - Efficient querying and listing of cached datasets
    - Cache persists even if data directories are deleted
    - Enables cache size tracking and cleanup
    - Supports cache management CLI commands
    """

    # Critical fields for cache key computation
    CRITICAL_FIELDS = ["src", "projectName", "version"]

    # Thread-local storage for database connections
    _thread_local = threading.local()

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize GlobalCacheManager.

        Parameters
        ----------
        cache_dir : pathlib.Path, optional
            Cache directory (defaults to ~/.cache/repo2data/)
        """
        self.cache_dir = cache_dir or get_cache_dir()
        self.db_path = self.cache_dir / 'cache.db'
        self.logger = logger

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a thread-safe database connection.

        Returns
        -------
        sqlite3.Connection
            Database connection for current thread
        """
        if not hasattr(self._thread_local, 'connection'):
            self._thread_local.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False
            )
            self._thread_local.connection.row_factory = sqlite3.Row
        return self._thread_local.connection

    def _init_database(self) -> None:
        """Initialize the cache database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create cache entries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_entries (
                cache_key TEXT PRIMARY KEY,
                destination_path TEXT NOT NULL,
                config TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                cache_version TEXT DEFAULT '3.0',
                download_key TEXT,
                size_bytes INTEGER DEFAULT 0,
                file_count INTEGER DEFAULT 0,
                metadata TEXT,
                created_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL
            )
        """)

        # Create index on destination_path for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_destination
            ON cache_entries(destination_path)
        """)

        # Create index on timestamp for cleanup operations
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON cache_entries(timestamp)
        """)

        conn.commit()
        self.logger.debug(f"Initialized cache database at {self.db_path}")

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

    def is_cached(
        self,
        config: Dict[str, Any],
        destination: Path,
        download_key: Optional[str] = None
    ) -> bool:
        """
        Check if data is already cached.

        Parameters
        ----------
        config : dict
            Current configuration
        destination : pathlib.Path
            Destination directory path
        download_key : str, optional
            Key for multi-download configurations

        Returns
        -------
        bool
            True if cached and data exists on disk
        """
        cache_key = self.compute_cache_key(config)

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT destination_path, timestamp, size_bytes
                FROM cache_entries
                WHERE cache_key = ?
                """,
                (cache_key,)
            )

            row = cursor.fetchone()

            if row:
                cached_path = Path(row['destination_path'])
                cached_time = row['timestamp']

                # Verify the data still exists on disk
                if cached_path.exists():
                    # Update last accessed time
                    cursor.execute(
                        """
                        UPDATE cache_entries
                        SET last_accessed = ?
                        WHERE cache_key = ?
                        """,
                        (datetime.now().isoformat(), cache_key)
                    )
                    conn.commit()

                    self.logger.info(
                        f"Cache hit! Data cached at {cached_time}"
                    )
                    return True
                else:
                    # Cache entry exists but data is gone - clean up
                    self.logger.warning(
                        f"Cache entry exists but data not found at {cached_path}"
                    )
                    self._remove_entry(cache_key)
                    return False

            self.logger.debug("No cache entry found")
            return False

        except sqlite3.Error as e:
            self.logger.error(f"Database error checking cache: {e}")
            return False

    def save_cache(
        self,
        config: Dict[str, Any],
        destination: Path,
        download_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Save cache entry with metadata.

        Parameters
        ----------
        config : dict
            Configuration that was used for download
        destination : pathlib.Path
            Destination directory path
        download_key : str, optional
            Key for multi-download configurations
        metadata : dict, optional
            Additional metadata to store (e.g., checksums, file info)
        """
        cache_key = self.compute_cache_key(config)
        now = datetime.now().isoformat()

        # Calculate directory size and file count
        size_bytes = 0
        file_count = 0
        if destination.exists():
            try:
                for entry in destination.rglob('*'):
                    if entry.is_file():
                        size_bytes += entry.stat().st_size
                        file_count += 1
            except Exception as e:
                self.logger.warning(f"Error calculating directory size: {e}")

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Insert or replace cache entry
            cursor.execute(
                """
                INSERT OR REPLACE INTO cache_entries
                (cache_key, destination_path, config, timestamp, cache_version,
                 download_key, size_bytes, file_count, metadata, created_at, last_accessed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cache_key,
                    str(destination.resolve()),
                    json.dumps(config),
                    now,
                    "3.0",
                    download_key,
                    size_bytes,
                    file_count,
                    json.dumps(metadata or {}),
                    now,
                    now
                )
            )

            conn.commit()
            self.logger.info(f"Cache entry saved (key: {cache_key[:16]}...)")

        except sqlite3.Error as e:
            self.logger.error(f"Failed to save cache entry: {e}")
            raise

    def get_cache_info(
        self,
        config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached information for a configuration.

        Parameters
        ----------
        config : dict
            Configuration to look up

        Returns
        -------
        dict or None
            Cache entry data if available, None otherwise
        """
        cache_key = self.compute_cache_key(config)

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM cache_entries WHERE cache_key = ?
                """,
                (cache_key,)
            )

            row = cursor.fetchone()
            if row:
                return {
                    'cache_key': row['cache_key'],
                    'destination_path': row['destination_path'],
                    'config': json.loads(row['config']),
                    'timestamp': row['timestamp'],
                    'cache_version': row['cache_version'],
                    'download_key': row['download_key'],
                    'size_bytes': row['size_bytes'],
                    'file_count': row['file_count'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                    'created_at': row['created_at'],
                    'last_accessed': row['last_accessed']
                }
            return None

        except sqlite3.Error as e:
            self.logger.error(f"Database error getting cache info: {e}")
            return None

    def list_all_cached(self) -> List[Dict[str, Any]]:
        """
        List all cached datasets.

        Returns
        -------
        list of dict
            List of all cache entries with metadata
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM cache_entries
                ORDER BY last_accessed DESC
                """
            )

            entries = []
            for row in cursor.fetchall():
                entries.append({
                    'cache_key': row['cache_key'],
                    'destination_path': row['destination_path'],
                    'config': json.loads(row['config']),
                    'timestamp': row['timestamp'],
                    'size_bytes': row['size_bytes'],
                    'file_count': row['file_count'],
                    'created_at': row['created_at'],
                    'last_accessed': row['last_accessed'],
                    'exists': Path(row['destination_path']).exists()
                })

            return entries

        except sqlite3.Error as e:
            self.logger.error(f"Database error listing cache: {e}")
            return []

    def get_total_cache_size(self) -> int:
        """
        Get total size of all cached data.

        Returns
        -------
        int
            Total size in bytes
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT SUM(size_bytes) as total FROM cache_entries")
            row = cursor.fetchone()

            return row['total'] or 0

        except sqlite3.Error as e:
            self.logger.error(f"Database error calculating total size: {e}")
            return 0

    def _remove_entry(self, cache_key: str) -> bool:
        """
        Remove a cache entry from the database.

        Parameters
        ----------
        cache_key : str
            Cache key to remove

        Returns
        -------
        bool
            True if removed successfully
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM cache_entries WHERE cache_key = ?", (cache_key,))
            conn.commit()

            return cursor.rowcount > 0

        except sqlite3.Error as e:
            self.logger.error(f"Database error removing entry: {e}")
            return False

    def invalidate_cache(
        self,
        config: Dict[str, Any]
    ) -> bool:
        """
        Invalidate cache for a specific configuration.

        Parameters
        ----------
        config : dict
            Configuration to invalidate

        Returns
        -------
        bool
            True if cache was invalidated
        """
        cache_key = self.compute_cache_key(config)
        removed = self._remove_entry(cache_key)

        if removed:
            self.logger.info(f"Cache invalidated (key: {cache_key[:16]}...)")
        else:
            self.logger.warning("No cache entry to invalidate")

        return removed

    def clean_orphaned_entries(self) -> int:
        """
        Remove cache entries where the data no longer exists on disk.

        Returns
        -------
        int
            Number of orphaned entries removed
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT cache_key, destination_path FROM cache_entries")
            entries = cursor.fetchall()

            removed = 0
            for entry in entries:
                if not Path(entry['destination_path']).exists():
                    self._remove_entry(entry['cache_key'])
                    removed += 1

            self.logger.info(f"Cleaned {removed} orphaned cache entries")
            return removed

        except sqlite3.Error as e:
            self.logger.error(f"Database error cleaning orphaned entries: {e}")
            return 0

    def clear_all(self) -> int:
        """
        Clear all cache entries (does not delete data files).

        Returns
        -------
        int
            Number of entries cleared
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as count FROM cache_entries")
            count = cursor.fetchone()['count']

            cursor.execute("DELETE FROM cache_entries")
            conn.commit()

            self.logger.info(f"Cleared all {count} cache entries")
            return count

        except sqlite3.Error as e:
            self.logger.error(f"Database error clearing cache: {e}")
            return 0

    def close(self) -> None:
        """Close database connections."""
        if hasattr(self._thread_local, 'connection'):
            self._thread_local.connection.close()
            del self._thread_local.connection

    def __repr__(self) -> str:
        """String representation."""
        entry_count = len(self.list_all_cached())
        return (
            f"GlobalCacheManager("
            f"cache_dir={self.cache_dir}, "
            f"entries={entry_count})"
        )

    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.close()
        except:
            pass
