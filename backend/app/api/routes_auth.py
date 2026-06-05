from fastapi import APIRouter

from app.schemas import AuthStatusOut, QRCodeOut

router = APIRouter(prefix="/api/auth", tags=["auth"])

# 简单内存登录态（v1 单用户本地工具）。real 模式应由 Playwright 持久化上下文判断。
_state = {"loggedIn": False}


@router.get("/status", response_model=AuthStatusOut)
def status():
    return AuthStatusOut(loggedIn=_state["loggedIn"])


@router.post("/login/qrcode", response_model=QRCodeOut)
def login_qrcode():
    # 演示环境返回占位二维码数据；real 模式应返回小红书扫码登录二维码。
    return QRCodeOut(qrcode="demo", note="演示环境：扫码登录占位")


@router.post("/login/confirm", response_model=AuthStatusOut)
def login_confirm():
    _state["loggedIn"] = True
    return AuthStatusOut(loggedIn=True)


@router.post("/logout", response_model=AuthStatusOut)
def logout():
    _state["loggedIn"] = False
    return AuthStatusOut(loggedIn=False)
