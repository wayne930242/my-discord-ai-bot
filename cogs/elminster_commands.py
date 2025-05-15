from utils.base_cog import BaseCog
from dotenv import load_dotenv
from elminster.agent import elminster_agent

from discord.ext import commands


class ElminsterCommands(BaseCog):
    def __init__(self, bot: commands.Bot):
        load_dotenv()
        use_map = {
            "default": "🪄 伊爾明斯特詠唱起複雜的咒文，施展起令人顫抖的魔法...",
            "search_agent": "🪄 伊爾明斯特喃喃自語著，施展一個通曉傳奇...",
        }
        err_msg = "咳咳...現在是老夫的休息時間......"
        super().__init__(
            bot=bot,
            app_name="elminster",
            db_url="sqlite:///./data/my_agent_data.db",
            use_function_map=use_map,
            error_message=err_msg,
            agent=elminster_agent,
        )


async def setup(bot: commands.Bot):
    cog_name = "ElminsterCommands"
    if not bot.get_cog(cog_name):
        await bot.add_cog(ElminsterCommands(bot))
        print(f"{cog_name} Cog loaded.")
    else:
        print(f"{cog_name} Cog already exists. No new instance added.")
