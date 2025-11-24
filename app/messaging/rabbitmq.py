from __future__ import annotations

import json
import logging
import threading
import time
from typing import Callable, Optional

import pika

from app.core.metrics import BROKER_EVENTS

logger = logging.getLogger(__name__)


class RabbitMQClient:
    def __init__(self, url: str, exchange: str = "robot.exchange", max_retries: int = 5) -> None:
        self.url = url
        self.exchange = exchange
        self.max_retries = max_retries
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel: Optional[pika.adapters.blocking_connection.BlockingChannel] = None
        self._lock = threading.Lock()
        self._connect()

    def _connect(self) -> None:
        with self._lock:
            attempts = 0
            while True:
                try:
                    params = pika.URLParameters(self.url)
                    self._connection = pika.BlockingConnection(params)
                    self._channel = self._connection.channel()
                    self._channel.exchange_declare(exchange=self.exchange, exchange_type="topic", durable=True)
                    logger.info("Connected to RabbitMQ")
                    BROKER_EVENTS.labels(broker="rabbitmq", event="connect").inc()
                    break
                except pika.exceptions.AMQPError as exc:
                    attempts += 1
                    if attempts <= 2:
                        # Only log first 2 attempts at debug level
                        logger.debug("RabbitMQ connection attempt %d failed: %s", attempts, exc)
                    else:
                        logger.warning("RabbitMQ connection attempt %d/%d failed: %s", attempts, self.max_retries or "∞", exc)
                    if self.max_retries and attempts >= self.max_retries:
                        raise
                    time.sleep(2)

    def publish_command(self, routing_key: str, payload: dict) -> None:
        message = json.dumps(payload)
        try:
            assert self._channel
            self._channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=message,
                properties=pika.BasicProperties(delivery_mode=2),
            )
            BROKER_EVENTS.labels(broker="rabbitmq", event="publish").inc()
            logger.info("Published command %s", routing_key)
        except pika.exceptions.AMQPError:
            logger.warning("Publish failed, attempting reconnect")
            self._connect()
            self.publish_command(routing_key, payload)

    def _handle_message(self, callback: Callable[[dict], None], ch, delivery_tag: int, body: bytes) -> None:
        try:
            callback(json.loads(body))
            if ch:
                ch.basic_ack(delivery_tag=delivery_tag)
            BROKER_EVENTS.labels(broker="rabbitmq", event="ack").inc()
        except Exception:
            logger.exception("Error handling message")
            if ch:
                ch.basic_nack(delivery_tag=delivery_tag, requeue=False)
            BROKER_EVENTS.labels(broker="rabbitmq", event="nack").inc()

    def consume(self, queue: str, callback: Callable[[dict], None]) -> None:
        def _consume() -> None:
            assert self._channel
            self._channel.queue_declare(queue=queue, durable=True)
            self._channel.queue_bind(queue=queue, exchange=self.exchange, routing_key=f"{queue}.*")

            def _handler(ch, method, properties, body):
                self._handle_message(callback, ch, method.delivery_tag, body)

            self._channel.basic_qos(prefetch_count=10)
            self._channel.basic_consume(queue=queue, on_message_callback=_handler)
            try:
                self._channel.start_consuming()
            except pika.exceptions.AMQPError:
                logger.warning("Consumer disconnected; reconnecting")
                BROKER_EVENTS.labels(broker="rabbitmq", event="disconnect").inc()
                self._connect()
                _consume()

        threading.Thread(target=_consume, daemon=True).start()
