"""App-wide exception types and their FastAPI error handlers"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class VendingMachineError(Exception):
    status_code: int = 500

    def __init__(self, message: str, reason: str | None = None):
        self.message = message
        self.reason = reason or message
        super().__init__(message)


class ValidationError(VendingMachineError):
    status_code = 422


class BusinessRuleError(VendingMachineError):
    status_code = 400


class InsufficientCashError(BusinessRuleError):
    pass


class OutOfStockError(BusinessRuleError):
    pass


class ChangeNotMakeableError(BusinessRuleError):
    pass


class InvalidQuantityError(BusinessRuleError):
    pass


class NotFoundError(VendingMachineError):
    status_code = 404


class ConcurrencyConflictError(BusinessRuleError):
    status_code = 400


class AuthenticationError(VendingMachineError):
    status_code = 401


class InfrastructureError(VendingMachineError):
    status_code = 503


class TrinoUnavailableError(InfrastructureError):
    pass


class DatabaseUnavailableError(InfrastructureError):
    pass


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(VendingMachineError)
    async def handle_vending_machine_error(request: Request, exc: VendingMachineError) -> JSONResponse:
        if exc.status_code >= 500:
            logger.exception("Infrastructure error on %s", request.url.path)
        else:
            logger.info("Business error on %s: %s", request.url.path, exc.reason)

        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message, "reason": exc.reason},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={"error": "internal_server_error", "reason": "Something went wrong. Please try again."},
        )
