from abc import ABC, abstractmethod
from typing import Any, Dict
from genpulse.types import TaskContext

class BaseEngine(ABC):
    """
    Base class for all generation engines (backends).
    Engines are responsible for low-level execution logic,
    whether local (Diffusers, ComfyUI) or remote (via Client wrapper).
    """

    @abstractmethod
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate parameters specific to this engine."""
        pass

    @abstractmethod
    async def execute(self, task: Dict[str, Any], context: TaskContext) -> Dict[str, Any]:
        """
        Execute the generation task.
        :param task: The full task dictionary.
        :param context: TaskContext for status updates and ID access.
        """
        pass

