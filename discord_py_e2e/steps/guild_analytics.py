import asyncio

from behave import *
from behave.api.async_step import async_run_until_complete

from discord_py_e2e import Args


@then("the bot has saved analytics with event {event:args} and command name {command_name:args}")
@async_run_until_complete
async def step_bot_response_contains(context, event: Args[str], command_name: Args[str]):
    event = event(context)
    command_name = command_name(context)

    analytics = await get_guild_analytics(context)
    assert analytics is not None, analytics

    assert analytics.event.value == event, analytics
    assert analytics.command_name == command_name, analytics


@then("the bot has no more analytics saved")
@async_run_until_complete
async def step_bot_response_contains(context):
    analytics = await get_guild_analytics(context)
    assert analytics is None


async def get_guild_analytics(context):
    for i in range(10):
        analytics = await context.evaluator.evaluate(_get_guild_analytics)
        if analytics is not None:
            return analytics
        await asyncio.sleep(0.1)
    return None


def _get_guild_analytics():
    from __main__ import bot
    if bot._guild_analytics:
        return bot._guild_analytics.pop()
    else:
        return None


def patch_guild_analytics_handler():
    from sql_helper.mixins.guild_analytics import GuildAnalyticsMixin
    from __main__ import bot

    bot._guild_analytics = []

    async def _set_guild_analytics_item(self, item):
        bot._guild_analytics.append(item)

    GuildAnalyticsMixin.write_guild_analytics_item = _set_guild_analytics_item
