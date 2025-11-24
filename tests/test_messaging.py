from app.messaging.rabbitmq import RabbitMQClient


class DummyChannel:
    def __init__(self):
        self.published = []

    def basic_publish(self, **kwargs):
        self.published.append(kwargs)

    def exchange_declare(self, **kwargs):
        pass

    def queue_declare(self, **kwargs):
        pass

    def queue_bind(self, **kwargs):
        pass

    def basic_qos(self, **kwargs):
        pass

    def basic_consume(self, **kwargs):
        pass

    def start_consuming(self):
        pass


def test_rabbitmq_publish_monkeypatch(monkeypatch):
    client = RabbitMQClient.__new__(RabbitMQClient)
    client.url = "amqp://guest:guest@localhost:5672/"
    client.exchange = "robot"
    client.max_retries = 1
    client._channel = DummyChannel()

    def connect_stub(self):
        self._channel = DummyChannel()

    monkeypatch.setattr(RabbitMQClient, "_connect", connect_stub)
    client.publish_command("robot.command", {"cmd": "start"})
    assert client._channel.published
