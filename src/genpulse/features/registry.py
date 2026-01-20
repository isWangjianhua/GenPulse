from typing import Dict, Type, Optional
from genpulse.features.base import BaseHandler

class HandlerRegistry:
    _handlers: Dict[str, Type[BaseHandler]] = {}

    @classmethod
    def register(cls, task_type: str):
        """Decorator to register a handler class for a specific task type"""
        def decorator(handler_cls: Type[BaseHandler]):
            cls._handlers[task_type] = handler_cls
            return handler_cls
        return decorator

    @classmethod
    def get_handler(cls, task_type: str) -> Optional[Type[BaseHandler]]:
        """Retrieve the handler class for a task type"""
        return cls._handlers.get(task_type)

    @classmethod
    def list_handlers(cls):
        return list(cls._handlers.keys())

# Global registry instance
registry = HandlerRegistry()

