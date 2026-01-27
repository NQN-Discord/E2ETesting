from behave import *
from behave.api.async_step import async_run_until_complete

import random

from discord_py_e2e.context import Context
from .dotted_arg import Args


@given("I run {command:args}")
@async_run_until_complete
async def step_run_command(context: Context, command: Args[str]) -> None:
    await _run_command(context, command)


@given("I run {command:args} as {{{message}}}")
@async_run_until_complete
async def step_run_command_as(context: Context, command: Args[str], message: str) -> None:
    await _run_command(context, command)
    context.args[message] = context.command_message


async def _run_command(context: Context, command: Args[str]):
    context.command_message = await context.channel.send(command(context))


@given("I reply to {{{message}}} with {command:args}")
@async_run_until_complete
async def step_reply_with_command(context: Context, message: str, command: Args[str]) -> None:
    await _reply_with_command(context, message, command)


@given("I reply to {{{message}}} with {command:args} as {{{message_2}}}")
@async_run_until_complete
async def step_reply_with_command_as(context: Context, message: str, command: Args[str], message_2: str) -> None:
    await _reply_with_command(context, message, command)
    context.args[message_2] = context.command_message


async def _reply_with_command(context: Context, message: str, command: Args[str]) -> None:
    """
    Reply to a message with a command.

    Args:
        context: The behave context
        message: The name of the message variable in context.args to reply to
        command: The command to send as a reply
    """
    message_obj = context.args.get(message)
    assert message_obj is not None, f"No message found with name '{message}' in context.args"

    context.command_message = await message_obj.reply(command(context))


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
