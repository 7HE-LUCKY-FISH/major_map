from fastapi import APIRouter, Response

# Simplified/stubbed auth endpoints so the router can be imported
# without requiring the full DB/session/security stack.
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(payload: dict):
    """Stubbed register endpoint. Returns basic echo of provided fields."""
    return {"email": payload.get("email"), "full_name": payload.get("full_name")}


@router.post("/login")
async def login(resp: Response, payload: dict):
    """Stubbed login: sets a mock httpOnly cookie and returns mock tokens."""
    access = "mock_access_token"
    refresh = "mock_refresh_token"
    resp.set_cookie(key="access_token", value=access, httponly=True)
    return {"access_token": access, "refresh_token": refresh}


@router.post("/logout")
async def logout(resp: Response):
    resp.delete_cookie("access_token")
    return {"ok": True}