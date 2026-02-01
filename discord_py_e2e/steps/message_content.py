import asyncio
from behave import *
from behave.api.async_step import async_run_until_complete
from discord import NotFound

from discord_py_e2e.context import Context
from ..dotted_arg import Args


@then("the bot response contains {text:args}")
@async_run_until_complete
async def step_bot_response_contains(context, text: Args[str]):
    assert (
        context.bot_response is not None
    ), "No bot response found. Make sure 'the bot responds with a message' step was executed before this step."
    text = text(context)

    # Check if the message content contains the specified text
    if context.bot_response.content and text in context.bot_response.content:
        return

    # If not in content, check if it's in embeds or components
    if context.raw_bot_response:
        raw_content = str(context.raw_bot_response)
        assert (
            text.lower() in raw_content.lower()
        ), f"Expected text '{text}' not found in bot response content: '{context.bot_response.content}' or raw data: '{raw_content}'"
    else:
        raise AssertionError(
            f"Expected text '{text}' not found in bot response: '{context.bot_response.content}' and no raw data available"
        )


@then("the message does not contain {text:args}")
@async_run_until_complete
async def step_bot_response_does_not_contain(context, text: Args[str]):
    assert (
        context.bot_response is not None
    ), "No bot response found. Make sure 'the bot responds with a message' step was executed before this step."
    text = text(context)

    # Check if the message content does not contain the specified text
    if context.bot_response.content and text not in context.bot_response.content:
        return

    # If not in content, check if it's in embeds or components
    if context.raw_bot_response:
        raw_content = str(context.raw_bot_response)
        assert (
            text.lower() not in raw_content.lower()
        ), f"Unexpected text '{text}' found in bot response raw data: '{raw_content}'"


@then("{{{message}}} is deleted")
@async_run_until_complete
async def step_message_is_deleted(context, message: str):
    """
    Check if a message has been deleted.
    Will wait for the message_delete event with a timeout of 3 seconds.

    Args:
        context: The behave context
        message: The name of the message variable in context.args
    """
    message_obj = context.args.get(message)
    assert message_obj is not None, f"No message found with name '{message}' in context.args"

    # First check if the message is already deleted
    try:
        await message_obj.channel.fetch_message(message_obj.id)
    except NotFound:
        # Message is already deleted
        return

    # Wait for the message_delete event
    try:
        await context.runner_bot.wait_for(
            "message_delete", check=lambda deleted_message: deleted_message.id == message_obj.id, timeout=3
        )
    except asyncio.TimeoutError:
        # If we time out, check one more time in case we missed the event
        try:
            await message_obj.channel.fetch_message(message_obj.id)
            raise AssertionError(f"Message {message} was not deleted after waiting 3 seconds")
        except NotFound:
            # Message was deleted after all
            pass


@then("{{{message}}} is not deleted")
@async_run_until_complete
async def step_message_is_not_deleted(context, message: str):
    """
    Check if a message has not been deleted.

    Args:
        context: The behave context
        message: The name of the message variable in context.args
    """
    message_obj = context.args.get(message)
    assert message_obj is not None, f"No message found with name '{message}' in context.args"

    try:
        await message_obj.channel.fetch_message(message_obj.id)
    except NotFound:
        raise AssertionError(f"Message {message} was deleted")


@then("the bot response equals {text:args}")
@async_run_until_complete
async def step_bot_response_equals(context, text: Args[str]):
    assert (
        context.bot_response is not None
    ), "No bot response found. Make sure 'the bot responds with a message' step was executed before this step."
    text = text(context)

    # Check if the message content equals the specified text
    assert (
        context.bot_response.content == text
    ), f"Bot response '{context.bot_response.content}' does not equal expected text '{text}'"


@then("there is a message in {{{channel}}} with content {content:args}")
@async_run_until_complete
async def step_channel_has_message_with_content(context, channel: str, content: Args[str]):
    """
    Check if a channel contains a message with the specified content.

    Args:
        context: The behave context
        channel: The name of the channel variable in context.args
        content: The expected content of the message
    """
    content = content(context)
    messages = await _get_messages_from_channel(context, channel)

    # Check if any message has the exact content
    assert any(
        m.content == content for m in messages
    ), f"No message found in channel {channel} with content '{content}'"


@then("there is a message in {{{channel}}} containing {text:args}")
@async_run_until_complete
async def step_channel_has_message_containing(context, channel: str, text: Args[str]):
    """
    Check if a channel contains a message that contains the specified text.

    Args:
        context: The behave context
        channel: The name of the channel variable in context.args
        text: The text to look for in messages
    """
    text = text(context)

    messages = await _get_messages_from_channel(context, channel)

    # Check if any message contains the text
    assert any(text in m.content for m in messages), f"No message found in channel {channel} containing '{text}'"


@then("{{{message_arg}}} contains {text:args}")
@async_run_until_complete
async def step_message_contains(context, message_arg: str, text: Args[str]):
    message = context.args[message_arg]
    text = text(context)
    assert text in message.content, f"text {text!r} not found in message {message.content!r}"


async def _get_messages_from_channel(context: Context, channel: str):
    channel_obj = context.args.get(channel)
    assert channel_obj is not None, f"No channel found with name '{channel}' in context.args"

    # Fetch messages in the channel
    messages = [message async for message in channel_obj.history(limit=50)]
    return messages
