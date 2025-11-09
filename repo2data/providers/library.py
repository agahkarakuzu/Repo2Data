"""Library provider for downloading using Python packages."""

import re
import subprocess
from pathlib import Path
from typing import Dict, Any
import warnings

from repo2data.providers.base import BaseProvider


class LibraryProvider(BaseProvider):
    """
    Provider for downloading data using Python library commands.

    SECURITY WARNING: This provider executes arbitrary Python code from
    configuration files. Only use with trusted configurations.

    Uses Python libraries (e.g., scikit-learn, nilearn) to download datasets.
    """

    # Whitelist of common safe imports for data downloading
    SAFE_IMPORTS = {
        'sklearn', 'scikit-learn',
        'nilearn',
        'tensorflow', 'tf',
        'keras',
        'torch', 'pytorch',
        'torchvision',
        'datasets',  # Hugging Face
    }

    def __init__(self, config: Dict[str, Any], destination: Path):
        """
        Initialize Library provider.

        Parameters
        ----------
        config : dict
            Configuration containing Python command in 'src'
        destination : pathlib.Path
            Destination directory
        """
        super().__init__(config, destination)
        self._warn_security_risk()

    def can_handle(self, source: str) -> bool:
        """
        Check if source is a Python import command.

        Parameters
        ----------
        source : str
            Source command

        Returns
        -------
        bool
            True if source starts with 'import'
        """
        return bool(re.match(r".*?(import.*?;).*", source))

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "Python Library"

    def _warn_security_risk(self) -> None:
        """Warn about security implications of executing arbitrary code."""
        warnings.warn(
            "LibraryProvider executes arbitrary Python code from "
            "configuration files. Only use with trusted sources.",
            category=SecurityWarning,
            stacklevel=3
        )

    def _validate_command_safety(self, command: str) -> None:
        """
        Perform basic safety validation on command.

        Parameters
        ----------
        command : str
            Python command to validate

        Raises
        ------
        ValueError
            If command contains potentially dangerous patterns

        Warnings
        --------
        This is NOT comprehensive security validation. It only catches
        obvious dangerous patterns.
        """
        # Check for dangerous patterns
        dangerous_patterns = [
            r'\bos\.system\b',
            r'\bsubprocess\.',
            r'\beval\b',
            r'\bexec\b',
            r'\b__import__\b',
            r'\bopen\(',  # File operations outside data downloads
            r'\brm\b',
            r'\bdel\b',
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, command):
                raise ValueError(
                    f"Command contains potentially dangerous pattern: {pattern}"
                )

        # Check if imports are from recognized safe libraries
        import_matches = re.findall(r'\bimport\s+(\w+)', command)
        for imported_module in import_matches:
            if imported_module not in self.SAFE_IMPORTS:
                self.logger.warning(
                    f"Importing '{imported_module}' which is not in the "
                    f"safe imports whitelist. Proceed with caution."
                )

    def download(self) -> Path:
        """
        Execute Python library download command.

        Returns
        -------
        pathlib.Path
            Path to destination directory

        Raises
        ------
        ValueError
            If command fails safety validation
        Exception
            If execution fails
        """
        self._ensure_destination_exists()

        # Prepare command with destination substitution
        command = self.source.replace("_dst", f'"{self.destination}"')

        self.logger.info(f"Executing library download command")
        self.logger.debug(f"Command: {command}")

        # Basic safety validation
        try:
            self._validate_command_safety(command)
        except ValueError as e:
            self.logger.error(f"Command failed safety validation: {e}")
            raise

        # Execute the Python command
        try:
            result = subprocess.run(
                ['python3', '-c', command],
                capture_output=True,
                text=True,
                check=False,
                timeout=600  # 10 minute timeout
            )

            if result.returncode != 0:
                self.logger.error(f"Command stderr: {result.stderr}")
                raise Exception(
                    f"Library download command failed with return code "
                    f"{result.returncode}"
                )

            if result.stdout:
                self.logger.debug(f"Command output: {result.stdout}")

            self.logger.info(
                f"Successfully executed library download to {self.destination}"
            )
            return self.destination

        except subprocess.TimeoutExpired:
            raise Exception(
                "Library download command timed out after 10 minutes"
            )
        except Exception as e:
            self.logger.error(f"Library download failed: {e}")
            raise


# Custom warning for security issues
class SecurityWarning(UserWarning):
    """Warning about security implications."""
    pass
