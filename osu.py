import os
import ossapi
import discord

from discord.ext import commands
from dotenv import load_dotenv

from data.store import RedisStore

load_dotenv()

OSU_CLIENT_ID = os.environ.get("osu-client-id")
OSU_CLIENT_SECRET = os.environ.get("osu-client-secret")
GRADE_IMAGE_URL = "https://raw.githubusercontent.com/mfaridn03/dilf-cup-bot/refs/heads/main/data/grades/{}.png"

class Osu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = ossapi.OssapiAsync(
            client_id=OSU_CLIENT_ID,
            client_secret=OSU_CLIENT_SECRET,
        )
    
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
        title = score.beatmapset.title
        diff = score.beatmap.version
        pp = score.pp or 0

        # data
        acc = round(score.accuracy * 100, 2)
        mods = [mod.acronym for mod in score.mods]
        # get rid of CL unless nomod
        if mods == ["CL"]:
            mods = ["NM"]
        else:
            mods.remove("CL")

        # hit counts
        n0 = score.statistics.miss or 0
        n50 = score.statistics.meh or 0
        n100 = score.statistics.ok or 0
        n300 = score.statistics.great or 0
        hit_text = f"""```ansi
[2;34m{n300}[0m/[2;36m{n100}[0m/[2;33m{n50}[0m/[2;31m{n0}[0m
```
"""
        # max combo
        play_combo = score.max_combo or 0
        beatmap = await self.api.beatmap(beatmap_id=score.beatmap_id)
        map_combo = beatmap.max_combo or -1

        if map_combo == -1:
            raise Exception(f"Beatmap max combo is None for beatmap ID: {score.beatmap_id}")

        # set up embed
        embed = discord.Embed()
        embed.title = f"{artist} - {title} [{diff}]"
        embed.url = score.beatmap.url
        embed.set_image(url=score.beatmapset.covers.cover)
        embed.set_footer(text=f"Mapset by {score.beatmapset.creator}")
        embed.set_thumbnail(url=GRADE_IMAGE_URL.format(score.rank.value))

        # fields
        embed.add_field(name="pp", value=f"{pp}pp")
        embed.add_field(name="mods", value=", ".join(mods))
        embed.add_field(name="acc", value=f"{acc}%")
        embed.add_field(name="combo", value=f"**{play_combo}x**/{map_combo}x")
        embed.add_field(name=" ", value=hit_text, inline=False)
        
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Osu(bot))