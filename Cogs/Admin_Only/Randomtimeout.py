import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime, timedelta, timezone

from Utility.general_utils import (
    load_json,
    save_json,
    add_minutes,
    RANDOM_CODES_FILE,
    FULL_DURATION_FILE,
)
from Utility.Security_Trap import trap_check_for_seal_unseal  # 🔒 Trap check

class RandomTimeout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.full_duration_users = load_json(FULL_DURATION_FILE, default=[])
        if not isinstance(self.full_duration_users, list):
            self.full_duration_users = []

    @commands.slash_command(
        name="randomtimeout",
        description="Randomly timeout a non-admin member (April Fools style)"
    )
    async def random_timeout(self, ctx: discord.ApplicationContext):
        # Defer response to avoid interaction timeout
        await ctx.defer()

        # 🚨 Step 1: Security Trap check (DM / non-admin)
        if not await trap_check_for_seal_unseal(ctx):
            return  # Trap will handle permanent seal if unauthorized

        guild = ctx.guild
        now = datetime.now(timezone.utc)

        # Eligible members: non-bot, non-admin, not full-duration, not currently timed out
        members = [
            m for m in guild.members
            if not m.bot and not m.guild_permissions.administrator
            and m.id not in self.full_duration_users
            and not (m.communication_disabled_until and m.communication_disabled_until > now)
        ]

        if not members:
            await ctx.followup.send("❌ No eligible members found.", ephemeral=True)
            return

        # Randomly pick a member
        selected = random.choice(members)
        duration_days = random.randint(5, 28)
        until = now + timedelta(days=duration_days)

        # Generate redemption info
        code = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=8))
        secret_number = random.randint(1, 100)
        reduction_percent = random.randint(10, 100)
        code_expiry = add_minutes(random.randint(3, 5))

        try:
            # Apply timeout
            await selected.edit(
                communication_disabled_until=until,
                reason="Random timeout prank"
            )

            # Save redemption code
            random_codes = load_json(RANDOM_CODES_FILE, default={})
            random_codes[str(selected.id)] = {
                "code": code,
                "expires_at": code_expiry,
                "reduction_percent": reduction_percent,
                "secret_number": secret_number,
                "attempts_left": 3
            }
            save_json(RANDOM_CODES_FILE, random_codes)

            # Calculate precise time left for the code
            expiry_dt = datetime.fromtimestamp(code_expiry, tz=timezone.utc)
            delta = expiry_dt - now
            minutes_left = delta.seconds // 60
            seconds_left = delta.seconds % 60

            # DM the member with code
            dm_message = (
                f"🎉 You've been randomly timed out for **{duration_days} days**!\n"
                f"Use `/redeem {code}` in DMs to unlock your guess attempt.\n"
                f"You have **{minutes_left} minutes and {seconds_left} seconds** to act!"
            )

            try:
                await asyncio.wait_for(selected.send(dm_message), timeout=5)
            except (discord.Forbidden, asyncio.TimeoutError):
                print(f"⚠️ Could not DM {selected} or it timed out.")
            except Exception as e:
                print(f"⚠️ Unexpected DM error for {selected}: {e}")

            # Respond to the admin
            await ctx.followup.send(
                f"{selected.mention} got hit with a **{duration_days}-day** timeout! 😈",
                ephemeral=True
            )

        except discord.Forbidden:
            await ctx.followup.send("❌ Missing permission to timeout that member.", ephemeral=True)
        except discord.HTTPException as e:
            await ctx.followup.send(f"⚠️ Timeout failed: {e}", ephemeral=True)

def setup(bot):
    bot.add_cog(RandomTimeout(bot))
