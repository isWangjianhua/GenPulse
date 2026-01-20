from typing import Optional
from .base import BaseMQ
from .redis_mq import RedisMQ
from genpulse import config

_mq_instance: Optional[BaseMQ] = None

def get_mq() -> BaseMQ:
    """
    Factory function to get the MQ instance based on configuration.
    Currently only supports 'redis'.
    """
    global _mq_instance
    if _mq_instance is None:
        mq_type = getattr(config, "MQ_TYPE", "redis").lower()
        if mq_type == "redis":
            _mq_instance = RedisMQ()
        # elif mq_type == "rabbitmq":
        #     _mq_instance = RabbitMQ()
        else:
            raise ValueError(f"Unsupported MQ type: {mq_type}")
    return _mq_instance

