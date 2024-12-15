import aio_pika
import json
import asyncio
import logging
from src.application.usecases.IUpdateUsecase import UpdateUserUseCase
from src.domain.entities.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RabbitMQConsumer:
    """RabbitMQ consumer for pub-sub setup with automatic reconnection and graceful shutdown."""

    def __init__(self, amqp_url: str, exchange_name: str, update_usecase: UpdateUserUseCase):
        self.amqp_url = amqp_url
        self.exchange_name = exchange_name
        self.update_usecase = update_usecase
        self.is_running = True
        self.consumer_task = None  # Background task for consuming messages

    async def start(self):
        """Start the consumer task."""
        logger.info("Starting RabbitMQ consumer...")
        self.consumer_task = asyncio.create_task(self.consume())

    async def consume(self):
        """Connect to RabbitMQ and continuously consume messages from the exchange."""
        while self.is_running:
            try:
                logger.info("Connecting to RabbitMQ...")
                connection = await aio_pika.connect_robust(self.amqp_url)
                logger.info("Connected to RabbitMQ")

                async with connection:
                    channel = await connection.channel()
                    logger.info("Channel created successfully")

                    # Declare exchange to ensure it exists
                    exchange = await channel.declare_exchange(
                        self.exchange_name, aio_pika.ExchangeType.FANOUT, durable=True
                    )
                    logger.info(f"Exchange '{self.exchange_name}' declared.")

                    # Create an exclusive, auto-delete queue for this consumer
                    queue = await channel.declare_queue(
                        "", exclusive=True, auto_delete=True
                    )
                    await queue.bind(exchange)
                    logger.info("Queue bound to exchange. Waiting for messages...")

                    # Start consuming messages
                    await self._consume_queue(queue)

            except Exception as e:
                logger.error(f"Connection error: {e}")
                logger.info("Reconnecting to RabbitMQ in 5 seconds...")
                await asyncio.sleep(5)

    async def _consume_queue(self, queue):
        logger.info("Started consuming messages...")
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                if not self.is_running:
                    logger.info("Stopping message consumption...")
                    break

                try:
                    async with message.process():
                        body = message.body.decode("utf-8")
                        logger.info(f"Received message: {body}")
                        await self.handle_message(body)

                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Optionally handle retries or move to dead-letter queues if required

    async def handle_message(self, message_body: str):
        """Handle and process incoming messages."""
        try:
            data = json.loads(message_body)
            logger.info(f"Decoded message: {data}")

            # Convert data to User entity and update
            user = User(
                username=data.get("username"),
                phone_number=data.get("phone_number"),
                bio=data.get("bio"),
                is_active=data.get("is_active"),
                updated_at=data.get("updated_at"),
                email=data.get("email"),
                social_links = data.get('social_links')
            )
            updated_user = await self.update_usecase.execute(user.email, user)
            if updated_user:
                logger.info(f"User updated successfully: {updated_user}")
            else:
                logger.warning("User not found or update failed.")

        except json.JSONDecodeError:
            logger.error("Invalid message format: unable to decode JSON.")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def stop(self):
        """Stop the consumer gracefully."""
        logger.info("Stopping RabbitMQ consumer...")
        self.is_running = False
        if self.consumer_task:
            await self.consumer_task
        logger.info("RabbitMQ consumer stopped.")
