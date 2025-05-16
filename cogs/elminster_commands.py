import os
from utils.base_cog import BaseCog
from elminster.agent import elminster_agent, USE_FUNCTION_MAP, ERROR_MESSAGE
from dotenv import load_dotenv
from discord.ext import commands


class ElminsterCommands(BaseCog):
    def __init__(self, bot: commands.Bot):
        load_dotenv()
        db_url = os.getenv("DB_URL", "sqlite:///./data/agent_data.db")

        super().__init__(
            bot=bot,
            app_name="elminster",
            db_url=db_url,
            use_function_map=USE_FUNCTION_MAP,
            error_message=ERROR_MESSAGE,
            agent=elminster_agent,
        )


async def setup(bot: commands.Bot):
    cog_name = "ElminsterCommands"
    if not bot.get_cog(cog_name):
        await bot.add_cog(ElminsterCommands(bot))
        print(f"{cog_name} Cog loaded.")
    else:
        print(f"{cog_name} Cog already exists. No new instance added.")
