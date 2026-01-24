from behave import *
from behave.api.async_step import async_run_until_complete

from discord_py_e2e.context import Context


async def _set_permissions(context: Context, target_member, permissions_str: str, channel):
    """
    Helper function to set permissions for a member in a channel.

    Args:
        context: The behave context
        target_member: The member to set permissions for
        permissions_str: Comma-separated list of permissions, each in quotes
        channel: The channel to set permissions in
    """
    permission_list = [p.strip(" \"'") for p in permissions_str.split(",")]

    manager_channel = context.manager_bot.get_channel(channel.id)
    permissions_dict = {permission: True for permission in permission_list}

    # Update the channel's permission overwrites for the target member
    await manager_channel.set_permissions(target_member, **permissions_dict)


@given("I have permissions {permissions}")
@async_run_until_complete
async def step_have_permissions(context: Context, permissions: str):
    """
    Give the user specific permissions in the current channel.

    The permissions parameter should be a comma-separated list of permission names,
    each enclosed in double quotes.

    Example: Given I have permissions "manage_messages", "read_message_history"
    """
    # Get the runner bot as a member
    runner_member = context.manager_bot.get_guild(context.guild.id).get_member(context.runner_bot.user.id)

    # Set the permissions in the current channel
    await _set_permissions(context, runner_member, permissions, context.channel)


@given("I have permission {permission}")
@async_run_until_complete
async def step_have_permission(context: Context, permission: str):
    """
    Give the user a specific permission in the current channel.
    """
    await step_have_permissions(context, permission)


@given("the bot has permissions {permissions}")
@async_run_until_complete
async def step_bot_has_permissions(context: Context, permissions: str):
    """
    Give the bot specific permissions in the current channel.

    The permissions parameter should be a comma-separated list of permission names,
    each enclosed in double quotes.

    Example: Given the bot has permissions "manage_messages", "read_message_history"
    """
    # Get the NQN bot as a member
    nqn_member = context.manager_bot.get_guild(context.guild.id).get_member(context.nqn_id)

    # Set the permissions in the current channel
    await _set_permissions(context, nqn_member, permissions, context.channel)


@given("the bot has permission {permission}")
@async_run_until_complete
async def step_bot_has_permission(context: Context, permission: str):
    """
    Give the bot a specific permission in the current channel.
    """
    await step_bot_has_permissions(context, permission)


@given("in channel {{{channel_name}}} I have permissions {permissions}")
@async_run_until_complete
async def step_have_permissions_in_channel(context: Context, channel_name: str, permissions: str):
    """
    Give the user specific permissions in a specific channel.

    The permissions parameter should be a comma-separated list of permission names,
    each enclosed in double quotes.

    Example: Given in channel {channel} I have permissions "manage_messages", "read_message_history"
    """
    # Get the channel from context.args
    target_channel = context.args[channel_name]

    # Get the runner bot as a member
    runner_member = context.manager_bot.get_guild(context.guild.id).get_member(context.runner_bot.user.id)

    # Set the permissions
    await _set_permissions(context, runner_member, permissions, target_channel)


@given("in channel {{{channel_name}}} I have permission {permission}")
@async_run_until_complete
async def step_have_permission_in_channel(context: Context, channel_name: str, permission: str):
    """
    Give the user a specific permission in a specific channel.
    """
    await step_have_permissions_in_channel(context, channel_name, permission)


@given("in channel {{{channel_name}}} the bot has permissions {permissions}")
@async_run_until_complete
async def step_bot_has_permissions_in_channel(context: Context, channel_name: str, permissions: str):
    """
    Give the bot specific permissions in a specific channel.

    The permissions parameter should be a comma-separated list of permission names,
    each enclosed in double quotes.

    Example: Given in channel {channel} the bot has permissions "manage_messages", "read_message_history"
    """
    # Get the channel from context.args
    target_channel = context.args[channel_name]

    # Get the NQN bot as a member
    nqn_member = context.manager_bot.get_guild(context.guild.id).get_member(context.nqn_id)

    # Set the permissions
    await _set_permissions(context, nqn_member, permissions, target_channel)


@given("in channel {{{channel_name}}} the bot has permission {permission}")
@async_run_until_complete
async def step_bot_has_permission_in_channel(context: Context, channel_name: str, permission: str):
    """
    Give the bot a specific permission in a specific channel.
    """
    await step_bot_has_permissions_in_channel(context, channel_name, permission)
