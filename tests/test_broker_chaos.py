import json
import threading
import time
from types import SimpleNamespace

import pika
import pytest

from app.core.metrics import BROKER_EVENTS
from app.messaging.mqtt_client import MQTTClient
from app.messaging.rabbitmq import RabbitMQClient


@pytest.mark.slow


class DummyChannel:
    def __init__(self, fail_first: bool = False):
        self.published = []
        self.fail_first = fail_first
        self.calls = 0
        self.acks = 0
        self.nacks = 0

    def basic_publish(self, **kwargs):
        self.calls += 1
        if self.fail_first and self.calls == 1:
            raise pika.exceptions.AMQPError("drop")
        self.published.append(kwargs)

    def basic_ack(self, **kwargs):
        self.acks += 1

    def basic_nack(self, **kwargs):
        self.nacks += 1


@pytest.fixture
def rabbit_client(monkeypatch):
    client = RabbitMQClient.__new__(RabbitMQClient)
    client.url = "amqp://guest:guest@localhost:5672/"
    client.exchange = "robot"
    client.max_retries = 1
    client._lock = threading.Lock()
    client._channel = DummyChannel(fail_first=True)

    def reconnect(self):
        self._channel = DummyChannel()

    monkeypatch.setattr(RabbitMQClient, "_connect", reconnect)
    return client


def test_rabbitmq_retry_and_metrics(rabbit_client):
    before = BROKER_EVENTS.labels(broker="rabbitmq", event="publish")._value.get()
    rabbit_client.publish_command("robot.command", {"cmd": "start"})
    assert rabbit_client._channel.published, "Message not published after retry"
    after = BROKER_EVENTS.labels(broker="rabbitmq", event="publish")._value.get()
    assert after == before + 1


def test_rabbitmq_slow_consumer_ack(monkeypatch):
    client = RabbitMQClient.__new__(RabbitMQClient)
    client._channel = DummyChannel()

    payloads = []

    def callback(message):
        time.sleep(0.01)
        payloads.append(message)

    client._handle_message(callback, client._channel, 1, json.dumps({"seq": 1}).encode())
    assert payloads == [{"seq": 1}]
    assert client._channel.acks == 1


def test_rabbitmq_duplicate_and_out_of_order(monkeypatch):
    client = RabbitMQClient.__new__(RabbitMQClient)
    client._channel = DummyChannel()
    received = []

    def callback(message):
        if message["seq"] not in received:
            received.append(message["seq"])

    client._handle_message(callback, client._channel, 1, json.dumps({"seq": 2}).encode())
    client._handle_message(callback, client._channel, 2, json.dumps({"seq": 2}).encode())
    client._handle_message(callback, client._channel, 3, json.dumps({"seq": 1}).encode())
    assert received == [2, 1]
    assert client._channel.acks == 3


class FakeMQTT:
    def __init__(self):
        self._callbacks = {}

    def publish(self, *_, **__):
        return SimpleNamespace(rc=0)

    def message_callback_add(self, topic, handler):
        self._callbacks[topic] = handler

    def subscribe(self, *_, **__):
        return


def _mqtt_client():
    client = MQTTClient.__new__(MQTTClient)
    client.host = "localhost"
    client.port = 1883
    client.client = FakeMQTT()
    client._callbacks = {}
    client._connected = threading.Event()
    client._connected.set()
    return client


def test_mqtt_dropped_connection(monkeypatch):
    client = _mqtt_client()

    def failing_publish(*args, **kwargs):
        return SimpleNamespace(rc=1)

    client.client.publish = failing_publish
    before = BROKER_EVENTS.labels(broker="mqtt", event="publish")._value.get()
    client.publish("robot/commands", {"cmd": "stop"}, qos=2)
    after = BROKER_EVENTS.labels(broker="mqtt", event="publish")._value.get()
    assert after == before, "Publish counter should not increment on failure"


def test_mqtt_duplicate_message_processing():
    client = _mqtt_client()
    received = []

    client.subscribe("robot/telemetry", lambda payload: received.append(payload["seq"]))
    client._dispatch("robot/telemetry", json.dumps({"seq": 1}))
    client._dispatch("robot/telemetry", json.dumps({"seq": 1}))
    client._dispatch("robot/telemetry", json.dumps({"seq": 2}))
    assert received == [1, 1, 2]


def test_mqtt_message_ordering_swapped():
    client = _mqtt_client()
    ordering = []
    client.subscribe("robot/telemetry", lambda payload: ordering.append(payload["seq"]))
    client._dispatch("robot/telemetry", json.dumps({"seq": 3}))
    client._dispatch("robot/telemetry", json.dumps({"seq": 2}))
    assert ordering == [3, 2]
