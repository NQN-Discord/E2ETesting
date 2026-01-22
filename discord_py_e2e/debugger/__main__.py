import asyncio

from discord import TeamMember
from discord_py_e2e.debugger.connection import connect_to_nqn


def _get_bot_owner() -> TeamMember:
    from __main__ import bot

    return bot.owner


async def main():
    evaluator = await connect_to_nqn()
    owner = await evaluator.evaluate(_get_bot_owner)
    print({slot: getattr(owner, slot) for slot in owner.__slots__})


if __name__ == "__main__":
    asyncio.run(main())
