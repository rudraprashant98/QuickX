from functools import lru_cache
import logging
from typing import Optional

from app.core.config import get_settings
from .mqtt_client import MQTTClient
from .rabbitmq import RabbitMQClient

logger = logging.getLogger(__name__)


@lru_cache()
def get_rabbitmq() -> Optional[RabbitMQClient]:
    settings = get_settings()
    if not settings.messaging_enabled:
        return None
    try:
        return RabbitMQClient(settings.rabbitmq_url, max_retries=settings.rabbitmq_max_retries)
    except Exception:
        logger.warning("RabbitMQ unavailable; continuing without broker")
        return None


@lru_cache()
def get_mqtt() -> Optional[MQTTClient]:
    settings = get_settings()
    if not settings.messaging_enabled:
        return None
    try:
        return MQTTClient(settings.mqtt_host, settings.mqtt_port)
    except Exception:
        logger.warning("MQTT unavailable; continuing without broker")
        return None
