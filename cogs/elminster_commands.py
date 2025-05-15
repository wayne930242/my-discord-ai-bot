from utils.base_cog import BaseCog
import os
from dotenv import load_dotenv
from elminster.agent import elminster_agent


class ElminsterCommands(BaseCog):
    def __init__(self, bot):
        load_dotenv()
        dm_list = os.getenv("DM_ID_WHITE_LIST", "").split(",")
        srv_list = os.getenv("SERVER_ID_WHITE_LIST", "").split(",")
        use_map = {
            "default": "🪄 *伊爾明斯特詠唱起複雜的咒文，施展起令人顫抖的魔法...*",
            "search_agent": "🪄 *伊爾明斯特詠喃喃自語著，施展一個通曉傳奇...*",
        }
        err_msg = "咳咳...現在是老夫的休息時間......"
        super().__init__(
            bot=bot,
            app_name="elminster",
            db_url="sqlite:///./data/my_agent_data.db",
            dm_whitelist=dm_list,
            server_whitelist=srv_list,
            use_function_map=use_map,
            error_message=err_msg,
            agent=elminster_agent,
        )


async def setup(bot):
    if not bot.get_cog("ElminsterCommands"):
        await bot.add_cog(ElminsterCommands(bot))
        print("ElminsterCommands Cog loaded.")
    else:
        print("ElminsterCommands Cog already exists.")
