import discord
from datetime import datetime, timezone
from Utility.general_utils import load_json, save_json, HARDLOCKS_FILE, PERMANENT_SEALS_FILE

# ------------------------------------------------------------
# Core trap checks
# ------------------------------------------------------------
async def trap_check_for_seal_unseal(ctx: discord.ApplicationContext, is_unseal: bool = False) -> bool:
    """
    Run preliminary checks:
    - Block usage in DM (temporary for DM commands, permanent for others)
    - Block non-admins in guild (permanent)
    - Handle separate flow for seal vs unseal
    Returns:
        True if allowed to continue
        False if trap triggered
    """
    user = ctx.author
    user_id = str(user.id)

    # -----------------------------------------------
    # Determine if this command belongs to DM_Only cogs
    # -----------------------------------------------
    is_dm_command = False
    if ctx.command and ctx.command.cog:
        if getattr(ctx.command.cog, "category", None) == "DM_Only":
            is_dm_command = True

    # ❌ DM check
    if ctx.guild is None and not is_dm_command:
        await permanent_self_seal(ctx, user, "Attempted to use seal/unseal in DM")
        return False

    # ❌ DM command misuse
    if ctx.guild is None and is_dm_command:
        # Instead of permanent seal, apply temporary block
        return await handle_temp_dm_misuse(ctx, user)

    # 🛡️ Admin check (still permanent for non-admins in guild)
    if not user.guild_permissions.administrator:
        action = "unseal" if is_unseal else "seal"
        await permanent_self_seal(ctx, user, f"Attempted to {action} without admin permissions")
        return False

    return True


# ------------------------------------------------------------
# Escalation for self-unseal attempts
# ------------------------------------------------------------
async def trap_check_self_unseal(ctx: discord.ApplicationContext, target_id: str) -> bool:
    """
    If a user tries to unseal themselves while under hardlock,
    escalate to permanent seal.
    """
    author_id = str(ctx.author.id)
    if author_id == target_id:
        hardlocks = load_json(HARDLOCKS_FILE, default={})
        if author_id in hardlocks:
            await permanent_self_seal(ctx, ctx.author, "Tried to bypass hardlock")
            return False
    return True


# ------------------------------------------------------------
# Temporary DM misuse handler
# ------------------------------------------------------------
async def handle_temp_dm_misuse(ctx: discord.ApplicationContext, user: discord.Member) -> bool:
    """
    For DM commands like /redeem or /tryguess:
    - Only temporary block or warning
    - Returns False to stop command execution
    """
    try:
        await ctx.respond(
            f"⚠️ Invalid attempt detected in DM.\n"
            f"You have been temporarily blocked from this action.",
            ephemeral=True
        )
    except discord.Forbidden:
        print(f"⚠️ Cannot respond to {user} in DM.")
    return False


# ------------------------------------------------------------
# Permanent seal action
# ------------------------------------------------------------
async def permanent_self_seal(ctx: discord.ApplicationContext, user: discord.Member, reason: str):
    """
    Apply a permanent seal to the invoking user.
    """
    user_id = str(user.id)
    permanent_seals = load_json(PERMANENT_SEALS_FILE, default={})
    permanent_seals[user_id] = {
        "sealed_at": int(datetime.now(timezone.utc).timestamp()),
        "reason": reason
    }
    save_json(PERMANENT_SEALS_FILE, permanent_seals)

    # Respond differently depending on whether the interaction was deferred
    try:
        if ctx.response.is_done():
            await ctx.followup.send(
                f"🚨 Unauthorized action detected.\n"
                f"User {user.mention} has been **permanently sealed**.\n"
                f"📝 Reason: {reason}",
                ephemeral=True
            )
        else:
            await ctx.respond(
                f"🚨 Unauthorized action detected.\n"
                f"User {user.mention} has been **permanently sealed**.\n"
                f"📝 Reason: {reason}",
                ephemeral=True
            )
    except discord.Forbidden:
        print(f"⚠️ Cannot send DM or respond in channel to {user}.")
    except Exception as e:
        print(f"⚠️ Unexpected error in permanent_self_seal: {e}")
