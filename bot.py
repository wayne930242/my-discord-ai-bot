# main.py
import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

elminster = commands.Bot(command_prefix="!el ", intents=intents, help_command=None)
strahd = commands.Bot(command_prefix="!st ", intents=intents, help_command=None)


def load_whitelist(env_key: str) -> list[str]:
    raw = os.getenv(env_key, "").strip()
    return [s.strip() for s in raw.split(",") if s.strip()]


DM_WHITELIST = load_whitelist("DM_ID_WHITE_LIST")
SRV_WHITELIST = load_whitelist("SERVER_ID_WHITE_LIST")


async def global_on_message(bot: commands.Bot, message: discord.Message):
    if message.author.bot:
        return

    if isinstance(message.channel, discord.DMChannel):
        if DM_WHITELIST and str(message.author.id) not in DM_WHITELIST:
            return
        query = message.content.strip()

    elif isinstance(message.channel, discord.TextChannel):
        if bot.user not in message.mentions:
            return
        guild_id = str(getattr(message.guild, "id", ""))
        if SRV_WHITELIST and guild_id not in SRV_WHITELIST:
            return
        query = message.clean_content.replace(f"<@!{bot.user.id}>", "").strip()
    else:
        return

    if not query:
        return

    await bot.process_commands(message)


for bot in (elminster, strahd):
    @bot.event
    async def on_message(message: discord.Message):
        await global_on_message(bot, message)


@elminster.event
async def on_ready():
    print(f"Elminster is online: {elminster.user} (ID: {elminster.user.id})")
    await elminster.load_extension("cogs.elminster_commands")


@strahd.event
async def on_ready():
    print(f"Strahd is online: {strahd.user} (ID: {strahd.user.id})")
    await strahd.load_extension("cogs.strahd_commands")


async def main():
    token_e = os.getenv("DISCORD_TOKEN_ELMINSTER")
    token_s = os.getenv("DISCORD_TOKEN_STRAHD")
    if not token_e or not token_s:
        print("Please set DISCORD_TOKEN_ELMINSTER and DISCORD_TOKEN_STRAHD in .env")
        return

    loop = asyncio.get_event_loop()
    loop.create_task(elminster.start(token_e))
    loop.create_task(strahd.start(token_s))
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except discord.errors.LoginFailure:
        print(
            "Login failed: Please check if DISCORD_TOKEN is correct and if Gateway Intents is set correctly."
        )
    except Exception as e:
        print(f"Bot startup failed: {e}")
