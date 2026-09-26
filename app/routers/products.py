"""Products router — handles GET /products, GET /status/{id}, and
GET /low-stock. Delegates everything to product_service."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.models.snack import Snack
from app.services import machine_config_serviceg, product_service
from app.schemas.pagination import PaginatedResponse, get_pagination
from app.core.route_validators import validate_snack_id
from app.schemas.snack import SnackMinimal, SnackDetailed
from app.schemas.purchase import PurchaseRequest, PurchaseResponse
from app.core.security import require_api_key

from app.schemas.snack import (
    AddSnackRequest,
    RestockRequest
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["products"])


@router.post("/add-snacks", response_model=Snack, dependencies=[Depends(require_api_key)])
def add_snack(request: AddSnackRequest) -> Snack:
    """Creates and inserts a brand new snack item into the product catalog."""
    logger.info("Adding new snack: %s", request.name)

    result = product_service.add_product(request)

    logger.info("Product successfully created.")
    return result


@router.patch("/snacks/{snack_id}/restock", response_model=Snack, dependencies=[Depends(require_api_key)])
@validate_snack_id("snack_id")
def restock_snack(snack_id: str, request: RestockRequest) -> Snack:
    """Increases the current inventory quantity for an existing snack item."""
    logger.info("Processing product inventory restock for ID: %s", snack_id)
    live_threshold = machine_config_serviceg.get_low_stock_threshold()  
    result = product_service.restock_product(snack_id, request, threshold=live_threshold)
    logger.info("Product inventory restock completed.")
    return result


@router.get("/products", response_model=PaginatedResponse[SnackMinimal])
def get_products(
    name: Optional[str] = Query(default=None, description="Filter by name (partial match)"),
    sold_out: Optional[bool] = Query(default=None, description="Filter by sold-out status"),
    pagination: tuple = Depends(get_pagination),
) -> PaginatedResponse[SnackMinimal]:
    """Retrieves a paginated list of products, optionally filtered by name or stock status."""
    page, page_size, _ = pagination
    logger.info("Executing product catalog query for page %d.", page)
    
    result = product_service.list_products(
        name=name,
        sold_out=sold_out,
        page=page,
        page_size=page_size,
    )
    logger.info("Product catalog query completed.")
    return result


@router.get("/products/{snack_id}", response_model=SnackDetailed)
@validate_snack_id("snack_id")
def get_status(snack_id: str) -> Snack:
    """Retrieves full information and stock status details for a single snack item."""
    logger.info("Retrieving product status for ID: %s", snack_id)

    result = product_service.get_product(snack_id)

    logger.info("Product status retrieved successfully.")
    return result


@router.post("/purchase-snack", response_model=PurchaseResponse)
@validate_snack_id("request", attr="snack_id")
def make_purchase(request: PurchaseRequest) -> PurchaseResponse:
    """Handles dispensing a snack by validating cash input, deducting stock, and returning change."""
    logger.info("Processing purchase transaction for product ID: %s", request.snack_id)
    
    live_threshold = machine_config_serviceg.get_low_stock_threshold()
    sale = product_service.purchase(
        snack_id=request.snack_id, 
        cash_amount=request.cash_amount, 
        threshold=live_threshold,
        quantity=request.quantity
    )
    
    logger.info("Purchase transaction completed successfully.")
    return PurchaseResponse(
        snack_id=sale.snack_id,
        snack_name=sale.snack_name_at_sale,
        quantity=sale.quantity,
        unit_price=sale.unit_price_at_sale,
        total_cost=sale.total_amount,
        cash_received=sale.cash_received,
        change_given=sale.change_given,
    )


@router.get("/low-stock", response_model=PaginatedResponse[Snack], dependencies=[Depends(require_api_key)])
def get_low_stock(
    name: Optional[str] = Query(default=None, description="Filter by name (partial match)"),
    pagination: tuple = Depends(get_pagination),
) -> PaginatedResponse[Snack]:
    """Retrieves a paginated list of all products currently running below the low stock threshold limit."""
    page, page_size, _ = pagination
    logger.info("Executing low-stock warning check.")
    
    live_threshold = machine_config_serviceg.get_low_stock_threshold()
    result = product_service.get_low_stock_products(
        threshold=live_threshold,
        name=name, 
        page=page, 
        page_size=page_size
    )
    
    logger.info("Low-stock warning check completed.")
    return result
