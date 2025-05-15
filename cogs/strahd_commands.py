from utils.base_cog import BaseCog
from dotenv import load_dotenv
from strahd.agent import strahd_agent

from discord.ext import commands


class StrahdCommands(BaseCog):
    def __init__(self, bot: commands.Bot):
        load_dotenv()
        use_map = {
            "default": "*史特拉德閉上了雙眼，彷彿正在計畫著什麼...*",
            "search_agent": "*史特拉德閉上了雙眼，聆聽著黑暗中的低語...*",
        }
        err_msg = "哼嗯......"
        super().__init__(
            bot=bot,
            app_name="strahd",
            db_url="sqlite:///./data/my_agent_data.db",
            use_function_map=use_map,
            error_message=err_msg,
            agent=strahd_agent,
        )


async def setup(bot):
    cog_name = "StrahdCommands"
    if not bot.get_cog(cog_name):
        await bot.add_cog(StrahdCommands(bot))
        print(f"{cog_name} Cog loaded.")
    else:
        print("StrahdCommands Cog already exists.")
