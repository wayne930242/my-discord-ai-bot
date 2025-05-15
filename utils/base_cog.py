import asyncio
import discord
import contextlib
from discord.ext import commands
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from utils.call_agent import stream_agent_responses
from google.adk.agents import Agent


class BaseCog(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        app_name: str,
        db_url: str,
        dm_whitelist: list[str],
        server_whitelist: list[str],
        use_function_map: dict[str, str],
        error_message: str,
        agent: Agent,
    ):
        self.bot = bot
        self.APP_NAME = app_name
        self.session_service = DatabaseSessionService(db_url)
        self.DM_ID_WHITELIST = dm_whitelist
        self.SERVER_ID_WHITELIST = server_whitelist
        self.USE_FUNCTION_MAP = use_function_map
        self.ERROR_MESSAGE = error_message
        self.user_sessions: dict[str, str] = {}
        self.agent = agent

    async def animate_thinking(self, msg: discord.Message):
        try:
            dots = 0
            while True:
                dots = (dots % 3) + 1
                await msg.edit(content=f"_（沉思著{'.' * dots}）_")
                await asyncio.sleep(0.8)
        except (asyncio.CancelledError, discord.errors.NotFound):
            return
        except Exception as e:
            print(f"[animate_thinking] Error: {e}")

    def _is_whitelisted(self, message: discord.Message) -> bool:
        if isinstance(message.channel, discord.DMChannel):
            return str(message.author.id) in self.DM_ID_WHITELIST
        guild_id = getattr(message.guild, "id", None)
        return guild_id and str(guild_id) in self.SERVER_ID_WHITELIST

    def _get_user_adk_id(self, message: discord.Message) -> str:
        if isinstance(message.channel, discord.DMChannel):
            return f"discord_user_{message.author.id}"
        return f"discord_guild_{message.guild.id}_channel_{message.channel.id}"

    async def _ensure_session(self, user_adk_id: str) -> str:
        session_id = self.user_sessions.get(user_adk_id)
        if not session_id:
            session = self.session_service.create_session(
                app_name=self.APP_NAME, user_id=user_adk_id
            )
            session_id = session.id
            self.user_sessions[user_adk_id] = session_id
            print(f"Created session {session_id} for {user_adk_id}")
        return session_id

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not self._is_whitelisted(message):
            return

        if self.bot.user in message.mentions:
            query = (
                message.content.replace(f"<@!{self.bot.user.id}>", "")
                .replace(f"<@{self.bot.user.id}>", "")
                .strip()
            )
        else:
            query = message.content.strip()

        if not query:
            return

        user_adk_id = self._get_user_adk_id(message)
        session_id = await self._ensure_session(user_adk_id)

        thinking_msg = await message.channel.send("_（沉思著...）_")
        anim_task = asyncio.create_task(self.animate_thinking(thinking_msg))

        try:
            runner = Runner(
                app_name=self.APP_NAME,
                session_service=self.session_service,
                agent=self.agent,
            )

            first_part = True
            async for part in stream_agent_responses(
                query=query,
                runner=runner,
                user_id=user_adk_id,
                session_id=session_id,
                use_function_map=self.USE_FUNCTION_MAP,
            ):
                if not anim_task.done():
                    anim_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await anim_task

                if first_part:
                    await thinking_msg.edit(content=part)
                    first_part = False
                else:
                    await message.channel.send(part)

            if first_part:
                await thinking_msg.edit(content="No response from agent.")

        except Exception as e:
            print(f"[on_message] Error: {e}")
            if not anim_task.done():
                anim_task.cancel()
            try:
                await thinking_msg.edit(content=self.ERROR_MESSAGE)
            except discord.errors.NotFound:
                await message.channel.send(self.ERROR_MESSAGE)
        finally:
            if anim_task and not anim_task.done():
                anim_task.cancel()
