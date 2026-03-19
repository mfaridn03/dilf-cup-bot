import discord

from discord.ext import commands


class EmbedUtils:
    GRADE_IMAGE_URL = "https://raw.githubusercontent.com/mfaridn03/dilf-cup-bot/refs/heads/main/data/grades/{}.png"

    @classmethod
    async def recent_score(
        cls,
        ctx: commands.Context,
        username: str,
        player_id: int,
        score,
        beatmap,
    ) -> discord.Embed:
        pp = score.pp or 0
        acc = round(score.accuracy * 100, 2)
        mods = [mod.acronym for mod in score.mods]
        if mods == ["CL"]:
            mods = ["NM"]
        elif "CL" in mods:
            mods.remove("CL")

        n0 = score.statistics.miss or 0
        n50 = score.statistics.meh or 0
        n100 = score.statistics.ok or 0
        n300 = score.statistics.great or 0
        hit_text = f"""```ansi
[2;34m{n300}[0m[2;30m/[0m[2;36m{n100}[0m[2;30m/[0m[2;33m{n50}[0m[2;30m/[0m[2;31m{n0}[0m
```"""

        play_combo = score.max_combo or 0
        map_combo = beatmap.max_combo or -1
        if map_combo == -1:
            raise ValueError(f"Beatmap max combo is None for beatmap ID: {score.beatmap_id}")

        embed = discord.Embed()
        embed.title = f"{score.beatmapset.artist} - {score.beatmapset.title} [{score.beatmap.version}]"
        embed.url = score.beatmap.url
        embed.set_image(url=score.beatmapset.covers.cover)
        embed.set_footer(text=f"Mapset by {score.beatmapset.creator}")
        embed.set_thumbnail(url=cls.GRADE_IMAGE_URL.format(score.rank.value))
        embed.set_author(
            name=username,
            url=f"https://osu.ppy.sh/users/{player_id}",
            icon_url=ctx.author.display_avatar.url,
        )
        embed.add_field(name="pp", value=str(pp))
        embed.add_field(name="mods", value=", ".join(mods))
        embed.add_field(name="acc", value=f"{acc}%")
        embed.add_field(name="combo", value=f"**{play_combo}x**/{map_combo}x")
        embed.add_field(name=" ", value=hit_text, inline=False)
        return embed