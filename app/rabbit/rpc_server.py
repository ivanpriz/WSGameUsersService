from typing import Optional, Callable

import aio_pika
from aio_pika import Message
from aio_pika.abc import AbstractIncomingMessage

from .rabbit import Rabbit
from app.utils.logging import get_logger


class RPCServer:
    _logger = get_logger("RPC_Server")

    def __init__(
            self,
            rabbit: Rabbit,
            queue_to_consume_name: str,
            message_processor: Callable
    ):
        self.rabbit = rabbit
        self.queue_to_consume_name = queue_to_consume_name
        self.tasks_queue: Optional[aio_pika.Queue] = None
        self.message_processor = message_processor

    async def _process_message(self, message: AbstractIncomingMessage):
        try:
            async with message.process(requeue=False):
                assert message.reply_to is not None
                payload = message.body.decode()

                self._logger.debug(
                    "Received message in q %s\n\twith payload %s\n\tand goin reply to %s",
                    self.queue_to_consume_name,
                    payload,
                    message.reply_to
                )

                response = str(self.message_processor(payload)).encode()

                await self.rabbit.channel.default_exchange.publish(
                    Message(
                        body=response,
                        correlation_id=message.correlation_id,
                    ),
                    routing_key=message.reply_to,
                )
                self._logger.debug(
                    "Received message in q %s\n\tto reply q%s",
                    self.queue_to_consume_name,
                    message.reply_to
                )

        except Exception:
            self._logger.exception("Processing error for message %r", message)

    async def run(self):
        self._logger.debug("RPC server for q %s started!", self.queue_to_consume_name)
        self.tasks_queue = await self.rabbit.declare_queue(self.queue_to_consume_name)

        async with self.tasks_queue.iterator() as qiterator:
            async for message in qiterator:
                await self._process_message(message)

