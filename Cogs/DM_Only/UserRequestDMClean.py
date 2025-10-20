# user_dm_cleanup.py
import discord
from discord.ext import commands
import asyncio

class UserDMCleanup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name="mydmclean",
        description="Delete messages in your DM channel with the bot"
    )
    async def mydmclean(
        self,
        ctx: discord.ApplicationContext,
        delete_their_messages: bool = discord.Option(
            bool,
            description="Also delete your own messages (optional)",
            default=False
        )
    ):
        await ctx.respond("🧹 Starting DM cleanup...", ephemeral=True)

        deleted_count = 0
        batch = 0

        dm_channel = ctx.author.dm_channel or await ctx.author.create_dm()

        async for message in dm_channel.history(limit=None):
            # Skip messages unless they are from the bot or optionally the user
            if message.author.id != self.bot.user.id and not (delete_their_messages and message.author.id == ctx.author.id):
                continue

            try:
                await message.delete()
                deleted_count += 1
                batch += 1
            except discord.HTTPException:
                continue

            if batch >= 5:
                await asyncio.sleep(15)
                batch = 0

        await ctx.followup.send(f"✅ Finished cleaning DMs. Deleted {deleted_count} messages.", ephemeral=True)

def setup(bot):
    bot.add_cog(UserDMCleanup(bot))
