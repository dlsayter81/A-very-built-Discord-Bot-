import asyncio

async def bind_cog_categories(bot):
    await asyncio.sleep(2)  # Give time for all cogs to load

    for cog_name, cog in bot.cogs.items():
        if not hasattr(cog, "category"):
            module_path = cog.__module__  # e.g. Cogs.DM_Only.Redemption_commands
            category = module_path.split(".")[1] if "." in module_path else None
            if category:
                cog.category = category
                print(f"🔧 Bound category '{category}' to cog '{cog_name}'")
