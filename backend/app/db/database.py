from supabase import Client, create_client

from app.core.config import settings


supabase: Client | None = (
    create_client(settings.supabase_url, settings.supabase_key)
    if settings.supabase_url and settings.supabase_key
    else None
)


def get_supabase_client(access_token: str | None = None) -> Client:
    if not settings.supabase_url or not settings.supabase_key:
        raise RuntimeError("Supabase is not configured")
    client = create_client(settings.supabase_url, settings.supabase_key)
    if access_token:
        client.postgrest.auth(access_token)
    return client


def get_trusted_supabase_client() -> Client:
    """Return the backend-only client used for tables without public RLS writes."""
    key = settings.supabase_service_role_key or settings.supabase_key
    if not settings.supabase_url or not key:
        raise RuntimeError("Supabase trusted backend credentials are not configured")
    return create_client(settings.supabase_url, key)