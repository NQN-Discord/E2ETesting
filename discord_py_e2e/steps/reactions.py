from __future__ import annotations

from behave import *
from behave.api.async_step import async_run_until_complete

from discord import Emoji, Message
from discord_py_e2e import Args
from discord_py_e2e.context import Context


@then("I add reaction {emote:arg} to {message:arg}")
@async_run_until_complete
async def step_add_reaction(context: Context, emote: Args[Emoji], message: Args[Message]):
    """
    Add a reaction to a message.

    Args:
        context: The behave context
        emote: The name of the emote variable in context.args to add as a reaction
        message: The name of the message variable in context.args to add the reaction to
    """
    message_obj = message(context)
    emote_obj = emote(context)

    # Add the reaction to the message
    await message_obj.add_reaction(emote_obj)


@then("{message:arg} has reaction {emote:arg}")
@async_run_until_complete
async def step_message_has_reaction(context: Context, message: Args[Message], emote: Args[Emoji]):
    """
    Check if a message has a specific reaction.
    If the reaction is not present, wait for it to be added.

    Args:
        context: The behave context
        message: The name of the message variable in context.args
        emote: The name of the emote variable in context.args
    """
    message_obj = message(context)
    emote_obj = emote(context)

    # Check if the reaction is already present
    if message_obj.reactions:
        has_reaction = any(reaction.emoji == emote_obj for reaction in message_obj.reactions)

        if has_reaction:
            return

    # If not, wait for the reaction_add event
    def _check(reaction, user):
        return reaction.message.id == message_obj.id and reaction.emoji == emote_obj

    # Wait for the reaction to be added
    await context.runner_bot.wait_for("reaction_add", check=_check, timeout=8)
