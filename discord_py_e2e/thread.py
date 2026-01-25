from __future__ import annotations

from behave import *
from behave.api.async_step import async_run_until_complete
from discord import Thread, TextChannel, ForumChannel, ChannelType

from discord_py_e2e.context import Context


async def _get_thread(context: Context, thread_type: str) -> Thread:
    channel_obj = context.manager_bot.get_guild(context.guild.id).get_channel(context.channel.id)

    # Ensure the channel is a text channel or forum channel that can have threads
    assert isinstance(channel_obj, (TextChannel, ForumChannel)), f"Channel {channel_obj.name} does not support threads"

    thread_type_enum = ChannelType.public_thread if thread_type.lower() == "public" else ChannelType.private_thread

    # Check for existing threads in the channel of the specified type
    existing_threads = [t for t in channel_obj.threads if t.type == thread_type_enum]

    thread_obj = None

    # Try to find an existing thread of the correct type
    if existing_threads:
        # Use the first available thread of the correct type
        thread_obj = existing_threads[0]

        # If the thread is archived, unarchive it
        if thread_obj.archived:
            # Use the edit method to unarchive the thread
            await thread_obj.edit(archived=False)

    # If no existing thread was found or could be unarchived, create a new one
    if thread_obj is None:
        if isinstance(channel_obj, ForumChannel):
            assert thread_type_enum == ChannelType.public_thread, "Forums cannot have private threads"
            thread_obj = await channel_obj.create_thread(
                name=f"{thread_type} thread",
                content="Thread for testing",
            )
        else:
            # For text channels, create a thread of the specified type
            thread_obj = await channel_obj.create_thread(
                name=f"{thread_type} thread",
                type=thread_type_enum,
            )

    return await context.runner_bot.fetch_channel(thread_obj.id)


@then("a new thread is created in {{{channel}}} as {{{thread}}}")
@async_run_until_complete
async def step_thread_created(context: Context, channel: str, thread: str):
    """
    Check if a new thread has been created in the specified channel and store it in context.args.

    Args:
        context: The behave context
        channel: The name of the channel variable in context.args
        thread: The name to store the thread under in context.args
    """
    channel_obj = context.args.get(channel)
    assert channel_obj is not None, f"No channel found with name '{channel}' in context.args"

    # Ensure the channel is a forum channel or a text channel that can have threads
    assert hasattr(channel_obj, "threads"), f"Channel {channel} does not support threads"

    # Get the reference timestamp from bot_response or command_message
    reference_message = context.bot_response or context.command_message

    assert reference_message is not None, "No reference message found to compare thread creation time"

    threads = channel_obj.threads

    assert threads, f"No threads found in channel {channel}"

    # Sort threads by creation time (newest first)
    threads_sorted = sorted(threads, key=lambda t: t.id, reverse=True)

    # Find the newest thread that was created after the reference message
    newest_thread = next((t for t in threads_sorted if t.id > reference_message.id), None)

    assert newest_thread is not None, f"No thread found in channel {channel} created after the command/response"

    # Store the thread in context.args
    context.args[thread] = newest_thread


@then("{{{thread}}} has the title '{title}'")
@async_run_until_complete
async def step_thread_has_title(context: Context, thread: str, title: str):
    """
    Check if a thread has the specified title.

    Args:
        context: The behave context
        thread: The name of the thread variable in context.args
        title: The expected title of the thread
    """
    thread_obj = context.args.get(thread)
    assert thread_obj is not None, f"No thread found with name '{thread}' in context.args"

    assert thread_obj.name == title, f"Thread title '{thread_obj.name}' does not match expected title '{title}'"
