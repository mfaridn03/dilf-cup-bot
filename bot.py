import os
import discord
import traceback
import redis.asyncio as aioredis

from discord.ext import commands
from jishaku.paginators import PaginatorInterface
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
        self.redis = None
        self._cogs = [
            "osu",
            "jishaku",
        ]
    
    async def start(self, token):
        try:
            for cog in self._cogs:
                await self.load_extension(cog)
                print(f"Cog {cog} loaded")
        except Exception as e:
            print(f"Error loading extension: {e}")
            return
        
        # load redis
        self.redis = aioredis.Redis()
        response = await self.redis.ping()
        print("Redis connected:", response)

        await super().start(token)

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        await super().on_ready()
    
    async def close(self):
        if self.redis is not None:
            print("Closing Redis")
            await self.redis.close()
            self.redis = None
        
        print("Bot closed")
        await super().close()

    async def on_message(self, message):
        ctx = await self.get_context(message)
        if ctx.author.bot or ctx.command is None:
            return
        
        await self.invoke(ctx)

    async def on_command_error(self, ctx, error):
        # fmt_message = "```py\n{0.__class__.__name__}: {0}\n```".format(error)
        
        err = ''.join(traceback.format_exception(
            type(error),
            error,
            error.__traceback__
        ))
        err_lines = err.splitlines()

        paginator = commands.Paginator(
            prefix="```py",
            suffix="```",
            max_size=1600
        )
        for line in err_lines:
            paginator.add_line(line)
        
        interface = PaginatorInterface(ctx.bot, paginator, owner=ctx.author)
        await interface.send_to(ctx)

    async def is_owner(self, user: discord.User):
        if user.id == int(os.environ.get("owner-discord-id")):
            return True

        return await super().is_owner(user)

if __name__ == "__main__":
    import asyncio

    token = os.environ.get("bot-token")
    if not token:
        raise Exception("bot token error")
    
    bot = DilfBot()
    asyncio.run(bot.start(token))
