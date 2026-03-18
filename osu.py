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

    @commands.command(name="set")
    async def cmd_set(self, ctx: commands.Context, username: str = None):
        """
        Set your osu username. Leave blank to unlink
        """

        if username is None:
            # check if user is linked
            if await self.bot.redis.exists(f"osu:discord:{ctx.author.id}"):
                await self.bot.redis.delete(f"osu:discord:{ctx.author.id}")
                return await ctx.send("Discord unlinked from player")
            else:
                return await ctx.send("You are not linked")

        # fetch player via api, send error if not found
        try:
            player = await self.api.user(
                user=username,
                mode=ossapi.GameMode.OSU,
                key=ossapi.UserLookupKey.USERNAME,
            )
        except ValueError:
            return await ctx.send(f"Player `{username}` not found")
        
        await self.bot.redis.set(f"osu:discord:{ctx.author.id}", player.id)
        await ctx.send(f"Discord linked to player `{player.username}`")

    @commands.command(name="recent", aliases=["r"])
    async def cmd_recent(self, ctx: commands.Context):
        """
        Fetch latest pass score
        """
        if not await self.bot.redis.exists(f"osu:discord:{ctx.author.id}"):
            return await ctx.send("You are not linked")
        
        player_id = int(await self.bot.redis.get(f"osu:discord:{ctx.author.id}"))
        recent_scores = await self.api.user_scores(
            user_id=player_id,
            type=ossapi.ScoreType.RECENT,
            include_fails=False,
            limit=1,
            mode=ossapi.GameMode.OSU,
            legacy_only=True,
        )
        if len(recent_scores) == 0:
            return await ctx.send("No recent passes found")
        
        score = recent_scores[0]
        artist = score.beatmapset.artist
        title = score.beatmapset.title_unicode
        diff = score.beatmap.version
        pp = score.pp

        await ctx.send(f"Last score: {artist} - {title} [{diff}] {pp}pp")


async def setup(bot):
    await bot.add_cog(Osu(bot))