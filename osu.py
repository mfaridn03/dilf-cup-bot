import os
import ossapi

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

OSU_CLIENT_ID = os.environ.get("osu-client-id")
OSU_CLIENT_SECRET = os.environ.get("osu-client-secret")

class Osu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = ossapi.OssapiAsync(
            client_id=OSU_CLIENT_ID,
            client_secret=OSU_CLIENT_SECRET,
        )

    @commands.command(name="ping")
    async def cmd_ping(self, ctx):
        await ctx.send("Pong!")

async def setup(bot):
    await bot.add_cog(Osu(bot))