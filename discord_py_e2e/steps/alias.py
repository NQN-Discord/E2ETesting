from behave import given
from behave.api.async_step import async_run_until_complete
from discord import Emoji

from discord_py_e2e.context import Context
from discord_py_e2e import Args


async def add_alias(user_id, partial_emote):
    from __main__ import bot
    from discord import Object

    user = Object(user_id)
    await bot.global_ctx.aliases.set_alias(user, partial_emote)


@given("I have created an alias for {emoji:arg}")
@async_run_until_complete
async def step_have_alias(context: Context, emoji: Args[Emoji]):
    """
    Creates an alias for the given emote using the evaluator.
    This directly adds the alias to the user's aliases without going through the UI.
    """
    emoji = emoji(context)

    # Add the alias directly using the evaluator
    await context.evaluator.evaluate(add_alias, context.runner_bot.user.id, emoji._to_partial())
