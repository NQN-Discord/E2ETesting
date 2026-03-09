from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, List, Callable, Any
from logging import getLogger

from behave import *
from behave.api.async_step import async_run_until_complete
from discord import Message, Member, File, User
from discord.abc import GuildChannel

from ..context import Context

if TYPE_CHECKING:
    from discord.types.message import Message as RawMessage
    from discord.types.interactions import MessageComponentInteraction


log = getLogger(__name__)


async def run_interaction(interaction):
    from __main__ import bot

    task = await bot.rabbit.parse_interaction_create_0(interaction)
    await task


@then("I press a button with custom id {custom_id:args}")
@async_run_until_complete
async def press_button_custom_id(context: Context, custom_id: Callable[[Context], str]):
    custom_id = custom_id(context)
    await _press_button(context, lambda button: custom_id in button["custom_id"])


@then("I press a button with label {label:args}")
@async_run_until_complete
async def press_button_label(context: Context, label: Callable[[Context], str]):
    label = label(context)
    await _press_button(context, lambda button: label in button["label"])


@then("I choose the option labelled {label:args} in the select with custom id {custom_id:args}")
@async_run_until_complete
async def choose_select_option_label_custom_id(
    context: Context, label: Callable[[Context], str], custom_id: Callable[[Context], str]
):
    label = label(context)
    custom_id = custom_id(context)
    await _choose_select_option(
        context,
        lambda select: f".{custom_id}." in select["custom_id"],
        lambda option: label in option["label"],
    )


async def _press_button(context: Context, check: Callable[[Any], bool]):
    raw_message = context.raw_bot_response
    buttons = get_buttons(raw_message)
    matched = next((button for button in buttons if "custom_id" in button and check(button)), None)
    assert matched is not None, list(get_buttons(raw_message))
    assert not matched.get("disabled", False)
    interaction = build_button_interaction(
        context.manager_bot.get_guild(context.guild.id).get_member(context.nqn_id),
        context.bot_response,
        raw_message,
        matched["custom_id"],
        context.guild.me,
    )
    await context.evaluator.evaluate(run_interaction, interaction=interaction)


async def _choose_select_option(
    context: Context,
    select_check: Callable[[Any], bool],
    option_check: Callable[[Any], bool],
):
    raw_message = context.raw_bot_response
    selects = get_selects(raw_message)
    matched_select = next((select for select in selects if select_check(select)), None)
    assert matched_select is not None, list(get_selects(raw_message))
    assert not matched_select.get("disabled", False)

    options = matched_select.get("options", [])
    matched_option = next((option for option in options if option_check(option)), None)
    assert matched_option is not None, options

    interaction = build_select_interaction(
        context.manager_bot.get_guild(context.guild.id).get_member(context.nqn_id),
        context.bot_response,
        raw_message,
        matched_select["custom_id"],
        [matched_option["value"]],
        context.guild.me,
    )
    await context.evaluator.evaluate(run_interaction, interaction=interaction)


@then("there exist buttons")
@async_run_until_complete
async def buttons_exist(context: Context):
    buttons = list(get_buttons(context.raw_bot_response))
    button_map = {}
    log.info("Found custom ids: %s", buttons)

    custom_ids = [row["custom_id"] for row in context.table]
    for button in buttons:
        for cid in custom_ids[:]:
            if cid in button.get("custom_id", ()):
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


@then("there are no buttons in the message")
@async_run_until_complete
async def no_buttons_exist(context: Context):
    buttons = list(get_buttons(context.raw_bot_response))
    assert len(buttons) == 0, f"Expected no buttons, but found: {buttons}"


@given('I use the context menu "{menu_name}" on {{{message_var}}}')
@async_run_until_complete
async def step_use_context_menu(context: Context, menu_name: str, message_var: str):
    """
    Uses a context menu on a message.
    This simulates right-clicking on a message and selecting a context menu option.
    """
    # Get the target message
    message = context.args[message_var]

    # Build the context menu interaction
    interaction = build_context_menu_interaction(
        context.manager_bot.get_guild(context.guild.id).get_member(context.nqn_id),
        message,
        menu_name,
        context.guild.me,
    )

    # Send the interaction to the bot
    await context.evaluator.evaluate(run_interaction, interaction=interaction)


def get_buttons(raw_message: RawMessage):
    buttons = (c for c in  deep_iter_components(raw_message["components"]) if c["type"] == 2)
    return buttons


def get_selects(raw_message: RawMessage):
    selects = (c for c in deep_iter_components(raw_message["components"]) if c["type"] == 3)
    return selects


def _serialise_user(user: User) -> dict:
    serialised = {
        "id": user.id,
        "username": user.name,
        "discriminator": user.discriminator,
        "avatar": user._avatar,
        "global_name": user.global_name,
        "bot": user.bot,
        "system": user.system,
        "mfa_enabled": False,
    }
    if hasattr(user, "_flags"):
        serialised |= {
            "flags": user._flags,
            "public_flags": user._flags,
        }
    return serialised


def _serialise_member(member: Member) -> dict:
    serialised = {
        "avatar": member._avatar,
        "banner": None,
        "collectibles": None,
        "communication_disabled_until": member.timed_out_until and member.timed_out_until.isoformat(),
        "display_name_styles": None,
        "flags": 0,
        "joined_at": member.joined_at.isoformat(),
        "mute": False,
        "nick": member.nick,
        "pending": member.pending,
        "permissions": str(member.guild_permissions.value),
        "premium_since": None,
        "roles": list(member._roles),
        "user": _serialise_user(member),
    }
    if member._permissions:
        serialised["permissions"] = member._permissions
    return serialised


def _serialise_message(message: Message) -> dict:
    serialised = {
        "id": str(message.id),
        "channel_id": str(message.channel.id),
        "author": _serialise_user(message.author),
        "content": message.content,
        "timestamp": message.created_at.isoformat(),
        "edited_timestamp": message.edited_at.isoformat() if message.edited_at else None,
        "mention_everyone": message.mention_everyone,
        "mentions": [],
        "mention_roles": [],
        "attachments": [],
        "embeds": [],
        "pinned": message.pinned,
        "tts": message.tts,
        "type": message.type.value,
    }
    if message.webhook_id:
        serialised["webhook_id"] = message.webhook_id
    return serialised


def _serialise_channel(channel: GuildChannel, me: Member) -> dict:
    channel_dict = {
        "flags": 0,
        "id": str(channel.id),
        "guild_id": str(channel.guild.id),
        "name": channel.name,
        "nsfw": channel.nsfw,
        "parent_id": str(channel.category_id),
        "last_message_id": None,
        "position": channel.position,
        "rate_limit_per_user": channel.slowmode_delay,
        "permissions": str(channel.permissions_for(me).value),
        "type": channel.type.value,
    }
    if hasattr(channel, "_flags"):
        channel_dict["flags"] = channel._flags
    if hasattr(channel, "bitrate"):
        channel_dict["bitrate"] = channel.bitrate
    if hasattr(channel, "user_limit"):
        channel_dict["user_limit"] = channel.user_limit
    if hasattr(channel, "topic"):
        channel_dict["topic"] = channel.topic
    return channel_dict


def _build_interaction_base(bot: Member, channel: GuildChannel, me: Member, interaction_type: int) -> dict:
    """
    Build the base structure for an interaction.

    Args:
        bot: The member of the bot
        channel: The channel where the interaction was triggered
        me: The member submitting the interaction
        interaction_type: The type of interaction

    Returns:
        A base interaction object
    """
    member = _serialise_member(me)
    channel_dict = _serialise_channel(channel, me)

    return {
        "type": interaction_type,
        "id": "1",
        "application_id": str(bot.id),
        "app_permissions": str(channel.permissions_for(bot).value),
        "attachment_size_limit": 8_000_000,
        "context": 0,
        "token": "token",
        "version": 1,
        "guild_id": str(channel.guild.id),
        "guild": None,
        "channel_id": str(channel.id),
        "channel": channel_dict,
        "authorizing_integration_owners": {"0": 1},
        "member": member,
    }


def build_button_interaction(
    bot: Member, message: Message, raw_message: RawMessage, custom_id: str, me: Member
) -> MessageComponentInteraction:
    """
    Build a button interaction.

    Args:
        bot: The bot's member
        message: The message that triggered the interaction
        raw_message: The raw message data
        custom_id: The custom ID of the button
        me: The member submitting the interaction

    Returns:
        A button interaction object
    """
    interaction = _build_interaction_base(bot, message.channel, me, 3)  # 3 = MessageComponent

    # Add button-specific data
    interaction["data"] = {"component_type": 2, "custom_id": custom_id}
    interaction["message"] = raw_message

    return interaction


def build_select_interaction(
    bot: Member,
    message: Message,
    raw_message: RawMessage,
    custom_id: str,
    values: list[str],
    me: Member,
) -> MessageComponentInteraction:
    """
    Build a select interaction.

    Args:
        bot: The bot's member
        message: The message that triggered the interaction
        raw_message: The raw message data
        custom_id: The custom ID of the select menu
        values: The values selected
        me: The member submitting the interaction

    Returns:
        A select interaction object
    """
    interaction = _build_interaction_base(bot, message.channel, me, 3)  # 3 = MessageComponent

    # Add select-specific data
    interaction["data"] = {
        "component_type": 3,
        "custom_id": custom_id,
        "values": values,
    }
    interaction["message"] = raw_message

    return interaction


def build_modal_interaction(
    *,
    bot: Member,
    channel: GuildChannel,
    custom_id: str,
    components: list[dict],
    me: Member,
    message: Message,
    to_resolve = None,
) -> dict:
    """
    Build a modal submit interaction.

    Args:
        bot: The bot's member
        channel: The channel which triggered the modal
        custom_id: The custom ID of the modal
        components: A dictionary of custom_id -> value pairs for the modal components
        me: The member submitting the interaction

    Returns:
        A modal submit interaction object
    """
    interaction = _build_interaction_base(bot, channel, me, 5)  # 5 = ModalSubmit

    interaction["data"] = {
        "custom_id": custom_id,
        "components": components,
    }
    if isinstance(message, Message):
        interaction["message"] = _serialise_message(message)
    if to_resolve is not None:
        interaction["data"]["resolved"] = _get_resolved_data(to_resolve)

    return interaction


def build_context_menu_interaction(bot: Member, message: Message, menu_name: str, me: Member) -> dict:
    """
    Build a context menu interaction.

    Args:
        bot: The bot's member
        message: The message that triggered the interaction
        menu_name: The name of the context menu
        me: The member submitting the interaction

    Returns:
        A context menu interaction object
    """
    interaction = _build_interaction_base(bot, message.channel, me, 2)  # 2 = ApplicationCommand

    # Add context menu specific data
    interaction["data"] = {
        "name": menu_name,
        "type": 3,  # 3 = MESSAGE type context menu
        "target_id": str(message.id),
        "resolved": {"messages": {str(message.id): _serialise_message(message)}},
    }

    return interaction


def patch_interaction_handler():
    import uuid, json, discord
    from io import BytesIO
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
        fields.pop("transient", None)

        channel = self.message.channel
        msg = channel.get_partial_message(message_id)
        await msg.edit(content=content, **fields)

    async def defer(self, *, transient: bool = False, ephemeral: bool = False):
        if not self._has_sent_initial:
            return await self.channel.send(content="<Loading...>")

    async def _request(self, initial, message, *, files: List[File] = []):
        if "type" not in message or message["type"] == 4:
            if getattr(self, "_should_edit_next", False) or initial:
                self._should_edit_next = False
                if not self.message.flags.ephemeral and (message.get("flags", 0) & 64 != 0):
                    # Ephemeral send on top of regular send
                    params = MultipartParameters(payload=message, multipart=[], files=files)
                    return await self.bot.http.send_message(self.channel.id, params=params)
                else:
                    assert not files
                    assert self.message.author.id == bot.user.id
                    return await edit(self, **message)
            else:
                assert self.message.author.id == bot.user.id
                params = MultipartParameters(payload=message, multipart=[], files=files)
                return await self._state.http.send_message(self.channel.id, params=params)
        elif message["type"] == 5:
            return
        elif message["type"] == 6:
            self._should_edit_next = True
            return
        elif message["type"] == 9:
            modal_id = str(uuid.uuid4())

            modal_data = message["data"]
            bot._modals[modal_id] = {
                "data": modal_data,
                "channel_id": self.channel.id,
                "message": self.message,
            }

            modal_message = f"[MODAL: {modal_id}]"
            dumped_data = json.dumps(modal_data, indent=2, sort_keys=True)
            await self.channel.send(
                modal_message, files=[discord.File(BytesIO(dumped_data.encode("utf-8")), filename="modal.json")]
            )
            return
        raise AssertionError("Don't know how to patch this yet!", repr(message))

    InteractionContext._request = _request
    InteractionContext.defer = defer
    ComponentContext.edit = edit


def _get_resolved_data(resolved_objects: list):
    resolved_data = defaultdict(dict)
    for resolved_object in resolved_objects:
        _add_resolved_data(resolved_data, resolved_object)
    return dict(resolved_data)


def _add_resolved_data[T](resolved_data: defaultdict[str, dict[str, Any]], param: T):
    resolved_data[_get_resolved_type(type(param))][str(param.id)] = _get_serialiser(type(param))(param)

def _get_serialiser(cls):
    serialisers = {
        GuildChannel: lambda channel: _serialise_channel(channel, channel.guild.me)
    }

    for base in cls.mro():
        if base in serialisers:
            return serialisers[base]
    raise ValueError(f"No serialiser found for class {cls}")


def _get_resolved_type(cls) -> str:
    types = {
        GuildChannel: "channels"
    }
    for base in cls.mro():
        if base in types:
            return types[base]
    raise ValueError(f"No serialiser found for class {cls}")


def deep_iter_components(comp):
    if isinstance(comp, list):
        for item in comp:
            yield from deep_iter_components(item)
    elif isinstance(comp, dict):
        yield comp

        if "components" in comp:
            yield from deep_iter_components(comp["components"])
        elif "component" in comp:
            yield from deep_iter_components(comp["component"])
