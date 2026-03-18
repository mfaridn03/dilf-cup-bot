import os
import discord

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

class DilfBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=",",
            intents=intents,
            case_insensitive=True,
            reconnect=True,
            status=discord.Status.do_not_disturb
        )
    
    async def start(self, token):
        try:
            await self.load_extension("osu")
            print("Extension loaded")
        except Exception as e:
            print(f"Error loading extension: {e}")
            return

        await super().start(token)
        

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        await super().on_ready()

    async def on_message(self, message):
        ctx = await self.get_context(message)
        if ctx.author.bot or ctx.command is None:
            return
        
        await self.invoke(ctx)

if __name__ == "__main__":
    import asyncio

    token = os.environ.get("bot-token")
    if not token:
        raise Exception("bot token error")
    
    bot = DilfBot()
    asyncio.run(bot.start(token))
