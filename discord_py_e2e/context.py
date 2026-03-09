from __future__ import annotations

from asyncio import AbstractEventLoop
from contextvars import ContextVar
from datetime import datetime
from typing import TYPE_CHECKING, Awaitable, Callable, List, Dict

from aiohttp import web
from behave.runner import Context as BehaveContext
from discord import Guild, Client, Message

if TYPE_CHECKING:
    from discord.guild import GuildChannel
    from discord.types.message import Message as RawMessage
    from discord_py_e2e.setup_rabbitmq import GatewayRabbit
    from discord_py_e2e.debugger.evalutation import EvaluationClient


_ctx = ContextVar("context")
get_ctx = _ctx.get


class Context(BehaveContext):
    loop: AbstractEventLoop
    guild: Guild
    channel: GuildChannel
    manager_bot: Client
    runner_bot: Client
    nqn_id: int
    evaluator: EvaluationClient

    webserver: web.Application
    rabbit: GatewayRabbit
    async_cleanup_fns: List[Callable[[Context], Awaitable[None]]]

    args: Dict[str, str]
    command_message: Message
    bot_response: Message
    raw_bot_response: RawMessage
    message_edit_times: List[datetime]
