import os
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
import httpx


app = FastAPI()

DISCORD_CLIENT_ID = os.environ.get('VITE_DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = os.environ.get('VITE_DISCORD_CLIENT_SECRET')
SESSION_SECRET = os.environ.get('DISCORD_SESSION_SECRET', 'dev-secret-change-me')
FRONTEND_ORIGINS = os.environ.get('FRONTEND_ORIGINS', 'http://localhost:5173')

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in FRONTEND_ORIGINS.split(',') if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)


class CodeExchange(BaseModel):
    code: str
    redirect_uri: Optional[str]


@app.get('/')
async def read_root():
    return {"hello": "world"}


@app.post('/api/auth/discord')
async def auth_discord(payload: CodeExchange, request: Request):
    if not DISCORD_CLIENT_ID or not DISCORD_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail='Discord client id/secret not configured')

    token_url = 'https://discord.com/api/oauth2/token'
    data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': payload.code,
        'redirect_uri': payload.redirect_uri or '',
    }

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    async with httpx.AsyncClient() as client:
        try:
            token_resp = await client.post(token_url, data=data, headers=headers, timeout=10.0)
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f'Error contacting Discord token endpoint: {exc}')

    if token_resp.status_code != 200:
        detail = token_resp.text
        raise HTTPException(status_code=400, detail=f'Token exchange failed: {detail}')

    token_json = token_resp.json()
    access_token = token_json.get('access_token')
    if not access_token:
        raise HTTPException(status_code=400, detail='No access_token returned from Discord')

    async with httpx.AsyncClient() as client:
        try:
            me_resp = await client.get('https://discord.com/api/users/@me', headers={'Authorization': f'Bearer {access_token}'}, timeout=10.0)
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f'Error fetching user from Discord: {exc}')

    if me_resp.status_code != 200:
        raise HTTPException(status_code=400, detail=f'Failed to fetch user: {me_resp.text}')

    user = me_resp.json()

    session_user = {
        'id': user.get('id'),
        'username': user.get('username'),
        'discriminator': user.get('discriminator'),
        'avatar': user.get('avatar'),
        'email': user.get('email') if 'email' in user else None,
    }

    request.session['user'] = session_user

    return JSONResponse({'user': session_user})


@app.get('/api/me')
async def api_me(request: Request):
    user = request.session.get('user')
    if not user:
        return JSONResponse({'user': None})
    return JSONResponse({'user': user})


@app.post('/api/logout')
async def api_logout(request: Request):
    request.session.pop('user', None)
    return JSONResponse({'ok': True})