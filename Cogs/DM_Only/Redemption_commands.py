# redemption_commands.py

import discord
from discord.ext import commands
import asyncio

from Utility.Redemption_Utility import (
    validate_code,
    unlock_guess,
    handle_guess,
    apply_reduction,
    is_sealed,
    store_dm_message,
    TIMEOUT_CODES_FILE,
)

class RedemptionCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def format_lock_time(self, seconds: float) -> str:
        periods = [
            ("year", 60 * 60 * 24 * 365),
            ("month", 60 * 60 * 24 * 30),
            ("day", 60 * 60 * 24),
            ("hour", 60 * 60),
            ("minute", 60),
            ("second", 1)
        ]
        parts = []
        for name, count in periods:
            value = int(seconds // count)
            if value:
                seconds -= value * count
                parts.append(f"{value} {name}{'s' if value != 1 else ''}")
        return ", ".join(parts)

    def get_seal_message(self, seal_status) -> str:
        if isinstance(seal_status, float):
            time_str = self.format_lock_time(seal_status)
            return (
                f"⛔ You are locked out from redemption attempts due to misuse.\n"
                f"Please wait **{time_str}** before trying again."
            )
        elif seal_status == "permanent":
            return (
                f"⛔ You are permanently sealed. The vault will not open.\n"
                f"Redemption is forbidden."
            )
        return ""

    @commands.slash_command(
        name="redeem",
        description="Redeem your timeout code to unlock a guess attempt"
    )
    async def redeem(
        self,
        ctx: discord.ApplicationContext,
        code: str = discord.Option(
            str,
            description="Your redemption code"
        )
    ):
        user_id = str(ctx.author.id)
        seal_status = is_sealed(user_id)
        if seal_status:
            await ctx.respond(self.get_seal_message(seal_status), ephemeral=True)
            return

        entry = validate_code(user_id, code)
        if not entry:
            await ctx.respond("❌ Invalid or expired code.", ephemeral=True)
            return

        # Store the message ID for automatic deletion later
        asyncio.create_task(store_dm_message(ctx.author, ctx.interaction, user_id, TIMEOUT_CODES_FILE))

        # Unlock the guess and trigger DM deletion after
        unlock_guess(user_id, bot=self.bot)

        await ctx.respond(
            f"🔓 Code accepted! You may now use `/tryguess <number>` to guess the secret number.\n"
            f"You have **{entry['attempts_left']} attempts**. Aim wisely."
        )

    @commands.slash_command(
        name="tryguess",
        description="Guess the secret number to reduce your timeout"
    )
    async def tryguess(
        self,
        ctx: discord.ApplicationContext,
        number: int = discord.Option(
            int,
            description="Your guess (1–100)",
            min_value=1,
            max_value=100
        )
    ):
        user_id = str(ctx.author.id)
        seal_status = is_sealed(user_id)
        if seal_status:
            await ctx.respond(self.get_seal_message(seal_status), ephemeral=True)
            return

        result = handle_guess(user_id, number)

        if result.get("error") == "⏳ Time's up! You failed to guess in time.":
            try:
                await ctx.author.send(
                    "⏳ You ran out of time for guessing the secret number.\n"
                    "Unfortunately, your guess attempt has failed."
                )
            except discord.Forbidden:
                pass
            await ctx.respond(f"❌ {result['error']}")
            return

        if result.get("error"):
            await ctx.respond(f"❌ {result['error']}")
            return

        if result["result"] == "miss":
            await ctx.respond(
                f"❌ Missed! You have **{result['attempts_left']} attempts** left.\n"
                f"Try again with `/tryguess <number>`."
            )
            return

        guild = self.bot.get_guild(self.bot.guild_id)
        member = guild.get_member(ctx.author.id) if guild else None
        if not member:
            await ctx.respond("⚠️ Could not find your member profile in the server.")
            return

        reduction = result["reduction"]
        secret = result["secret"]
        response = await apply_reduction(member, reduction)

        if result["result"] == "full":
            message = (
                f"🎯 You were within range of the secret number **{secret}**.\n"
                f"✅ Timeout reduced by **{reduction}%**.\n"
                f"{response}"
            )
        elif result["result"] == "half":
            message = (
                f"❌ You were not within range of the secret number **{secret}**.\n"
                f"⚖️ Because this was an admin-initialized second chance, your timeout was reduced by **{reduction}%**.\n"
                f"{response}"
            )

        await ctx.respond(message)

def setup(bot):
    bot.add_cog(RedemptionCommands(bot))
