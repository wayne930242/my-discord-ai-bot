from discord.ext import commands
from elminster.agent import root_agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from utils.call_agent import call_agent_async


class AgentCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="agent",
        help="Agent will answer your question. Usage: !agent <your question>",
    )
    async def agent_command(self, ctx: commands.Context, *, user_query: str):
        APP_NAME = "elminster"
        USER_ID = str(ctx.author.id)
        SESSION_ID = str(ctx.message.id)

        session_service = InMemorySessionService()
        session = session_service.create_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
        )
        runner = Runner(
            app_name=APP_NAME,
            session_service=session_service,
            agent=root_agent,
        )
        response = await call_agent_async(
            user_query, runner, USER_ID, session_id=SESSION_ID
        )
        await ctx.send(response)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        pass


async def setup(bot):
    # Ensure GeneralCommands is only added once, or use a different name if it's a different cog.
    # If 'cogs.commands' also defines 'GeneralCommands', that's the source of the 'already loaded' error.
    if not bot.get_cog("AgentCommands"):
        await bot.add_cog(AgentCommands(bot))
        print("AgentCommands Cog has been loaded by agent_commands.py.")
    else:
        print(
            "AgentCommands Cog was already loaded (possibly by another file). Skipping add_cog in agent_commands.py."
        )
