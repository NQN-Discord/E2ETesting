from behave import then
from behave.api.async_step import async_run_until_complete

from discord import TextChannel
from discord_py_e2e import Args
from nqn_common import GuildSettings


async def get_guild_settings(guild_id: int) -> GuildSettings:
    from __main__ import bot

    guild = bot.get_guild(guild_id)
    await guild.all()

    guild_settings = await bot.global_ctx.guild_settings.get_settings(guild)
    return guild_settings


@then("the bot's prefix is now {expected_prefix:args}")
@async_run_until_complete
async def step_bot_response_contains(context, expected_prefix: Args[str]):
    expected_prefix = expected_prefix(context)

    guild_settings = await context.evaluator.evaluate(get_guild_settings, context.guild.id)

    assert (
        guild_settings.prefix == expected_prefix
    ), f"Expected prefix {expected_prefix!r}, got {guild_settings.prefix!r}"


@then("the bot's audit channel is now unset")
@async_run_until_complete
async def step_bot_audit_channel_is_set(context):
    guild_settings = await context.evaluator.evaluate(get_guild_settings, context.guild.id)
    assert guild_settings.audit_channel is None


@then("the bot's audit channel is now {channel:arg}")
@async_run_until_complete
async def step_bot_audit_channel_is_set(context, channel: Args[TextChannel]):
    channel = channel(context)

    guild_settings = await context.evaluator.evaluate(get_guild_settings, context.guild.id)
    assert guild_settings.audit_channel == channel.id
