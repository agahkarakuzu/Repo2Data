"""Pydantic models for configuration validation."""

from typing import Optional, Union, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class SingleDownloadConfig(BaseModel):
    """Model for a single download configuration entry."""

    model_config = ConfigDict(extra='allow')

    src: str = Field(
        min_length=1,
        description="Source URL or command (GitHub, Zenodo, OSF, etc.)"
    )
    projectName: str = Field(
        min_length=1,
        description="Project/dataset name for identification"
    )
    dst: Optional[str] = Field(
        default=None,
        description="Destination directory for downloaded files, relative to this file"
    )
    dataLayout: Optional[str] = Field(
        default=None,
        description="Special data layout handling"
    )
    remote_filepath: Optional[Union[str, List[str]]] = Field(
        default=None,
        description="Remote file paths (OSF only)"
    )
    version: Optional[str] = Field(
        default=None,
        description="Version identifier for cache busting"
    )
    recursive: Optional[bool] = Field(
        default=None,
        description="Enable recursive download for directory structures"
    )

    @field_validator('dataLayout')
    @classmethod
    def validate_data_layout(cls, v: Optional[str]) -> Optional[str]:
        """Validate that dataLayout is 'neurolibre' if specified."""
        if v is not None and v != "neurolibre":
            raise ValueError("dataLayout must be 'neurolibre' when specified")
        return v


class MultiDownloadConfig(BaseModel):
    """Model for multiple download configurations."""

    model_config = ConfigDict(extra='allow')

    root: Dict[str, SingleDownloadConfig] = Field(
        description="Dictionary of named download configurations"
    )

    @model_validator(mode='before')
    @classmethod
    def parse_dict(cls, data: Any) -> Dict[str, Any]:
        """
        Convert the input dict into the expected format.

        This allows us to accept:
        {
            "download1": {"src": "...", "projectName": "..."},
            "download2": {"src": "...", "projectName": "..."}
        }

        And convert it to:
        {
            "root": {
                "download1": {"src": "...", "projectName": "..."},
                "download2": {"src": "...", "projectName": "..."}
            }
        }
        """
        if isinstance(data, dict) and 'root' not in data:
            # Wrap the entire dict in 'root' key
            return {'root': data}
        return data


def validate_config(config: Dict[str, Any]) -> Union[SingleDownloadConfig, MultiDownloadConfig]:
    """
    Validate a configuration dictionary using appropriate Pydantic model.

    Args:
        config: Configuration dictionary from YAML/JSON

    Returns:
        Validated Pydantic model instance

    Raises:
        ValueError: If validation fails
    """
    if not config:
        raise ValueError("Configuration cannot be empty")

    # Check if this is a multi-download configuration
    # Multi-download has dict values, single-download has primitive values
    first_key = next(iter(config))
    first_value = config[first_key]

    try:
        if isinstance(first_value, dict):
            # Multi-download configuration
            return MultiDownloadConfig.model_validate(config)
        else:
            # Single download configuration
            return SingleDownloadConfig.model_validate(config)
    except Exception as e:
        raise ValueError(f"Configuration validation failed: {str(e)}") from e
