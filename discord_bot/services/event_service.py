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
                    "SELECT event_id, user_id, guild_id, time_of_event, event_name, event_details FROM event WHERE guild_id = $1 ORDER BY time_of_event ASC LIMIT $2",
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
                    "SELECT event_id, user_id, guild_id, time_of_event, event_name, event_details FROM event WHERE time_of_event <= $1 ORDER BY time_of_event ASC",
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


# Singleton instance
event_service = EventService()
