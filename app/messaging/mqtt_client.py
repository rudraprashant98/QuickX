from __future__ import annotations

import json
import logging
import threading
import time
from typing import Callable

import paho.mqtt.client as mqtt

from app.core.metrics import BROKER_EVENTS

logger = logging.getLogger(__name__)


class MQTTClient:
    def __init__(
        self,
        host: str,
        port: int = 1883,
        client_id: str = "robotics-client",
        auto_start: bool = True,
    ) -> None:
        self.host = host
        self.port = port
        self.client = mqtt.Client(client_id=client_id, clean_session=False)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self._callbacks: dict[str, Callable[[dict], None]] = {}
        self._connected = threading.Event()
        if auto_start:
            self._start()

    def _start(self) -> None:
        def _loop():
            attempts = 0
            while True:
                try:
                    self.client.connect(self.host, self.port, keepalive=30)
                    self.client.loop_forever()
                except Exception as exc:
                    attempts += 1
                    if attempts <= 3:
                        # Only log first 3 attempts at debug level
                        logger.debug("MQTT connection attempt %d failed: %s", attempts, exc)
                    else:
                        logger.warning("MQTT connection attempt %d failed: %s", attempts, exc)
                    BROKER_EVENTS.labels(broker="mqtt", event="disconnect").inc()
                    time.sleep(2)

        threading.Thread(target=_loop, daemon=True).start()

    def _on_connect(self, client, userdata, flags, rc):  # noqa: D401
        if rc == 0:
            logger.info("Connected to MQTT broker")
            self._connected.set()
            BROKER_EVENTS.labels(broker="mqtt", event="connect").inc()
            for topic in self._callbacks:
                client.subscribe(topic, qos=1)
        else:
            logger.error("MQTT connection failed with rc=%s", rc)

    def _on_disconnect(self, client, userdata, rc):  # noqa: D401
        self._connected.clear()
        logger.warning("MQTT disconnected rc=%s", rc)

    def publish(self, topic: str, payload: dict, qos: int = 1) -> None:
        message = json.dumps(payload)
        if not self._connected.wait(timeout=5):
            logger.error("MQTT publish skipped; broker unavailable")
            return
        result = self.client.publish(topic, message, qos=qos)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            BROKER_EVENTS.labels(broker="mqtt", event="publish").inc()
        else:
            logger.error("MQTT publish failed rc=%s", result.rc)

    def _dispatch(self, topic: str, message: str) -> None:
        callback = self._callbacks.get(topic)
        if not callback:
            return
        try:
            data = json.loads(message)
            callback(data)
            BROKER_EVENTS.labels(broker="mqtt", event="ack").inc()
        except Exception:
            logger.exception("MQTT handler error")

    def subscribe(self, topic: str, callback: Callable[[dict], None], qos: int = 1) -> None:
        self._callbacks[topic] = callback

        def _handler(client, userdata, msg):
            self._dispatch(topic, msg.payload.decode())

        self.client.message_callback_add(topic, _handler)
        if self._connected.is_set():
            self.client.subscribe(topic, qos=qos)
