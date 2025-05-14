import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if DISCORD_TOKEN is None:
    print("Error: DISCORD_TOKEN is not set in the .env file.")
    exit()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("Bot is ready and online!")
    print("------")
    await load_cogs()


async def load_cogs():
    """Load all .py files in the cogs folder as extensions"""
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"Successfully loaded Cog: {filename[:-3]}")
            except Exception as e:
                print(f"Failed to load Cog {filename[:-3]}: {e}")


try:
    bot.run(DISCORD_TOKEN)
except discord.errors.LoginFailure:
    print(
        "Login failed: Please check your DISCORD_TOKEN is correct and Privileged Gateway Intents is correctly configured."
    )
except Exception as e:
    print(f"An error occurred while running the bot: {e}")
