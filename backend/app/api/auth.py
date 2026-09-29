from fastapi import APIRouter, Depends
from app.core.security import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/me", summary="Return the authenticated user's identity")
def me(user: dict = Depends(get_current_user)):
    return {"id": user["id"], "email": user.get("email")}
