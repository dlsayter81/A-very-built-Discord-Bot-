import discord
from discord.ext import commands
from datetime import datetime, timezone
from typing import Annotated

from Utility.general_utils import (
    load_json,
    save_json,
    HARDLOCKS_FILE,
    RANDOM_CODES_FILE,
    PERMANENT_SEALS_FILE
)
from Utility.Security_Trap import trap_check_for_seal_unseal  # 🔒 Trap utility

class SealAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name="seal",
        description="Admin-only: Hardlock a user until a specific date (MM/DD/YY) or permanently"
    )
    async def seal(
        self,
        ctx: discord.ApplicationContext,
        user: Annotated[
            discord.Member,
            discord.Option(description="User to seal (mention or ID)")
        ],
        date: Annotated[
            str,
            discord.Option(description="Date in MM/DD/YY format", required=False)
        ] = None,
        reason: Annotated[
            str,
            discord.Option(description="Reason for sealing", required=False)
        ] = "Manual seal"
    ):
        # Defer to avoid interaction timeout
        await ctx.defer()

        # 🚨 Step 1: Security Trap check
        if not await trap_check_for_seal_unseal(ctx, is_unseal=False):
            return  # Trap already handled unauthorized use

        target_id = str(user.id)

        # 🧱 Step 2: Permanent Seal if no date is provided
        if not date:
            permanent_seals = load_json(PERMANENT_SEALS_FILE, default={})
            permanent_seals[target_id] = {
                "sealed_at": int(datetime.now(timezone.utc).timestamp()),
                "reason": reason
            }
            save_json(PERMANENT_SEALS_FILE, permanent_seals)

            # Clear any random timeout codes
            timeout_codes = load_json(RANDOM_CODES_FILE, default={})
            if target_id in timeout_codes:
                del timeout_codes[target_id]
                save_json(RANDOM_CODES_FILE, timeout_codes)

            await ctx.followup.send(
                f"🔒 <@{target_id}> has been **permanently sealed**.\n"
                f"Reason: *{reason}*",
                ephemeral=True
            )
            return

        # 🕒 Step 3: Timed Seal (date provided)
        try:
            lock_until_dt = datetime.strptime(date, "%m/%d/%y").replace(tzinfo=timezone.utc)
            lock_until_ts = lock_until_dt.timestamp()
        except ValueError:
            await ctx.followup.send("❌ Invalid date format. Use MM/DD/YY.", ephemeral=True)
            return

        hardlocked = load_json(HARDLOCKS_FILE, default={})
        hardlocked[target_id] = {
            "misuse_attempts": 0,
            "hardlock_until": lock_until_ts,
            "hardlock_reason": reason
        }
        save_json(HARDLOCKS_FILE, hardlocked)

        # Clear any random timeout codes
        timeout_codes = load_json(RANDOM_CODES_FILE, default={})
        if target_id in timeout_codes:
            del timeout_codes[target_id]
            save_json(RANDOM_CODES_FILE, timeout_codes)

        await ctx.followup.send(
            f"🔒 <@{target_id}> has been sealed until **{lock_until_dt.strftime('%B %d, %Y')}**.\n"
            f"Reason: *{reason}*",
            ephemeral=True
        )


def setup(bot):
    bot.add_cog(SealAdmin(bot))
