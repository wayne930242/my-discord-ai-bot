from utils.base_cog import BaseCog
from strahd.agent import strahd_agent, USE_FUNCTION_MAP, ERROR_MESSAGE
from discord.ext import commands


class StrahdCommands(BaseCog):
    def __init__(self, bot: commands.Bot):
        super().__init__(
            bot=bot,
            app_name="strahd",
            db_url="sqlite:///./data/strahd_agent_data.db",
            use_function_map=USE_FUNCTION_MAP,
            error_message=ERROR_MESSAGE,
            agent=strahd_agent,
        )


async def setup(bot):
    cog_name = "StrahdCommands"
    if not bot.get_cog(cog_name):
        await bot.add_cog(StrahdCommands(bot))
        print(f"{cog_name} Cog loaded.")
    else:
        print("StrahdCommands Cog already exists.")
