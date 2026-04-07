import asyncio
import importlib
import os
import sys

from .dotted_arg import Args
from .context import Context, _ctx
from .tag_handlers import process_tags
from .channel import ChannelBuilder
from . import steps
from .setup_rabbitmq import setup_rabbitmq
from .setup_bot import setup_bot, setup_manager, reset_bot_config


async def before_all(context: Context):
    from .debugger.connection import connect_to_nqn

    if not context._runner.step_registry.steps["given"]:
        _reload_all_steps()
    _ctx.set(context)
    nqn_pid = context.config.userdata.getint("nqn_pid", None)
    if nqn_pid is not None:
        print("Passed in NQN PID:", nqn_pid)

    context.evaluator = evaluator = await connect_to_nqn(nqn_pid=nqn_pid)
    context.async_cleanup_fns = []
    context.nqn_id, context.rabbit, context.runner_bot, context.manager_bot = await asyncio.gather(
        evaluator.evaluate(_get_nqn_id),
        setup_rabbitmq(context),
        setup_bot(),
        setup_manager(),
    )
    context.guild = context.runner_bot.get_guild(int(os.environ["GUILD_ID"]))

    await evaluator.evaluate(steps.interactions.patch_interaction_handler)

    context.bot_response = None
    context.raw_bot_response = None
    steps.responds_with_message.add_edit_handler(context)

    _add_traceback_handler(context)

    for cleanup_fn in context.async_cleanup_fns:
        context.add_cleanup(lambda: context.loop.run_until_complete(cleanup_fn(context)))


async def before_scenario(context: Context):
    context.args = {}
    context.message_edit_times = []
    context.bot_response = None
    context.raw_bot_response = None
    context.command_message = None
    ChannelBuilder.reset_ctx_channel(context)

    await context.evaluator.evaluate(reset_bot_config, context.guild.id)
    context.add_cleanup(lambda: context.loop.run_until_complete(asyncio.sleep(1)))


def before_step(context: Context):
    if context.bot_response is not None:
        context.message_edit_times.append(context.bot_response.edited_at)


def after_scenario(context: Context):
    context.loop.run_until_complete(steps.modals.check_unhandled_modals(context))


def _add_traceback_handler(context: Context):
    tb_handler = lambda tb: _traceback_handler(context, tb)
    context.evaluator.add_traceback_handler(tb_handler)
    context.add_cleanup(context.evaluator.remove_traceback_handler, tb_handler)


def _traceback_handler(context: Context, traceback: str):
    context.abort("Failed due to traceback")


def _get_nqn_id() -> int:
    from __main__ import bot

    return bot.user.id


def _reload_all_steps():
    # Fix for jetbrains behave plugin
    for mod_name, module in sys.modules.copy().items():
        if "discord_py_e2e." in mod_name:
            importlib.reload(module)
