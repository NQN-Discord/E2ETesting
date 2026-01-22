import logging

from behave import *
from behave.api.async_step import async_run_until_complete

from discord_py_e2e.context import Context


@then("the bot responds with a message")
@async_run_until_complete
async def step_bot_responds(context):
    def _check(m):
        return (
            m.channel.id == command_message.channel.id and m.id > command_message.id and m.author.id == context.nqn_id
        )

    cached_messages = context.runner_bot.cached_messages
    command_message = context.command_message
    response = next((m for m in cached_messages if _check(m)), None)
    if response is None:
        response = await context.runner_bot.wait_for("message", check=_check, timeout=3)

    assert response is not None
    raw_msg_with_components = await context.runner_bot.http.get_message(
        channel_id=response.channel.id, message_id=response.id
    )
    assert raw_msg_with_components

    logging.info(f"Received message with content: {response.content}")
    logging.debug(f"Raw message content: {raw_msg_with_components!r}")

    if response.content and "an error occurred whilst processing your command" in response.content.lower():
        raise AssertionError(f"Test failed: Bot response contains an exception message: '{response.content}'")

    context.bot_response = response
    context.raw_bot_response = raw_msg_with_components


def add_edit_handler(context: Context):
    @context.runner_bot.event
    async def on_raw_message_edit(payload):
        if context.bot_response is None:
            return
        if payload.message_id != context.bot_response.id:
            return
        context.raw_bot_response = payload.data
