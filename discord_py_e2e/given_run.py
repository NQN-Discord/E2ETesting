from typing import Optional, Dict, Any

from behave import *
from behave.api.async_step import async_run_until_complete

import random
from discord import Message

from discord_py_e2e.context import Context


def format_command_args(context: Context, command: str) -> str:
    formatted_args = {}
    for key, value in context.args.items():
        if hasattr(value, "mention"):
            formatted_args[key] = value.mention
        else:
            formatted_args[key] = value

    return command.format(**formatted_args)


@given("I run '{command}'")
@async_run_until_complete
async def step_run_command(context: Context, command: str) -> None:
    context.command_message = await context.channel.send(format_command_args(context, command))


@given("I run '{command}' as {{{message}}}")
@async_run_until_complete
async def step_run_command_as(context: Context, command: str, message: str) -> None:
    sent_message: Message = await context.channel.send(format_command_args(context, command))
    context.command_message = sent_message
    context.args[message] = sent_message


@given("argument {{{name}}} is '{value}'")
@async_run_until_complete
async def step_arg_value(context: Context, name: str, value: str):
    context.args[name] = value


@given("argument {{{name}}} is a rendered emote")
@async_run_until_complete
async def step_arg_emote(context: Context, name: str):
    emoji = random.choice(context.guild.emojis)
    context.args[name] = str(emoji)


@given("argument {{{name}}} is a {channel_type} channel")
@async_run_until_complete
async def step_arg_channel_type(context: Context, name: str, channel_type: str):
    # Find a channel of the specified type in the guild
    channel = next((channel for channel in context.guild.channels if channel.type.name == channel_type), None)

    if channel is None:
        raise ValueError(f"No {channel_type} channel found in the guild")

    context.args[name] = channel
