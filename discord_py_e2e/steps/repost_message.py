from behave import given
from behave.api.async_step import async_run_until_complete

from discord_py_e2e.context import Context
from discord_py_e2e import Args


async def _create_webhook_message(guild_id, channel_id, user, content):
    from __main__ import bot
    from nqn_common.audit_log import add_log

    guild = bot.get_guild(guild_id)
    await guild.all()
    channel = guild.get_channel(channel_id)
    message = await bot.global_ctx.webhooks.send_webhook(
        channel,
        content=content,
        username=user.display_name,
        avatar_url=user.display_avatar.url,
    )

    await add_log(
        bot.global_ctx,
        message,
        user,
    )
    return message.id


async def create_webhook_message(context, user, content):
    message_id = await context.evaluator.evaluate(
        _create_webhook_message,
        context.guild.id,
        context.channel.id,
        user,
        content,
    )

    message = next((m for m in context.runner_bot.cached_messages if m.id == message_id), None)
    if message is None:
        message = await context.runner_bot.wait_for("message", check=lambda m: m.id == message_id, timeout=5)
    return message


@given("I have reposted a message {content:args} as {{{message_var}}}")
@async_run_until_complete
async def step_repost_message(context: Context, content: Args[str], message_var: str):
    """
    Creates a message with an emoji through NQN's webhook system.
    This simulates a user posting a message with an emoji that gets reposted by NQN.
    """
    content = content(context)
    message = await create_webhook_message(context, context.runner_bot.user, content)

    # Store the message in the context
    context.args[message_var] = message


@given("another user has reposted a message {content:args} as {{{message_var}}}")
@async_run_until_complete
async def step_other_user_repost_message(context: Context, content: Args[str], message_var: str):
    """
    Creates a message with an emoji through NQN's webhook system, but from another user.
    """
    content = content(context)

    message = await create_webhook_message(context, context.manager_bot.user, content)
    context.args[message_var] = message
