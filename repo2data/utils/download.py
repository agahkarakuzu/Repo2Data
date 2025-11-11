"""Download utilities for progress tracking, verification, and validation."""

import hashlib
import shutil
from pathlib import Path
from typing import Optional, Callable, BinaryIO
from rich.progress import (
    Progress,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    TextColumn
)
from rich.console import Console

console = Console()


def get_available_disk_space(path: Path) -> int:
    """
    Get available disk space at the given path.

    Parameters
    ----------
    path : Path
        Path to check

    Returns
    -------
    int
        Available space in bytes
    """
    stat = shutil.disk_usage(path)
    return stat.free


def check_disk_space(path: Path, required_bytes: int, buffer_mb: int = 100) -> bool:
    """
    Check if there's enough disk space for a download.

    Parameters
    ----------
    path : Path
        Destination path
    required_bytes : int
        Required space in bytes
    buffer_mb : int
        Additional buffer space in MB to require (default: 100MB)

    Returns
    -------
    bool
        True if enough space is available

    Raises
    ------
    OSError
        If not enough disk space is available
    """
    available = get_available_disk_space(path)
    buffer_bytes = buffer_mb * 1024 * 1024
    needed = required_bytes + buffer_bytes

    if available < needed:
        raise OSError(
            f"Insufficient disk space. "
            f"Required: {_format_bytes(needed)}, "
            f"Available: {_format_bytes(available)}"
        )

    return True


def compute_checksum(
    file_path: Path,
    algorithm: str = "sha256",
    chunk_size: int = 8192
) -> str:
    """
    Compute checksum of a file.

    Parameters
    ----------
    file_path : Path
        Path to file
    algorithm : str
        Hash algorithm (sha256, md5, sha1)
    chunk_size : int
        Size of chunks to read

    Returns
    -------
    str
        Hexadecimal checksum string

    Raises
    ------
    ValueError
        If algorithm is not supported
    """
    algorithm = algorithm.lower()

    if algorithm not in hashlib.algorithms_available:
        raise ValueError(
            f"Unsupported algorithm: {algorithm}. "
            f"Available: {', '.join(sorted(hashlib.algorithms_available))}"
        )

    hash_obj = hashlib.new(algorithm)

    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            hash_obj.update(chunk)

    return hash_obj.hexdigest()


def verify_checksum(
    file_path: Path,
    expected_checksum: str,
    algorithm: str = "sha256"
) -> bool:
    """
    Verify file checksum matches expected value.

    Parameters
    ----------
    file_path : Path
        Path to file
    expected_checksum : str
        Expected checksum (hexadecimal)
    algorithm : str
        Hash algorithm used

    Returns
    -------
    bool
        True if checksums match

    Raises
    ------
    ValueError
        If checksums don't match
    """
    actual = compute_checksum(file_path, algorithm)

    if actual.lower() != expected_checksum.lower():
        raise ValueError(
            f"Checksum mismatch for {file_path.name}!\n"
            f"Expected ({algorithm}): {expected_checksum}\n"
            f"Actual   ({algorithm}): {actual}\n\n"
            f"The file may be corrupted or tampered with."
        )

    return True


def download_with_progress(
    response_iter: Callable,
    file_handle: BinaryIO,
    total_size: Optional[int] = None,
    description: str = "Downloading",
    chunk_size: int = 8192
) -> int:
    """
    Download data with a progress bar.

    Parameters
    ----------
    response_iter : callable
        Iterator that yields data chunks (e.g., response.iter_content)
    file_handle : BinaryIO
        Open file handle to write to
    total_size : int, optional
        Total size in bytes (if known)
    description : str
        Description to show in progress bar
    chunk_size : int
        Size of chunks to download

    Returns
    -------
    int
        Total bytes downloaded
    """
    downloaded = 0

    with Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        DownloadColumn(),
        "•",
        TransferSpeedColumn(),
        "•",
        TimeRemainingColumn(),
        console=console,
        transient=False  # Keep progress bar visible after completion
    ) as progress:

        task = progress.add_task(
            description,
            total=total_size
        )

        for chunk in response_iter(chunk_size=chunk_size):
            if chunk:
                file_handle.write(chunk)
                chunk_len = len(chunk)
                downloaded += chunk_len
                progress.update(task, advance=chunk_len)

    return downloaded


def _format_bytes(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"
