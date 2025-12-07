import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import asyncpg


class ProposalService:
    def __init__(self):
        self.db_pool: Optional[asyncpg.Pool] = None
        self.event_service = None  # Will be set after initialization

    async def init_db_pool(self, database_url: str):
        self.db_pool = await asyncpg.create_pool(database_url, min_size=1, max_size=5)
        logging.info("DEBUG ProposalService: Database pool initialized")

    async def close_db_pool(self):
        if self.db_pool:
            await self.db_pool.close()

    async def create_proposal(
        self, guild_id: str, user_id: str, username: str, time_of_event: datetime, event_name: str, event_details: str
    ) -> Optional[int]:
        if not self.db_pool:
            logging.info("WARNING ProposalService: Database pool not initialized")
            return None

        if time_of_event.tzinfo is not None:
            try:
                time_of_event = time_of_event.astimezone(timezone.utc).replace(tzinfo=None)
            except Exception:
                time_of_event = time_of_event.replace(tzinfo=None)
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO event_proposal (user_id, username, guild_id, time_of_event, event_name, event_details)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING proposal_id
                """,
                user_id,
                username,
                guild_id,
                time_of_event,
                event_name,
                event_details,
            )
            return int(row["proposal_id"]) if row else None

    async def list_proposals(self, guild_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        if not self.db_pool:
            return []

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT proposal_id, user_id, username, guild_id, time_of_event, event_name, event_details, created_at, approved, time_approved, event_id FROM event_proposal WHERE guild_id = $1 ORDER BY created_at ASC LIMIT $2",
                guild_id,
                limit,
            )
            proposals = []
            for row in rows:
                proposals.append(
                    {
                        "proposal_id": int(row["proposal_id"]),
                        "user_id": row["user_id"],
                        "username": row["username"],
                        "guild_id": row["guild_id"],
                        "time_of_event": row["time_of_event"].isoformat(),
                        "event_name": row["event_name"],
                        "event_details": row["event_details"],
                        "created_at": row["created_at"].isoformat(),
                        "approved": bool(row["approved"]),
                        "time_approved": row["time_approved"].isoformat() if row["time_approved"] else None,
                        "event_id": int(row["event_id"]) if row["event_id"] else None,
                    }
                )
            return proposals

    async def get_proposal(self, proposal_id: int) -> Optional[Dict[str, Any]]:
        if not self.db_pool:
            logging.info("WARNING ProposalService: Database pool not initialized")
            return None
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT proposal_id, user_id, username, guild_id, time_of_event, event_name, event_details, created_at, approved, time_approved, event_id FROM event_proposal WHERE proposal_id = $1",
                proposal_id,
            )
            if not row:
                return None
            return {
                "proposal_id": int(row["proposal_id"]),
                "user_id": row["user_id"],
                "username": row["username"],
                "guild_id": row["guild_id"],
                "time_of_event": row["time_of_event"].isoformat(),
                "event_name": row["event_name"],
                "event_details": row["event_details"],
                "created_at": row["created_at"].isoformat(),
                "approved": bool(row["approved"]),
                "time_approved": row["time_approved"].isoformat() if row["time_approved"] else None,
                "event_id": int(row["event_id"]) if row["event_id"] else None,
            }

    async def approve_proposal(self, proposal_id: int, approver_user_id: str) -> Optional[int]:
        if not self.event_service:
            logging.error("ERROR ProposalService: event_service not set")
            return None

        proposal = await self.get_proposal(proposal_id)
        if not proposal:
            return None

        time_of_event = datetime.fromisoformat(proposal["time_of_event"])
        event_id = await self.event_service.create_event(
            guild_id=proposal["guild_id"],
            user_id=proposal["user_id"],
            username=proposal.get("username"),
            time_of_event=time_of_event,
            event_name=proposal["event_name"],
            event_details=proposal["event_details"],
        )
        if event_id is None:
            return None

        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE event_proposal SET approved = TRUE, time_approved = NOW(), event_id = $1 WHERE proposal_id = $2",
                event_id,
                proposal_id,
            )

        return event_id

    async def delete_proposal(self, proposal_id: int) -> bool:
        if not self.db_pool:
            logging.info("WARNING ProposalService: Database pool not initialized")
            return False
        async with self.db_pool.acquire() as conn:
            await conn.execute("DELETE FROM event_proposal WHERE proposal_id = $1", proposal_id)
            return True


proposal_service = ProposalService()
