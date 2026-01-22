from typing import Any, Callable

import json
import asyncio

CONTENT_LENGTH = "Content-Length:"


class DAPClient:
    def __init__(self, host="127.0.0.1", port=5678):
        self.on_message_handlers = []
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self.seq = 1
        self._pending_requests = {}

    async def initialize(self):
        await self._connect()

        capabilities = {
            "pathFormat": "path",
            "clientID": "vscode",
            "adapterID": "test",
            "supportsVariableType": True,
            "supportsRunInTerminalRequest": True,
            "supportsArgsCanBeInterpretedByShell": True,
            "supportsStartDebuggingRequest": False,
        }
        await self._request("initialize", capabilities)
        await self._request("attach", {"name": "Remote Attach", "redirectOutput": True})
        await self._request("configurationDone")

    def add_on_message_handler(self, handler: Callable[[dict[str, Any]], None]) -> None:
        self.on_message_handlers.append(handler)

    async def evaluate(self, expression: str) -> int:
        return await self._request("evaluate", {"expression": expression})

    async def _connect(self) -> None:
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        # Start the background reading task
        asyncio.create_task(self._listen())

    async def _listen(self) -> None:
        while not self.reader.at_eof():
            header_data = await self.reader.readuntil(b"\r\n\r\n")
            content_length = 0
            for line in header_data.decode().split("\r\n"):
                if line.startswith(CONTENT_LENGTH):
                    content_length = int(line.removeprefix(CONTENT_LENGTH).strip())

            body_data = await self.reader.readexactly(content_length)
            message = json.loads(body_data.decode("utf-8"))
            self._handle_message(message)

    def _handle_message(self, message):
        for handler in self.on_message_handlers:
            handler(message)

    async def _request(self, command: str, arguments=None) -> int:
        payload = {"command": command, "arguments": arguments or {}, "type": "request", "seq": self.seq}
        body = json.dumps(payload).encode()
        header = f"Content-Length: {len(body)}\r\n\r\n".encode()

        self.writer.write(header + body)
        await self.writer.drain()

        current_seq = self.seq
        self.seq += 1
        return current_seq
