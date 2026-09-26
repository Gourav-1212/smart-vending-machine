"""Product service — handles catalog searching, product management, stock replenishment, and checkout transactions."""

import asyncio
import logging  
from typing import List, Optional, Dict

from app.core.exceptions import NotFoundError, InvalidQuantityError
from app.models.snack import Snack
from app.websocket import event_publisher
from app.repositories import snack_repository, trino_snack_repository, cash_float_repository, sale_repository
from app.schemas.pagination import PaginatedResponse
from app.schemas.snack import AddSnackRequest, RestockRequest
from app.core.config import get_settings

from app.infrastructure.mongo_client import start_transaction
from app.models.sale import Sale

from app.core.exceptions import (
    ChangeNotMakeableError,
    ConcurrencyConflictError,
    InsufficientCashError,
    NotFoundError,
    OutOfStockError,
)

logger = logging.getLogger(__name__)

def list_products(
    name: Optional[str] = None,
    sold_out: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResponse[Snack]:
    """Retrieves a paginated list of snacks based on search filters like name and stock availability."""
    logger.debug("Searching products list with pagination filters.")
    offset = (page - 1) * page_size
    items = trino_snack_repository.list_all(
        name=name, sold_out=sold_out, limit=page_size, offset=offset
    )
    total = trino_snack_repository.count_all(name=name, sold_out=sold_out)
    return PaginatedResponse(
        items=items,
        page=page,
        page_size=page_size,
        total_items=total
    )


def list_all_products() -> List[Snack]:
    """Fetches every product in the catalog without pagination. 
    
    This is for internal background updates only (e.g., live WebSocket sync).
    """
    logger.debug("Fetching all products in database for internal snapshot.")
    return trino_snack_repository.list_all()


def get_product(snack_id: str) -> Snack:
    """Finds and returns a single product using its unique ID."""
    logger.debug("Fetching single product by ID: %s", snack_id)
    snack = trino_snack_repository.get_by_id(snack_id)
    if snack is None:
        raise NotFoundError("Snack not found", reason="No snack with that id")
    return snack


def add_product(request: AddSnackRequest) -> Snack:
    """Saves a new snack item to the database after verifying that the name is unique."""
    logger.info("Checking if product name already exists before adding.")
    existing = snack_repository.get_by_name(request.name)
    if existing is not None:
        raise InvalidQuantityError(
            "Snack already exists",
            reason=f"A snack named '{request.name}' already exists — use restock instead",
        )

    new_product = Snack(
        name=request.name,
        description=request.description,
        price=request.price,
        quantity=request.quantity,
        sold_out=(request.quantity == 0),
    )
    result = snack_repository.insert(new_product)
    logger.info("Successfully added new product to database.")
    return result


def _broadcast_inventory_change(
    snack_id: str, snack_name: str, new_quantity: int, sold_out: bool, crossed_low_stock: bool
) -> None:
    """Sends immediate inventory adjustment updates to connected live streaming clients."""
    try:
        logger.debug("Sending updated inventory details to live WebSocket channel.")
        asyncio.run(
            event_publisher.publish_inventory_change(
                snack_id, snack_name, new_quantity, sold_out, crossed_low_stock
            )
        )
    except Exception:
        logger.exception("Failed to send inventory update alert via WebSocket.")


def restock_product(product_id: str, request: RestockRequest, threshold: int) -> Snack:
    """Increases the current inventory level of a specific snack item and pushes live updates."""
    logger.info("Adding new stock quantities for product ID: %s", product_id)
    updated_product = snack_repository.restock(product_id, request.quantity)
    if updated_product is None:
        raise NotFoundError("Product not found", reason="No product with that id")
    
    crossed_low_stock = updated_product.quantity <= threshold
    if crossed_low_stock:
        logger.warning("Product restocked, but total count is still below low stock alert limit.")
    
    _broadcast_inventory_change(
        snack_id=product_id,
        snack_name=updated_product.name,
        new_quantity=updated_product.quantity,
        sold_out=updated_product.sold_out,
        crossed_low_stock=crossed_low_stock,
    )

    logger.info("Product restock finished successfully.")
    return updated_product


def get_low_stock_products(
    threshold: int, name: Optional[str] = None, page: int = 1, page_size: int = 20
) -> PaginatedResponse[Snack]:
    """Finds all products whose current quantities have fallen below the warning limit."""
    logger.debug("Fetching items running lower than threshold boundary limit: %d", threshold)
    offset = (page - 1) * page_size
    items = snack_repository.list_low_stock(
        threshold, name=name, limit=page_size, offset=offset
    )
    total = snack_repository.count_low_stock(threshold, name=name)
    return PaginatedResponse(
        items=items,
        page=page,
        page_size=page_size,
        total_items=total
    )


def calculate_change(amount_needed: int, available_coins: Dict[int, int]) -> Optional[Dict[int, int]]:
    """Determines the fewest physical coins and notes needed to make exact change from current vault contents."""
    logger.debug("Calculating fewest coins possible to return exact change value.")
    if amount_needed == 0:
        return {}
    individual_coins = []
    for denomination, count in available_coins.items():
        individual_coins.extend([denomination] * count)

    infinity = float("inf")
    min_notes_needed = [infinity] * (amount_needed + 1)
    min_notes_needed[0] = 0
    last_coin_used = [None] * (amount_needed + 1)

    for coin in individual_coins:
        for amount in range(amount_needed, coin - 1, -1):
            if min_notes_needed[amount - coin] + 1 < min_notes_needed[amount]:
                min_notes_needed[amount] = min_notes_needed[amount - coin] + 1
                last_coin_used[amount] = (amount - coin, coin)

    if min_notes_needed[amount_needed] == infinity:
        logger.warning("Cannot find a matching combination of coins to make exact change.")
        return None
    
    change_breakdown: Dict[int, int] = {}
    amount = amount_needed
    while amount > 0:
        smaller_amount, coin = last_coin_used[amount]
        change_breakdown[coin] = change_breakdown.get(coin, 0) + 1
        amount = smaller_amount

    return change_breakdown


def split_cash_into_denominations(amount: int, denomination_list: List[int]) -> Dict[int, int]:
    """Calculates the currency breakdown of incoming payments into individual coin/note buckets."""
    logger.debug("Splitting total customer cash intake into individual denominations breakdown.")
    breakdown: Dict[int, int] = {}
    amount_left = amount
    for denomination in sorted(denomination_list, reverse=True):
        notes_used = amount_left // denomination
        if notes_used:
            breakdown[denomination] = notes_used
            amount_left -= denomination * notes_used
    return breakdown


def purchase(snack_id: str, cash_amount: int, threshold: int, quantity: int = 1) -> Sale:
    """Processes a user checkout lifecycle by validating funds, reserving inventory, and calculating change inside a transaction."""
    logger.info("Starting checks to validate purchase request availability parameters.")
    snack = snack_repository.get_by_id(snack_id)
    if snack is None:
        raise NotFoundError("Snack not found", reason="No snack with that id")

    total_price = snack.price * quantity

    if cash_amount < total_price:
        raise InsufficientCashError(
            "Insufficient cash",
            reason=f"Price is {snack.price}, received {cash_amount}",
        )

    if snack.quantity < quantity or snack.sold_out:
        raise OutOfStockError("Out of stock", reason=f"{snack.name} is sold out")

    change_owed = cash_amount - total_price

    cash_float = cash_float_repository.get()
    change_breakdown = calculate_change(change_owed, cash_float.denominations)
    if change_breakdown is None:
        raise ChangeNotMakeableError(
            "Cannot make exact change",
            reason="Machine cannot make exact change right now",
        )

    settings = get_settings()
    cash_in_breakdown = split_cash_into_denominations(cash_amount, settings.denominations)

    logger.info("Validation passed. Opening database transaction to record purchase sale details.")
    with start_transaction() as session:
        stock_was_decremented = snack_repository.try_decrement_stock(snack_id, quantity, session)
        if not stock_was_decremented:
            logger.warning("Another checkout session completed first. Stock item just sold out.")
            raise ConcurrencyConflictError(
                "Out of stock", reason=f"{snack.name} just sold out"
            )

        float_changes: Dict[int, int] = {}
        for denomination, count in cash_in_breakdown.items():
            float_changes[denomination] = float_changes.get(denomination, 0) + count
        for denomination, count in change_breakdown.items():
            float_changes[denomination] = float_changes.get(denomination, 0) - count
        
        cash_float_repository.update_cash_inventory(float_changes, session=session)

        new_sale = Sale(
            snack_id=snack_id,
            snack_name_at_sale=snack.name,
            unit_price_at_sale=snack.price,
            quantity=quantity,
            total_amount=total_price,
            cash_received=cash_amount,
            change_given=change_breakdown,
        )
