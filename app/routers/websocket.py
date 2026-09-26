"""WebSocket router — handles persistent streaming connections for tracking inventory updates in real time."""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services import product_service
from app.websocket.connection_manager import connection_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/inventory")
async def inventory_socket(websocket: WebSocket) -> None:
    """Manages the lifecycle of a real-time inventory monitoring stream connection.

    Accepts incoming client connections, transmits a comprehensive baseline 
    snapshot of the current inventory state, and maintains an open pipeline 
    to listen for client disconnect signals.
    """
    logger.info("New WebSocket client attempting connection.")
    await connection_manager.connect(websocket)
    logger.info("WebSocket connection established successfully.")

    try:
        current_snacks = product_service.list_all_products()
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
        logger.info("Transmitting initial state snapshot to client.")
        await connection_manager.send_to_one(websocket, current_state)
        logger.info("Initial state snapshot successfully transmitted.")

        while True:
            # Keep the connection open and listen for data from the client
            await websocket.receive_text()

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        logger.info("WebSocket connection closed cleanly by client disconnect.")
