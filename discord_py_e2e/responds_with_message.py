from behave import *
from behave.api.async_step import async_run_until_complete


@then("the bot responds with a message")
@async_run_until_complete
async def step_bot_responds(context):
    def _check(m):
        return m.channel.id == command_message.channel.id and m.id > command_message.id and m.author.id == context.bot.user.id

    cached_messages = context.runner_bot.cached_messages
    command_message = context.command_message
    response = next((m for m in cached_messages if _check(m)), None)
    if response is None:
        response = await context.runner_bot.wait_for("message", check=_check, timeout=3)

    context.bot_response = response
    assert response is not None
