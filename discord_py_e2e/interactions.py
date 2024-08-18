from __future__ import annotations

from typing import TYPE_CHECKING, List
from logging import getLogger

from behave import *
from behave.api.async_step import async_run_until_complete
from discord import Message, Member, File
from nqn_common.dpy.components.context.base import InteractionContext
from nqn_common.dpy.components.context.component import ComponentContext

if TYPE_CHECKING:
    from discord.types.message import Message as RawMessage
    from discord.types.interactions import MessageComponentInteraction


log = getLogger(__name__)


@then("I press button with custom id '{custom_id}'")
@async_run_until_complete
async def press_button(context, custom_id: str):
    raw_message = context.raw_bot_response
    buttons = get_buttons(raw_message)
    matched = next((button for button in buttons if custom_id in button["custom_id"]), None)
    assert matched is not None, list(get_buttons(raw_message))
    assert not matched.get("disabled", False)
    interaction = build_button_interaction(context.bot.user.id, context.bot_response, raw_message, matched["custom_id"], context.guild.me)
    task = await context.bot.rabbit.parse_interaction_create_0(interaction)
    await task


@then("there exist buttons with custom ids")
@async_run_until_complete
async def buttons_exist(context):
    button_custom_ids = [b["custom_id"] for b in get_buttons(context.raw_bot_response)]
    log.info("Found custom ids: %s", button_custom_ids)

    custom_ids = [row["custom_id"] for row in context.table]
    for custom_id in button_custom_ids:
        for cid in custom_ids[:]:
            if cid in custom_id:
                custom_ids.remove(cid)
    assert not custom_ids, custom_ids


def get_buttons(raw_message: RawMessage):
    inner_components = (c for ar in raw_message["components"] for c in ar["components"])
    buttons = (c for c in inner_components if c["type"] == 2)
    return buttons


def build_button_interaction(bot_id: int, message: Message, raw_message: RawMessage, custom_id: str, me: Member) -> MessageComponentInteraction:
    user = {
        "id": me.id,
        "username": me.name,
        "discriminator": me.discriminator,
        "avatar": me._avatar,
        "global_name": me.global_name,
        "bot": me.bot,
        "system": me.system,
        "mfa_enabled": False,
        "flags": me._flags,
        "public_flags": me._flags,
    }
    member = {
        "avatar": me._avatar,
        "user": user,
        "nick": me.nick,
        "premium_since": None,
        "pending": False,
        "communication_disabled_until": me.timed_out_until and me.timed_out_until.isoformat(),
        "roles": me._roles,
        "joined_at": me.joined_at.isoformat(),
    }
    if me._permissions:
        member["permissions"] = me._permissions
    channel = {
        "id": message.channel.id,
        "type": message.channel.type.value,
        "name": message.channel.name,
        "nsfw": message.channel.nsfw,
        "parent_id": message.channel.category_id,
        "last_message_id": None,
        "position": message.channel.position,
        "slowmode_delay": message.channel.slowmode_delay,
        "permission_overwrites": [o._asdict() for o in message.channel._overwrites]
    }
    if hasattr(message.channel, "bitrate"):
        channel["bitrate"] = message.channel.bitrate
    if hasattr(message.channel, "user_limit"):
        channel["user_limit"] = message.channel.user_limit

    return {
        "type": 3,
        "id": 1,
        "application_id": bot_id,
        "token": "token",
        "version": 1,
        "guild_id": message.guild.id,
        "guild": None,
        "channel_id": message.channel.id,
        "channel": channel,
        "authorizing_integration_owners": {"0": 1},
        "data": {
            "component_type": 2,
            "custom_id": custom_id
        },
        "message": raw_message,
        "user": user,
        "member": member
    }


def patch_interaction_handler():
    async def edit(self, content: str = None, *, message_id=None, **fields):
        if message_id is None:
            message_id = self.message.id
        if "embed" in fields and "embeds" in fields:
            embed = fields.pop("embed")
            if embed is not None:
                fields["embeds"] = [embed]

        channel = self.message.channel
        msg = channel.get_partial_message(message_id)
        await msg.edit(content=content, **fields)

    async def _request(self, initial, message, *, files: List[File] = []):
        if "type" not in message or message["type"] == 4:
            if getattr(self, "_should_edit_next", False):
                self._should_edit_next = False
                await edit(content=message["content"], files=files, **message)
            else:
                raise AssertionError("Sending?")
        elif message["type"] == 5:
            return
        elif message["type"] == 6:
            self._should_edit_next = True
            return
        raise AssertionError("Don't know how to patch this yet!")

    InteractionContext._request = _request
    ComponentContext.edit = edit
