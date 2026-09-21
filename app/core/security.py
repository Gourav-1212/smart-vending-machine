"""API key check for operator/admin routes."""

from fastapi import Header

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError


def require_api_key(x_api_key: str = Header(default=None)) -> None:
    settings = get_settings()
    if x_api_key is None or x_api_key != settings.operator_api_key:
        raise AuthenticationError(
            "Invalid API key", reason="Missing or incorrect API key"
        )
