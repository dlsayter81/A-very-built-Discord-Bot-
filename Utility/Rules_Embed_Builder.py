import discord

def build_rules_embed() -> discord.Embed:
    embed = discord.Embed(
        title="📜 Server Rules & Entry Ritual",
        description=(
            "Welcome to the realm.\n\n"
            "Please read the rules carefully. To begin your initiation, click the 🧿 button below.\n"
            "You will receive a symbolic code via DM. You must emojize it and send it back.\n"
            "Only then will the gates open."
        ),
        color=discord.Color.gold()
    )
    embed.set_footer(text="This ritual is sacred. Misuse will be rejected.")
    return embed
