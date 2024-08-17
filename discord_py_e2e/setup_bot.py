import asyncio
import os
from discord import Intents, Client


async def setup_bot():
    bot_token = os.environ[f"RUNNER_TOKEN"]
    intents = Intents.default()
    intents.messages = True
    bot = Client(intents=intents)
    await bot.login(token=bot_token)
    asyncio.create_task(bot.connect())
    await bot.wait_until_ready()
    return bot
