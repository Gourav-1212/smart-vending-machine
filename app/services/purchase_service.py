"""Purchase service — validates a purchase, works out change, and runs
the transaction that updates stock, cash float, and records the sale."""

import asyncio
import logging
from typing import Dict, List, Optional

from app.core.config import get_settings
from app.core.exceptions import (
    ChangeNotMakeableError,
    ConcurrencyConflictError,
    InsufficientCashError,
    NotFoundError,
    OutOfStockError,
)
from app.infrastructure.mongo_client import start_transaction
from app.models.sale import Sale
from app.repositories import cash_float_repository, sale_repository, snack_repository
from app.websocket import event_publisher

logger = logging.getLogger(__name__)

def calculate_change(amount_needed: int, available_coins: Dict[int, int]) -> Optional[Dict[int, int]]:
    """Works out the fewest coins/notes that add up to amount_needed,
    using only what's listed in available_coins. Returns None if it
    cannot be made exactly."""
    if amount_needed == 0:
        return {}

    # Turn {denomination: count} into one coin per list entry, so the
    # algorithm below can never use more of a denomination than we have.
    individual_coins = []
    for denomination, count in available_coins.items():
        individual_coins.extend([denomination] * count)

    infinity = float("inf")
    # min_notes_needed[x] = fewest coins needed to make amount x
    min_notes_needed = [infinity] * (amount_needed + 1)
    min_notes_needed[0] = 0
    # last_coin_used[x] = (smaller amount, coin) that led to the best answer for x
    last_coin_used = [None] * (amount_needed + 1)

    for coin in individual_coins:
        for amount in range(amount_needed, coin - 1, -1):
            if min_notes_needed[amount - coin] + 1 < min_notes_needed[amount]:
                min_notes_needed[amount] = min_notes_needed[amount - coin] + 1
                last_coin_used[amount] = (amount - coin, coin)

    if min_notes_needed[amount_needed] == infinity:
        return None

    # Walk backward through last_coin_used to see which coins were picked.
    change_breakdown: Dict[int, int] = {}
    amount = amount_needed
    while amount > 0:
        smaller_amount, coin = last_coin_used[amount]
        change_breakdown[coin] = change_breakdown.get(coin, 0) + 1
        amount = smaller_amount

    return change_breakdown


def split_cash_into_denominations(amount: int, denomination_list: List[int]) -> Dict[int, int]:
    """Breaks the customer's payment into a note/coin breakdown so it can
    be added to the float. The API only receives a total number, not which
    physical notes were inserted, so this picks the fewest notes possible
    — safe here since cash coming IN has no availability limit to respect."""
    breakdown: Dict[int, int] = {}
    amount_left = amount
    for denomination in sorted(denomination_list, reverse=True):
        notes_used = amount_left // denomination
        if notes_used:
            breakdown[denomination] = notes_used
            amount_left -= denomination * notes_used
    return breakdown

def _broadcast_inventory_change(
    snack_id: str, snack_name: str, new_quantity: int, sold_out: bool, crossed_low_stock: bool
) -> None:
    """Bridges our sync service code to the async event publisher. A
    broadcast failure is caught here and never allowed to fail the
    purchase that triggered it."""
    try:
        asyncio.run(
            event_publisher.publish_inventory_change(
                snack_id, snack_name, new_quantity, sold_out, crossed_low_stock
            )
        )
    except Exception:
        logger.exception("Failed to broadcast inventory change after purchase")

def purchase(snack_id: str, cash_amount: int) -> Sale:
    snack = snack_repository.get_by_id(snack_id)
    if snack is None:
        raise NotFoundError("Snack not found", reason="No snack with that id")

    if cash_amount < snack.price:
        raise InsufficientCashError(
            "Insufficient cash",
            reason=f"Price is {snack.price}, received {cash_amount}",
        )

    if snack.quantity <= 0 or snack.sold_out:
        raise OutOfStockError("Out of stock", reason=f"{snack.name} is sold out")

    change_owed = cash_amount - snack.price

    cash_float = cash_float_repository.get()
    change_breakdown = calculate_change(change_owed, cash_float.denominations)
    if change_breakdown is None:
        raise ChangeNotMakeableError(
            "Cannot make exact change",
            reason="Machine cannot make exact change right now",
        )

    settings = get_settings()
    cash_in_breakdown = split_cash_into_denominations(cash_amount, settings.denominations)

    with start_transaction() as session:
        stock_was_decremented = snack_repository.try_decrement_stock(snack_id, session)
        if not stock_was_decremented:
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
            cash_received=cash_amount,
            change_given=change_breakdown,
        )
        completed_sale = sale_repository.insert(new_sale, session=session)
        # Transaction has committed successfully — the sale is real. Now,
        # and only now, tell any connected clients. This runs after the
        # `with` block ends, so a broadcast failure can never roll back
        # or fail an already-successful purchase.
    updated_snack = snack_repository.get_by_id(snack_id)
    settings_threshold = get_settings().low_stock_threshold
    crossed_low_stock = updated_snack.quantity <= settings_threshold
    _broadcast_inventory_change(
        snack_id=snack_id,
        snack_name=updated_snack.name,
        new_quantity=updated_snack.quantity,
        sold_out=updated_snack.sold_out,
        crossed_low_stock=crossed_low_stock,
    )

    return completed_sale
