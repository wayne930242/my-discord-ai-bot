import asyncio
import os
import discord
import contextlib
from dotenv import load_dotenv
from discord.ext import commands
from elminster.agent import root_agent
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from utils.call_agent import stream_agent_responses

DM_ID_WHITELIST = os.getenv("DM_ID_WHITE_LIST", "").split(",")
SERVER_ID_WHITELIST = os.getenv("SERVER_ID_WHITE_LIST", "").split(",")


class AgentCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.APP_NAME = "elminster"
        db_url = "sqlite:///./data/my_agent_data.db"

        self.session_service = DatabaseSessionService(db_url)
        self.user_sessions = {}

    async def animate_thinking(self, msg: discord.Message):
        try:
            dots = 0
            while True:
                dots = (dots % 3) + 1
                await msg.edit(content="_（沉思中" + "." * dots + "）_")
                await asyncio.sleep(0.8)
        except asyncio.CancelledError:
            return
        except discord.errors.NotFound:
            return
        except Exception as e:
            print(f"Error in animate_thinking: {e}")
            return

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        is_dm = isinstance(message.channel, discord.DMChannel)

        if is_dm and str(message.author.id) not in DM_ID_WHITELIST:
            print(f"DM from non-whitelisted user {message.author.id}, ignoring.")
            return

        is_mention = self.bot.user in message.mentions
        if not (is_dm or is_mention):
            return

        if is_mention:
            query = (
                message.content.replace(f"<@!{self.bot.user.id}>", "")
                .replace(f"<@{self.bot.user.id}>", "")
                .strip()
            )
        else:  # is_dm
            query = message.content.strip()

        if not query:
            return

        # Session management
        if is_dm:
            user_adk_id = f"discord_user_{message.author.id}"
            session_key_for_cache = user_adk_id
        else:  # Server channel
            guild_id = message.guild.id
            if str(guild_id) not in SERVER_ID_WHITELIST:
                print(f"Message from non-whitelisted server {guild_id}, ignoring.")
                return
            user_adk_id = f"discord_guild_{guild_id}_channel_{message.channel.id}"
            session_key_for_cache = user_adk_id

        session_id = self.user_sessions.get(session_key_for_cache)
        if not session_id:
            try:
                session = self.session_service.create_session(
                    app_name=self.APP_NAME, user_id=user_adk_id
                )
                session_id = session.id
                self.user_sessions[session_key_for_cache] = session_id
                print(f"Created new session {session_id} for ADK user {user_adk_id}")
            except Exception as e:
                print(f"Error creating session for {user_adk_id}: {e}")
                await message.channel.send(f"Error creating session: {e}")
                return
        else:
            print(f"Using existing session {session_id} for ADK user {user_adk_id}")

        thinking_msg = await message.channel.send("_（沉思中...）_")
        anim_task = asyncio.create_task(self.animate_thinking(thinking_msg))

        last_sent_message = thinking_msg
        is_first_part = True

        try:
            runner = Runner(
                app_name=self.APP_NAME,
                session_service=self.session_service,
                agent=root_agent,
            )

            async for response_part in stream_agent_responses(
                query, runner, user_id=user_adk_id, session_id=session_id
            ):
                if not anim_task.done():
                    anim_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await anim_task

                if is_first_part:
                    await last_sent_message.edit(content=response_part)
                    is_first_part = False
                else:
                    last_sent_message = await message.channel.send(response_part)

            if not anim_task.done():
                anim_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await anim_task
                if is_first_part:
                    await last_sent_message.edit(
                        content="The agent did not provide a response."
                    )

        except Exception as e:
            print(f"Error processing message: {e}")
            if not anim_task.done():
                anim_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await anim_task
            error_message_to_user = (
                f"咳咳...現在是老夫的休息時間......"
            )
            try:
                await thinking_msg.edit(content=error_message_to_user)
            except discord.errors.NotFound:
                await message.channel.send(error_message_to_user)

        finally:
            if anim_task and not anim_task.done():
                anim_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await anim_task


async def setup(bot):
    load_dotenv()

    if not bot.get_cog("AgentCommands"):
        cog_instance = AgentCommands(bot)
        await bot.add_cog(cog_instance)
        print("AgentCommands Cog loaded.")
    else:
        print("AgentCommands Cog already exists.")
