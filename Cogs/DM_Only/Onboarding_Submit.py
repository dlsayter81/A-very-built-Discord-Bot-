import discord
from discord.ext import commands
from discord import Option
from datetime import timedelta
from Utility.general_utils import load_json, save_json, JOIN_CODES_FILE, FAILURE_LOG_FILE
from Utility.emoji_validator import extract_emojis, decode_emoji_sequence
from Utility.Role_Utility import assign_member_role
from Utility.time_gate import get_lockout_timestamp, is_locked_out, get_remaining_lockout

MAX_FAILURES = 3
LOCKOUT_DURATION = timedelta(hours=15)

class Onboarding_Submit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def clean(self, text: str) -> str:
        return "".join(c for c in text if c.isalnum()).upper()

    @discord.slash_command(name="submit", description="Submit your emojiized initiation code")
    async def submit(
        self,
        ctx: discord.ApplicationContext,
        code: str = Option(str, "Paste your emojiized code here")
    ):
        user_id = str(ctx.user.id)

        # 🔒 Load failure log
        failure_log = load_json(FAILURE_LOG_FILE, default={})
        failure = failure_log.get(user_id, {"failures": 0})

        # 🛡 Check lockout
        if "locked_until" in failure and is_locked_out(failure["locked_until"]):
            hours, minutes = get_remaining_lockout(failure["locked_until"])
            await ctx.respond(
                f"⛔ You're locked out due to failed attempts.\n"
                f"Try again in {hours}h {minutes}m or contact an admin.",
                ephemeral=True
            )
            return

        # 🧼 Lockout expired — reset failure count if present
        if "locked_until" in failure and not is_locked_out(failure["locked_until"]):
            failure = {"failures": 0}
            failure_log[user_id] = failure
            save_json(FAILURE_LOG_FILE, failure_log)

        # 📜 Check if there's an active trial
        trials = load_json(JOIN_CODES_FILE, default={})
        trial = trials.get(user_id)
        if not trial:
            await ctx.respond(
                "⚠️ You don't have an active trial. Please click 'Begin Trial' again.",
                ephemeral=True
            )
            return

        # 🧠 Decode and verify code
        emojis = extract_emojis(code)
        decoded = self.clean(decode_emoji_sequence(emojis))
        expected = self.clean(trial["code"])

        if decoded == expected:
            # ✅ Success — reset failure count
            if user_id in failure_log:
                failure_log[user_id] = {"failures": 0}
                save_json(FAILURE_LOG_FILE, failure_log)

            # 🧽 Remove trial
            if user_id in trials:
                del trials[user_id]
                save_json(JOIN_CODES_FILE, trials)

            await ctx.respond(
                "✅ Your code is valid. Welcome through the gate.",
                ephemeral=True
            )
            await assign_member_role(self.bot, ctx.author)

        else:
            # ❌ Failed attempt
            failure["failures"] += 1

            if failure["failures"] >= MAX_FAILURES:
                # ⛔ Lockout
                failure["locked_until"] = get_lockout_timestamp(LOCKOUT_DURATION)
                await ctx.respond(
                    f"⛔ Too many failed attempts. You're locked out for {int(LOCKOUT_DURATION.total_seconds() // 3600)} hours.",
                    ephemeral=True
                )
            else:
                remaining = MAX_FAILURES - failure["failures"]
                await ctx.respond(
                    f"❌ Incorrect code.\n"
                    f"🔍 I decoded your input as: `{decoded}`\n"
                    f"📜 I expected: `{expected}`\n"
                    f"⏳ You have {remaining} more attempt{'s' if remaining != 1 else ''} before lockout.\n"
                    f"Press the 'Begin Trial' button to retry.",
                    ephemeral=True
                )

            # 📝 Save updated failure log
            failure_log[user_id] = failure
            save_json(FAILURE_LOG_FILE, failure_log)

            # 🧨 Clear trial so they must hit button again
            if user_id in trials:
                del trials[user_id]
                save_json(JOIN_CODES_FILE, trials)

def setup(bot):
    bot.add_cog(Onboarding_Submit(bot))
