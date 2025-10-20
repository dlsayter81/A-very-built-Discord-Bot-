# 🤖 A Very Built Discord Bot

Welcome to **A Very Built Discord Bot** — a modular, admin-focused Discord bot built with [Pycord](https://docs.pycord.dev). Designed for symbolic clarity, secure orchestration, and server-side rituals, this bot is ideal for managing Discord communities with precision and control.

## 🔐 Purpose

This bot is intended for **administrative use only**. Sensitive commands are locked to a specific channel and require elevated roles. All configuration is handled via environment variables to ensure security and flexibility.

---

## 📦 Requirements

- Python 3.10+
- Git
- Discord bot token and client ID
- Virtual environment (recommended)

---

## 🚀 Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/dlsayter81/A-very-built-Discord-Bot-.git
cd A-very-built-Discord-Bot-


2. Configure Environment Variables

Create a .env file in the root directory of the project and add the following variables:
DISCORD_TOKEN=your_bot_token_here
GUILD_ID=your_guild_id_here
ALLOWED_CHANNEL_ID=channel_id_for_admin_commands
BOT_OWNER_ID=your_discord_user_id
MEMBER_ROLE_ID=role_id_for_general_members

Note: Fill in the values with the actual information for your server.



🔧 Quickstart with .bat Scripts

To set up and launch the bot using the included batch files:

1. Create the environment and install dependencies

A requirements.txt file is provided. Use the Runonce.bat script to:

Create a new virtual environment in a folder named env

Install all required dependencies

Run the script by double-clicking Runonce.bat.

2. Launch the Bot

After setup:

Activate the environment (automatically done by the batch scripts)

Run the bot by double-clicking Bot_Loader.bat

This will start the bot with the previously configured environment.

Your bot should now be live and ready for administrative tasks!


