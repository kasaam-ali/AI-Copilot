"""Shared FastAPI dependencies."""

import secrets

from fastapi import Header, HTTPException, status

from app.config import get_settings


def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Guard mutating routes with a static API key.

    Full authentication and role-based access control are deferred (see plan Phase 8).
    """
    settings = get_settings()
    expected = settings.app_api_key
    if x_api_key is None or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )
