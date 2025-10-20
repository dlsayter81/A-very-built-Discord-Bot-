import discord
from discord.ext import commands
from Utility.general_utils import load_json, save_json, PERMANENT_SEALS_FILE
from Utility.Security_Trap import trap_check_for_seal_unseal  # 🔒 Global trap

class PermanentUnseal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name="permanent_unseal",
        description="Server Owner Only: Remove a permanent seal from a user"
    )
    async def permanent_unseal(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Member = None,
        user_id: str = None
    ):
        # Defer to avoid interaction timeout
        await ctx.defer()

        # 🚨 Global trap (anti-DM / non-admin / abuse)
        if not await trap_check_for_seal_unseal(ctx):
            return  # Trap handles misuse (e.g., sealing or blocking)

        # 👑 Only server owner can unseal
        if not ctx.guild or ctx.author.id != ctx.guild.owner_id:
            await ctx.followup.send(
                "❌ Only the **server owner** can run this command.",
                ephemeral=True
            )
            return

        # 🆔 Resolve target ID
        target_id = str(user.id) if user else str(user_id) if user_id else None
        if not target_id:
            await ctx.followup.send(
                "❌ You must provide a user mention or a user ID.",
                ephemeral=True
            )
            return

        # 🧹 Remove from permanent seals file
        permanent_seals = load_json(PERMANENT_SEALS_FILE, default={})
        if target_id not in permanent_seals:
            await ctx.followup.send(
                f"⚠️ User <@{target_id}> does not have a permanent seal.",
                ephemeral=True
            )
            return

        permanent_seals.pop(target_id)
        save_json(PERMANENT_SEALS_FILE, permanent_seals)

        await ctx.followup.send(
            f"✅ Permanent seal removed for <@{target_id}>.",
            ephemeral=True
        )

def setup(bot):
    bot.add_cog(PermanentUnseal(bot))
