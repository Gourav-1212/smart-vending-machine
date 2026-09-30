"""Reusable route-level validators. Currently: validating that a
snack_id looks like a real MongoDB ObjectId before the route's actual
logic runs, so a malformed id becomes a clean 404 instead of a raw
crash — usable on any route that takes a snack_id, regardless of
whether it arrives as a path parameter or a field inside the request
body."""

import functools
from typing import Callable, Optional

from bson import ObjectId
from bson.errors import InvalidId

from app.core.exceptions import NotFoundError


def validate_snack_id(param_name: str, attr: Optional[str] = None) -> Callable:
    """
    param_name: the route function's parameter to check.
    attr: if that parameter is a request body object (not the id
    itself), the field on it that holds the actual snack_id.

    Examples:
        @validate_snack_id("snack_id")                — snack_id is a path param
        @validate_snack_id("request", attr="snack_id") — snack_id is request.snack_id
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(**kwargs):
            value = kwargs.get(param_name)
            snack_id = getattr(value, attr) if attr else value

            try:
                ObjectId(snack_id)
            except InvalidId:
                raise NotFoundError(
                    "Snack not found", reason="No snack with that id"
                )

            return func(**kwargs)

        return wrapper

    return decorator