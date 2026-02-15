from __future__ import annotations

import re
from ast import literal_eval
from logging import getLogger
import copy

from behave import *
from behave.api.async_step import async_run_until_complete

from discord import ComponentType
from .interactions import run_interaction, build_modal_interaction
from ..dotted_arg import render_template, _dotted_arg

log = getLogger(__name__)

CUSTOM_ID_REGEX = re.compile(r"\d\.\S\.(.+)")


def get_and_reset_modals():
    """
    Get the remaining modals from the bot and reset the dictionary.
    Returns the modals that were present before resetting.
    """
    from __main__ import bot

    modals, bot._modals = bot._modals, {}
    return modals


async def check_unhandled_modals(context):
    """
    Check if there are any unhandled modals and fail the test if any are found.
    """
    # Get the remaining modals from the bot and reset them
    remaining_modals = await context.evaluator.evaluate(get_and_reset_modals)

    if remaining_modals:
        # Format a nice error message
        modal_details = "\n".join(
            f"  - Modal ID: {modal_id}, Title: {data.get('title', 'Unknown')}"
            for modal_id, data in remaining_modals.items()
        )
        # Fail the test
        assert not remaining_modals, f"The following modals were sent but not handled:\n{modal_details}"


def _get_modal(modal_id: str):
    from __main__ import bot

    return bot._modals.pop(modal_id)


@then("the bot responds with a modal")
@async_run_until_complete
async def bot_responds_with_modal(context):
    """
    Check if the bot responded with a modal by looking for a message with the modal ID.
    """

    def _check(m):
        return m.author.id == context.nqn_id and "[MODAL: " in m.content

    # Wait for the bot to respond with a message
    message = context.runner_bot.cached_messages[-1]
    if not _check(message):
        message = await context.runner_bot.wait_for(
            "message",
            check=_check,
            timeout=5,
        )

    # Extract the modal ID from the message
    match = re.search(r"\[MODAL: ([^\]]+)\]", message.content)
    assert match, f"Could not extract modal ID from message: {message.content}"
    modal_id = match.group(1)

    # Get the modal data from the bot
    modal_data = await context.evaluator.evaluate(_get_modal, modal_id)
    assert modal_data, f"No modal data found for ID: {modal_id}"
    context.modal_data = modal_data


@then('the modal title is "{title}"')
def modal_title_is(context, title):
    assert context.modal_data is not None, "No modal data available. Did you check for a modal response first?"
    actual_title = context.modal_data["data"]["title"]
    assert actual_title == title, f"Expected modal title '{title}', but got '{actual_title}'"


@then("I fill in the modal with the following information")
@async_run_until_complete
async def fill_in_modal(context):
    """
    Fill in a modal with the provided information and submit it.
    """
    assert context.modal_data is not None, "No modal data available. Did you check for a modal response first?"

    # Get the values from the table
    component_values = {}
    resolved_objects = []
    for row in context.table:
        component_values[row["custom_id"]] = literal_eval(render_template(context, template=row["value"]))
        if row.get("resolved"):
            resolved_objects.append(_dotted_arg(row["resolved"])(context))

    channel_id = context.modal_data["channel_id"]

    components = inject_custom_ids_to_components(context.modal_data["data"].get("components", []), component_values)

    interaction = build_modal_interaction(
        bot=context.manager_bot.get_guild(context.guild.id).get_member(context.nqn_id),
        channel=context.runner_bot.get_channel(channel_id),
        custom_id=context.modal_data["data"]["custom_id"],
        components=components,
        me=context.guild.me,
        message=context.modal_data["message"],
        to_resolve=resolved_objects,
    )

    # Submit the modal
    await context.evaluator.evaluate(run_interaction, interaction=interaction)
    context.modal_data = None


def component_id_matches(component_id, test_id):
    match = CUSTOM_ID_REGEX.match(component_id)
    if match:
        return match.group(1) == test_id
    else:
        return component_id == test_id


def inject_custom_ids_to_components(components, component_values):
    """
    Inject user input values into components based on custom_id.

    Args:
        components: The components to update
        component_values: Dictionary mapping custom_id to user input values

    Returns:
        Updated components with injected values
    """

    def _inject_values(comp):
        if isinstance(comp, list):
            for item in comp:
                _inject_values(item)
        elif isinstance(comp, dict):
            if "custom_id" in comp:
                for test_id, value in component_values.items():
                    if component_id_matches(comp["custom_id"], test_id):
                        if comp["type"] in (
                            ComponentType.user_select.value,
                            ComponentType.role_select.value,
                            ComponentType.channel_select.value,
                            ComponentType.mentionable_select.value,
                            ComponentType.checkbox_group.value,
                        ):
                            comp["values"] = value
                        else:
                            comp["value"] = value

            if "components" in comp:
                _inject_values(comp["components"])
            elif "component" in comp:
                _inject_values(comp["component"])

    components_copy = copy.deepcopy(components)
    _inject_values(components_copy)
    return components_copy
