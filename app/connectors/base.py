"""Base connector interface for Google Workspace integrations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseConnector(ABC):
    name: str = "base"
    
    @abstractmethod
    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch and normalize records from the source."""
        raise NotImplementedError