import os
import discord

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=",", intents=intents)


@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")


bot_token = os.environ.get("bot-token")
if not bot_token:
    raise Exception("bot token error")

bot.run(bot_token)