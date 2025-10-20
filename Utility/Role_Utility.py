import discord
from os import getenv

MEMBER_ROLE_ID = int(getenv("MEMBER_ROLE_ID"))
GUILD_ID = int(getenv("GUILD_ID"))

async def assign_member_role(bot: discord.Bot, user: discord.User):
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print(f"⚠️ Guild with ID {GUILD_ID} not found.")
        return

    member = guild.get_member(user.id)
    if not member:
        try:
            member = await guild.fetch_member(user.id)
        except discord.NotFound:
            print(f"⚠️ User {user.id} not found in guild.")
            return

    role = guild.get_role(MEMBER_ROLE_ID)
    if role:
        await member.add_roles(role, reason="Passed initiation trial")
    else:
        print(f"⚠️ Role ID {MEMBER_ROLE_ID} not found in guild {guild.name}")
