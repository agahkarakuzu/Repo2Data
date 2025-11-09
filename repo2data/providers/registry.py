"""Provider registry for auto-discovering and selecting providers."""

from pathlib import Path
from typing import Dict, Any, List, Type, Optional
import logging

from repo2data.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Registry for data provider plugins.

    Manages provider registration and selection based on source URLs.
    """

    def __init__(self):
        """Initialize the provider registry."""
        self._providers: List[Type[BaseProvider]] = []
        self._provider_instances: Dict[str, BaseProvider] = {}

    def register(self, provider_class: Type[BaseProvider]) -> Type[BaseProvider]:
        """
        Register a provider class.

        Can be used as a decorator:
        @registry.register
        class MyProvider(BaseProvider):
            ...

        Parameters
        ----------
        provider_class : Type[BaseProvider]
            Provider class to register

        Returns
        -------
        Type[BaseProvider]
            The same provider class (for decorator pattern)
        """
        if not issubclass(provider_class, BaseProvider):
            raise TypeError(
                f"{provider_class} must inherit from BaseProvider"
            )

        self._providers.append(provider_class)
        logger.debug(f"Registered provider: {provider_class.__name__}")
        return provider_class

    def get_provider(
        self,
        source: str,
        config: Dict[str, Any],
        destination: Path
    ) -> BaseProvider:
        """
        Get appropriate provider for the given source.

        Providers are checked in reverse registration order
        (last registered first).

        Parameters
        ----------
        source : str
            Source URL or command
        config : dict
            Configuration dictionary
        destination : pathlib.Path
            Destination directory

        Returns
        -------
        BaseProvider
            Provider instance that can handle the source

        Raises
        ------
        ValueError
            If no provider can handle the source
        """
        # Try providers in reverse order (last registered has priority)
        for provider_class in reversed(self._providers):
            # Create temporary instance to check if it can handle the source
            temp_instance = provider_class(config, destination)
            if temp_instance.can_handle(source):
                logger.info(
                    f"Selected provider: {temp_instance.provider_name} "
                    f"for source: {source}"
                )
                return temp_instance

        raise ValueError(
            f"No provider found for source: {source}\n"
            f"Available providers: "
            f"{', '.join(p.__name__ for p in self._providers)}"
        )

    def list_providers(self) -> List[str]:
        """
        Get list of registered provider names.

        Returns
        -------
        list of str
            Names of registered providers
        """
        return [p.__name__ for p in self._providers]

    def clear(self) -> None:
        """Clear all registered providers."""
        self._providers.clear()
        self._provider_instances.clear()
        logger.debug("Provider registry cleared")

    def __len__(self) -> int:
        """Get number of registered providers."""
        return len(self._providers)

    def __repr__(self) -> str:
        """String representation of the registry."""
        return (
            f"ProviderRegistry("
            f"providers={len(self._providers)}, "
            f"registered={self.list_providers()})"
        )
