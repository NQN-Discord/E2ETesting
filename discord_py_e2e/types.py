from __future__ import annotations

from typing import Callable, TYPE_CHECKING

import behave
import parse


from .context import Context

if TYPE_CHECKING:
    from discord.guild import GuildChannel


@parse.with_pattern(r"\w+ channel")
def channel_parser(channel_type: str) -> Callable[[Context], GuildChannel]:
    def _build(context: Context) -> GuildChannel:
        channels = context.guild.channels
    return _build


behave.register_type(channel=channel_parser)
