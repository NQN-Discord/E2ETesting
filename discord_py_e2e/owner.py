from behave import given
from behave.api.async_step import async_run_until_complete


@given("I own the bot")
@async_run_until_complete
async def step_is_owner(context):
    """
    Set the user as the owner of the bot.
    This allows the user to run owner-only commands.
    """
    original_owner_id = await context.evaluator.evaluate(get_owner_id)

    await context.evaluator.evaluate(set_user_as_owner, context.runner_bot.user.id)
    context.add_cleanup(
        lambda: context.loop.run_until_complete(context.evaluator.evaluate(set_user_as_owner, original_owner_id))
    )


def get_owner_id():
    from __main__ import bot

    return bot.owner_id


def set_user_as_owner(user_id):
    from __main__ import bot

    bot.owner_id = user_id
