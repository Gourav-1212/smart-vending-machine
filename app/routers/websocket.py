"""WebSocket router — the /ws/inventory endpoint. A client connects here,
immediately receives the current full state, then stays open to receive
future inventory_change events pushed by event_publisher."""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services import product_service
from app.websocket.connection_manager import connection_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/inventory")
async def inventory_socket(websocket: WebSocket) -> None:
    await connection_manager.connect(websocket)

    try:
        
        current_snacks = product_service.list_products()
        current_state = {
            "event": "initial_state",
            "snacks": [
                {
                    "snack_id": snack.id,
                    "snack_name": snack.name,
                    "quantity": snack.quantity,
                    "sold_out": snack.sold_out,
                }
                for snack in current_snacks
            ],
        }
        await connection_manager.send_to_one(websocket, current_state)

        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)

