import discord
from discord.ext import commands
from Utility.Rules_Embed_Builder import build_rules_embed
from UI.Join_Gate_View import JoinGateView

class JoinGatekeeper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="rules", description="Show the server rules")
    async def rules(self, ctx: discord.ApplicationContext):
        embed = build_rules_embed()
        view = JoinGateView()
        await ctx.respond(embed=embed, view=view)

def setup(bot):
    bot.add_cog(JoinGatekeeper(bot))
