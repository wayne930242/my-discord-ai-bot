import asyncio
import discord
import contextlib
from discord.ext import commands
from elminster.agent import root_agent
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from utils.call_agent import call_agent_async


class AgentCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.APP_NAME = "elminster"
        db_url = "sqlite:///./my_agent_data.db"
        self.session_service = DatabaseSessionService(db_url)
        self.user_sessions = {}

    async def animate_thinking(self, msg: discord.Message):
        try:
            dots = 0
            while True:
                dots = (dots % 6) + 1
                await msg.edit(content="_（沉思中" + "." * dots + "）_")
                await asyncio.sleep(0.2)
        except asyncio.CancelledError:
            return

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        is_dm = isinstance(message.channel, discord.DMChannel)
        is_mention = self.bot.user in message.mentions
        if not (is_dm or is_mention):
            return

        if is_mention:
            query = (
                message.content.replace(f"<@!{self.bot.user.id}>", "")
                .replace(f"<@{self.bot.user.id}>", "")
                .strip()
            )
        else:
            query = message.content.strip()

        if is_dm:
            session_key = f"dm-{message.author.id}"
        else:
            guild_id = message.guild.id if message.guild else message.author.id
            session_key = f"{guild_id}-{message.channel.id}"

        if session_key not in self.user_sessions:
            session = self.session_service.create_session(
                app_name=self.APP_NAME, user_id=session_key
            )
            self.user_sessions[session_key] = session.id
        session_id = self.user_sessions[session_key]

        thinking_msg = await message.channel.send("沉思中")

        anim_task = asyncio.create_task(self.animate_thinking(thinking_msg))

        try:
            runner = Runner(
                app_name=self.APP_NAME,
                session_service=self.session_service,
                agent=root_agent,
            )
            response = await call_agent_async(
                query, runner, user_id=session_key, session_id=session_id
            )
        except Exception as e:
            response = f"回應時發生錯誤：{e}"
        finally:
            anim_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await anim_task

        await thinking_msg.edit(content=response)


async def setup(bot):
    if not bot.get_cog("AgentCommands"):
        await bot.add_cog(AgentCommands(bot))
        print("AgentCommands Cog 已載入。")
