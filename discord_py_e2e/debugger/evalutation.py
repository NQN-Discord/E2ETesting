import inspect
import asyncio
import sys
from itertools import count
import pickle
import base64
from typing import Callable, Generic, Any

from ._io import DAPClient

request_id = None
b64pickled_args = ""


class EvaluationClient:
    def __init__(self, client: DAPClient):
        self.client = client
        client.add_on_message_handler(self._on_message)
        self._traceback_request_ids = set()
        self._waiters = {}
        self._responses = {}
        self._send_result_src = self._get_src(_send_result)
        self._request_id = count(1)
        self._traceback_handlers = [self._print_traceback]

    def add_traceback_handler(self, handler: Callable[[str], None]):
        self._traceback_handlers.insert(0, handler)

    def remove_traceback_handler(self, handler: Callable[[str], None]):
        self._traceback_handlers.remove(handler)

    async def evaluate[T](self, expression: Callable[[], Generic[T]], /, *args, **kwargs) -> T:
        function_source = self._get_src(expression)
        request_id = next(self._request_id)
        b64pickled_args = base64.b64encode(pickle.dumps((args, kwargs)))
        traceback_request_id = await self.client.evaluate(
            f"{request_id=}\n{b64pickled_args=}\n{self._send_result_src}\n\n@_send_result\n{function_source}"
        )
        self._traceback_request_ids.add(traceback_request_id)
        evaluation = pickle.loads(base64.b64decode(await self._wait_for_message(request_id)))
        if isinstance(evaluation, Exception):
            raise evaluation
        return evaluation

    async def _wait_for_message(self, request_id: int) -> Any:
        event = asyncio.Event()
        self._waiters[request_id] = event
        await event.wait()
        return self._responses.pop(request_id)

    def _get_src(self, fnc: Callable) -> str:
        return inspect.getsource(fnc)

    def _on_message(self, message: dict[str, Any]):
        if message["type"] == "event" and message["event"] == "output":
            output = message["body"]["output"]
            if isinstance(output, dict):
                if (request_id := output.get("_request_id")) in self._waiters:
                    self._responses[request_id] = output["_data"]
                    self._waiters.pop(request_id).set()
            elif message["body"].get("category") == "stdout":
                print(output)
            elif message["body"].get("category") == "stderr":
                self._handle_traceback(output)
        elif message["type"] == "response" and message["request_seq"] in self._traceback_request_ids:
            self._traceback_request_ids.remove(message["request_seq"])
            if not message["success"]:
                self._handle_traceback(message["message"])

    def _handle_traceback(self, message: str):
        for handler in self._traceback_handlers:
            handler(message)

    def _print_traceback(self, message: str):
        print("(Remote traceback:)", file=sys.stderr)
        print(message, file=sys.stderr)


def _send_result(wraps):
    from _pydevd_bundle.pydevd_constants import get_global_debugger
    import pickle, base64, inspect
    from __main__ import bot

    py_db = get_global_debugger()
    args, kwargs = pickle.loads(base64.b64decode(b64pickled_args))
    data = wraps(*args, **kwargs)
    if inspect.isawaitable(data):

        @bot.loop.create_task(data).add_done_callback
        def _cb(future):
            data = future.exception() or future.result()
            cmd = py_db.cmd_factory.make_console_message(
                {"_request_id": request_id, "_data": base64.b64encode(pickle.dumps(data)).decode()}
            )
            py_db.writer.add_command(cmd)

    else:
        cmd = py_db.cmd_factory.make_console_message(
            {"_request_id": request_id, "_data": base64.b64encode(pickle.dumps(data)).decode()}
        )
        py_db.writer.add_command(cmd)
