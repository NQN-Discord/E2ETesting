from __future__ import annotations

from behave import *
from behave.api.async_step import async_run_until_complete

from discord_py_e2e.context import Context


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
