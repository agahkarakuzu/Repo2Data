"""Configuration validation using JSON Schema."""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validate configuration against JSON schema."""

    # JSON Schema for single download configuration
    SINGLE_DOWNLOAD_SCHEMA = {
        "type": "object",
        "required": ["src", "projectName"],
        "properties": {
            "src": {
                "type": "string",
                "minLength": 1,
                "description": "Source URL or command"
            },
            "dst": {
                "type": "string",
                "description": "Destination directory"
            },
            "projectName": {
                "type": "string",
                "minLength": 1,
                "description": "Project/dataset name"
            },
            "dataLayout": {
                "type": "string",
                "enum": ["neurolibre"],
                "description": "Special data layout handling"
            },
            "remote_filepath": {
                "oneOf": [
                    {"type": "string"},
                    {"type": "array", "items": {"type": "string"}}
                ],
                "description": "Remote file paths (OSF only)"
            },
            "version": {
                "type": "string",
                "description": "Version for cache busting"
            },
            "recursive": {
                "type": "boolean",
                "description": "Recursive download flag"
            }
        },
        "additionalProperties": True
    }

    def __init__(self):
        """Initialize the ConfigValidator."""
        self._jsonschema_available = self._check_jsonschema_support()

    def _check_jsonschema_support(self) -> bool:
        """Check if jsonschema is available."""
        try:
            import jsonschema
            return True
        except ImportError:
            logger.warning(
                "jsonschema not installed. Schema validation disabled. "
                "Install with: pip install jsonschema"
            )
            return False

    def validate(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration structure.

        Parameters
        ----------
        config : dict
            Configuration to validate

        Returns
        -------
        bool
            True if valid

        Raises
        ------
        ValueError
            If configuration is invalid
        """
        if not config:
            raise ValueError("Configuration is empty")

        # Detect if multi-download or single download
        first_key = next(iter(config))
        first_value = config[first_key]

        if isinstance(first_value, dict):
            # Multi-download configuration
            return self._validate_multi_download(config)
        else:
            # Single download configuration
            return self._validate_single_download(config)

    def _validate_single_download(self, config: Dict[str, Any]) -> bool:
        """
        Validate single download configuration.

        Parameters
        ----------
        config : dict
            Single download configuration

        Returns
        -------
        bool
            True if valid

        Raises
        ------
        ValueError
            If validation fails
        """
        if self._jsonschema_available:
            try:
                import jsonschema
                jsonschema.validate(
                    instance=config,
                    schema=self.SINGLE_DOWNLOAD_SCHEMA
                )
            except jsonschema.ValidationError as e:
                raise ValueError(f"Configuration validation failed: {e.message}")
        else:
            # Fallback validation without jsonschema
            self._basic_validation(config, "config")

        logger.debug("Single download configuration validated")
        return True

    def _validate_multi_download(self, config: Dict[str, Any]) -> bool:
        """
        Validate multi-download configuration.

        Parameters
        ----------
        config : dict
            Multi-download configuration

        Returns
        -------
        bool
            True if valid

        Raises
        ------
        ValueError
            If validation fails
        """
        for key, sub_config in config.items():
            if not isinstance(sub_config, dict):
                raise ValueError(
                    f"Multi-download entry '{key}' must be a dictionary"
                )

            if self._jsonschema_available:
                try:
                    import jsonschema
                    jsonschema.validate(
                        instance=sub_config,
                        schema=self.SINGLE_DOWNLOAD_SCHEMA
                    )
                except jsonschema.ValidationError as e:
                    raise ValueError(
                        f"Validation failed for '{key}': {e.message}"
                    )
            else:
                # Fallback validation
                self._basic_validation(sub_config, key)

        logger.debug(
            f"Multi-download configuration validated ({len(config)} downloads)"
        )
        return True

    def _basic_validation(self, config: Dict[str, Any], key: str) -> None:
        """
        Basic validation without jsonschema.

        Parameters
        ----------
        config : dict
            Configuration to validate
        key : str
            Key name for error messages

        Raises
        ------
        ValueError
            If validation fails
        """
        required_fields = ["src", "projectName"]

        for field in required_fields:
            if field not in config:
                raise ValueError(
                    f"Missing required field '{field}' in {key}"
                )

        # Validate src
        if not config["src"] or not isinstance(config["src"], str):
            raise ValueError(
                f"'src' must be a non-empty string in {key}"
            )

        # Validate projectName
        if (not config["projectName"] or
                not isinstance(config["projectName"], str)):
            raise ValueError(
                f"'projectName' must be a non-empty string in {key}"
            )

        # Validate dst if present
        if "dst" in config and not isinstance(config["dst"], str):
            raise ValueError(f"'dst' must be a string in {key}")

        # Validate dataLayout if present
        if "dataLayout" in config:
            if config["dataLayout"] not in ["neurolibre"]:
                raise ValueError(
                    f"Invalid dataLayout '{config['dataLayout']}' in {key}"
                )
