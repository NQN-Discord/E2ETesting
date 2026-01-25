from __future__ import annotations

from behave import *
from behave.api.async_step import async_run_until_complete

from discord_py_e2e.context import Context


@then("I add reaction {{{emote}}} to {{{message}}}")
@async_run_until_complete
async def step_add_reaction(context: Context, emote: str, message: str):
    """
    Add a reaction to a message.

    Args:
        context: The behave context
        emote: The name of the emote variable in context.args to add as a reaction
        message: The name of the message variable in context.args to add the reaction to
    """
    message_obj = context.args.get(message)
    assert message_obj is not None, f"No message found with name '{message}' in context.args"

    emote_str = context.args.get(emote)
    assert emote_str is not None, f"No emote found with name '{emote}' in context.args"

    # Add the reaction to the message
    await message_obj.add_reaction(emote_str)


@then("{{{message}}} has reaction {{{emote}}}")
@async_run_until_complete
async def step_message_has_reaction(context: Context, message: str, emote: str):
    """
    Check if a message has a specific reaction.
    If the reaction is not present, wait for it to be added.

    Args:
        context: The behave context
        message: The name of the message variable in context.args
        emote: The name of the emote variable in context.args
    """
    message_obj = context.args.get(message)
    assert message_obj is not None, f"No message found with name '{message}' in context.args"

    emote_str = context.args.get(emote)
    assert emote_str is not None, f"No emote found with name '{emote}' in context.args"

    # Check if the reaction is already present
    if message_obj.reactions:
        has_reaction = any(str(reaction.emoji) == emote_str for reaction in message_obj.reactions)

        if has_reaction:
            return

    # If not, wait for the reaction_add event
    def _check(reaction, user):
        return reaction.message.id == message_obj.id and str(reaction.emoji) == emote_str

    # Wait for the reaction to be added
    await context.runner_bot.wait_for("reaction_add", check=_check, timeout=3)
