import os
import asyncpg
from dotenv import load_dotenv
import datetime
import logging
import sys
import discord
import asyncio
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

load_dotenv()

class ConfigManager:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self._init_lock = asyncio.Lock()
        
    async def get_pool(self) -> Optional[asyncpg.Pool]:
        """Get the database pool, creating it if necessary."""
        if self.pool is None:
            async with self._init_lock:
                # Check again in case another task created the pool
                if self.pool is None:
                    await self.init()
        return self.pool

    async def init(self):
        """Initialize the database connection pool and tables."""
        if self.pool is not None:
            return

        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL environment variable not set!")
            return

        try:
            logger.info("Creating database connection pool...")
            self.pool = await asyncpg.create_pool(
                database_url,
                min_size=2,
                max_size=20,
                max_inactive_connection_lifetime=300.0,  # 5 minutes
                command_timeout=60,
                server_settings={
                    'application_name': 'GuardIon Bot',
                    'client_min_messages': 'notice'
                }
            )
            logger.info("Database connection pool created successfully")

            # Initialize tables
            await self._init_tables()
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            if self.pool:
                await self.pool.close()
                self.pool = None
            raise

    async def _init_tables(self):
        """Initialize database tables."""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                logger.info("Initializing database tables...")
                
                # Create guild_config table
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
                
                # Create warnings table
                await conn.execute('''
                    DO $$ 
                    BEGIN
                        CREATE TABLE IF NOT EXISTS warnings (
                            id BIGSERIAL PRIMARY KEY,
                            guild_id BIGINT,
                            user_id BIGINT,
                            moderator_id BIGINT,
                            reason TEXT,
                            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        );
                    EXCEPTION 
                        WHEN duplicate_table THEN NULL;
                    END $$;
                ''')
                
                # Create tempbans table
                await conn.execute('''
                    DO $$ 
                    BEGIN
                        CREATE TABLE IF NOT EXISTS tempbans (
                            id BIGSERIAL PRIMARY KEY,
                            guild_id BIGINT,
                            user_id BIGINT,
                            moderator_id BIGINT,
                            reason TEXT,
                            unban_time TIMESTAMP WITH TIME ZONE,
                            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            active BOOLEAN DEFAULT true
                        );
                    EXCEPTION 
                        WHEN duplicate_table THEN NULL;
                    END $$;
                ''')
                
                logger.info("Database tables initialized successfully")

    async def close(self):
        """Close the database connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Database connection pool closed")

    async def _ensure_guild_exists(self, guild_id: int):
        """Ensure a guild entry exists in the guild_config table."""
        pool = await self.get_pool()
        if not pool:
            logger.error("Database pool not available")
            return False
            
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    'INSERT INTO guild_config (guild_id) VALUES ($1) ON CONFLICT DO NOTHING',
                    guild_id
                )
            return True
        except Exception as e:
            logger.error(f"Error ensuring guild exists: {str(e)}")
            return False

    # Log Channel Methods
    async def set_log_channel(self, guild_id: int, channel_id: int):
        await self._ensure_guild_exists(guild_id)
        pool = await self.get_pool()
        if not pool:
            logger.error("Database pool not available")
            return
            
        try:
            async with pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO guild_config (guild_id, log_channel_id)
                    VALUES ($1, $2)
                    ON CONFLICT (guild_id)
                    DO UPDATE SET log_channel_id = $2, log_enabled = true
                ''', guild_id, channel_id)
        except Exception as e:
            logger.error(f"Error setting log channel: {str(e)}")

    async def get_log_channel(self, guild_id: int) -> int:
        await self._ensure_guild_exists(guild_id)
        pool = await self.get_pool()
        if not pool:
            logger.error("Database pool not available")
            return None
            
        try:
            async with pool.acquire() as conn:
                record = await conn.fetchrow('SELECT log_channel_id, log_enabled FROM guild_config WHERE guild_id = $1', guild_id)
                if record and record['log_enabled']:
                    return record['log_channel_id']
                return None
        except Exception as e:
            logger.error(f"Error getting log channel: {str(e)}")
            return None

    async def toggle_logging(self, guild_id: int, enabled: bool):
        await self._ensure_guild_exists(guild_id)
        pool = await self.get_pool()
        if not pool:
            logger.error("Database pool not available")
            return
            
        try:
            async with pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO guild_config (guild_id, log_enabled)
                    VALUES ($1, $2)
                    ON CONFLICT (guild_id)
                    DO UPDATE SET log_enabled = $2
                ''', guild_id, enabled)
        except Exception as e:
            logger.error(f"Error toggling logging: {str(e)}")

    async def is_logging_enabled(self, guild_id: int) -> bool:
        await self._ensure_guild_exists(guild_id)
        pool = await self.get_pool()
        if not pool:
            logger.error("Database pool not available")
            return False
            
        try:
            async with pool.acquire() as conn:
                record = await conn.fetchrow('SELECT log_enabled FROM guild_config WHERE guild_id = $1', guild_id)
                return record['log_enabled'] if record else False
        except Exception as e:
            logger.error(f"Error checking logging status: {str(e)}")
            return False

    # Welcome Channel Methods
    async def set_welcome_channel(self, guild_id: int, channel_id: int):
        await self._ensure_guild_exists(guild_id)
        pool = await self.get_pool()
        if not pool:
            logger.error("Database pool not available")
            return
            
        try:
            async with pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO guild_config (guild_id, welcome_channel_id)
                    VALUES ($1, $2)
                    ON CONFLICT (guild_id)
                    DO UPDATE SET welcome_channel_id = $2, welcome_enabled = true
                ''', guild_id, channel_id)
        except Exception as e:
            logger.error(f"Error setting welcome channel: {str(e)}")

    async def get_welcome_channel(self, guild_id: int) -> int:
        await self._ensure_guild_exists(guild_id)
        pool = await self.get_pool()
        if not pool:
            logger.error("Database pool not available")
            return None
            
        try:
            async with pool.acquire() as conn:
                record = await conn.fetchrow('SELECT welcome_channel_id, welcome_enabled FROM guild_config WHERE guild_id = $1', guild_id)
                if record and record['welcome_enabled']:
                    return record['welcome_channel_id']
                return None
        except Exception as e:
            logger.error(f"Error getting welcome channel: {str(e)}")
            return None

    async def toggle_welcome(self, guild_id: int, enabled: bool):
        await self._ensure_guild_exists(guild_id)
        pool = await self.get_pool()
        if not pool:
            logger.error("Database pool not available")
            return
            
        try:
            async with pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO guild_config (guild_id, welcome_enabled)
                    VALUES ($1, $2)
                    ON CONFLICT (guild_id)
                    DO UPDATE SET welcome_enabled = $2
                ''', guild_id, enabled)
        except Exception as e:
            logger.error(f"Error toggling welcome: {str(e)}")

    async def is_welcome_enabled(self, guild_id: int) -> bool:
        await self._ensure_guild_exists(guild_id)
        pool = await self.get_pool()
        if not pool:
            logger.error("Database pool not available")
            return False
            
        try:
            async with pool.acquire() as conn:
                record = await conn.fetchrow('SELECT welcome_enabled FROM guild_config WHERE guild_id = $1', guild_id)
                return record['welcome_enabled'] if record else False
        except Exception as e:
            logger.error(f"Error checking welcome status: {str(e)}")
            return False

    # Auto Role Methods
    async def set_auto_role(self, guild_id: int, role_id: int):
        await self._ensure_guild_exists(guild_id)
        pool = await self.get_pool()
        if not pool:
            logger.error("Database pool not available")
            return
            
        try:
            async with pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO guild_config (guild_id, auto_role_id)
                    VALUES ($1, $2)
                    ON CONFLICT (guild_id)
                    DO UPDATE SET auto_role_id = $2, auto_role_enabled = true
                ''', guild_id, role_id)
        except Exception as e:
            logger.error(f"Error setting auto role: {str(e)}")

    async def get_auto_role(self, guild_id: int) -> int:
        await self._ensure_guild_exists(guild_id)
        pool = await self.get_pool()
        if not pool:
            logger.error("Database pool not available")
            return None
            
        try:
            async with pool.acquire() as conn:
                record = await conn.fetchrow('SELECT auto_role_id, auto_role_enabled FROM guild_config WHERE guild_id = $1', guild_id)
                if record and record['auto_role_enabled']:
                    return record['auto_role_id']
                return None
        except Exception as e:
            logger.error(f"Error getting auto role: {str(e)}")
            return None

    async def toggle_auto_role(self, guild_id: int, enabled: bool):
        await self._ensure_guild_exists(guild_id)
        pool = await self.get_pool()
        if not pool:
            logger.error("Database pool not available")
            return
            
        try:
            async with pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO guild_config (guild_id, auto_role_enabled)
                    VALUES ($1, $2)
                    ON CONFLICT (guild_id)
                    DO UPDATE SET auto_role_enabled = $2
                ''', guild_id, enabled)
        except Exception as e:
            logger.error(f"Error toggling auto role: {str(e)}")

    async def is_auto_role_enabled(self, guild_id: int) -> bool:
        await self._ensure_guild_exists(guild_id)
        pool = await self.get_pool()
        if not pool:
            logger.error("Database pool not available")
            return False
            
        try:
            async with pool.acquire() as conn:
                record = await conn.fetchrow('SELECT auto_role_enabled FROM guild_config WHERE guild_id = $1', guild_id)
                return record['auto_role_enabled'] if record else False
        except Exception as e:
            logger.error(f"Error checking auto role status: {str(e)}")
            return False

    # Anti-invite methods
    async def set_anti_invite(self, guild_id: int, enabled: bool) -> bool:
        await self._ensure_guild_exists(guild_id)
        pool = await self.get_pool()
        if not pool:
            logger.error("Database pool not available")
            return False
            
        try:
            async with pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO guild_config (guild_id, anti_invite_enabled)
                    VALUES ($1, $2)
                    ON CONFLICT (guild_id)
                    DO UPDATE SET anti_invite_enabled = $2
                ''', guild_id, enabled)
            return True
        except Exception as e:
            logger.error(f"Error setting anti invite: {str(e)}")
            return False

    async def is_anti_invite_enabled(self, guild_id: int) -> bool:
        await self._ensure_guild_exists(guild_id)
        pool = await self.get_pool()
        if not pool:
            logger.error("Database pool not available")
            return False
            
        try:
            async with pool.acquire() as conn:
                record = await conn.fetchrow('SELECT anti_invite_enabled FROM guild_config WHERE guild_id = $1', guild_id)
                return record['anti_invite_enabled'] if record else False
        except Exception as e:
            logger.error(f"Error checking anti invite status: {str(e)}")
            return False

    # Warning Methods
    async def add_warning(self, guild_id: int, user_id: int, moderator_id: int, reason: str) -> int:
        await self._ensure_guild_exists(guild_id)
        pool = await self.get_pool()
        if not pool:
            logger.error("Database pool not available")
            return None
            
        try:
            async with pool.acquire() as conn:
                cursor = await conn.execute('''
                    INSERT INTO warnings (guild_id, user_id, moderator_id, reason, timestamp)
                    VALUES ($1, $2, $3, $4, $5)
                ''', guild_id, user_id, moderator_id, reason, datetime.datetime.now(datetime.timezone.utc))
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error adding warning: {str(e)}")
            return None

    async def get_warnings(self, guild_id: int, user_id: int) -> list:
        pool = await self.get_pool()
        if not pool:
            logger.error("Database pool not available")
            return []
            
        try:
            async with pool.acquire() as conn:
                return await conn.fetch('''
                    SELECT id, moderator_id, reason, timestamp
                    FROM warnings
                    WHERE guild_id = $1 AND user_id = $2
                    ORDER BY timestamp DESC
                ''', guild_id, user_id)
        except Exception as e:
            logger.error(f"Error getting warnings: {str(e)}")
            return []

    async def remove_warning(self, warning_id: int, guild_id: int) -> bool:
        pool = await self.get_pool()
        if not pool:
            logger.error("Database pool not available")
            return False
            
        try:
            async with pool.acquire() as conn:
                await conn.execute('DELETE FROM warnings WHERE id = $1 AND guild_id = $2', warning_id, guild_id)
            return True
        except Exception as e:
            logger.error(f"Error removing warning: {str(e)}")
            return False

    async def clear_warnings(self, guild_id: int, user_id: int) -> int:
        pool = await self.get_pool()
        if not pool:
            logger.error("Database pool not available")
            return 0
            
        try:
            async with pool.acquire() as conn:
                await conn.execute('DELETE FROM warnings WHERE guild_id = $1 AND user_id = $2', guild_id, user_id)
            return 1
        except Exception as e:
            logger.error(f"Error clearing warnings: {str(e)}")
            return 0

    # Tempban Methods
    async def add_tempban(self, guild_id: int, user_id: int, moderator_id: int, reason: str, unban_time: datetime.datetime) -> int:
        pool = await self.get_pool()
        if not pool:
            logger.error("Database pool not available")
            return None
            
        try:
            async with pool.acquire() as conn:
                cursor = await conn.execute('''
                    INSERT INTO tempbans (guild_id, user_id, moderator_id, reason, unban_time, timestamp)
                    VALUES ($1, $2, $3, $4, $5, $6)
                ''', guild_id, user_id, moderator_id, reason, unban_time, datetime.datetime.now(datetime.timezone.utc))
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error adding tempban: {str(e)}")
            return None

    async def get_active_tempbans(self, guild_id: int = None) -> list:
        pool = await self.get_pool()
        if not pool:
            logger.error("Database pool not available")
            return []
            
        try:
            async with pool.acquire() as conn:
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
        except Exception as e:
            logger.error(f"Error getting active tempbans: {str(e)}")
            return []

    async def deactivate_tempban(self, guild_id: int, user_id: int) -> bool:
        pool = await self.get_pool()
        if not pool:
            logger.error("Database pool not available")
            return False
            
        try:
            async with pool.acquire() as conn:
                await conn.execute('UPDATE tempbans SET active = false WHERE guild_id = $1 AND user_id = $2 AND active = true', guild_id, user_id)
            return True
        except Exception as e:
            logger.error(f"Error deactivating tempban: {str(e)}")
            return False

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
