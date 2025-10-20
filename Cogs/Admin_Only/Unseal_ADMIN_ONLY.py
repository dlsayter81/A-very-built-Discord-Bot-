import discord
from discord.ext import commands

from Utility.Redemption_Utility import unseal_user
from Utility.Security_Trap import (
    trap_check_for_seal_unseal,  # General misuse trap (DM / non-admin)
    trap_check_self_unseal       # Self-unseal escalation
)

class UnsealAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name="unseal",
        description="Admin-only: Remove a user from the hardlock list"
    )
    async def unseal(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Member = None,
        user_id: str = None
    ):
        # Defer response to avoid interaction timeout
        await ctx.defer()

        # 🚨 Step 1: Security Trap for DM / non-admin misuse
        if not await trap_check_for_seal_unseal(ctx, is_unseal=True):
            return  # Trap already handled unauthorized use

        # Step 2: Determine target ID
        if user:
            target_id = str(user.id)
        elif user_id:
            target_id = str(user_id)
        else:
            await ctx.followup.send(
                "❌ You must specify a user or user ID to unseal.",
                ephemeral=True
            )
            return

        # 🚨 Step 3: Self-unseal escalation trap
        if not await trap_check_self_unseal(ctx, target_id):
            return  # Trap applied permanent seal if user tried to bypass hardlock

        # 🧹 Step 4: Perform actual unseal
        try:
            success = unseal_user(target_id)
        except Exception as e:
            await ctx.followup.send(
                f"⚠️ An error occurred while unsealing: {e}",
                ephemeral=True
            )
            return

        if success:
            await ctx.followup.send(
                f"✅ User <@{target_id}> has been unsealed successfully.",
                ephemeral=True
            )
        else:
            await ctx.followup.send(
                f"❌ Failed to unseal user <@{target_id}>.",
                ephemeral=True
            )

    @unseal.error
    async def unseal_error(self, ctx, error):
        # Handles permission errors or any uncaught exceptions
        if isinstance(error, commands.MissingPermissions):
            await ctx.followup.send(
                "❌ You must be a server admin to use this command.",
                ephemeral=True
            )
        else:
            await ctx.followup.send(
                f"⚠️ Unexpected error: {error}",
                ephemeral=True
            )


def setup(bot):
    bot.add_cog(UnsealAdmin(bot))
