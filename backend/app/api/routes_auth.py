from fastapi import APIRouter

from app.schemas import AuthStatusOut, QRCodeOut
from app.services.login import login_manager

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/status", response_model=AuthStatusOut)
def status():
    return AuthStatusOut(
        loggedIn=login_manager.logged_in,
        status=login_manager.status,
        error=login_manager.error,
    )


@router.post("/login/qrcode", response_model=QRCodeOut)
async def login_qrcode():
    result = await login_manager.start_qrcode()
    return QRCodeOut(**result)


@router.post("/logout", response_model=AuthStatusOut)
async def logout():
    await login_manager.logout()
    return AuthStatusOut(loggedIn=False, status="idle")
