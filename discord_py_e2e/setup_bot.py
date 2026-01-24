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
