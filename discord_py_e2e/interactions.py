from __future__ import annotations

from typing import TYPE_CHECKING, List
from logging import getLogger

from behave import *
from behave.api.async_step import async_run_until_complete
from discord import Message, Member, File
from discord.abc import GuildChannel

if TYPE_CHECKING:
    from discord.types.message import Message as RawMessage
    from discord.types.interactions import MessageComponentInteraction


log = getLogger(__name__)


async def run_interaction(interaction):
    from __main__ import bot

    task = await bot.rabbit.parse_interaction_create_0(interaction)
    await task


@then("I press a button with custom id '{custom_id}'")
@async_run_until_complete
async def press_button(context, custom_id: str):
    raw_message = context.raw_bot_response
    buttons = get_buttons(raw_message)
    matched = next((button for button in buttons if custom_id in button["custom_id"]), None)
    assert matched is not None, list(get_buttons(raw_message))
    assert not matched.get("disabled", False)
    interaction = build_button_interaction(
        context.nqn_id,
        context.bot_response,
        raw_message,
        matched["custom_id"],
        context.guild.me,
    )
    await context.evaluator.evaluate(run_interaction, interaction=interaction)


@then("there exist buttons")
@async_run_until_complete
async def buttons_exist(context):
    buttons = list(get_buttons(context.raw_bot_response))
    button_map = {}
    log.info("Found custom ids: %s", buttons)

    custom_ids = [row["custom_id"] for row in context.table]
    for button in buttons:
        for cid in custom_ids[:]:
            if cid in button["custom_id"]:
                custom_ids.remove(cid)
                button_map[cid] = button
    if "disabled" in context.table.headings:
        for row in context.table.rows:
            custom_id, disabled = row["custom_id"], row["disabled"]
            assert disabled in ("true", "false")
            disabled = disabled == "true"
            button = button_map[custom_id]
            assert button.get("disabled", False) == disabled

    assert not custom_ids, custom_ids


def get_buttons(raw_message: RawMessage):
    inner_components = (c for ar in raw_message["components"] for c in ar["components"])
    buttons = (c for c in inner_components if c["type"] == 2)
    return buttons


def _build_interaction_base(bot_id: int, channel: GuildChannel, me: Member, interaction_type: int) -> dict:
    """
    Build the base structure for an interaction.

    Args:
        bot_id: The ID of the bot
        channel: The channel where the interaction was triggered
        me: The member submitting the interaction
        interaction_type: The type of interaction

    Returns:
        A base interaction object
    """
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
        "roles": list(me._roles),
        "joined_at": me.joined_at.isoformat(),
    }
    if me._permissions:
        member["permissions"] = me._permissions
    channel_dict = {
        "id": str(channel.id),
        "guild_id": str(channel.guild.id),
        "type": channel.type.value,
        "name": channel.name,
        "nsfw": channel.nsfw,
        "parent_id": str(channel.category_id),
        "last_message_id": None,
        "position": channel.position,
        "rate_limit_per_user": channel.slowmode_delay,
        "permissions": str(channel.permissions_for(me).value),
    }
    if hasattr(channel, "flags"):
        channel_dict["flags"] = channel._flags
    if hasattr(channel, "bitrate"):
        channel_dict["bitrate"] = channel.bitrate
    if hasattr(channel, "user_limit"):
        channel_dict["user_limit"] = channel.user_limit

    return {
        "type": interaction_type,
        "id": str(1),
        "application_id": str(bot_id),
        "attachment_size_limit": 8_000_000,
        "token": "token",
        "version": 1,
        "guild_id": str(channel.guild.id),
        "guild": None,
        "channel_id": str(channel.id),
        "channel": channel_dict,
        "authorizing_integration_owners": {"0": 1},
        "user": user,
        "member": member,
    }


def build_button_interaction(
    bot_id: int, message: Message, raw_message: RawMessage, custom_id: str, me: Member
) -> MessageComponentInteraction:
    """
    Build a button interaction.

    Args:
        bot_id: The ID of the bot
        message: The message that triggered the interaction
        raw_message: The raw message data
        custom_id: The custom ID of the button
        me: The member submitting the interaction

    Returns:
        A button interaction object
    """
    interaction = _build_interaction_base(bot_id, message.channel, me, 3)  # 3 = MessageComponent

    # Add button-specific data
    interaction["data"] = {"component_type": 2, "custom_id": custom_id}
    interaction["message"] = raw_message

    return interaction


def build_modal_interaction(
    bot_id: int, channel: GuildChannel, raw_message: RawMessage, custom_id: str, components: list[dict], me: Member
) -> dict:
    """
    Build a modal submit interaction.

    Args:
        bot_id: The ID of the bot
        channel: The channel where the modal was triggered
        custom_id: The custom ID of the modal
        components: A dictionary of custom_id -> value pairs for the modal components
        me: The member submitting the interaction

    Returns:
        A modal submit interaction object
    """
    interaction = _build_interaction_base(bot_id, channel, me, 5)  # 5 = ModalSubmit

    interaction["data"] = {
        "custom_id": custom_id,
        "components": components,
    }
    interaction["message"] = raw_message

    return interaction


def patch_interaction_handler():
    import uuid, json
    from discord.http import MultipartParameters

    from nqn_common.dpy.components.context.base import InteractionContext
    from nqn_common.dpy.components.context.component import ComponentContext

    from __main__ import bot

    bot._modals = {}

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

    async def defer(self, *, transient: bool = False, ephemeral: bool = False):
        if not self._has_sent_initial:
            return await self.channel.send(content="<Loading...>")

    async def _request(self, initial, message, *, files: List[File] = []):
        if "type" not in message or message["type"] == 4:
            if getattr(self, "_should_edit_next", False):
                self._should_edit_next = False
                if not self.message.flags.ephemeral and (message.get("flags", 0) & 64 != 0):
                    # Ephemeral send on top of regular send
                    params = MultipartParameters(payload=message, multipart=[], files=files)
                    return await self.bot.http.send_message(self.channel.id, params=params)
                else:
                    assert not files
                    return await edit(self, **message)
            else:
                raise AssertionError("Sending?")
        elif message["type"] == 5:
            return
        elif message["type"] == 6:
            self._should_edit_next = True
            return
        elif message["type"] == 9:
            modal_id = str(uuid.uuid4())
            modal_data = message["data"]
            bot._modals[modal_id] = modal_data

            modal_message = (
                f"[MODAL: {modal_id}]\n>>> Data:\n```json\n{json.dumps(modal_data, indent=2, sort_keys=True)}\n```"
            )
            await self.channel.send(modal_message)
            return
        raise AssertionError("Don't know how to patch this yet!", repr(message))

    InteractionContext._request = _request
    InteractionContext.defer = defer
    ComponentContext.edit = edit
