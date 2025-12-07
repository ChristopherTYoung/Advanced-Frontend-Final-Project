from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse

from services.auth_service import auth_service

router = APIRouter()


@router.get("/api/auth/login")
async def auth_login():
    auth_url = auth_service.get_authorization_url()
    return RedirectResponse(url=auth_url)


@router.get("/api/auth/callback")
async def auth_callback(code: Optional[str] = None, request: Request = None):
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code provided")

    access_token = await auth_service.exchange_code_for_token(code)

    request.session["access_token"] = access_token

    user_info = await auth_service.get_user_info(access_token)

    request.session["user"] = user_info

    return RedirectResponse(url=auth_service.get_frontend_redirect_url(success=True))


@router.get("/api/me")
async def api_me(request: Request):
    user = request.session.get("user")
    if not user:
        return JSONResponse({"user": None})
    return JSONResponse({"user": user})


@router.post("/api/logout")
async def api_logout(request: Request):
    request.session.pop("user", None)
    request.session.pop("access_token", None)
    return JSONResponse({"ok": True})
