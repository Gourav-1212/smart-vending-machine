"""Products router — handles GET /products, GET /status/{id}, and
GET /low-stock. Delegates everything to product_service."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.models.snack import Snack
from app.services import product_service
from app.schemas.pagination import PaginatedResponse, get_pagination
from app.core.route_validators import validate_snack_id
from app.schemas.snack.snack_request import AddSnackRequest,RestockRequest
from app.schemas.snack.snack_response import SnackDetailed,SnackMinimal
from app.schemas.purchase import PurchaseRequest, PurchaseResponse
from app.core.security import require_api_key

from app.schemas.snack.snack_request import (
    AddSnackRequest,
    RestockRequest
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["products"])


@router.post("/add-snack", response_model=SnackDetailed, dependencies=[Depends(require_api_key)])
def add_snack(request: AddSnackRequest) -> Snack:
    """Creates and inserts a brand new snack item into the product catalog."""
    logger.info("Adding new snack: %s", request.name)

    result = product_service.add_product(request)

    logger.info("Product successfully created.")
    return result


@router.patch("/snack/{snack_id}/restock", response_model=SnackDetailed, dependencies=[Depends(require_api_key)])
@validate_snack_id("snack_id")
def restock_snack(snack_id: str, request: RestockRequest) -> Snack:
    """Increases the current inventory quantity for an existing snack item."""
    logger.info("Processing product inventory restock for ID: %s", snack_id) 
    result = product_service.restock_product(snack_id, request)
    logger.info("Product inventory restock completed.")
    return result


@router.get("/products", response_model=PaginatedResponse[SnackMinimal])
def get_products(
    name: Optional[str] = Query(
        default=None,
        min_length=1,
        max_length=100,
        pattern=r"^.*\S.*$",
        description="Filter by name (partial match, non-empty)",
        error_messages={"string_pattern_mismatch": "The name can't be space only"},
    ),
    sold_out: Optional[bool] = Query(default=None, description="Filter by sold-out status"),
    pagination: tuple = Depends(get_pagination),
) -> PaginatedResponse[SnackMinimal]:
    """Retrieves a paginated list of products, optionally filtered by name or stock status."""
    page, page_size, _ = pagination
    logger.info("Executing product catalog query for page %d.", page)
    clean_name = name.strip() if name else None
    
    result = product_service.list_products(
        name=clean_name,
        sold_out=sold_out,
        page=page,
        page_size=page_size,
    )
    logger.info("Product catalog query completed.")
    return result


@router.get("/product/{snack_id}", response_model=SnackDetailed)
@validate_snack_id("snack_id")
def get_product_details(snack_id: str) -> Snack:
    """Retrieves full information and stock status details for a single snack item."""
    logger.info("Retrieving product status for ID: %s", snack_id)

    result = product_service.get_product_details(snack_id)

    logger.info("Product status retrieved successfully.")
    return result


@router.post("/purchase-snack", response_model=PurchaseResponse)
@validate_snack_id("request", attr="snack_id")
def make_purchase(request: PurchaseRequest) -> PurchaseResponse:
    """Handles dispensing a snack by validating cash input, deducting stock, and returning change."""
    logger.info("Processing purchase transaction for product ID: %s", request.snack_id)
    return product_service.purchase(
        snack_id= request.snack_id,
        cash_amount=request.cash_amount,
        quantity=request.quantity,
    )


@router.get("/low-stock", response_model=PaginatedResponse[SnackDetailed], dependencies=[Depends(require_api_key)])
def get_low_stock(
    name: Optional[str] = Query(
        default=None, 
        min_length=1,
        max_length=100,
        pattern=r"^.*\S.*$",
        description="Filter by name (partial match, non-empty)"
    ),
    pagination: tuple = Depends(get_pagination),
) -> PaginatedResponse[SnackDetailed]:
    """Retrieves a paginated list of all products currently running below the low stock threshold limit."""
    page, page_size, _ = pagination
    logger.info("Executing low-stock warning check.")
    return product_service.get_low_stock_products(
        name=name,
        page=page,
        page_size=page_size,
    )