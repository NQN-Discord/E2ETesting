import asyncio
import os
from discord import Intents, Client


async def setup_bot():
    bot_token = os.environ["RUNNER_TOKEN"]
    intents = Intents.default()
    intents.message_content = True
    bot = Client(intents=intents)
    await bot.login(token=bot_token)
    asyncio.create_task(bot.connect())
    await bot.wait_until_ready()
    return bot


async def setup_manager():
    bot_token = os.environ["MANAGER_TOKEN"]
    intents = Intents.default()
    intents.members = True
    bot = Client(intents=intents)
    await bot.login(token=bot_token)
    asyncio.create_task(bot.connect())
    await bot.wait_until_ready()
    return bot


async def reset_bot_config(guild_id: int):
    from __main__ import bot

    guild = bot.get_guild(guild_id)
    await guild.all()

    # Reset guild settings to defaults.
    guild_settings = bot.global_ctx.guild_settings.default_settings(guild)
    await guild_settings.save()
