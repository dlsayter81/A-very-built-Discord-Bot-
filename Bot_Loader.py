# BOT_LOADER.py -------------------> Updated Bot Loader
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from Utility.Cogs_Binder import bind_cog_categories

import os
import asyncio
from datetime import datetime, timezone

# =========================================================
# Load environment variables
# =========================================================
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID"))
ALLOWED_CHANNEL_ID = int(os.getenv("ALLOWED_CHANNEL_ID"))
MEMBER_ROLE_ID = int(os.getenv("MEMBER_ROLE_ID"))


# =========================================================
# Bot setup
# =========================================================
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents, owner_id=BOT_OWNER_ID)
bot.guild_id = GUILD_ID
bot.seal_channel_id = ALLOWED_CHANNEL_ID

# =========================================================
# Imports
# =========================================================
from Utility.Permission_Scopes import set_command_visibility
from Utility.timer_utils import has_timer_expired, cancel_guess_timer, _user_timers
from Utility import code_cleanup  # Cleanup expired redemption codes
bot.loop.create_task(bind_cog_categories(bot))  # ← Add this line

# =========================================================
# 🔒 Global trap check (replaces individual trap calls)
# =========================================================
@bot.check
async def trap_global_check(ctx: discord.ApplicationContext) -> bool:
    """
    Centralized trap:
    - Applies permanent self-seal to unauthorized users
    - Stops command execution for DM/non-admin/channel violations
    - Exempts all cogs inside the DM_Only folder
    """
    from Utility.Security_Trap import trap_check_for_seal_unseal

    # Exempt all commands whose cogs were loaded from DM_Only folder
    if ctx.command and ctx.command.cog and getattr(ctx.command.cog, "category", None) == "DM_Only":
        return True

    try:
        return await trap_check_for_seal_unseal(ctx)
    except Exception as e:
        print(f"⚠️ Error in global trap check: {e}")
        return False

# =========================================================
# COG LOADER
# =========================================================
def load_all_cogs():
    COG_CATEGORIES = ["Admin_Only", "Bot_Owner_Only", "DM_Only", "Server_Owner_Only"]
    BASE_PATH = "Cogs"

    for category in COG_CATEGORIES:
        folder_path = os.path.join(BASE_PATH, category)
        if not os.path.isdir(folder_path):
            continue

        for filename in os.listdir(folder_path):
            if filename.endswith(".py") and not filename.startswith("_"):
                module_path = f"{BASE_PATH}.{category}.{filename[:-3]}".replace("/", ".")
                try:
                    bot.load_extension(module_path)
                    print(f"📦 {filename[:-3]} loaded from {category}.")

                    # Attach folder category to the cog instance
                    cog = bot.get_cog(filename[:-3])
                    if cog:
                        cog.category = category

                    # Server_Owner_Only owner-only check
                    if category == "Server_Owner_Only" and cog:
                        for command in cog.get_application_commands():
                            async def owner_only_check(ctx: discord.ApplicationContext):
                                return ctx.author.id == BOT_OWNER_ID
                            command.checks.append(owner_only_check)

                except Exception as e:
                    print(f"❌ Failed to load {filename[:-3]} from {category}: {e}")

    # Apply visibility rules to all slash commands
    for command in bot.application_commands:
        set_command_visibility(command)

# =========================================================
# Background tasks
# =========================================================
@tasks.loop(seconds=5)
async def monitor_expired_timers():
    """Check 30-second guess timers and DM users if expired."""
    expired_users = []

    for user_id, info in list(_user_timers.items()):
        if has_timer_expired(user_id):
            expired_users.append(user_id)
            cancel_guess_timer(user_id)

    for user_id in expired_users:
        guild = bot.get_guild(GUILD_ID)
        if guild:
            member = guild.get_member(int(user_id))
            if member:
                try:
                    await member.send(
                        "⏳ You ran out of time for guessing the secret number.\n"
                        "Unfortunately, your guess attempt has failed."
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass

# =========================================================
# Bot ready event
# =========================================================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print("🔧 Bot is ready and cogs are loaded.")

    # Start background tasks
    monitor_expired_timers.start()
    bot.loop.create_task(code_cleanup.cleanup_expired_codes(bot))

# =========================================================
# RUN BOT
# =========================================================
if __name__ == "__main__":
    load_all_cogs()
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ DISCORD_TOKEN not found in .env file.")
