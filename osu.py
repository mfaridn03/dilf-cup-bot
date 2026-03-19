import os
import ossapi
import discord

from discord.ext import commands
from dotenv import load_dotenv

from data.store import RedisStore
from utils import EmbedUtils

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

    @commands.is_owner()
    @commands.command(name="close")
    async def cmd_close(self, ctx: commands.Context):
        await ctx.send("shutting down")
        await self.bot.close()
    
    @commands.is_owner()
    @commands.command(name="set")
    async def cmd_set(self, ctx: commands.Context, member: discord.Member = None, username: str = None):
        """
        Sets osu username. Leave blank to unlink
        """
        if member is None:
            member = ctx.author
        elif member.bot:
            return

        # unlinking
        if not username:
            if not await self.bot.redis.get_discord_osu(member.id):
                return await ctx.send("You are not linked")
            return await self.bot.redis.unlink_discord_osu(member.id)

        # linking
        # fetch player via api, send error if not found
        try:
            player = await self.api.user(
                user=username,
                mode=ossapi.GameMode.OSU,
                key=ossapi.UserLookupKey.USERNAME,
            )
        except ValueError:
            return await ctx.send(f"Player `{username}` not found")
        
        await self.bot.redis.link_discord_osu(member.id, player.id)
        await self.bot.redis.cache_osuname(member.id, player.username)
        
        await ctx.send(f"{member.name} linked to player `{player.username}`")

    @commands.command(name="recent", aliases=["r"])
    async def cmd_recent(self, ctx: commands.Context):
        """
        Fetch latest pass score
        """
        player_id = await self.bot.redis.get_discord_osu(ctx.author.id)
        if not player_id:
            return await ctx.send("You are not linked")

        embed = await EmbedUtils.recent_score(
            ctx=ctx,
            api=self.api,
            redis=self.bot.redis,
            player_id=player_id,
        )
        
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Osu(bot))