"""Validation utilities for configuration and data."""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def validate_config_structure(config: Dict[str, Any]) -> bool:
    """
    Validate basic structure of a configuration dictionary.

    Parameters
    ----------
    config : dict
        Configuration dictionary to validate

    Returns
    -------
    bool
        True if valid, False otherwise

    Raises
    ------
    ValueError
        If required fields are missing
    """
    required_fields = ["src", "projectName"]

    # Check if this is a multi-download config
    first_key = next(iter(config))
    first_value = config[first_key]

    if isinstance(first_value, dict):
        # Multi-download: validate each sub-config
        for key, sub_config in config.items():
            if not isinstance(sub_config, dict):
                continue
            _validate_single_config(sub_config, key)
    else:
        # Single download
        _validate_single_config(config)

    return True


def _validate_single_config(
    config: Dict[str, Any],
    key: str = "config"
) -> None:
    """
    Validate a single configuration entry.

    Parameters
    ----------
    config : dict
        Configuration dictionary
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

    # Validate src is not empty
    if not config["src"] or not isinstance(config["src"], str):
        raise ValueError(f"'src' must be a non-empty string in {key}")

    # Validate projectName is not empty
    if not config["projectName"] or not isinstance(config["projectName"], str):
        raise ValueError(
            f"'projectName' must be a non-empty string in {key}"
        )

    # Validate dst if present
    if "dst" in config and not isinstance(config["dst"], str):
        raise ValueError(f"'dst' must be a string in {key}")

    logger.debug(f"Configuration validated for {key}")
