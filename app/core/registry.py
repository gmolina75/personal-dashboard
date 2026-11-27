"""Unified registry for all data connectors and services."""

from typing import Dict, Type
from abc import ABC, abstractmethod


class BaseConnector(ABC):
    """Base class for all data connectors."""
    name: str = "base"
    source: str = "base"
    
    @abstractmethod
    async def fetch(self) -> list[dict]:
        """Fetch data from the source and return list of record dicts."""
        raise NotImplementedError


class Registry:
    """Registry for all connectors and services."""
    
    def __init__(self):
        self._connectors: Dict[str, Type[BaseConnector]] = {}
    
    def register(self, connector_cls: Type[BaseConnector]) -> None:
        """Register a connector class."""
        self._connectors[connector_cls.name] = connector_cls
    
    def get_connector(self, name: str) -> Type[BaseConnector] | None:
        """Get a connector by name."""
        return self._connectors.get(name)
    
    def list_connectors(self) -> list[str]:
        """List all registered connector names."""
        return list(self._connectors.keys())


# Global registry instance
registry = Registry()