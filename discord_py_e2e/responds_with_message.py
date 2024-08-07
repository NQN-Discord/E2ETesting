from behave import *
from behave.api.async_step import async_run_until_complete


@then("the bot responds with a message")
@async_run_until_complete
async def step_bot_responds(context):
    print("Respond check")
