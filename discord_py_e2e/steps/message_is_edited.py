from behave import *
from behave.api.async_step import async_run_until_complete


@then("the message is edited")
@async_run_until_complete
async def step_message_is_edited(context):
    def _check(_, after):
        return after.id == context.bot_response.id

    previous_step, current_step = context.message_edit_times[-2:]
    if current_step == previous_step:
        await context.runner_bot.wait_for("message_edit", check=_check, timeout=3)
        current_step = context.message_edit_times[-1] = context.bot_response.edited_at

    if previous_step is None:
        assert current_step is not None
    else:
        assert current_step > previous_step
