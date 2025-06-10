from nats.aio.client import Client as NATS
from logging import Logger
import json


class NatsPublisher:
    def __init__(self, logger: Logger, host: str, port: int, stream: str):
        self.host = host
        self.port = port
        self.logger = logger
        self.stream = stream
        self.nc = NATS()
        self.js = None

    async def connect(self):
        try:
            await self.nc.connect(f"{self.host}:{self.port}")
            self.js = self.nc.jetstream()
            self.logger.info(f"Connected to NATS at {self.host}:{self.port}")
        except Exception as e:
            self.logger.error(f"Failed to connect to NATS: {e}")
            raise e


class NatsPublish:
    def __init__(self, logger: Logger, publisher: NatsPublisher, channel: str):
        self.logger = logger
        self.publisher = publisher
        self.channel = channel

    async def publish(self, message: dict):
        try:
            await self.publisher.js.publish(
                f"{self.publisher.stream}.{self.channel}", json.dumps(message).encode()
            )
            self.logger.debug(f"Published message to {self.channel}: {message}")
        except Exception as e:
            self.logger.error(f"Failed to publish message: {e}")
