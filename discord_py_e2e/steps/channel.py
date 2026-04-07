from typing import Callable, TYPE_CHECKING

from behave import given
from behave.api.async_step import async_run_until_complete

from discord_py_e2e import ChannelBuilder
from discord_py_e2e.context import Context
from discord_py_e2e.steps.thread import _get_thread

if TYPE_CHECKING:
    from discord.guild import GuildChannel


@given("I am in a {channel_type:channel}")
@async_run_until_complete
async def step_user_in_channel(context: Context, channel_type: Callable[[GuildChannel], bool]):
    ChannelBuilder._add_filter_to_ctx(context, channel_type)
    assert context._channel_builder.verify_filters_can_match(), "No channels match!"


@given("I am in a {thread_type} thread in a {channel_type:channel}")
@async_run_until_complete
async def step_user_in_thread(context: Context, thread_type: str, channel_type: Callable[[GuildChannel], bool]):
    ChannelBuilder._add_filter_to_ctx(context, channel_type)
    assert context._channel_builder.verify_filters_can_match(), "No channels match!"
    context._channel_builder._channel = await _get_thread(context, thread_type)
