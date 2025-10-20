import discord
from discord.ui import View, button
from Utility.general_utils import load_json, save_json, JOIN_CODES_FILE, FAILURE_LOG_FILE
from Utility.code_generator import generate_code
from Utility.emoji_validator import letter_map, number_map
from Utility.time_gate import get_lockout_timestamp, is_locked_out, get_remaining_lockout

MAX_FAILURES = 3  # 👈 How many tries allowed before lockout

class JoinGateView(View):
    @button(label="Begin Trial", style=discord.ButtonStyle.primary, emoji="🧿")
    async def begin_trial(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)

        # 🔒 Load failure log and check lockout
        failure_log = load_json(FAILURE_LOG_FILE, default={})
        failure = failure_log.get(user_id, {"failures": 0})

        # ⛔ Check active lockout
        if "locked_until" in failure:
            if is_locked_out(failure["locked_until"]):
                # ❌ Still locked — remove lingering trial just in case
                trial_data = load_json(JOIN_CODES_FILE, default={})
                if user_id in trial_data:
                    del trial_data[user_id]
                    save_json(JOIN_CODES_FILE, trial_data)

                hours, minutes = get_remaining_lockout(failure["locked_until"])
                await interaction.response.send_message(
                    f"⛔ You are locked out due to failed attempts.\n"
                    f"🕒 Try again in {hours}h {minutes}m or contact an admin.",
                    ephemeral=True
                )

                # 📨 Optional personal DM notice if not already sent
                try:
                    await interaction.user.send(
                        f"⛔ You are locked out of the initiation process for {hours}h {minutes}m.\n"
                        "Please try again later or contact an administrator."
                    )
                except discord.Forbidden:
                    pass

                return
            else:
                # 🔓 Lockout expired — reset failure count
                failure = {"failures": 0}
                failure_log[user_id] = failure
                save_json(FAILURE_LOG_FILE, failure_log)

        # 🧭 Personal feedback about attempts left
        remaining_attempts = MAX_FAILURES - failure.get("failures", 0)
        if failure.get("failures", 0) > 0:
            await interaction.response.send_message(
                f"⚠️ You have {remaining_attempts} attempt{'s' if remaining_attempts != 1 else ''} remaining "
                f"before you will be locked out.",
                ephemeral=True
            )

        # 🧪 Generate trial code
        trial = generate_code(user_id, expires_in=15)
        trial_data = load_json(JOIN_CODES_FILE, default={})
        trial_data[user_id] = trial
        save_json(JOIN_CODES_FILE, trial_data)

        # 📜 Build the embed
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

        # 📩 DM the user the code
        try:
            await interaction.user.send(embed=embed)
            # 🪄 If they already got a warning above, don't send a second response
            if failure.get("failures", 0) == 0:
                await interaction.response.send_message(
                    "Check your DMs for the ritual code.",
                    ephemeral=True
                )
            else:
                # If a warning was already sent, send a follow-up
                await interaction.followup.send(
                    "📩 Check your DMs for the ritual code.",
                    ephemeral=True
                )
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ I couldn't DM you. Please check your privacy settings and try again.",
                ephemeral=True
            )
