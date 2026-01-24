import asyncio
import importlib
import os
import sys

if not hasattr(sys.modules["__main__"], "bot"):
    # Allow tests with the jetbrains debugger enabled.
    for path in sys.path[:]:
        if "JetBrains" in path:
            sys.path.remove(path)
    for mod_name in sys.modules.copy():
        if "pydev" in mod_name:
            del sys.modules[mod_name]


from .debugger.connection import connect_to_nqn
from .utils import generate_snowflake
from .given_run import step_run_command, step_arg_emote, step_arg_value
from .channel import step_user_in_channel, ChannelBuilder
from .responds_with_message import step_bot_responds, add_edit_handler
from .interactions import press_button, buttons_exist, patch_interaction_handler
from .message_is_edited import step_message_is_edited
from .message_content import (
    step_bot_response_contains,
    step_bot_response_equals,
    step_bot_response_matches_table,
    step_message_is_deleted,
    step_message_is_not_deleted,
)
from .modals import bot_responds_with_modal, fill_in_modal, check_unhandled_modals
from .setup_rabbitmq import setup_rabbitmq
from .setup_bot import setup_bot, setup_manager
from .context import _ctx
from .permissions import step_have_permission, step_have_permissions, step_bot_has_permission, step_bot_has_permissions


async def before_all(context):
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

    await evaluator.evaluate(patch_interaction_handler)

    context.bot_response = None
    context.raw_bot_response = None
    add_edit_handler(context)

    _add_traceback_handler(context)

    for cleanup_fn in context.async_cleanup_fns:
        context.add_cleanup(lambda: context.loop.run_until_complete(cleanup_fn(context)))


def before_scenario(context):
    context.args = {}
    context.message_edit_times = []
    context.bot_response = None
    context.raw_bot_response = None
    context.command_message = None
    ChannelBuilder.reset_ctx_channel(context)

    context.add_cleanup(lambda: context.loop.run_until_complete(asyncio.sleep(1)))


def before_step(context):
    if context.bot_response is not None:
        context.message_edit_times.append(context.bot_response.edited_at)


def after_scenario(context):
    context.loop.run_until_complete(check_unhandled_modals(context))


def _add_traceback_handler(context):
    tb_handler = lambda tb: _traceback_handler(context, tb)
    context.evaluator.add_traceback_handler(tb_handler)
    context.add_cleanup(context.evaluator.remove_traceback_handler, tb_handler)


def _traceback_handler(context, traceback: str):
    context.abort("Failed due to traceback")


def _get_nqn_id() -> int:
    from __main__ import bot

    return bot.user.id


def _reload_all_steps():
    # Fix for jetbrains behave plugin
    for mod_name, module in sys.modules.copy().items():
        if "discord_py_e2e." in mod_name:
            importlib.reload(module)
