from typing import Optional

from behave import *
from behave.api.async_step import async_run_until_complete

import random

from discord_py_e2e.context import Context


@given("I run '{command}'")
@async_run_until_complete
async def step_run_command(context: Context, command: str):
    context.command_message = await context.channel.send(command.format(**context.args))


@given("Argument {{{name}}} is '{value}'")
@async_run_until_complete
async def step_arg_value(context: Context, name: str, value: str):
    context.args[name] = value


@given("Argument {{{name}}} is a rendered emote")
@async_run_until_complete
async def step_arg_emote(context: Context, name: str):
    emoji = random.choice(context.guild.emojis)
    context.args[name] = str(emoji)
