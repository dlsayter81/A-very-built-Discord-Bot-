import discord
from discord.ext import commands
import os

# Load the allowed channel ID from environment
ALLOWED_CHANNEL_ID = int(os.getenv("ALLOWED_CHANNEL_ID", 0))

# Symbolic scope registry
COMMAND_SCOPES = {
    "randomtimeout": ["channel", "admin"],
    "seal": ["channel", "admin"],
    "unseal": ["channel", "admin"],
    "perment_unseal": ["channel", "admin"],
    "retry": ["channel", "admin"],
    "redeem": ["dm"],
    "tryguess": ["dm"]
}

def set_command_visibility(command: discord.SlashCommand):
    """
    Safely applies symbolic scope restrictions without breaking command registration.
    Only updates dm_permission if necessary; does not touch default_permissions.update().
    """
    scopes = COMMAND_SCOPES.get(command.name.lower(), [])

    # Hide commands from DMs if they should not be used there
    if "admin" in scopes or "channel" in scopes:
        try:
            command.dm_permission = False
        except AttributeError:
            # fallback if dm_permission not available
            pass

    # Commands with "dm" scope can remain visible in DMs
    if "dm" in scopes:
        try:
            command.dm_permission = True
        except AttributeError:
            pass
