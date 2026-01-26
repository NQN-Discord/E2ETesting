from typing import Optional, Dict, Any

from behave import *
from behave.api.async_step import async_run_until_complete

import random
from discord import Message

from discord_py_e2e.context import Context


class _DotAccessDict:
    def __init__(self, args):
        self.args = args

    def __getitem__(self, key):
        # Check if this is a dotted path
        if "." in key:
            obj_name, *attrs = key.split(".")  # Split on first dot
            if obj_name in self.args:
                obj = self.args[obj_name]
                # Handle nested attributes (a.b.c)
                for part in attrs:
                    obj = getattr(obj, part)
                return obj
            return f"{{{key}}}"

        return self.args[key]


def format_command_args(context: Context, command: str) -> str:
    return command.format_map(_DotAccessDict(context.args))


@given("I run '{command}'")
@async_run_until_complete
async def step_run_command(context: Context, command: str) -> None:
    await _run_command(context, command)


@given("I run '{command}' as {{{message}}}")
@async_run_until_complete
async def step_run_command_as(context: Context, command: str, message: str) -> None:
    await _run_command(context, command)
    context.args[message] = context.command_message


async def _run_command(context: Context, command: str):
    context.command_message = await context.channel.send(format_command_args(context, command))


@given("I reply to {{{message}}} with '{command}'")
@async_run_until_complete
async def step_reply_with_command(context: Context, message: str, command: str) -> None:
    await _reply_with_command(context, message, command)


@given("I reply to {{{message}}} with '{command}' as {{{message_2}}}")
@async_run_until_complete
async def step_reply_with_command_as(context: Context, message: str, command: str, message_2: str) -> None:
    await _reply_with_command(context, message, command)
    context.args[message_2] = context.command_message


async def _reply_with_command(context: Context, message: str, command: str) -> None:
    """
    Reply to a message with a command.

    Args:
        context: The behave context
        message: The name of the message variable in context.args to reply to
        command: The command to send as a reply
    """
    message_obj = context.args.get(message)
    assert message_obj is not None, f"No message found with name '{message}' in context.args"

    formatted_command = format_command_args(context, command)
    context.command_message = await message_obj.reply(formatted_command)


@given("argument {{{name}}} is '{value}'")
@async_run_until_complete
async def step_arg_value(context: Context, name: str, value: str):
    context.args[name] = value


@given("there exists a custom emote {{{name}}}")
@async_run_until_complete
async def step_arg_emote(context: Context, name: str):
    emoji = random.choice(context.guild.emojis)
    context.args[name] = emoji


@given("argument {{{name}}} is a {channel_type} channel")
@async_run_until_complete
async def step_arg_channel_type(context: Context, name: str, channel_type: str):
    # Find a channel of the specified type in the guild
    channel = next((channel for channel in context.guild.channels if channel.type.name == channel_type), None)

    if channel is None:
        raise ValueError(f"No {channel_type} channel found in the guild")

    context.args[name] = channel
