from __future__ import annotations

import os
from typing import TYPE_CHECKING

from rabbit_helper import Rabbit

if TYPE_CHECKING:
    from discord.types.gateway import MessageCreateEvent, GuildCreateEvent, GuildDeleteEvent


class GatewayRabbit(Rabbit):
    @Rabbit.sender("COMMAND", 0)
    def send_command(self, message: MessageCreateEvent, prefix: str, unprefixed_content: str):
        return {
            "message": message,
            "server_prefix": prefix,
            "unprefixed_content": unprefixed_content
        }

    @Rabbit.sender("GUILD_CREATE", 0)
    def send_guild_create(self, guild: GuildCreateEvent):
        return guild

    @Rabbit.sender("GUILD_DELETE", 0)
    def send_guild_delete(self, guild: GuildDeleteEvent):
        return guild


async def setup_rabbitmq(context) -> GatewayRabbit:
    uri = os.environ["RABBIT_URI"]
    rabbit = GatewayRabbit(uri)
    await rabbit.connect()
    return rabbit

