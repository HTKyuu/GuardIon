# Guard Ion Discord Moderation Bot

A comprehensive Discord moderation bot built with discord.py, featuring server management, moderation tools, and logging capabilities.

## Features

- **Moderation Commands**
  - Ban/Unban/Softban
  - Kick
  - Warn System
  - Message Clear
  - Channel Lock/Unlock
  - Slowmode Management

- **Utility Features**
  - User Information
  - Guild Information
  - Help Command
  - Logging System

- **Setup Commands**
  - Log Channel Configuration
  - Welcome Messages
  - Auto-Role System
  - Anti-Invite System

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your Discord bot token:
```
DISCORD_TOKEN=your_token_here
```

3. Run the bot:
```bash
python bot.py
```

## Permissions

- Moderation commands require appropriate moderator permissions
- Setup commands require Manage Server permission
- Some commands require specific channel or role permissions

## License

This project is licensed under the MIT License - see the LICENSE file for details.
