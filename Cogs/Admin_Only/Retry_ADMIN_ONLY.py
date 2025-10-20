import discord
from discord.ext import commands
import random
from datetime import datetime, timezone

from Utility.general_utils import (
    load_json,
    save_json,
    add_minutes,
    TIMEOUT_CODES_FILE,
)
from Utility.Security_Trap import trap_check_for_seal_unseal  # 🔒 Trap check

class RetryCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name="retry",
        description="Give a user another chance and let them earn a mute reduction"
    )
    async def retry(
        self,
        ctx: discord.ApplicationContext,
        target: discord.Member = discord.Option(
            discord.Member,
            description="User to retry (mention or ID)"
        ),
        reduction_percent: int = discord.Option(
            int,
            description="Mute reduction percentage (leave blank for random)",
            required=False,
            min_value=1,
            max_value=100
        )
    ):
        # Defer to prevent interaction timeout
        await ctx.defer()

        # 🚨 Step 1: Security trap check (DM / non-admin)
        if not await trap_check_for_seal_unseal(ctx):
            return  # Trap applies permanent seal if unauthorized

        # 🎲 Random reduction if none provided
        if reduction_percent is None:
            reduction_percent = random.randint(10, 100)

        # 🔐 Generate code and secret number
        code = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=8))
        secret_number = random.randint(1, 100)
        code_minutes = random.randint(3, 5)
        expires_at = add_minutes(code_minutes)

        # 📦 Store redemption data
        timeout_codes = load_json(TIMEOUT_CODES_FILE, default={})
        timeout_codes[str(target.id)] = {
            "code": code,
            "expires_at": expires_at,
            "reduction_percent": reduction_percent,
            "secret_number": secret_number,
            "attempts_left": 3,
            "can_guess": False
        }
        save_json(TIMEOUT_CODES_FILE, timeout_codes)

        # 📩 Try DMing the user
        expiry_dt = datetime.fromtimestamp(expires_at, tz=timezone.utc)
        delta = expiry_dt - datetime.now(timezone.utc)
        minutes_left = delta.seconds // 60
        seconds_left = delta.seconds % 60

        try:
            await target.send(
                f"🔁 You've been granted a second chance.\n"
                f"Use `/redeem {code}` in DMs to unlock your guess attempt.\n"
                f"You have **{minutes_left} minutes and {seconds_left} seconds** to act.\n"
                f"Guess close to the secret number to reduce your timeout!"
            )
            dm_status = "📩 DM sent successfully."
        except discord.Forbidden:
            dm_status = "⚠️ Could not DM the user (DMs are closed)."
        except discord.HTTPException as e:
            dm_status = f"⚠️ Failed to DM user: {e}"

        # ✅ Confirm to admin
        await ctx.followup.send(
            f"🔁 {target.mention} has been given another chance.\n"
            f"🧠 Redemption code: `{code}` (expires in {minutes_left}m {seconds_left}s)\n"
            f"📉 Reduction potential: {reduction_percent}%\n"
            f"{dm_status}",
            ephemeral=True
        )

    @retry.error
    async def retry_error(self, ctx, error):
        # Handle permission errors or uncaught exceptions
        if isinstance(error, commands.MissingPermissions):
            await ctx.followup.send(
                "❌ You must be a server admin to use this command.",
                ephemeral=True
            )
        else:
            await ctx.followup.send(
                f"⚠️ An error occurred: {error}",
                ephemeral=True
            )

def setup(bot):
    bot.add_cog(RetryCommands(bot))
