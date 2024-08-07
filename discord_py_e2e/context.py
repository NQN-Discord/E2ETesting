from __future__ import annotations

from asyncio import AbstractEventLoop
from typing import TYPE_CHECKING, Awaitable, Callable, List

from aiohttp import web
from behave.runner import Context as BehaveContext
from discord import Guild

if TYPE_CHECKING:
    from discord_py_e2e.setup_rabbitmq import GatewayRabbit


class Context(BehaveContext):
    loop: AbstractEventLoop
    guild: Guild
    webserver: web.Application
    rabbit: GatewayRabbit
    async_cleanup_fns: List[Callable[[Context], Awaitable[None]]]
