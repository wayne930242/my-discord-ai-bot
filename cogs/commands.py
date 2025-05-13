from discord.ext import commands


class GeneralCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="hello", help="Bot will say hello to you")
    async def hello_command(self, ctx):
        """Bot will say hello to you"""
        if ctx.author == self.bot.user:
            return
        await ctx.send("Hello there!")

    @commands.command(name="ask", help="Ask a question (ADK integration todo)")
    async def ask_command(self, ctx, *, user_query: str):
        """
        Ask a question, the bot will record it.
        Usage: !ask [your question]
        """
        if ctx.author == self.bot.user:
            return
        await ctx.send(f"You asked: {user_query} (ADK integration todo)")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        pass


async def setup(bot):
    await bot.add_cog(GeneralCommands(bot))
    print("GeneralCommands Cog has been loaded.")
