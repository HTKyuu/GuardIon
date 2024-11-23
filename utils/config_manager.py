import aiosqlite
import discord
import asyncio
import os
from datetime import datetime, timezone

class ConfigManager:
    def __init__(self):
        # Create data directory if it doesn't exist
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Set database file path in the data directory
        self.db_file = os.path.join(self.data_dir, "bot_config.db")
        self.initialized = False
        self._lock = asyncio.Lock()

    async def init(self):
        if self.initialized:
            return

        async with self._lock:
            if self.initialized:
                return
            
            try:
                async with aiosqlite.connect(self.db_file) as db:
                    # Store timestamps in UTC
                    await db.execute("PRAGMA timezone='UTC'")
                    
                    # Create tables if they don't exist
                    await db.execute('''
                        CREATE TABLE IF NOT EXISTS guild_config (
                            guild_id INTEGER PRIMARY KEY,
                            log_channel_id INTEGER,
                            welcome_channel_id INTEGER,
                            auto_role_id INTEGER,
                            log_enabled BOOLEAN DEFAULT 0,
                            welcome_enabled BOOLEAN DEFAULT 0,
                            auto_role_enabled BOOLEAN DEFAULT 0,
                            anti_invite_enabled BOOLEAN DEFAULT 0
                        )
                    ''')

                    # Add anti_invite_enabled column if it doesn't exist
                    try:
                        await db.execute('ALTER TABLE guild_config ADD COLUMN anti_invite_enabled BOOLEAN DEFAULT 0')
                    except:
                        pass  # Column already exists
                    
                    # Create warnings table
                    await db.execute('''
                        CREATE TABLE IF NOT EXISTS warnings (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            guild_id INTEGER,
                            user_id INTEGER,
                            moderator_id INTEGER,
                            reason TEXT,
                            timestamp TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%S.000+00:00', 'now')),
                            FOREIGN KEY (guild_id) REFERENCES guild_config(guild_id)
                        )
                    ''')

                    # Create tempbans table
                    await db.execute('''
                        CREATE TABLE IF NOT EXISTS tempbans (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            guild_id INTEGER,
                            user_id INTEGER,
                            moderator_id INTEGER,
                            reason TEXT,
                            unban_time TEXT NOT NULL,
                            timestamp TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%S.000+00:00', 'now')),
                            active BOOLEAN DEFAULT 1,
                            FOREIGN KEY (guild_id) REFERENCES guild_config(guild_id)
                        )
                    ''')
                    await db.commit()
            except Exception as e:
                print(f"Error initializing database: {e}")
            
            self.initialized = True

    async def _ensure_guild_exists(self, guild_id: int):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute(
                'INSERT OR IGNORE INTO guild_config (guild_id) VALUES (?)',
                (guild_id,)
            )
            await db.commit()

    # Log Channel Methods
    async def set_log_channel(self, guild_id: int, channel_id: int):
        await self._ensure_guild_exists(guild_id)
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute(
                'UPDATE guild_config SET log_channel_id = ?, log_enabled = 1 WHERE guild_id = ?',
                (channel_id, guild_id)
            )
            await db.commit()

    async def get_log_channel(self, guild_id: int) -> int:
        await self._ensure_guild_exists(guild_id)
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute(
                'SELECT log_channel_id, log_enabled FROM guild_config WHERE guild_id = ?',
                (guild_id,)
            ) as cursor:
                result = await cursor.fetchone()
                if result and result[1]:  # Check if logging is enabled
                    return result[0]
                return None

    async def toggle_logging(self, guild_id: int, enabled: bool):
        await self._ensure_guild_exists(guild_id)
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute(
                'UPDATE guild_config SET log_enabled = ? WHERE guild_id = ?',
                (enabled, guild_id)
            )
            await db.commit()

    async def is_logging_enabled(self, guild_id: int) -> bool:
        await self._ensure_guild_exists(guild_id)
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute(
                'SELECT log_enabled FROM guild_config WHERE guild_id = ?',
                (guild_id,)
            ) as cursor:
                result = await cursor.fetchone()
                return bool(result[0]) if result else False

    # Welcome Channel Methods
    async def set_welcome_channel(self, guild_id: int, channel_id: int):
        await self._ensure_guild_exists(guild_id)
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute(
                'UPDATE guild_config SET welcome_channel_id = ?, welcome_enabled = 1 WHERE guild_id = ?',
                (channel_id, guild_id)
            )
            await db.commit()

    async def get_welcome_channel(self, guild_id: int) -> int:
        await self._ensure_guild_exists(guild_id)
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute(
                'SELECT welcome_channel_id, welcome_enabled FROM guild_config WHERE guild_id = ?',
                (guild_id,)
            ) as cursor:
                result = await cursor.fetchone()
                if result and result[1]:  # Check if welcome messages are enabled
                    return result[0]
                return None

    async def toggle_welcome(self, guild_id: int, enabled: bool):
        await self._ensure_guild_exists(guild_id)
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute(
                'UPDATE guild_config SET welcome_enabled = ? WHERE guild_id = ?',
                (enabled, guild_id)
            )
            await db.commit()

    async def is_welcome_enabled(self, guild_id: int) -> bool:
        await self._ensure_guild_exists(guild_id)
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute(
                'SELECT welcome_enabled FROM guild_config WHERE guild_id = ?',
                (guild_id,)
            ) as cursor:
                result = await cursor.fetchone()
                return bool(result[0]) if result else False

    # Auto Role Methods
    async def set_auto_role(self, guild_id: int, role_id: int):
        await self._ensure_guild_exists(guild_id)
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute(
                'UPDATE guild_config SET auto_role_id = ?, auto_role_enabled = 1 WHERE guild_id = ?',
                (role_id, guild_id)
            )
            await db.commit()

    async def get_auto_role(self, guild_id: int) -> int:
        await self._ensure_guild_exists(guild_id)
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute(
                'SELECT auto_role_id, auto_role_enabled FROM guild_config WHERE guild_id = ?',
                (guild_id,)
            ) as cursor:
                result = await cursor.fetchone()
                if result and result[1]:  # Check if auto-role is enabled
                    return result[0]
                return None

    async def toggle_auto_role(self, guild_id: int, enabled: bool):
        await self._ensure_guild_exists(guild_id)
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute(
                'UPDATE guild_config SET auto_role_enabled = ? WHERE guild_id = ?',
                (enabled, guild_id)
            )
            await db.commit()

    async def is_auto_role_enabled(self, guild_id: int) -> bool:
        await self._ensure_guild_exists(guild_id)
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute(
                'SELECT auto_role_enabled FROM guild_config WHERE guild_id = ?',
                (guild_id,)
            ) as cursor:
                result = await cursor.fetchone()
                return bool(result[0]) if result else False

    # Anti-invite methods
    async def set_anti_invite(self, guild_id: int, enabled: bool) -> bool:
        await self._ensure_guild_exists(guild_id)
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute(
                'UPDATE guild_config SET anti_invite_enabled = ? WHERE guild_id = ?',
                (enabled, guild_id)
            )
            await db.commit()
            return True

    async def is_anti_invite_enabled(self, guild_id: int) -> bool:
        await self._ensure_guild_exists(guild_id)
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute(
                'SELECT anti_invite_enabled FROM guild_config WHERE guild_id = ?',
                (guild_id,)
            ) as cursor:
                result = await cursor.fetchone()
                return bool(result[0]) if result else False

    # Warning Methods
    async def add_warning(self, guild_id: int, user_id: int, moderator_id: int, reason: str) -> int:
        await self._ensure_guild_exists(guild_id)
        async with aiosqlite.connect(self.db_file) as db:
            cursor = await db.execute(
                'INSERT INTO warnings (guild_id, user_id, moderator_id, reason) VALUES (?, ?, ?, ?)',
                (guild_id, user_id, moderator_id, reason)
            )
            await db.commit()
            return cursor.lastrowid

    async def get_warnings(self, guild_id: int, user_id: int) -> list:
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute(
                'SELECT id, moderator_id, reason, timestamp FROM warnings WHERE guild_id = ? AND user_id = ? ORDER BY timestamp DESC',
                (guild_id, user_id)
            ) as cursor:
                warnings = await cursor.fetchall()
                processed_warnings = []
                for warning in warnings:
                    warning_id, mod_id, reason, timestamp = warning
                    try:
                        # Try parsing with milliseconds and timezone
                        dt = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f%z')
                    except ValueError:
                        try:
                            # Try parsing without timezone (old format)
                            dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                            # Convert to UTC
                            dt = dt.replace(tzinfo=timezone.utc)
                        except ValueError:
                            # If all else fails, use current time
                            dt = datetime.now(timezone.utc)
                    processed_warnings.append((warning_id, mod_id, reason, dt))
                return processed_warnings

    async def remove_warning(self, guild_id: int, warning_id: int) -> bool:
        async with aiosqlite.connect(self.db_file) as db:
            cursor = await db.execute(
                'DELETE FROM warnings WHERE guild_id = ? AND id = ?',
                (guild_id, warning_id)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def clear_warnings(self, guild_id: int, user_id: int) -> int:
        async with aiosqlite.connect(self.db_file) as db:
            cursor = await db.execute(
                'DELETE FROM warnings WHERE guild_id = ? AND user_id = ?',
                (guild_id, user_id)
            )
            await db.commit()
            return cursor.rowcount

    # Tempban Methods
    async def add_tempban(self, guild_id: int, user_id: int, moderator_id: int, reason: str, unban_time: str) -> int:
        async with aiosqlite.connect(self.db_file) as db:
            cursor = await db.execute(
                'INSERT INTO tempbans (guild_id, user_id, moderator_id, reason, unban_time) VALUES (?, ?, ?, ?, ?)',
                (guild_id, user_id, moderator_id, reason, unban_time)
            )
            await db.commit()
            return cursor.lastrowid

    async def get_active_tempbans(self, guild_id: int = None) -> list:
        async with aiosqlite.connect(self.db_file) as db:
            if guild_id:
                query = '''
                    SELECT guild_id, user_id, moderator_id, reason, unban_time, timestamp 
                    FROM tempbans 
                    WHERE guild_id = ? AND active = 1 AND unban_time <= strftime('%Y-%m-%dT%H:%M:%S.000+00:00', 'now')
                '''
                params = (guild_id,)
            else:
                query = '''
                    SELECT guild_id, user_id, moderator_id, reason, unban_time, timestamp 
                    FROM tempbans 
                    WHERE active = 1 AND unban_time <= strftime('%Y-%m-%dT%H:%M:%S.000+00:00', 'now')
                '''
                params = ()
            
            async with db.execute(query, params) as cursor:
                tempbans = await cursor.fetchall()
                return [(guild_id, user_id, mod_id, reason, 
                        datetime.strptime(unban_time, '%Y-%m-%dT%H:%M:%S.%f%z'),
                        datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f%z'))
                        for guild_id, user_id, mod_id, reason, unban_time, timestamp in tempbans]

    async def deactivate_tempban(self, guild_id: int, user_id: int) -> bool:
        async with aiosqlite.connect(self.db_file) as db:
            cursor = await db.execute(
                'UPDATE tempbans SET active = 0 WHERE guild_id = ? AND user_id = ? AND active = 1',
                (guild_id, user_id)
            )
            await db.commit()
            return cursor.rowcount > 0

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
