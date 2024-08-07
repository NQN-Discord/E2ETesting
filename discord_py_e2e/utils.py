from datetime import datetime

from discord.utils import time_snowflake


def generate_snowflake() -> int:
    return time_snowflake(datetime.now())
