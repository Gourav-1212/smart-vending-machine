"""Product service — everything that reads or changes a product (snack),
whether triggered by a customer or an operator."""

import asyncio
import logging  
from typing import Dict, List

from app.core.config import get_settings
from app.core.exceptions import NotFoundError,InvalidQuantityError
from app.models.snack import Snack
from app.repositories import  snack_repository
from app.websocket import event_publisher

logger = logging.getLogger(__name__)

def list_products() -> List[Snack]:
    return snack_repository.list_all()


def get_product_status(snack_id: str) -> Snack:
    snack = snack_repository.get_by_id(snack_id)
    if snack is None:
        raise NotFoundError("Snack not found", reason="No snack with that id")
    return snack

def add_product(name: str, description: str, price: int, quantity: int) -> Snack:
    if price <= 0:
        raise InvalidQuantityError("Invalid price", reason="Price must be greater than 0")
    if quantity < 0:
        raise InvalidQuantityError("Invalid quantity", reason="Quantity cannot be negative")

    new_product = Snack(
        name=name,
        description=description,
        price=price,
        quantity=quantity,
        sold_out=(quantity == 0),
    )
    return snack_repository.insert(new_product)
def _broadcast_inventory_change(
    snack_id: str, snack_name: str, new_quantity: int, sold_out: bool, crossed_low_stock: bool
) -> None:
    """Same sync-to-async bridge used in purchase_service. A broadcast
    failure here must never fail a restock that already succeeded."""
    try:
        asyncio.run(
            event_publisher.publish_inventory_change(
                snack_id, snack_name, new_quantity, sold_out, crossed_low_stock
            )
        )
    except Exception:
        logger.exception("Failed to broadcast inventory change after restock")


def restock_product(product_id: str, quantity_to_add: int) -> Snack:
    if quantity_to_add <= 0:
        raise InvalidQuantityError(
            "Invalid quantity", reason="Restock quantity must be greater than 0"
        )

    updated_product = snack_repository.restock(product_id, quantity_to_add)
    if updated_product is None:
        raise NotFoundError("Product not found", reason="No product with that id")
    # Restock already succeeded and is saved — broadcasting happens
    # after, same reasoning as the purchase flow: a WebSocket failure
    # must never affect an already-successful operation.
    settings = get_settings()
    crossed_low_stock = updated_product.quantity <= settings.low_stock_threshold
    _broadcast_inventory_change(
        snack_id=product_id,
        snack_name=updated_product.name,
        new_quantity=updated_product.quantity,
        sold_out=updated_product.sold_out,
        crossed_low_stock=crossed_low_stock,
    )

    return updated_product


def get_low_stock_products() -> List[Snack]:
    settings = get_settings()
    return snack_repository.list_low_stock(settings.low_stock_threshold)


