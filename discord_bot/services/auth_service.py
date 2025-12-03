import os
from typing import Optional, Dict, Any
from urllib.parse import urlencode
import httpx
from fastapi import HTTPException


class AuthService:
    def __init__(self):
        self.client_id = os.environ.get("VITE_DISCORD_CLIENT_ID")
        self.client_secret = os.environ.get("VITE_DISCORD_CLIENT_SECRET")
        self.redirect_uri = os.environ.get("DISCORD_REDIRECT_URI", "http://localhost:8000/api/auth/callback")
        self.scope = os.environ.get("DISCORD_SCOPE", "identify email guilds")
        self.frontend_origin = os.environ.get("FRONTEND_ORIGINS", "http://localhost:5173").split(",")[0].strip()

    def get_authorization_url(self) -> str:
        if not self.client_id:
            raise HTTPException(status_code=500, detail="Discord client id not configured")

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": self.scope,
            "prompt": "consent",
        }

        return f"https://discord.com/api/oauth2/authorize?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> str:
        if not self.client_id or not self.client_secret:
            raise HTTPException(status_code=500, detail="Discord client id/secret not configured")

        token_url = "https://discord.com/api/oauth2/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        async with httpx.AsyncClient() as client:
            try:
                token_resp = await client.post(token_url, data=data, headers=headers, timeout=10.0)
            except httpx.HTTPError as exc:
                raise HTTPException(status_code=502, detail=f"Error contacting Discord token endpoint: {exc}")

        if token_resp.status_code != 200:
            detail = token_resp.text
            raise HTTPException(status_code=400, detail=f"Token exchange failed: {detail}")

        token_json = token_resp.json()
        access_token = token_json.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="No access_token returned from Discord")

        return access_token

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                me_resp = await client.get(
                    "https://discord.com/api/users/@me",
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10.0,
                )
            except httpx.HTTPError as exc:
                raise HTTPException(status_code=502, detail=f"Error fetching user from Discord: {exc}")

        if me_resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Failed to fetch user: {me_resp.text}")

        user = me_resp.json()

        return {
            "id": user.get("id"),
            "username": user.get("username"),
            "discriminator": user.get("discriminator"),
            "avatar": user.get("avatar"),
            "email": user.get("email") if "email" in user else None,
        }

    async def get_user_guilds(self, access_token: str) -> list:
        async with httpx.AsyncClient() as client:
            try:
                guilds_resp = await client.get(
                    "https://discord.com/api/users/@me/guilds",
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10.0,
                )
            except httpx.HTTPError as exc:
                raise HTTPException(status_code=502, detail=f"Error fetching guilds from Discord: {exc}")

        if guilds_resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Failed to fetch guilds: {guilds_resp.text}")

        return guilds_resp.json()

    def get_frontend_redirect_url(self, success: bool = True) -> str:
        if success:
            return f"{self.frontend_origin}/?auth=success"
        else:
            return f"{self.frontend_origin}/?auth=error"


auth_service = AuthService()
