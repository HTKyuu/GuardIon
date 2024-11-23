import os
import asyncpg
from dotenv import load_dotenv
import datetime
import logging
import sys
import asyncio
from typing import Optional
from contextlib import asynccontextmanager

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
        self._reconnect_interval = 5  # seconds
        self._max_retries = 3
        
    @asynccontextmanager
    async def acquire_connection(self):
        """Safely acquire a database connection with retries."""
        retries = 0
        while retries < self._max_retries:
            try:
                if not self.pool:
                    await self.init()
                if not self.pool:
                    raise Exception("Failed to initialize connection pool")
                    
                async with self.pool.acquire() as conn:
                    yield conn
                    return
            except Exception as e:
                logger.error(f"Database connection error (attempt {retries + 1}/{self._max_retries}): {str(e)}")
                if self.pool:
                    await self.pool.close()
                    self.pool = None
                retries += 1
                if retries < self._max_retries:
                    await asyncio.sleep(self._reconnect_interval)
                    
        raise Exception("Failed to acquire database connection after maximum retries")

    async def init(self):
        """Initialize the database connection pool."""
        if self.pool:
            return

        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL environment variable not set!")
            return

        try:
            logger.info("Creating database connection pool...")
            self.pool = await asyncpg.create_pool(
                database_url,
                min_size=1,
                max_size=5,
                max_inactive_connection_lifetime=30.0,  # 30 seconds
                command_timeout=10,
                server_settings={
                    'application_name': 'GuardIon Bot',
                    'client_min_messages': 'error'
                }
            )
            logger.info("Successfully connected to PostgreSQL database")
            await self._init_tables()
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            if self.pool:
                await self.pool.close()
                self.pool = None
            raise

    async def _init_tables(self):
        """Initialize database tables."""
        async with self.acquire_connection() as conn:
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

    async def _ensure_guild_exists(self, guild_id: int) -> bool:
        """Ensure a guild entry exists in the guild_config table."""
        try:
            async with self.acquire_connection() as conn:
                await conn.execute(
                    'INSERT INTO guild_config (guild_id) VALUES ($1) ON CONFLICT DO NOTHING',
                    guild_id
                )
            return True
        except Exception as e:
            logger.error(f"Error ensuring guild exists: {str(e)}")
            return False

    # Log Channel Methods
    async def set_log_channel(self, guild_id: int, channel_id: int) -> bool:
        try:
            await self._ensure_guild_exists(guild_id)
            async with self.acquire_connection() as conn:
                await conn.execute('''
                    UPDATE guild_config 
                    SET log_channel_id = $2, log_enabled = true
                    WHERE guild_id = $1
                ''', guild_id, channel_id)
            return True
        except Exception as e:
            logger.error(f"Error setting log channel: {str(e)}")
            return False

    async def get_log_channel(self, guild_id: int) -> Optional[int]:
        try:
            async with self.acquire_connection() as conn:
                record = await conn.fetchrow(
                    'SELECT log_channel_id, log_enabled FROM guild_config WHERE guild_id = $1',
                    guild_id
                )
                return record['log_channel_id'] if record and record['log_enabled'] else None
        except Exception as e:
            logger.error(f"Error getting log channel: {str(e)}")
            return None

    async def toggle_logging(self, guild_id: int, enabled: bool) -> bool:
        try:
            async with self.acquire_connection() as conn:
                await conn.execute('''
                    UPDATE guild_config 
                    SET log_enabled = $2
                    WHERE guild_id = $1
                ''', guild_id, enabled)
            return True
        except Exception as e:
            logger.error(f"Error toggling logging: {str(e)}")
            return False

    async def is_logging_enabled(self, guild_id: int) -> bool:
        try:
            async with self.acquire_connection() as conn:
                record = await conn.fetchrow(
                    'SELECT log_enabled FROM guild_config WHERE guild_id = $1',
                    guild_id
                )
                return record['log_enabled'] if record else False
        except Exception as e:
            logger.error(f"Error checking logging status: {str(e)}")
            return False

    # Welcome Channel Methods
    async def set_welcome_channel(self, guild_id: int, channel_id: int) -> bool:
        try:
            await self._ensure_guild_exists(guild_id)
            async with self.acquire_connection() as conn:
                await conn.execute('''
                    UPDATE guild_config 
                    SET welcome_channel_id = $2, welcome_enabled = true
                    WHERE guild_id = $1
                ''', guild_id, channel_id)
            return True
        except Exception as e:
            logger.error(f"Error setting welcome channel: {str(e)}")
            return False

    async def get_welcome_channel(self, guild_id: int) -> Optional[int]:
        try:
            async with self.acquire_connection() as conn:
                record = await conn.fetchrow(
                    'SELECT welcome_channel_id, welcome_enabled FROM guild_config WHERE guild_id = $1',
                    guild_id
                )
                return record['welcome_channel_id'] if record and record['welcome_enabled'] else None
        except Exception as e:
            logger.error(f"Error getting welcome channel: {str(e)}")
            return None

    async def toggle_welcome(self, guild_id: int, enabled: bool) -> bool:
        try:
            async with self.acquire_connection() as conn:
                await conn.execute('''
                    UPDATE guild_config 
                    SET welcome_enabled = $2
                    WHERE guild_id = $1
                ''', guild_id, enabled)
            return True
        except Exception as e:
            logger.error(f"Error toggling welcome: {str(e)}")
            return False

    async def is_welcome_enabled(self, guild_id: int) -> bool:
        try:
            async with self.acquire_connection() as conn:
                record = await conn.fetchrow(
                    'SELECT welcome_enabled FROM guild_config WHERE guild_id = $1',
                    guild_id
                )
                return record['welcome_enabled'] if record else False
        except Exception as e:
            logger.error(f"Error checking welcome status: {str(e)}")
            return False

    # Auto Role Methods
    async def set_auto_role(self, guild_id: int, role_id: int) -> bool:
        try:
            await self._ensure_guild_exists(guild_id)
            async with self.acquire_connection() as conn:
                await conn.execute('''
                    UPDATE guild_config 
                    SET auto_role_id = $2, auto_role_enabled = true
                    WHERE guild_id = $1
                ''', guild_id, role_id)
            return True
        except Exception as e:
            logger.error(f"Error setting auto role: {str(e)}")
            return False

    async def get_auto_role(self, guild_id: int) -> Optional[int]:
        try:
            async with self.acquire_connection() as conn:
                record = await conn.fetchrow(
                    'SELECT auto_role_id, auto_role_enabled FROM guild_config WHERE guild_id = $1',
                    guild_id
                )
                return record['auto_role_id'] if record and record['auto_role_enabled'] else None
        except Exception as e:
            logger.error(f"Error getting auto role: {str(e)}")
            return None

    async def toggle_auto_role(self, guild_id: int, enabled: bool) -> bool:
        try:
            async with self.acquire_connection() as conn:
                await conn.execute('''
                    UPDATE guild_config 
                    SET auto_role_enabled = $2
                    WHERE guild_id = $1
                ''', guild_id, enabled)
            return True
        except Exception as e:
            logger.error(f"Error toggling auto role: {str(e)}")
            return False

    async def is_auto_role_enabled(self, guild_id: int) -> bool:
        try:
            async with self.acquire_connection() as conn:
                record = await conn.fetchrow(
                    'SELECT auto_role_enabled FROM guild_config WHERE guild_id = $1',
                    guild_id
                )
                return record['auto_role_enabled'] if record else False
        except Exception as e:
            logger.error(f"Error checking auto role status: {str(e)}")
            return False

    # Anti-invite methods
    async def set_anti_invite(self, guild_id: int, enabled: bool) -> bool:
        try:
            async with self.acquire_connection() as conn:
                await conn.execute('''
                    UPDATE guild_config 
                    SET anti_invite_enabled = $2
                    WHERE guild_id = $1
                ''', guild_id, enabled)
            return True
        except Exception as e:
            logger.error(f"Error setting anti invite: {str(e)}")
            return False

    async def is_anti_invite_enabled(self, guild_id: int) -> bool:
        try:
            async with self.acquire_connection() as conn:
                record = await conn.fetchrow(
                    'SELECT anti_invite_enabled FROM guild_config WHERE guild_id = $1',
                    guild_id
                )
                return record['anti_invite_enabled'] if record else False
        except Exception as e:
            logger.error(f"Error checking anti invite status: {str(e)}")
            return False

    # Warning Methods
    async def add_warning(self, guild_id: int, user_id: int, moderator_id: int, reason: str) -> int:
        try:
            async with self.acquire_connection() as conn:
                cursor = await conn.execute('''
                    INSERT INTO warnings (guild_id, user_id, moderator_id, reason, timestamp)
                    VALUES ($1, $2, $3, $4, $5)
                ''', guild_id, user_id, moderator_id, reason, datetime.datetime.now(datetime.timezone.utc))
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error adding warning: {str(e)}")
            return None

    async def get_warnings(self, guild_id: int, user_id: int) -> list:
        try:
            async with self.acquire_connection() as conn:
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
        try:
            async with self.acquire_connection() as conn:
                await conn.execute('DELETE FROM warnings WHERE id = $1 AND guild_id = $2', warning_id, guild_id)
            return True
        except Exception as e:
            logger.error(f"Error removing warning: {str(e)}")
            return False

    async def clear_warnings(self, guild_id: int, user_id: int) -> int:
        try:
            async with self.acquire_connection() as conn:
                await conn.execute('DELETE FROM warnings WHERE guild_id = $1 AND user_id = $2', guild_id, user_id)
            return 1
        except Exception as e:
            logger.error(f"Error clearing warnings: {str(e)}")
            return 0

    # Tempban Methods
    async def add_tempban(self, guild_id: int, user_id: int, moderator_id: int, reason: str, unban_time: datetime.datetime) -> int:
        try:
            async with self.acquire_connection() as conn:
                cursor = await conn.execute('''
                    INSERT INTO tempbans (guild_id, user_id, moderator_id, reason, unban_time, timestamp)
                    VALUES ($1, $2, $3, $4, $5, $6)
                ''', guild_id, user_id, moderator_id, reason, unban_time, datetime.datetime.now(datetime.timezone.utc))
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error adding tempban: {str(e)}")
            return None

    async def get_active_tempbans(self, guild_id: int = None) -> list:
        try:
            async with self.acquire_connection() as conn:
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
        try:
            async with self.acquire_connection() as conn:
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
