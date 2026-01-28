import asyncio
from behave import given
from behave.api.async_step import async_run_until_complete

from discord import Emoji
from discord_py_e2e import Context, Args


async def _verify_emoji_exists(emote_id: int) -> bool:
    from __main__ import bot

    async with bot.postgres() as pg:
        emote_hash = await pg.get_emote_hash(emote_id)
        return emote_hash is not None


@given("{emoji:arg} exists in the emote_ids table")
@async_run_until_complete
async def step_arg_emote(context: Context, emoji: Args[Emoji]):
    emoji = emoji(context)
    for retries in range(5):
        exists = await context.evaluator.evaluate(_verify_emoji_exists, emote_id=emoji.id)
        if exists:
            return
        if retries != 4:
            await asyncio.sleep(1)
    raise AssertionError(f"Emoji {emoji} does not exist in the database after 5 retries")
