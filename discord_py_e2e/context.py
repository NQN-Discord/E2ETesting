from __future__ import annotations

from asyncio import AbstractEventLoop
from contextvars import ContextVar
from typing import TYPE_CHECKING, Awaitable, Callable, List

from aiohttp import web
from behave.runner import Context as BehaveContext
from discord import Guild, Client, Message

if TYPE_CHECKING:
    from discord.guild import GuildChannel
    from discord.types.message import Message as RawMessage
    from discord_py_e2e.setup_rabbitmq import GatewayRabbit


_ctx = ContextVar("context")
get_ctx = _ctx.get


class Context(BehaveContext):
    loop: AbstractEventLoop
    guild: Guild
    channel: GuildChannel
    bot: Client
    runner_bot: Client
    command_message: Message
    bot_response: Message
    raw_bot_response: RawMessage

    webserver: web.Application
    rabbit: GatewayRabbit
    async_cleanup_fns: List[Callable[[Context], Awaitable[None]]]
