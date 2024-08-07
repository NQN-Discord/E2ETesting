from .types import *
from .utils import *
from .given_run import *
from .given_channel import *
from .responds_with_message import *
from .setup_rabbitmq import setup_rabbitmq


def before_all(context):
    context.async_cleanup_fns = []
    context.rabbit = context.loop.run_until_complete(setup_rabbitmq(context))

    for cleanup_fn in context.async_cleanup_fns:
        context.add_cleanup(lambda: context.loop.run_until_complete(cleanup_fn(context)))
