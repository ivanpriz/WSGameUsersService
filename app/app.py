import asyncio
import json

from app.rabbit import Rabbit, RPCServer
from app.config import Config
from app.user_manager import UserManager
from app.utils.logging import get_logger


class App:
    logger = get_logger("App")

    def __init__(self):
        self.rabbit = Rabbit(Config.RABBITMQ_URI)
        self.users_manager = UserManager(
            usernames_file=Config.USERNAMES_FILE,
            colors_file=Config.COLORS_FILE,
        )
        self.users_create_server = RPCServer(
            rabbit=self.rabbit,
            queue_to_consume_name=Config.USERS_TO_CREATE_QUEUE,
            message_processor=lambda x: json.dumps(self.users_manager.create_user(x))
        )
        self.users_delete_server = RPCServer(
            rabbit=self.rabbit,
            queue_to_consume_name=Config.USERS_TO_DELETE_QUEUE,
            message_processor=lambda x: json.dumps(self.users_manager.delete_user(x))
        )

    async def _on_start(self):
        await self.rabbit.connect()
        await self.rabbit.create_channel()

    async def _run(self):
        asyncio.create_task(self.users_delete_server.run())
        asyncio.create_task(self.users_create_server.run())

    async def start(self):
        await self._on_start()
        self.logger.debug("App started!")
        await self._run()
        self.logger.debug("App stopped!")
