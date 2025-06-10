import logging
import asyncio
import os
from dotenv import load_dotenv
from ai_server import AiModel
from nats_decorator import NatsPublisher
import rabbit

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run():
    nats_publisher = NatsPublisher(
        logger,
        os.getenv("NATS_HOST"),
        int(os.getenv("NATS_PORT")),
        os.getenv("NATS_STREAM"),
    )
    await nats_publisher.connect()
    ai_model = AiModel(logger)
    tokenizer = ai_model.return_tokenizer()
    rabbitmq_consumer = rabbit.AsyncRabbitMQConsumer(
        logger,
        os.getenv("RABBIT_HOST"),
        os.getenv("RABBIT_USERNAME"),
        os.getenv("RABBIT_PASSWORD"),
        int(os.getenv("RABBIT_PORT")),
        ai_model,
        nats_publisher,
        tokenizer,
        os.getenv("RABBIT_QUEUE_NAME")
    )
    await rabbitmq_consumer.run()


if __name__ == "__main__":
    asyncio.run(run())
