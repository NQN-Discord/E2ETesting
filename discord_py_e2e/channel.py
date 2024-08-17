from __future__ import annotations

from typing import Callable, List, Tuple, TYPE_CHECKING

import behave
import parse
from behave import *
from behave.api.async_step import async_run_until_complete


from discord_py_e2e.context import Context


if TYPE_CHECKING:
    from discord.guild import GuildChannel


class ChannelBuilder:
    def __init__(self, ctx: Context):
        self._ctx = ctx
        self._filters: List[Callable[[Context, GuildChannel], bool]] = []
        self._channel = None

    @classmethod
    def _add_filter_to_ctx(cls, ctx: Context, filter_func: Callable[[Context, GuildChannel], bool]):
        if not hasattr(ctx.__class__, "channel"):
            ctx.__class__.channel = property(lambda self: self._channel_builder())

        try:
            ctx._channel_builder
        except KeyError:
            ctx._channel_builder = cls(ctx)

        ctx._channel_builder._add_filter(filter_func)

    def _add_filter(self, filter_func: Callable[[Context, GuildChannel], bool]):
        assert self._channel is None
        self._filters.append(filter_func)

    def __call__(self):
        if self._channel is not None:
            return self._channel

        for channel in self._ctx.guild.channels:
            if all(filter_func(channel) for filter_func in self._filters):
                self._channel = channel
                return channel


@parse.with_pattern(r"\w+ channel")
def _channel_type(channel_type: str) -> Callable[[GuildChannel], bool]:
    channel_type = channel_type.removesuffix(" channel")

    return lambda channel: channel.type.name == channel_type


behave.register_type(channel=_channel_type)


@given("I am in a {channel_type:channel}")
@async_run_until_complete
async def step_user_in_channel(context: Context, channel_type: Callable[[GuildChannel], bool]):
    ChannelBuilder._add_filter_to_ctx(context, channel_type)
