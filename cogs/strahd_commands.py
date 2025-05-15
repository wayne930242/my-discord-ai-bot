from utils.base_cog import BaseCog
import os
from dotenv import load_dotenv
from strahd.agent import strahd_agent


class StrahdCommands(BaseCog):
    def __init__(self, bot):
        load_dotenv()
        dm_list = os.getenv("DM_ID_WHITE_LIST", "").split(",")
        srv_list = os.getenv("SERVER_ID_WHITE_LIST", "").split(",")
        use_map = {
            "default": "*史特拉德閉上了雙眼，彷彿正在計畫著什麼...*",
            "search_agent": "*史特拉德閉上了雙眼，聆聽著黑暗中的低語...*",
        }
        err_msg = "哼嗯......"
        super().__init__(
            bot=bot,
            app_name="strahd",
            db_url="sqlite:///./data/my_agent_data.db",
            dm_whitelist=dm_list,
            server_whitelist=srv_list,
            use_function_map=use_map,
            error_message=err_msg,
            agent=strahd_agent,
        )


async def setup(bot):
    if not bot.get_cog("StrahdCommands"):
        await bot.add_cog(StrahdCommands(bot))
        print("StrahdCommands Cog loaded.")
    else:
        print("StrahdCommands Cog already exists.")
