from collections.abc import Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import create_client

from app.core.config import settings


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Bearer token required")
    token = credentials.credentials

    try:
        # Dedicated client for validating the user's JWT.
        # Do not reuse the global database client here.
        auth_client = create_client(
            settings.supabase_url,
            settings.supabase_key,
        )

        response = auth_client.auth.get_user(token)

    except Exception as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired access token") from exc

    if not response.user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not authenticated")

    return {
        "id": response.user.id,
        "email": response.user.email,
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