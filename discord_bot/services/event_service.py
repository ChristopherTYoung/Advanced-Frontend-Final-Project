"""Event Service - manages event storage and retrieval."""
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import asyncpg

class EventService:
    def __init__(self):
        self.db_pool: Optional[asyncpg.Pool] = None

    async def init_db_pool(self, database_url: str):
        try:
            self.db_pool = await asyncpg.create_pool(database_url, min_size=1, max_size=5)
            print("DEBUG EventService: Database pool initialized")
        except Exception as e:
            print(f"ERROR EventService: Failed to initialize database pool: {e}")
            import traceback; traceback.print_exc()

    async def close_db_pool(self):
        if self.db_pool:
            await self.db_pool.close()
            print("DEBUG EventService: Database pool closed")

    async def create_event(self, guild_id: str, user_id: str, time_of_event: datetime, event_name: str, event_details: str) -> Optional[int]:
        if not self.db_pool:
            print("WARNING EventService: Database pool not initialized")
            return None
        try:
            if time_of_event.tzinfo is not None:
                try:
                    time_of_event = time_of_event.astimezone(timezone.utc).replace(tzinfo=None)
                except Exception:
                    time_of_event = time_of_event.replace(tzinfo=None)
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO event (user_id, guild_id, time_of_event, event_name, event_details)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING event_id
                    """,
                    user_id,
                    guild_id,
                    time_of_event,
                    event_name,
                    event_details,
                )
                return int(row["event_id"]) if row else None
        except Exception as e:
            print(f"ERROR EventService: Failed to create event: {e}")
            import traceback; traceback.print_exc()
            return None

    async def list_events(self, guild_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        if not self.db_pool:
            print("WARNING EventService: Database pool not initialized")
            return []
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT event_id, user_id, guild_id, time_of_event, event_name, event_details, canceled FROM event WHERE guild_id = $1 ORDER BY time_of_event ASC LIMIT $2",
                    guild_id,
                    limit,
                )
                events = []
                for row in rows:
                    events.append({
                        "event_id": int(row["event_id"]),
                        "user_id": row["user_id"],
                        "guild_id": row["guild_id"],
                        "time_of_event": row["time_of_event"].isoformat(),
                        "event_name": row["event_name"],
                        "event_details": row["event_details"],
                        "canceled": row["canceled"].isoformat() if row["canceled"] else None,
                    })
                return events
        except Exception as e:
            print(f"ERROR EventService: Failed to list events: {e}")
            import traceback; traceback.print_exc()
            return []

    async def get_due_events(self, up_to: datetime) -> List[Dict[str, Any]]:
        if not self.db_pool:
            print("WARNING EventService: Database pool not initialized")
            return []

        if up_to.tzinfo is not None:
            up_to = up_to.astimezone(timezone.utc).replace(tzinfo=None)

        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT event_id, user_id, guild_id, time_of_event, event_name, event_details FROM event WHERE time_of_event <= $1 AND canceled IS NULL ORDER BY time_of_event ASC",
                    up_to,
                )
                events = []
                for row in rows:
                    events.append({
                        "event_id": int(row["event_id"]),
                        "user_id": row["user_id"],
                        "guild_id": row["guild_id"],
                        "time_of_event": row["time_of_event"].isoformat(),
                        "event_name": row["event_name"],
                        "event_details": row["event_details"],
                    })
                return events
        except Exception as e:
            print(f"ERROR EventService: Failed to get due events: {e}")
            import traceback; traceback.print_exc()
            return []

    async def delete_event(self, event_id: int) -> bool:
        if not self.db_pool:
            print("WARNING EventService: Database pool not initialized")
            return False
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("DELETE FROM event WHERE event_id = $1", event_id)
                return True
        except Exception as e:
            print(f"ERROR EventService: Failed to delete event {event_id}: {e}")
            import traceback; traceback.print_exc()
            return False

    async def cancel_event(self, event_id: int, canceled_by: Optional[str] = None) -> bool:
        """Mark an event as canceled by setting the canceled timestamp. Returns True if updated."""
        if not self.db_pool:
            print("WARNING EventService: Database pool not initialized")
            return False
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute(
                    "UPDATE event SET canceled = NOW() WHERE event_id = $1",
                    event_id,
                )
                # asyncpg returns command tag like 'UPDATE <n>' where <n> is number of rows
                try:
                    parts = result.split()
                    if len(parts) >= 2:
                        count = int(parts[-1])
                        return count > 0
                except Exception:
                    pass
                return False
        except Exception as e:
            print(f"ERROR EventService: Failed to cancel event {event_id}: {e}")
            import traceback; traceback.print_exc()
            return False

    # --- Proposal methods ---
    async def create_proposal(self, guild_id: str, user_id: str, time_of_event: datetime, event_name: str, event_details: str) -> Optional[int]:
        if not self.db_pool:
            print("WARNING EventService: Database pool not initialized")
            return None
        try:
            if time_of_event.tzinfo is not None:
                try:
                    time_of_event = time_of_event.astimezone(timezone.utc).replace(tzinfo=None)
                except Exception:
                    time_of_event = time_of_event.replace(tzinfo=None)
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO event_proposal (user_id, guild_id, time_of_event, event_name, event_details)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING proposal_id
                    """,
                    user_id,
                    guild_id,
                    time_of_event,
                    event_name,
                    event_details,
                )
                return int(row["proposal_id"]) if row else None
        except Exception as e:
            print(f"ERROR EventService: Failed to create proposal: {e}")
            import traceback; traceback.print_exc()
            return None

    async def list_proposals(self, guild_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        if not self.db_pool:
            print("WARNING EventService: Database pool not initialized")
            return []
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT proposal_id, user_id, guild_id, time_of_event, event_name, event_details, created_at, approved, time_approved, event_id FROM event_proposal WHERE guild_id = $1 ORDER BY created_at ASC LIMIT $2",
                    guild_id,
                    limit,
                )
                proposals = []
                for row in rows:
                    proposals.append({
                        "proposal_id": int(row["proposal_id"]),
                        "user_id": row["user_id"],
                        "guild_id": row["guild_id"],
                        "time_of_event": row["time_of_event"].isoformat(),
                        "event_name": row["event_name"],
                        "event_details": row["event_details"],
                        "created_at": row["created_at"].isoformat(),
                        "approved": bool(row["approved"]),
                        "time_approved": row["time_approved"].isoformat() if row["time_approved"] else None,
                        "event_id": int(row["event_id"]) if row["event_id"] else None,
                    })
                return proposals
        except Exception as e:
            print(f"ERROR EventService: Failed to list proposals: {e}")
            import traceback; traceback.print_exc()
            return []

    async def get_proposal(self, proposal_id: int) -> Optional[Dict[str, Any]]:
        if not self.db_pool:
            print("WARNING EventService: Database pool not initialized")
            return None
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT proposal_id, user_id, guild_id, time_of_event, event_name, event_details, created_at, approved, time_approved, event_id FROM event_proposal WHERE proposal_id = $1",
                    proposal_id,
                )
                if not row:
                    return None
                return {
                    "proposal_id": int(row["proposal_id"]),
                    "user_id": row["user_id"],
                    "guild_id": row["guild_id"],
                    "time_of_event": row["time_of_event"].isoformat(),
                    "event_name": row["event_name"],
                    "event_details": row["event_details"],
                    "created_at": row["created_at"].isoformat(),
                    "approved": bool(row["approved"]),
                    "time_approved": row["time_approved"].isoformat() if row["time_approved"] else None,
                    "event_id": int(row["event_id"]) if row["event_id"] else None,
                }
        except Exception as e:
            print(f"ERROR EventService: Failed to fetch proposal {proposal_id}: {e}")
            import traceback; traceback.print_exc()
            return None

    async def approve_proposal(self, proposal_id: int, approver_user_id: str) -> Optional[int]:
        """Approve a proposal: create an event and mark the proposal approved with timestamps and FK to event."""
        proposal = await self.get_proposal(proposal_id)
        if not proposal:
            return None
        try:
            from datetime import datetime

            time_of_event = datetime.fromisoformat(proposal["time_of_event"])
            event_id = await self.create_event(
                guild_id=proposal["guild_id"],
                user_id=proposal["user_id"],
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
        except Exception as e:
            print(f"ERROR EventService: Failed to approve proposal {proposal_id}: {e}")
            import traceback; traceback.print_exc()
            return None

    async def delete_proposal(self, proposal_id: int) -> bool:
        if not self.db_pool:
            print("WARNING EventService: Database pool not initialized")
            return False
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("DELETE FROM event_proposal WHERE proposal_id = $1", proposal_id)
                return True
        except Exception as e:
            print(f"ERROR EventService: Failed to delete proposal {proposal_id}: {e}")
            import traceback; traceback.print_exc()
            return False


# Singleton instance
event_service = EventService()
