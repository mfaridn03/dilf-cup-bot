import os
import ossapi
import discord

from discord.ext import commands
from dotenv import load_dotenv

from data.playertop import PlayerTop
from utils import EmbedUtils, TopPlaysPaginator

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
    @commands.command(name="clearscores", aliases=["cs"])
    async def cmd_clearscores(self, ctx: commands.Context):
        """
        Reset all scores for a user
        """
        await self.bot.redis.reset_scores(ctx)
        await ctx.send(f"Scores reset for {ctx.author.name}")
    
    @commands.is_owner()
    @commands.command(name="set")
    async def cmd_set(self, ctx: commands.Context, member: discord.Member = None, *, username: str = None):
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
            return await ctx.send("No recent passes found", reference=ctx.message)

        score = recent_scores[0]
        score.pp = score.pp or 0  # thanks ppy
        
        #  1=ranked, 2=approved
        unranked = False
        if score.beatmap.ranked.value not in {1, 2}:
            unranked = True

        username = await self.bot.redis.get_osuname(ctx.author.id)

        # fetch combo from cache
        if not await self.bot.redis.has_beatmap_combo(score.beatmap_id):
            beatmap = await self.api.beatmap(beatmap_id=score.beatmap_id)

            assert beatmap.max_combo is not None, "Beatmap max combo is None"
            await self.bot.redis.cache_beatmap_combo(score.beatmap_id, beatmap.max_combo)

        beatmap_max_combo = await self.bot.redis.get_beatmap_combo(score.beatmap_id)
        embed = await EmbedUtils.recent_score(
            ctx=ctx,
            username=username,
            player_id=player_id,
            score=score,
            beatmap_max_combo=beatmap_max_combo,
        )

        # save score to db
        if unranked:
            msg = "Map is not ranked/approved, score not saved!!"
            embed.colour = discord.Colour.orange()
        elif await self.bot.redis.save_score(ctx, score):
            msg = "New entry added"
            embed.colour = discord.Colour.green()
        else:
            msg = "Did not overwrite existing score"
            embed.colour = discord.Colour.red()
        
        await ctx.send(msg, embed=embed, reference=ctx.message)

    @commands.command(name="top")
    async def cmd_top(self, ctx: commands.Context):
        """
        Fetch top scores for a user
        """
        player_id = await self.bot.redis.get_discord_osu(ctx.author.id)
        if not player_id:
            return await ctx.send("You are not linked")
        
        scores = await self.bot.redis.get_scores(ctx.author.id)
        top = PlayerTop(ctx.author.id, scores)
        toplist = top.sort()

        entries = [top.format_entry(entry) for entry in toplist]

        paginator = TopPlaysPaginator(
            entries=entries,
            author_name=ctx.author.name,
            player_id=player_id,
            total_pp=top.total_pp,
            avatar_url=ctx.author.display_avatar.url,
        )
        paginator.message = await ctx.send(embed=paginator.build_embed(), view=paginator)

async def setup(bot):
    await bot.add_cog(Osu(bot))