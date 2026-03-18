import os
import ossapi
import discord

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

    @commands.is_owner()
    @commands.command(name="set")
    async def cmd_set(self, ctx: commands.Context, member: discord.Member = None, username: str = None):
        """
        Set your osu username. Leave blank to unlink
        """
        if member is None:
            member = ctx.author
        elif member.bot:
            return

        if username is None:
            # check if user is linked
            if await self.bot.redis.exists(f"osu:discord:{member.id}"):
                await self.bot.redis.delete(f"osu:discord:{member.id}")
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
        
        await self.bot.redis.set(f"osu:discord:{member.id}", player.id)
        await ctx.send(f"{member.name} linked to player `{player.username}`")

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
        title = score.beatmapset.title
        diff = score.beatmap.version
        pp = score.pp

        # data
        acc = round(score.accuracy * 100, 2)
        mods = [mod.acronym for mod in score.mods]
        # get rid of CL unless nomod
        if mods == ["CL"]:
            mods = "NM"
        else:
            mods.remove("CL")

        # set up embed
        embed = discord.Embed()
        embed.title = f"{artist} - {title} [{diff}]"
        embed.url = score.beatmap.url
        embed.set_image(url=score.beatmapset.covers.cover)
        embed.set_footer(text=f"Mapset by {score.beatmapset.creator}")

        # fields
        embed.add_field(name="pp", value=f"{pp}pp")
        embed.add_field(name="acc", value=f"{acc}%")
        embed.add_field(name="mods", value=", ".join(mods), inline=False)
        
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Osu(bot))