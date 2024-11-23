import os
import asyncpg
from dotenv import load_dotenv
import datetime
import discord
import asyncio

load_dotenv()

class ConfigManager:
    def __init__(self):
        self.pool = None
        
    async def init(self):
        if not self.pool:
            # Get PostgreSQL connection URL from Railway's environment variable
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                raise ValueError("DATABASE_URL environment variable not set")
            
            # Create connection pool
            self.pool = await asyncpg.create_pool(database_url)
            
            # Create tables if they don't exist
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS guild_config (
                        guild_id BIGINT PRIMARY KEY,
                        log_channel_id BIGINT,
                        welcome_channel_id BIGINT,
                        auto_role_id BIGINT,
                        log_enabled BOOLEAN DEFAULT false,
                        welcome_enabled BOOLEAN DEFAULT false,
                        auto_role_enabled BOOLEAN DEFAULT false,
                        anti_invite_enabled BOOLEAN DEFAULT false
                    )
                ''')
                
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS warnings (
                        id SERIAL PRIMARY KEY,
                        guild_id BIGINT,
                        user_id BIGINT,
                        moderator_id BIGINT,
                        reason TEXT,
                        timestamp TIMESTAMP WITH TIME ZONE
                    )
                ''')
                
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS tempbans (
                        id SERIAL PRIMARY KEY,
                        guild_id BIGINT,
                        user_id BIGINT,
                        moderator_id BIGINT,
                        reason TEXT,
                        unban_time TIMESTAMP WITH TIME ZONE,
                        timestamp TIMESTAMP WITH TIME ZONE,
                        active BOOLEAN DEFAULT true,
                        FOREIGN KEY (guild_id) REFERENCES guild_config(guild_id)
                    )
                ''')

    async def _ensure_guild_exists(self, guild_id: int):
        async with self.pool.acquire() as conn:
            await conn.execute(
                'INSERT OR IGNORE INTO guild_config (guild_id) VALUES ($1)',
                (guild_id,)
            )

    # Log Channel Methods
    async def set_log_channel(self, guild_id: int, channel_id: int):
        await self._ensure_guild_exists(guild_id)
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO guild_config (guild_id, log_channel_id)
                VALUES ($1, $2)
                ON CONFLICT (guild_id)
                DO UPDATE SET log_channel_id = $2, log_enabled = true
            ''', guild_id, channel_id)

    async def get_log_channel(self, guild_id: int) -> int:
        await self._ensure_guild_exists(guild_id)
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow('SELECT log_channel_id, log_enabled FROM guild_config WHERE guild_id = $1', guild_id)
            if record and record['log_enabled']:
                return record['log_channel_id']
            return None

    async def toggle_logging(self, guild_id: int, enabled: bool):
        await self._ensure_guild_exists(guild_id)
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO guild_config (guild_id, log_enabled)
                VALUES ($1, $2)
                ON CONFLICT (guild_id)
                DO UPDATE SET log_enabled = $2
            ''', guild_id, enabled)

    async def is_logging_enabled(self, guild_id: int) -> bool:
        await self._ensure_guild_exists(guild_id)
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow('SELECT log_enabled FROM guild_config WHERE guild_id = $1', guild_id)
            return record['log_enabled'] if record else False

    # Welcome Channel Methods
    async def set_welcome_channel(self, guild_id: int, channel_id: int):
        await self._ensure_guild_exists(guild_id)
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO guild_config (guild_id, welcome_channel_id)
                VALUES ($1, $2)
                ON CONFLICT (guild_id)
                DO UPDATE SET welcome_channel_id = $2, welcome_enabled = true
            ''', guild_id, channel_id)

    async def get_welcome_channel(self, guild_id: int) -> int:
        await self._ensure_guild_exists(guild_id)
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow('SELECT welcome_channel_id, welcome_enabled FROM guild_config WHERE guild_id = $1', guild_id)
            if record and record['welcome_enabled']:
                return record['welcome_channel_id']
            return None

    async def toggle_welcome(self, guild_id: int, enabled: bool):
        await self._ensure_guild_exists(guild_id)
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO guild_config (guild_id, welcome_enabled)
                VALUES ($1, $2)
                ON CONFLICT (guild_id)
                DO UPDATE SET welcome_enabled = $2
            ''', guild_id, enabled)

    async def is_welcome_enabled(self, guild_id: int) -> bool:
        await self._ensure_guild_exists(guild_id)
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow('SELECT welcome_enabled FROM guild_config WHERE guild_id = $1', guild_id)
            return record['welcome_enabled'] if record else False

    # Auto Role Methods
    async def set_auto_role(self, guild_id: int, role_id: int):
        await self._ensure_guild_exists(guild_id)
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO guild_config (guild_id, auto_role_id)
                VALUES ($1, $2)
                ON CONFLICT (guild_id)
                DO UPDATE SET auto_role_id = $2, auto_role_enabled = true
            ''', guild_id, role_id)

    async def get_auto_role(self, guild_id: int) -> int:
        await self._ensure_guild_exists(guild_id)
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow('SELECT auto_role_id, auto_role_enabled FROM guild_config WHERE guild_id = $1', guild_id)
            if record and record['auto_role_enabled']:
                return record['auto_role_id']
            return None

    async def toggle_auto_role(self, guild_id: int, enabled: bool):
        await self._ensure_guild_exists(guild_id)
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO guild_config (guild_id, auto_role_enabled)
                VALUES ($1, $2)
                ON CONFLICT (guild_id)
                DO UPDATE SET auto_role_enabled = $2
            ''', guild_id, enabled)

    async def is_auto_role_enabled(self, guild_id: int) -> bool:
        await self._ensure_guild_exists(guild_id)
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow('SELECT auto_role_enabled FROM guild_config WHERE guild_id = $1', guild_id)
            return record['auto_role_enabled'] if record else False

    # Anti-invite methods
    async def set_anti_invite(self, guild_id: int, enabled: bool) -> bool:
        await self._ensure_guild_exists(guild_id)
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO guild_config (guild_id, anti_invite_enabled)
                VALUES ($1, $2)
                ON CONFLICT (guild_id)
                DO UPDATE SET anti_invite_enabled = $2
            ''', guild_id, enabled)
            return True

    async def is_anti_invite_enabled(self, guild_id: int) -> bool:
        await self._ensure_guild_exists(guild_id)
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow('SELECT anti_invite_enabled FROM guild_config WHERE guild_id = $1', guild_id)
            return record['anti_invite_enabled'] if record else False

    # Warning Methods
    async def add_warning(self, guild_id: int, user_id: int, moderator_id: int, reason: str) -> int:
        await self._ensure_guild_exists(guild_id)
        async with self.pool.acquire() as conn:
            cursor = await conn.execute('''
                INSERT INTO warnings (guild_id, user_id, moderator_id, reason, timestamp)
                VALUES ($1, $2, $3, $4, $5)
            ''', guild_id, user_id, moderator_id, reason, datetime.datetime.now(datetime.timezone.utc))
            return cursor.fetchone()[0]

    async def get_warnings(self, guild_id: int, user_id: int) -> list:
        async with self.pool.acquire() as conn:
            return await conn.fetch('''
                SELECT id, moderator_id, reason, timestamp
                FROM warnings
                WHERE guild_id = $1 AND user_id = $2
                ORDER BY timestamp DESC
            ''', guild_id, user_id)

    async def remove_warning(self, warning_id: int, guild_id: int) -> bool:
        async with self.pool.acquire() as conn:
            await conn.execute('DELETE FROM warnings WHERE id = $1 AND guild_id = $2', warning_id, guild_id)
            return True

    async def clear_warnings(self, guild_id: int, user_id: int) -> int:
        async with self.pool.acquire() as conn:
            await conn.execute('DELETE FROM warnings WHERE guild_id = $1 AND user_id = $2', guild_id, user_id)
            return 1

    # Tempban Methods
    async def add_tempban(self, guild_id: int, user_id: int, moderator_id: int, reason: str, unban_time: datetime.datetime) -> int:
        async with self.pool.acquire() as conn:
            cursor = await conn.execute('''
                INSERT INTO tempbans (guild_id, user_id, moderator_id, reason, unban_time, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6)
            ''', guild_id, user_id, moderator_id, reason, unban_time, datetime.datetime.now(datetime.timezone.utc))
            return cursor.fetchone()[0]

    async def get_active_tempbans(self, guild_id: int = None) -> list:
        async with self.pool.acquire() as conn:
            if guild_id:
                query = '''
                    SELECT guild_id, user_id, moderator_id, reason, unban_time, timestamp 
                    FROM tempbans 
                    WHERE guild_id = $1 AND active = true AND unban_time > $2
                '''
                params = (guild_id, datetime.datetime.now(datetime.timezone.utc))
            else:
                query = '''
                    SELECT guild_id, user_id, moderator_id, reason, unban_time, timestamp 
                    FROM tempbans 
                    WHERE active = true AND unban_time > $1
                '''
                params = (datetime.datetime.now(datetime.timezone.utc),)
            
            return await conn.fetch(query, *params)

    async def deactivate_tempban(self, guild_id: int, user_id: int) -> bool:
        async with self.pool.acquire() as conn:
            await conn.execute('UPDATE tempbans SET active = false WHERE guild_id = $1 AND user_id = $2 AND active = true', guild_id, user_id)
            return True

    # Utility method for sending logs
    async def send_log(self, guild: discord.Guild, embed: discord.Embed):
        log_channel_id = await self.get_log_channel(guild.id)
        if log_channel_id:
            channel = guild.get_channel(log_channel_id)
            if channel:
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    pass
