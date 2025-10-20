import discord
from discord.ui import View, button
from Utility.general_utils import load_json, save_json, JOIN_CODES_FILE
from Utility.code_generator import generate_code
from Utility.emoji_validator import letter_map, number_map

class JoinGateView(View):
    @button(label="Begin Trial", style=discord.ButtonStyle.primary, emoji="🧿")
    async def begin_trial(self, button: discord.ui.Button, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        trial = generate_code(user_id, expires_in=15)

        # Save the trial
        data = load_json(JOIN_CODES_FILE, default={})
        data[user_id] = trial
        save_json(JOIN_CODES_FILE, data)

        # Build the embed
        embed = discord.Embed(
            title="🧿 Your Initiation Code",
            description=(
                f"Your code is: `{trial['code']}`\n\n"
                "Please emojize it using the symbols below and send it back here.\n"
                "Only exact matches will be accepted. Formatting quirks like spacing are forgiven."
            ),
            color=discord.Color.blue()
        )

        embed.add_field(name="🔡 Letters A–Z", value=" ".join(letter_map.keys()), inline=False)
        embed.add_field(name="🔢 Numbers 0–9", value=" ".join(number_map.keys()), inline=False)
        embed.set_footer(text="This ritual is sacred. Misuse will be rejected.")

        try:
            await interaction.user.send(embed=embed)
            await interaction.response.send_message("Check your DMs for the ritual code.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I couldn't DM you. Please check your privacy settings.", ephemeral=True)
