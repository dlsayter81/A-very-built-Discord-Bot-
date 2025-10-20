# dm_cleanup.py
import discord
from discord.ext import commands
import asyncio

class DMCleanup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name="dmclean",
        description="Delete all of the bot's DMs from a user (Bot Owner only)"
    )
    @commands.is_owner()
    async def dmclean(
        self,
        ctx: discord.ApplicationContext,
        target: discord.User = discord.Option(discord.User, description="User whose DMs to clean")
    ):
        await ctx.respond(f"🧹 Starting DM cleanup for {target}...", ephemeral=True)
        deleted_count = 0
        batch = 0

        # Ensure DM channel exists
        dm_channel = target.dm_channel or await target.create_dm()

        async for message in dm_channel.history(limit=None):
            if message.author.id != self.bot.user.id:
                continue  # only delete bot's messages

            try:
                await message.delete()
                deleted_count += 1
                batch += 1
            except discord.HTTPException:
                continue  # skip any failed deletes

            # Throttle after every 5 messages
            if batch >= 5:
                await asyncio.sleep(15)
                batch = 0

        await ctx.followup.send(
            f"✅ Finished cleaning DMs. Deleted {deleted_count} messages.",
            ephemeral=True
        )

def setup(bot):
    bot.add_cog(DMCleanup(bot))
