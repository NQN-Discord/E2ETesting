from typing import Callable

from behave import *
from behave.api.async_step import async_run_until_complete
from discord import TextChannel

from discord_py_e2e.context import Context


@given("a {channel:channel} exists")
@async_run_until_complete
async def step_channel_exists(context: Context, channel: Callable[[Context], TextChannel]):
    pass
    #await get_channel(context.bots["runner"]).send(command)


@given("I am in a {get_channel:channel}")
@async_run_until_complete
async def step_user_in_channel(context: Context, get_channel: Callable[[Context], TextChannel]):
    context.channel = get_channel(context)
    print(context.channel)
