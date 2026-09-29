from collections.abc import Callable

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Bearer token required")

    token = credentials.credentials
    validation_key = settings.supabase_service_role_key or settings.supabase_key

    if not settings.supabase_url or not validation_key:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Supabase authentication is not configured")

    # Validate the exact access token issued by the Supabase project. Calling
    # the Auth user endpoint directly avoids relying on client auth state on
    # the Render server and works with both legacy and current Supabase JWT
    # signing configurations.
    try:
        response = httpx.get(
            f"{settings.supabase_url.rstrip('/')}/auth/v1/user",
            headers={
                "apikey": validation_key,
                "Authorization": f"Bearer {token}",
            },
            timeout=10.0,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Unable to validate Supabase access token") from exc

    if response.status_code in (401, 403):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired access token")

    if response.status_code >= 400:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Supabase authentication service returned an error")

    try:
        user = response.json()
    except ValueError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Invalid response from Supabase authentication service") from exc

    user_id = user.get("id")
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not authenticated")

    return {
        "id": user_id,
        "email": user.get("email"),
        "access_token": token,
    }


def require_role(*roles: str) -> Callable:
    def dependency(user: dict = Depends(get_current_user)) -> dict:
        client = __import__("app.db.database", fromlist=["get_supabase_client"]).get_supabase_client(
            user["access_token"]
        )
        response = client.table("profile_roles").select("role").eq("profile_id", user["id"]).execute()
        found = {row.get("role") for row in (response.data or [])}
        if not found.intersection(roles):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
        user["roles"] = sorted(found)
        return user
    return dependency


def require_any_role(*roles: str) -> Callable:
    return require_role(*roles)


require_admin = require_role("admin")
require_reviewer = require_role("admin", "auditor")
