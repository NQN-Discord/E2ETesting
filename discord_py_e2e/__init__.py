import os

from .utils import *
from .given_run import *
from .channel import *
from .responds_with_message import *
from .interactions import *
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

    for cleanup_fn in context.async_cleanup_fns:
        context.add_cleanup(lambda: context.loop.run_until_complete(cleanup_fn(context)))


def before_scenario(context):
    ChannelBuilder.reset_ctx_channel(context)
