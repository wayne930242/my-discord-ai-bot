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
                for char in ["/", "-", "\\", "|"]:
                    await message.edit(content=f"_{char}（沉思著...）_")
                    await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            pass
        except discord.errors.NotFound:
            pass

    def _get_user_adk_id(self, message: discord.Message) -> str:
        return f"discord_user_{message.author.id}"

    async def _ensure_session(self, user_adk_id: str) -> str:
        """
        Ensures a valid session ID for the given user ADK ID.
        Retrieves from local cache or creates a new one via session_service.
        The session_service methods (get_session, create_session) are assumed to be synchronous.
        """
        # 1. 檢查本地緩存
        if user_adk_id in self.user_sessions:
            existing_session_id = self.user_sessions[user_adk_id]
            try:
                # 2. 嘗試從 session_service 獲取（驗證）會話 - REMOVED await
                # Assuming get_session takes session_id as a keyword argument
                session_obj = self.session_service.get_session(
                    session_id=existing_session_id
                )

                if session_obj:
                    # print(f"DEBUG: Using existing session from cache: {existing_session_id} for user: {user_adk_id}")
                    return existing_session_id
                else:
                    # print(f"DEBUG: Session {existing_session_id} for user {user_adk_id} not found by get_session or invalid. Removing from cache.")
                    del self.user_sessions[user_adk_id]
            except (
                Exception
            ) as e:  # Catch any exception from get_session (e.g., if session truly doesn't exist and it raises error)
                # print(f"DEBUG: Error validating session {existing_session_id} for user {user_adk_id}: {e}. Removing from cache and creating new.")
                if (
                    user_adk_id in self.user_sessions
                ):  # Ensure it's still there before deleting
                    del self.user_sessions[user_adk_id]

        # 3. 如果緩存中沒有，或現有會話無效，則創建一個新會話
        # print(f"DEBUG: Creating new session for user: {user_adk_id}, app: {self.APP_NAME}")
        try:
            # REMOVED await - Call create_session synchronously
            new_session_obj = self.session_service.create_session(
                user_id=user_adk_id,
                app_name=self.APP_NAME,
                # Add other parameters if your create_session requires them
            )

            # Validate the returned object and that it has an 'id'
            if (
                new_session_obj is None
            ):  # Handle case where create_session might return None on failure
                raise ValueError(
                    "create_session returned None, indicating failure to create a session."
                )
            if not hasattr(new_session_obj, "id"):
                actual_type = type(new_session_obj).__name__
                raise TypeError(
                    f"Session object (type: {actual_type}) returned by create_session does not have an 'id' attribute. Object: {new_session_obj}"
                )

            new_session_id = new_session_obj.id
            self.user_sessions[user_adk_id] = new_session_id
            # print(f"DEBUG: Created and cached new session: {new_session_id} for user: {user_adk_id}")
            return new_session_id
        except Exception as e:
            # The CRITICAL log will now show the specific error from the synchronous call or the subsequent checks
            print(
                f"CRITICAL: Failed to create session for user {user_adk_id} with app {self.APP_NAME}. Error: {e}"
            )
            raise RuntimeError(
                f"Failed to create or ensure session for user {user_adk_id}"
            ) from e

    @commands.Cog.listener("on_message")
    async def _on_message(self, message: discord.Message):
        if message.author.bot or not isinstance(
            message.channel, (discord.DMChannel, discord.TextChannel)
        ):
            return

        is_dm = isinstance(message.channel, discord.DMChannel)
        is_mention = self.bot.user and self.bot.user in message.mentions
        query = ""

        if is_dm:
            query = message.content.strip()
        elif is_mention and self.bot.user:
            query = message.content.replace(f"<@{self.bot.user.id}>", "", 1)
            query = query.replace(f"<@!{self.bot.user.id}>", "", 1).strip()
        else:
            return

        if not query:
            return

        user_adk_id = self._get_user_adk_id(message)
        session_id = await self._ensure_session(user_adk_id)

        thinking_msg = None
        anim_task = None
        agent_responded_content = False

        try:
            thinking_msg = await message.channel.send("_（沉思著...）_")
            anim_task = asyncio.create_task(self.animate_thinking(thinking_msg))

            runner = Runner(
                app_name=self.APP_NAME,
                session_service=self.session_service,
                agent=self.agent,
            )

            first_part = True
            full_response_parts = []

            async for part_data in stream_agent_responses(
                query=query,
                runner=runner,
                user_id=user_adk_id,
                session_id=session_id,
                use_function_map=self.USE_FUNCTION_MAP,
            ):
                part_content = ""
                is_function_call_message = False

                if isinstance(part_data, str):
                    part_content = part_data
                elif (
                    isinstance(part_data, dict)
                    and "message" in part_data
                    and "is_function_call" in part_data
                ):
                    part_content = part_data["message"]
                    is_function_call_message = part_data["is_function_call"]

                if not part_content:
                    continue

                agent_responded_content = True

                if anim_task and not anim_task.done():
                    anim_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await anim_task

                if is_function_call_message and thinking_msg:
                    await thinking_msg.edit(content=part_content)
                    first_part = True
                    full_response_parts = []
                elif first_part and thinking_msg:
                    await thinking_msg.edit(content=part_content)
                    full_response_parts.append(part_content)
                    first_part = False
                else:
                    if (
                        full_response_parts
                        and thinking_msg
                        and len(full_response_parts[-1]) + len(part_content) < 1980
                    ):
                        full_response_parts[-1] += part_content
                        await thinking_msg.edit(content=full_response_parts[-1])
                    elif thinking_msg:
                        if not full_response_parts:
                            await message.channel.send(part_content)
                        else:
                            await message.channel.send(part_content)

            if first_part and not agent_responded_content and thinking_msg:
                if anim_task and not anim_task.done():
                    anim_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await anim_task
                await thinking_msg.edit(content="No response from agent.")

        except Exception as e:
            print(f"[BaseCog_on_message] Error: {e}")
            if anim_task and not anim_task.done():
                anim_task.cancel()

            error_content_to_send = self.ERROR_MESSAGE
            if thinking_msg:
                try:
                    await thinking_msg.edit(content=error_content_to_send)
                except discord.errors.NotFound:
                    await message.channel.send(error_content_to_send)
            else:
                await message.channel.send(error_content_to_send)
        finally:
            if anim_task and not anim_task.done():
                anim_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await anim_task

        return
