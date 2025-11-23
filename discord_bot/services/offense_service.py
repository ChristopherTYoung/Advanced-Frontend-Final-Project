import asyncpg
from typing import Optional


class OffenseService:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        print("DEBUG OffenseService: Database pool initialized")

    async def record_offense(
        self,
        guild_id: str,
        channel_id: str,
        user_id: Optional[str],
        body: Optional[str],
        picture: Optional[bytes] = None,
        offensive_score: Optional[int] = None
    ) -> Optional[int]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO offense (guild_id, channel_id, user_id, body, picture, offensive_score)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING offense_id
                """,
                guild_id,
                channel_id,
                user_id,
                body,
                picture,
                offensive_score
            )
            if row:
                print(f"DEBUG: Recorded offense {row['offense_id']} for guild {guild_id}")
                return row['offense_id']
            return None

    async def get_offenses(self, guild_id: str, limit: int = 50) -> list:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT offense_id, guild_id, channel_id, user_id, body, picture, time_of_offense, offensive_score
                FROM offense
                WHERE guild_id = $1
                ORDER BY offense_id DESC
                LIMIT $2
                """,
                guild_id,
                limit
            )
            return [dict(row) for row in rows]

    async def close(self):
        """Close database connections"""
        print("DEBUG OffenseService: Database pool closed")


offense_service: Optional[OffenseService] = None
