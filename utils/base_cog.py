import asyncio
import contextlib

import discord
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
        use_function_map: dict[str, str],
        error_message: str,
        agent: Agent,
    ):
        self.bot = bot
        self.APP_NAME = app_name
        try:
            self.session_service = DatabaseSessionService(db_url)
            print(f"Session Service: {self.session_service}")
        except Exception as e:
            print(f"❌ Cannot create session_service, error: {e}")
        self.USE_FUNCTION_MAP = use_function_map
        self.ERROR_MESSAGE = error_message
        self.user_sessions: dict[str, str] = {}
        self.agent = agent

    def _get_user_adk_id(self, message: discord.Message) -> str:
        return f"discord_user_{message.author.id}"

    async def _ensure_session(self, user_adk_id: str) -> str:
        if user_adk_id in self.user_sessions:
            return self.user_sessions[user_adk_id]

        try:
            new_session = self.session_service.create_session(
                user_id=user_adk_id,
                app_name=self.APP_NAME,
            )
            if new_session is None or not hasattr(new_session, "id"):
                raise RuntimeError(
                    "The session object returned by create_session is invalid."
                )
            session_id = new_session.id
            self.user_sessions[user_adk_id] = session_id
            return session_id
        except Exception as e:
            print(f"[BaseCog] Failed to create session for {user_adk_id}: {e}")
            raise RuntimeError(f"Failed to create session: {e}") from e

    @commands.Cog.listener("on_message")
    async def _on_message(self, message: discord.Message):
        if message.author.bot or not isinstance(
            message.channel, (discord.DMChannel, discord.TextChannel)
        ):
            return

        is_dm = isinstance(message.channel, discord.DMChannel)
        is_mention = self.bot.user and self.bot.user in message.mentions

        if is_dm:
            query = message.content.strip()
        elif is_mention:
            query = (
                message.content.replace(f"<@{self.bot.user.id}>", "", 1)
                .replace(f"<@!{self.bot.user.id}>", "", 1)
                .strip()
            )
        else:
            return

        if not query:
            return

        user_adk_id = self._get_user_adk_id(message)
        try:
            session_id = await self._ensure_session(user_adk_id)
        except RuntimeError:
            return await message.channel.send(self.ERROR_MESSAGE)

        try:
            runner = Runner(
                app_name=self.APP_NAME,
                session_service=self.session_service,
                agent=self.agent,
            )

            async for part_data in stream_agent_responses(
                query=query,
                runner=runner,
                user_id=user_adk_id,
                session_id=session_id,
                use_function_map=self.USE_FUNCTION_MAP,
            ):
                if isinstance(part_data, str):
                    part_content = part_data
                else:
                    part_content = part_data.get("message", "")

                if not part_content:
                    continue

                for chunk in [
                    part_content[i : i + 2000]
                    for i in range(0, len(part_content), 2000)
                ]:
                    await message.channel.send(chunk)

        except Exception as e:
            print(f"[BaseCog_on_message] Error processing message: {e}")
            await message.channel.send(self.ERROR_MESSAGE)
