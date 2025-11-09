"""Archive decompression utilities."""

import os
from pathlib import Path
from typing import List
import logging

logger = logging.getLogger(__name__)


class Decompressor:
    """
    Handle automatic decompression of archive files.

    Supports various archive formats using patoolib.
    """

    def __init__(self, directory: Path):
        """
        Initialize Decompressor.

        Parameters
        ----------
        directory : pathlib.Path
            Directory containing files to decompress
        """
        self.directory = Path(directory)
        self.logger = logger
        self._patool_available = self._check_patool_support()

    def _check_patool_support(self) -> bool:
        """Check if patool is available."""
        try:
            import patoolib
            return True
        except ImportError:
            self.logger.warning(
                "patool not installed. Archive decompression disabled. "
                "Install with: pip install patool"
            )
            return False

    def decompress_all(self) -> List[Path]:
        """
        Decompress all archive files in the directory.

        Archives are extracted in-place and then deleted.

        Returns
        -------
        list of pathlib.Path
            Paths of successfully decompressed archives

        Raises
        ------
        ImportError
            If patool is not available
        """
        if not self._patool_available:
            self.logger.warning(
                "Skipping decompression - patool not available"
            )
            return []

        if not self.directory.exists():
            self.logger.warning(
                f"Directory does not exist: {self.directory}"
            )
            return []

        import patoolib
        decompressed = []

        files = list(self.directory.iterdir())
        self.logger.debug(
            f"Checking {len(files)} files for decompression"
        )

        for file_path in files:
            if not file_path.is_file():
                continue

            try:
                # Check if file is an archive
                archive_format = patoolib.get_archive_format(str(file_path))

                if archive_format:
                    self.logger.info(
                        f"Decompressing {file_path.name} ({archive_format})"
                    )

                    # Extract archive
                    patoolib.extract_archive(
                        str(file_path),
                        outdir=str(self.directory),
                        interactive=False
                    )

                    # Delete the archive after successful extraction
                    file_path.unlink()
                    self.logger.debug(f"Deleted archive: {file_path.name}")

                    decompressed.append(file_path)

            except patoolib.util.PatoolError as e:
                # Not an archive or unsupported format
                self.logger.debug(
                    f"Skipping {file_path.name}: {e}"
                )
                continue
            except Exception as e:
                self.logger.error(
                    f"Error decompressing {file_path.name}: {e}"
                )
                # Don't delete file if extraction failed
                continue

        if decompressed:
            self.logger.info(
                f"Successfully decompressed {len(decompressed)} archive(s)"
            )
        else:
            self.logger.debug("No archives found to decompress")

        return decompressed

    def decompress_file(self, file_path: Path) -> bool:
        """
        Decompress a specific archive file.

        Parameters
        ----------
        file_path : pathlib.Path
            Path to archive file

        Returns
        -------
        bool
            True if successfully decompressed

        Raises
        ------
        ImportError
            If patool is not available
        FileNotFoundError
            If file does not exist
        """
        if not self._patool_available:
            raise ImportError(
                "patool is required for decompression. "
                "Install with: pip install patool"
            )

        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        import patoolib

        try:
            # Check if it's an archive
            archive_format = patoolib.get_archive_format(str(file_path))

            if not archive_format:
                self.logger.info(f"{file_path.name} is not an archive")
                return False

            self.logger.info(
                f"Decompressing {file_path.name} ({archive_format})"
            )

            # Extract to parent directory
            output_dir = file_path.parent

            patoolib.extract_archive(
                str(file_path),
                outdir=str(output_dir),
                interactive=False
            )

            # Delete archive
            file_path.unlink()
            self.logger.info(f"Decompressed and deleted {file_path.name}")

            return True

        except patoolib.util.PatoolError as e:
            self.logger.error(f"Decompression failed: {e}")
            return False

    def is_archive(self, file_path: Path) -> bool:
        """
        Check if file is a recognized archive format.

        Parameters
        ----------
        file_path : pathlib.Path
            Path to file

        Returns
        -------
        bool
            True if file is a recognized archive
        """
        if not self._patool_available:
            return False

        import patoolib

        try:
            archive_format = patoolib.get_archive_format(str(file_path))
            return archive_format is not None
        except patoolib.util.PatoolError:
            return False

    def list_supported_formats(self) -> List[str]:
        """
        Get list of supported archive formats.

        Returns
        -------
        list of str
            Supported archive format names
        """
        if not self._patool_available:
            return []

        import patoolib

        formats = patoolib.list_formats()
        return sorted(formats)

    def __repr__(self) -> str:
        """String representation of Decompressor."""
        return (
            f"Decompressor("
            f"directory={self.directory}, "
            f"patool_available={self._patool_available})"
        )
