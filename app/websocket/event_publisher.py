"""Event publisher — the one place business logic goes to announce an
inventory change. Services call this; they never touch the connection
manager directly."""

import logging

from app.websocket.connection_manager import connection_manager

logger = logging.getLogger(__name__)


async def publish_inventory_change(
    snack_id: str,
    snack_name: str,
    new_quantity: int,
    sold_out: bool,
    crossed_low_stock: bool,
) -> None:
    message = {
        "event": "inventory_change",
        "snack_id": snack_id,
        "snack_name": snack_name,
        "quantity": new_quantity,
        "sold_out": sold_out,
        "crossed_low_stock": crossed_low_stock,
    }
    await connection_manager.broadcast(message)
