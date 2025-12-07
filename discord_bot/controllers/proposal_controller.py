from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from services.auth_service import auth_service
from services.proposal_service import proposal_service
from schemas import ProposalCreateRequest


router = APIRouter()


def _user_is_admin(user_guilds: list, guild_id: str) -> bool:
    for g in user_guilds:
        if str(g.get("id")) == str(guild_id):
            if g.get("owner"):
                return True
            perms = g.get("permissions")
            try:
                if perms is not None and int(perms) & 0x20:
                    return True
            except Exception:
                pass
    return False


@router.post("/api/guilds/{guild_id}/proposals")
async def api_create_proposal(guild_id: str, payload: ProposalCreateRequest, request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated - no access token")

    try:
        user_guilds = await auth_service.get_user_guilds(access_token)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Authentication required; please sign in again")
    user_guild_ids = {g["id"] for g in user_guilds}
    if guild_id not in user_guild_ids:
        raise HTTPException(status_code=403, detail="You don't have access to this guild")

    proposal_id = await proposal_service.create_proposal(
        guild_id=guild_id,
        user_id=payload.user_id,
        username=payload.username,
        time_of_event=payload.time_of_event,
        event_name=payload.event_name,
        event_details=payload.event_details,
    )

    if not proposal_id:
        raise HTTPException(status_code=500, detail="Failed to create proposal")

    return JSONResponse({"ok": True, "proposal_id": proposal_id})


@router.get("/api/guilds/{guild_id}/proposals")
async def api_list_proposals(guild_id: str, request: Request, limit: int = 100):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated - no access token")

    try:
        user_guilds = await auth_service.get_user_guilds(access_token)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Authentication required; please sign in again")
    if not _user_is_admin(user_guilds, guild_id):
        raise HTTPException(status_code=403, detail="Admin permissions required to view proposals")

    proposals = await proposal_service.list_proposals(guild_id=guild_id, limit=min(limit, 500))
    return JSONResponse({"proposals": proposals})


@router.post("/api/guilds/{guild_id}/proposals/{proposal_id}/approve")
async def api_approve_proposal(guild_id: str, proposal_id: int, request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated - no access token")

    try:
        user_guilds = await auth_service.get_user_guilds(access_token)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Authentication required; please sign in again")
    if not _user_is_admin(user_guilds, guild_id):
        raise HTTPException(status_code=403, detail="Admin permissions required to approve proposals")

    event_id = await proposal_service.approve_proposal(proposal_id, approver_user_id=user.get("id"))
    if not event_id:
        raise HTTPException(status_code=500, detail="Failed to approve proposal")

    return JSONResponse({"ok": True, "event_id": event_id})


@router.delete("/api/guilds/{guild_id}/proposals/{proposal_id}")
async def api_reject_proposal(guild_id: str, proposal_id: int, request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated - no access token")

    try:
        user_guilds = await auth_service.get_user_guilds(access_token)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Authentication required; please sign in again")
    if not _user_is_admin(user_guilds, guild_id):
        raise HTTPException(status_code=403, detail="Admin permissions required to reject proposals")

    deleted = await proposal_service.delete_proposal(proposal_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete proposal")

    return JSONResponse({"ok": True})
