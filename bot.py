import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN_ELMINSTER = os.getenv("DISCORD_TOKEN_ELMINSTER")
DISCORD_TOKEN_STRAHD = os.getenv("DISCORD_TOKEN_STRAHD")

if DISCORD_TOKEN_ELMINSTER is None:
    print("Error: DISCORD_TOKEN_ELMINSTER is not set in the .env file.")
    exit()

if DISCORD_TOKEN_STRAHD is None:
    print("Error: DISCORD_TOKEN_STRAHD is not set in the .env file.")
    exit()


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

elminster = commands.Bot(command_prefix="!", intents=intents, help_command=None)
strahd = commands.Bot(command_prefix="!", intents=intents, help_command=None)


@elminster.event
async def on_ready():
    print(f"Logged in as {elminster.user.name} (ID: {elminster.user.id})")
    print("Bot is ready and online!")
    print("------")
    await elminster.load_extension("cogs.elminster_commands")


@strahd.event
async def on_ready():
    print(f"Logged in as {strahd.user.name} (ID: {strahd.user.id})")
    print("Bot is ready and online!")
    print("------")
    await strahd.load_extension("cogs.strahd_commands")


try:
    # elminster.run(DISCORD_TOKEN_ELMINSTER)
    strahd.run(DISCORD_TOKEN_STRAHD)
except discord.errors.LoginFailure:
    print(
        "Login failed: Please check your DISCORD_TOKEN is correct and Privileged Gateway Intents is correctly configured."
    )
except Exception as e:
    print(f"An error occurred while running the bot: {e}")
