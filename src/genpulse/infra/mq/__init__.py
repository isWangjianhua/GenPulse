from typing import Optional
from .base import BaseMQ
from genpulse import config

_mq_instance: Optional[BaseMQ] = None

def get_mq() -> BaseMQ:
    """
    Factory function to get the MQ instance.
    GenPulse now uses Celery exclusively.
    """
    global _mq_instance
    if _mq_instance is None:
        # We ignore config.MQ_TYPE mostly now, or check if it's purposefully set invalidly
        from .celery_mq import CeleryMQ
        _mq_instance = CeleryMQ()
    return _mq_instance

