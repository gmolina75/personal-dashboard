"""Base connector interface for Google Workspace integrations.

Extends the registry base connector with additional attributes.
"""

from typing import List, Dict, Any
from app.core.registry import BaseConnector as RegistryBaseConnector

class BaseConnector(RegistryBaseConnector):
    """Base connector extending registry with Google Workspace capabilities."""
    
    source: str = "base"
    
    @abstractmethod
    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch and normalize records from the source.
        
        Returns:
            List of normalized record dictionaries with keys:
            - id: str (unique identifier)
            - source: str (connector name)
            - type: str (message, event, task, document)
            - title: str
            - snippet: str
            - url: str
            - ts_start: int (unix timestamp)
            - ts_end: int (unix timestamp)
            - meta_json: dict
            - priority: int
            - updated_at: int (unix timestamp)
        """
        raise NotImplementedError