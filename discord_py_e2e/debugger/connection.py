import asyncio

import psutil
from debugpy.server.cli import attach_to_pid, options

from discord_py_e2e.debugger.evalutation import EvaluationClient
from ._io import DAPClient


def _get_nqn_pid() -> int:
    for proc in psutil.process_iter(["pid", "name", "exe"]):
        if proc.info["name"] == "python.exe" and "uv" in proc.exe():
            script = proc.cmdline()[-1]
            if "NQNBackend" in script and script.endswith("main.py"):
                return proc.pid
    raise RuntimeError("Could not find NQNBackend process")


def _attach_to_process(pid, address):
    options.target = pid
    options.mode = "listen"
    options.address = address
    attach_to_pid()


def _build_state(state_type):
    return state_type(dispatch=None, handlers={}, hooks={}, http=None)


def _enable_pickling():
    import copyreg
    from discord.client import ConnectionState
    from discord.shard import AutoShardedConnectionState
    from discord import enums
    from discord.enums import Enum

    from discord_py_e2e.debugger.connection import _build_state

    for enum in enums.__all__:
        enum_type = getattr(enums, enum)
        if enum_type is not Enum:
            enum_value_type = enum_type._enum_value_cls_
            setattr(enums, enum_value_type.__name__, enum_value_type)

    for state_type in (ConnectionState, AutoShardedConnectionState):
        copyreg.pickle(state_type, lambda state: (_build_state, (type(state),), {}))


async def connect_to_nqn(nqn_pid: int | None = None) -> EvaluationClient:
    _enable_pickling()
    address = ("127.0.0.1", 5678)

    client = DAPClient(*address)
    try:
        await client.initialize()
    except ConnectionRefusedError:
        nqn_pid = nqn_pid or _get_nqn_pid()
        _attach_to_process(nqn_pid, address)
        for i in range(10):
            print("Attempting to connect to NQNBackend - connection", i + 1, "of 10")
            try:
                await client.initialize()
            except ConnectionRefusedError:
                await asyncio.sleep(1)
            else:
                break
        else:
            raise

    evaluator = EvaluationClient(client)
    await evaluator.evaluate(_enable_pickling)
    return evaluator
