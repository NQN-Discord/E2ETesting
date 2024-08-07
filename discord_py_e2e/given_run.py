from behave import *
from behave.api.async_step import async_run_until_complete

from discord_py_e2e.context import Context


@given("I run {command}")
@async_run_until_complete
async def step_run_command(context: Context, command: str):
    await context.channel.send(command)
