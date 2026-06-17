from fastapi import APIRouter, Depends, HTTPException

from t_alpha.api.auth import create_admin_token, get_current_admin_user
from t_alpha.api.deps import get_settings
from t_alpha.api.schemas import AdminUser, LoginRequest, LoginResponse
from t_alpha.config import Settings


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, settings: Settings = Depends(get_settings)):
    if request.username != settings.admin_username or request.password != settings.admin_password:
        raise HTTPException(status_code=401, detail="invalid username or password")
    return LoginResponse(
        access_token=create_admin_token(request.username, settings),
        user=AdminUser(username=request.username),
    )


@router.get("/me", response_model=AdminUser)
def me(username: str = Depends(get_current_admin_user)):
    return AdminUser(username=username)


@router.post("/logout")
def logout(username: str = Depends(get_current_admin_user)):
    return {"status": "ok", "username": username}
