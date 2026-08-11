import logging

from behave import *
from behave.api.async_step import async_run_until_complete

from discord_py_e2e.context import Context


@given("error messages are allowed")
def step_error_messages_are_allowed(context):
    context.allow_error_messages = True


@given("error messages are not allowed")
def step_error_messages_are_not_allowed(context):
    context.allow_error_messages = False


@then("the bot responds with a message")
@async_run_until_complete
async def step_bot_responds(context):
    message_to_check_for = context.bot_response or context.command_message

    def _check(m):
        return (
            m.channel.id == message_to_check_for.channel.id
            and m.id > message_to_check_for.id
            and m.author.id == context.nqn_id
            and not (m.content.startswith("[MODAL: "))
        )

    cached_messages = context.runner_bot.cached_messages
    response = next((m for m in cached_messages if _check(m)), None)
    if response is None:
        response = await context.runner_bot.wait_for("message", check=_check, timeout=5)

    assert response is not None
    raw_msg_with_components = await context.runner_bot.http.get_message(
        channel_id=response.channel.id, message_id=response.id
    )
    assert raw_msg_with_components

    logging.info(f"Received message with content: {response.content}")
    logging.debug(f"Raw message content: {raw_msg_with_components!r}")

    if response.content and "an error occurred whilst processing your command" in response.content.lower():
        if not context.allow_error_messages:
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
