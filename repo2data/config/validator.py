"""Configuration validation using Pydantic models."""

from typing import Dict, Any
import logging
from pydantic import ValidationError

from .models import MultiDownloadConfig, validate_config

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validate configuration using Pydantic models."""

    def __init__(self):
        """Initialize the ConfigValidator."""
        logger.debug("ConfigValidator initialized with Pydantic models")

    def validate(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration structure using Pydantic.

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

        try:
            # Use the validation function from models.py
            # This handles both single and multi-download configs
            validated = validate_config(config)

            # Log the type of configuration validated
            if isinstance(validated, MultiDownloadConfig):
                num_downloads = len(validated.root)
                logger.debug(
                    f"Multi-download configuration validated ({num_downloads} downloads)"
                )
            else:
                logger.debug("Single download configuration validated")

            return True

        except ValidationError as e:
            # Format Pydantic validation errors nicely
            error_messages = []
            for error in e.errors():
                loc = " -> ".join(str(l) for l in error['loc'])
                msg = error['msg']
                error_messages.append(f"{loc}: {msg}")

            raise ValueError(
                f"Configuration validation failed:\n" +
                "\n".join(error_messages)
            )
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            raise ValueError(f"Configuration validation failed: {str(e)}")
