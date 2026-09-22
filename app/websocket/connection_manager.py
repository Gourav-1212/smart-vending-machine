"""Connection manager — keeps track of every connected WebSocket client
and broadcasts messages to all of them. One client failing to receive a
message never affects the others."""

import logging
from typing import List

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket client connected (%d active)", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info("WebSocket client disconnected (%d active)", len(self.active_connections))

    async def send_to_one(self, websocket: WebSocket, message: dict) -> None:
        await websocket.send_json(message)

    async def broadcast(self, message: dict) -> None:
        """Sends message to every connected client. A client whose send
        fails is dropped from the list — it does not stop the message
        from reaching everyone else, and it never raises back to whoever
        called broadcast (e.g. the purchase flow)."""
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                logger.info("Dropping a WebSocket client that failed to receive a broadcast")
                dead_connections.append(connection)

        for connection in dead_connections:
            self.disconnect(connection)


# One shared instance for the whole app — every module that needs to
# broadcast or manage connections imports this same object.
connection_manager = ConnectionManager()
