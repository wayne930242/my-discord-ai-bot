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
        self.session_service = DatabaseSessionService(db_url)
        self.USE_FUNCTION_MAP = use_function_map
        self.ERROR_MESSAGE = error_message
        self.user_sessions: dict[str, str] = {}
        self.agent = agent

    async def animate_thinking(self, message: discord.Message):
        try:
            while True:
                for char in ["`/`", "`-`", "`\\`", "`|`"]:
                    await message.edit(content=f"_{char} （沉思著...）_")
                    await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            pass
        except discord.errors.NotFound:
            pass

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

        thinking_msg = await message.channel.send("_（沉思著...）_")
        anim_task = asyncio.create_task(self.animate_thinking(thinking_msg))

        try:
            runner = Runner(
                app_name=self.APP_NAME,
                session_service=self.session_service,
                agent=self.agent,
            )

            first_part = True
            full_response_parts: list[str] = []

            async for part_data in stream_agent_responses(
                query=query,
                runner=runner,
                user_id=user_adk_id,
                session_id=session_id,
                use_function_map=self.USE_FUNCTION_MAP,
            ):
                if anim_task and not anim_task.done():
                    anim_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await anim_task

                if isinstance(part_data, str):
                    part_content = part_data
                    is_function_call = False
                else:
                    part_content = part_data.get("message", "")
                    is_function_call = part_data.get("is_function_call", False)

                if not part_content:
                    continue

                if first_part:
                    await thinking_msg.edit(content=part_content)
                    full_response_parts.append(part_content)
                    first_part = False
                else:
                    last = full_response_parts[-1]
                    if len(last) + len(part_content) < 1980:
                        full_response_parts[-1] = last + part_content
                        await thinking_msg.edit(content=full_response_parts[-1])
                    else:
                        await message.channel.send(part_content)

            if first_part:
                await thinking_msg.edit(content="No response from agent.")

        except Exception as e:
            print(f"[BaseCog_on_message] Error processing message: {e}")
            if anim_task and not anim_task.done():
                anim_task.cancel()
            try:
                await thinking_msg.edit(content=self.ERROR_MESSAGE)
            except discord.errors.NotFound:
                await message.channel.send(self.ERROR_MESSAGE)
        finally:
            if anim_task and not anim_task.done():
                anim_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await anim_task
