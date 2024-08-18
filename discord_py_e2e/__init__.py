import os

from .utils import generate_snowflake
from .given_run import step_run_command
from .channel import step_user_in_channel, ChannelBuilder
from .responds_with_message import step_bot_responds, add_edit_handler
from .interactions import press_button, buttons_exist, patch_interaction_handler
from .message_is_edited import step_message_is_edited
from .setup_rabbitmq import setup_rabbitmq
from .setup_bot import setup_bot
from .context import _ctx


async def before_all(context):

    _ctx.set(context)

    context.async_cleanup_fns = []
    context.rabbit = await setup_rabbitmq(context)
    context.runner_bot = await setup_bot()
    context.guild = context.runner_bot.get_guild(int(os.environ["GUILD_ID"]))
    patch_interaction_handler()
    add_edit_handler(context)

    for cleanup_fn in context.async_cleanup_fns:
        context.add_cleanup(lambda: context.loop.run_until_complete(cleanup_fn(context)))


def before_scenario(context):
    context.message_edit_times = []
    context.bot_response = None
    context.raw_bot_response = None
    context.command_message = None
    ChannelBuilder.reset_ctx_channel(context)


def before_step(context):
    if context.bot_response is not None:
        context.message_edit_times.append(context.bot_response.edited_at)
