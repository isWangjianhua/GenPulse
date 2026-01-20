from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseHandler(ABC):
    @abstractmethod
    def validate_params(self, params: Dict[Any, Any]) -> bool:
        """Validate task parameters"""
        pass

    @abstractmethod
    async def execute(self, task: Dict[Any, Any], context: Dict[Any, Any]) -> Dict[Any, Any]:
        """Core execution logic"""
        pass

