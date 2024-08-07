import asyncio
import os
from discord import Intents, Client


async def setup_bot(context):
    bot_token = os.environ[f"RUNNER_TOKEN"]
    intents = Intents.default()
    intents.messages = True
    context.runner_bots = bot = Client(intents=intents)
    await bot.login(token=bot_token)
    asyncio.create_task(bot.connect())
