# GitHub Commit Monitor Bot

A Telegram bot designed to monitor GitHub repositories for new commits and notify users automatically.

## Overview

The GitHub Commit Monitor Bot continuously tracks specified GitHub repositories and sends real-time notifications about new commits directly to your Telegram chat. It supports both public and private repositories with configurable monitoring intervals.

## Features

| Feature | Description |
|---------|-------------|
| **Multi-Repository Support** | Monitor multiple GitHub repositories simultaneously |
| **Real-Time Notifications** | Instant alerts for new commits with detailed information |
| **Private Repository Support** | Monitor private repositories with proper GitHub token permissions |
| **Multi-Language Interface** | Available in English and Persian (Farsi) |
| **Configurable Check Intervals** | Adjustable monitoring frequency (default: 60 seconds) |
| **Manual Check Capability** | Trigger immediate repository checks on demand |
| **Statistics Tracking** | View monitoring statistics and system status |
| **Admin Controls** | Restrict bot access to authorized users only |

## Prerequisites

Before setting up the bot, ensure you have:

1. **GitHub Account** with repositories to monitor
2. **Telegram Account** and the Telegram app
3. **Python 3.7+** installed on your system

## Setup Instructions

### Step 1: Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow the prompts to name your bot
4. Save the provided bot token securely

### Step 2: Generate GitHub Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Name your token (e.g., "Telegram Bot Monitor")
4. Select these scopes:
   - `repo` (for private repository access)
   - `public_repo` (if only monitoring public repositories)
5. Click "Generate token" and copy it immediately

### Step 3: Configure the Bot

1. Clone or download the bot files to your server
2. Install required dependencies:
   ```bash
   pip install pyTelegramBotAPI requests python-dotenv
   ```
3. Create a `.env` file with the following configuration:
   ```
   BOT_TOKEN=your_telegram_bot_token_here
   GITHUB_TOKEN=your_github_personal_access_token_here
   ADMIN_CHAT_IDS=your_telegram_user_id_here
   CHECK_INTERVAL=60
   DATABASE_PATH=github_bot.db
   LOG_FILE=github_bot.log
   LOG_LEVEL=INFO
   ```
4. Replace `your_telegram_user_id_here` with your actual Telegram user ID (you can get this from `@userinfobot` on Telegram)

### Step 4: Run the Bot

1. Start the bot with:
   ```bash
   python bot.py
   ```
2. The bot will test the GitHub API connection and start monitoring
3. Open Telegram and start a chat with your bot
4. Send `/start` to initialize the bot

## Usage Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Initialize the bot and display welcome message | `/start` |
| `/help` | Display detailed usage instructions | `/help` |
| `/add` | Add a repository to monitor | `/add username/repository-name` |
| `/remove` | Remove a repository from monitoring | `/remove username/repository-name` |
| `/list` | List all monitored repositories | `/list` |
| `/check` | Manually check for new commits | `/check` |
| `/stats` | Display bot statistics and status | `/stats` |
| `/status` | Check GitHub API connection status | `/status` |
| `/language` | Change bot interface language | `/language` |

## Repository Management

- Add repositories using the format: `username/repository-name`
- The bot automatically detects the default branch
- Notifications include:
  - Commit message
  - Author information
  - Timestamp
  - File change statistics
  - Direct links to the commit and repository

## Technical Details

- **Database**: SQLite for storing user preferences and repository data
- **API Integration**: GitHub REST API v3
- **Monitoring**: Background thread with configurable interval
- **Error Handling**: Comprehensive logging and error recovery
- **Security**: Admin-only access with configurable user IDs

## Troubleshooting

Common issues and solutions:

1. **Bot not responding**: Verify the bot token in `.env` file
2. **Repository not found**: Ensure the repository exists and the GitHub token has proper permissions
3. **No notifications**: Check if the repository has new commits and verify the bot is running
4. **Connection errors**: Validate GitHub token and internet connectivity

## File Structure

```
github-monitor-bot/
├── bot.py              # Main bot application
├── config.py           # Configuration settings
├── database.py         # Database operations
├── github_api.py       # GitHub API interactions
├── monitor.py          # Repository monitoring logic
├── translation_manager.py  # Multi-language support
├── translations.json   # Language strings
└── .env               # Environment variables (create this)
```

## Support

For additional assistance:
1. Review the `/help` command in the bot
2. Check the log file for error messages
3. Verify all tokens and IDs are correctly configured

The bot will automatically reconnect if temporary network issues occur and continue monitoring your repositories according to the configured interval.