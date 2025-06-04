from behave import *
from behave.api.async_step import async_run_until_complete


@then('the bot response contains "{text}"')
@async_run_until_complete
async def step_bot_response_contains(context, text):
    assert (
        context.bot_response is not None
    ), "No bot response found. Make sure 'the bot responds with a message' step was executed before this step."

    # Check if the message content contains the specified text
    if context.bot_response.content and text in context.bot_response.content:
        return

    # If not in content, check if it's in embeds or components
    if context.raw_bot_response:
        raw_content = str(context.raw_bot_response)
        assert (
            text.lower() in raw_content.lower()
        ), f"Expected text '{text}' not found in bot response content: '{context.bot_response.content}' or raw data: '{raw_content}'"
    else:
        raise AssertionError(
            f"Expected text '{text}' not found in bot response: '{context.bot_response.content}' and no raw data available"
        )


@then('the bot response equals "{text}"')
@async_run_until_complete
async def step_bot_response_equals(context, text):
    assert (
        context.bot_response is not None
    ), "No bot response found. Make sure 'the bot responds with a message' step was executed before this step."

    # Check if the message content equals the specified text
    assert (
        context.bot_response.content == text
    ), f"Bot response '{context.bot_response.content}' does not equal expected text '{text}'"


@then("the bot response matches the table")
@async_run_until_complete
async def step_bot_response_matches_table(context):
    assert (
        context.bot_response is not None
    ), "No bot response found. Make sure 'the bot responds with a message' step was executed before this step."

    # Check if the message content contains all the texts in the table
    for row in context.table:
        text = row["text"]
        if text in context.bot_response.content:
            continue

        # If not in content, check if it's in embeds or components
        if context.raw_bot_response:
            raw_content = str(context.raw_bot_response)
            assert (
                text.lower() in raw_content.lower()
            ), f"Expected text '{text}' not found in bot response content: '{context.bot_response.content}' or raw data: '{raw_content}'"
        else:
            raise AssertionError(
                f"Expected text '{text}' not found in bot response: '{context.bot_response.content}' and no raw data available"
            )
