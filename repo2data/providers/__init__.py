"""Data provider plugins for various sources."""

from repo2data.providers.base import BaseProvider
from repo2data.providers.registry import ProviderRegistry

# Global provider registry instance
registry = ProviderRegistry()

__all__ = ['BaseProvider', 'ProviderRegistry', 'registry']
