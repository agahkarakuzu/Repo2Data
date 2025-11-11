"""Configuration file loader supporting JSON and YAML formats."""

import json
import os
import re
import urllib.request
from pathlib import Path
from typing import Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Load and parse configuration files in JSON or YAML format.

    Supports loading from:
    - Local file paths (.json, .yaml, .yml)
    - GitHub repository URLs
    - MyST configuration files (myst.yml)
    - Automatic format detection
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the ConfigLoader.

        Parameters
        ----------
        config_path : str, optional
            Path to config file or GitHub URL.
            Defaults to './data_requirement.json'
        """
        self.config_path = config_path or "data_requirement.json"
        self._yaml_available = self._check_yaml_support()

    def _check_yaml_support(self) -> bool:
        """Check if YAML support is available."""
        try:
            import yaml
            return True
        except ImportError:
            logger.warning(
                "PyYAML not installed. YAML support disabled. "
                "Install with: pip install pyyaml"
            )
            return False

    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file or URL.

        Returns
        -------
        dict
            Parsed configuration dictionary

        Raises
        ------
        FileNotFoundError
            If config file is not found
        ValueError
            If config format is invalid
        """
        logger.debug(f"Loading configuration from: {self.config_path}")

        # Check if it's a GitHub URL
        if re.match(r".*?(github\.com).*?", self.config_path):
            return self._load_from_github()
        # Check if it's a file path
        elif self._is_config_file(self.config_path):
            return self._load_from_file(self.config_path)
        else:
            raise ValueError(
                f"{self.config_path} is neither a valid URL nor a "
                "recognized config file (.json, .yaml, .yml)"
            )

    def _is_config_file(self, path: str) -> bool:
        """Check if path is a recognized config file format."""
        return bool(re.match(r".*?\.(json|yaml|yml)$", path.lower()))

    def _is_myst_config(self, config: Dict[str, Any], filename: str = "") -> bool:
        """Check if this is a MyST configuration file."""
        # MyST files have 'project' and/or 'version' at root level
        # and filename is typically myst.yml or myst.yaml
        is_myst_filename = 'myst' in filename.lower()
        has_project = 'project' in config
        has_version_and_project = 'version' in config and 'project' in config

        return is_myst_filename or has_project or has_version_and_project

    def _load_from_github(self) -> Dict[str, Any]:
        """
        Load configuration from GitHub repository.

        Tries root directory first, then binder/ directory.

        Returns
        -------
        dict
            Parsed configuration

        Raises
        ------
        Exception
            If no config file found in repository
        """
        orga_repo = re.match(
            r".*?github\.com(/.*/.*)", self.config_path
        )[1]

        # Try different locations and formats
        locations = [
            ("root", ""),
            ("binder", "binder/")
        ]
        formats = ["json", "yaml", "yml"]

        for loc_name, loc_path in locations:
            for fmt in formats:
                if fmt != "json" and not self._yaml_available:
                    continue

                filename = f"data_requirement.{fmt}"
                raw_url = (
                    f"https://raw.githubusercontent.com{orga_repo}/"
                    f"HEAD/{loc_path}{filename}"
                )

                try:
                    logger.debug(f"Trying {raw_url}")
                    with urllib.request.urlopen(raw_url) as response:
                        content = response.read().decode()

                    if fmt == "json":
                        config = json.loads(content)
                    else:
                        import yaml
                        config = yaml.safe_load(content)

                    logger.debug(
                        f"Loaded {filename} from GitHub ({loc_name} directory)"
                    )
                    return self._normalize_config(config, filename)

                except urllib.error.HTTPError:
                    continue
                except Exception as e:
                    logger.debug(f"Error loading {raw_url}: {e}")
                    continue

        raise Exception(
            f"{self.config_path} does not contain a data_requirement file "
            "(tried .json, .yaml, .yml in root and binder/ directories)"
        )

    def _load_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load configuration from local file.

        Parameters
        ----------
        file_path : str
            Path to configuration file

        Returns
        -------
        dict
            Parsed configuration

        Raises
        ------
        FileNotFoundError
            If file does not exist
        ValueError
            If file format is invalid
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")

        suffix = path.suffix.lower()
        filename = path.name

        try:
            with open(path, 'r', encoding='utf-8') as f:
                if suffix == '.json':
                    config = json.load(f)
                elif suffix in ['.yaml', '.yml']:
                    if not self._yaml_available:
                        raise ImportError(
                            "PyYAML is required for YAML files. "
                            "Install with: pip install pyyaml"
                        )
                    import yaml
                    config = yaml.safe_load(f)
                else:
                    raise ValueError(f"Unsupported file format: {suffix}")

            logger.debug(f"Loaded configuration from {file_path}")
            return self._normalize_config(config, filename)

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {e}")
        except Exception as e:
            if 'yaml' in str(type(e).__module__):
                raise ValueError(f"Invalid YAML in {file_path}: {e}")
            raise

    def _normalize_config(
        self,
        config: Dict[str, Any],
        filename: str = ""
    ) -> Dict[str, Any]:
        """
        Normalize configuration structure.

        Handles:
        - YAML files with 'data' top-level key
        - MyST configuration files with project metadata
        - Project name inference from GitHub URL

        Parameters
        ----------
        config : dict
            Raw configuration dictionary
        filename : str
            Name of the config file (for MyST detection)

        Returns
        -------
        dict
            Normalized configuration
        """
        # Check if this is a MyST config file
        if self._is_myst_config(config, filename):
            return self._normalize_myst_config(config)

        # If config has a single 'data' key, unwrap it
        if len(config) == 1 and 'data' in config:
            logger.debug("Unwrapping 'data' field from config")
            return config['data']

        return config

    def _normalize_myst_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize MyST configuration file.

        MyST files have 'project' metadata and may have 'data' requirements.
        If projectName is missing, infer it from project.github.

        Parameters
        ----------
        config : dict
            MyST configuration dictionary

        Returns
        -------
        dict
            Normalized configuration with data requirements
        """
        # Extract data requirements
        if 'data' not in config:
            raise ValueError(
                "MyST config file must have a 'data' field with download requirements"
            )

        data_config = config['data']

        # If it's a dict (single or multiple downloads), process it
        if isinstance(data_config, dict):
            # Check if we need to infer projectName
            project_metadata = config.get('project', {})

            # Helper function to infer project name from GitHub URL
            def infer_project_name(github_url: str) -> str:
                """Extract project name from GitHub URL."""
                # Handle full URLs like https://github.com/username/repo
                match = re.search(r'github\.com/([^/]+)/([^/\s]+)', github_url)
                if match:
                    username, repo = match.groups()
                    # Remove .git suffix if present
                    repo = repo.rstrip('.git')
                    # Combine as username_repo in lowercase
                    return f"{username}_{repo}".lower()
                return None

            # Check if this is a single download without projectName
            if 'src' in data_config and 'projectName' not in data_config:
                # Try to infer from project.github
                if 'github' in project_metadata:
                    inferred_name = infer_project_name(project_metadata['github'])
                    if inferred_name:
                        data_config['projectName'] = inferred_name
                        logger.debug(
                            f"Inferred projectName '{inferred_name}' "
                            f"from project.github"
                        )

            # Check if this is multi-download where some entries lack projectName
            elif 'src' not in data_config:
                # This might be multi-download
                for key, value in data_config.items():
                    if isinstance(value, dict) and 'src' in value:
                        if 'projectName' not in value:
                            # Try to infer from project.github
                            if 'github' in project_metadata:
                                inferred_name = infer_project_name(
                                    project_metadata['github']
                                )
                                if inferred_name:
                                    value['projectName'] = f"{inferred_name}_{key}"
                                    logger.debug(
                                        f"Inferred projectName '{inferred_name}_{key}' "
                                        f"for download '{key}'"
                                    )

        return data_config

    def save(
        self,
        config: Dict[str, Any],
        output_path: str,
        format: Optional[str] = None
    ) -> None:
        """
        Save configuration to file.

        Parameters
        ----------
        config : dict
            Configuration to save
        output_path : str
            Output file path
        format : str, optional
            Output format ('json' or 'yaml'). If None, inferred from path

        Raises
        ------
        ValueError
            If format is invalid or cannot be inferred
        """
        path = Path(output_path)

        if format is None:
            suffix = path.suffix.lower()
            if suffix == '.json':
                format = 'json'
            elif suffix in ['.yaml', '.yml']:
                format = 'yaml'
            else:
                raise ValueError(
                    f"Cannot infer format from {output_path}. "
                    "Specify format parameter."
                )

        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            if format == 'json':
                json.dump(config, f, indent=2)
            elif format == 'yaml':
                if not self._yaml_available:
                    raise ImportError(
                        "PyYAML is required for YAML output. "
                        "Install with: pip install pyyaml"
                    )
                import yaml
                yaml.dump(config, f, default_flow_style=False)
            else:
                raise ValueError(f"Unsupported format: {format}")

        logger.debug(f"Configuration saved to {output_path}")
