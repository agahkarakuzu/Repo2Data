"""Library provider for downloading using Python packages.

DEPRECATED: This provider is deprecated due to security concerns.
Executing arbitrary Python code from configuration files poses significant
security risks and is no longer recommended.

For library-based dataset downloads, we recommend:
1. Installing the library and downloading data separately
2. Using dedicated providers (HTTP, S3, etc.) for the data
3. Creating custom provider plugins for specific libraries if needed
"""

import re
import subprocess
from pathlib import Path
from typing import Dict, Any
import warnings

from repo2data.providers.base import BaseProvider


class LibraryProvider(BaseProvider):
    """
    DEPRECATED: Provider for downloading data using Python library commands.

    This provider is disabled by default due to security concerns.
    Executing arbitrary Python code from configuration files is a
    significant security risk.

    SECURITY WARNING: This provider executes arbitrary Python code.
    DO NOT use with untrusted configuration files.
    """

    # This provider is DISABLED by default for security
    ENABLED = False

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
        self._show_deprecation_warning()

    def can_handle(self, source: str) -> bool:
        """
        Check if source is a Python import command.

        DISABLED: This provider is deprecated for security reasons.

        Parameters
        ----------
        source : str
            Source command

        Returns
        -------
        bool
            False (provider disabled)
        """
        # Return False to disable this provider by default
        if not self.ENABLED:
            return False

        return bool(re.match(r".*?(import.*?;).*", source))

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return "Python Library (DEPRECATED)"

    def _show_deprecation_warning(self) -> None:
        """Show strong deprecation warning."""
        warnings.warn(
            "\n" + "=" * 70 + "\n"
            "LibraryProvider is DEPRECATED and disabled by default.\n\n"
            "SECURITY RISK: This provider executes arbitrary Python code\n"
            "from configuration files, which poses serious security risks.\n\n"
            "Recommended alternatives:\n"
            "1. Install the Python library and download data separately\n"
            "2. Use HTTP/S3/other providers to download pre-packaged data\n"
            "3. Create custom provider plugins for specific libraries\n\n"
            "This provider will be removed in a future version.\n"
            + "=" * 70,
            category=DeprecationWarning,
            stacklevel=3
        )

    def download(self) -> Path:
        """
        Execute Python library download command.

        DEPRECATED: This method is disabled by default for security.

        Returns
        -------
        pathlib.Path
            Path to destination directory

        Raises
        ------
        RuntimeError
            Provider is disabled
        """
        if not self.ENABLED:
            raise RuntimeError(
                "LibraryProvider is disabled for security reasons.\n\n"
                "Executing arbitrary Python code from configuration files "
                "is a significant security risk.\n\n"
                "Please use alternative methods:\n"
                "1. Install the library and download data separately:\n"
                "   pip install scikit-learn\n"
                "   python -c 'from sklearn.datasets import fetch_data; "
                "fetch_data(data_home=\"./data\")'\n\n"
                "2. Download pre-packaged data using HTTP/S3 providers\n\n"
                "3. Create a custom provider for your specific library\n\n"
                "If you absolutely must use this provider (NOT recommended),\n"
                "set LibraryProvider.ENABLED = True before importing."
            )

        # If somehow enabled, show additional warnings
        self.logger.error(
            "LibraryProvider is executing arbitrary code - "
            "this is a serious security risk!"
        )

        self._ensure_destination_exists()

        # Prepare command with destination substitution
        command = self.source.replace("_dst", f'"{self.destination}"')

        self.logger.warning(f"Executing potentially unsafe command: {command}")

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
                f"Library download completed (NOT RECOMMENDED)"
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
