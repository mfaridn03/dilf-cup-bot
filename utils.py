import discord
import ossapi

from discord.ext import commands

class ModUtils:
    @classmethod
    def MOD_ORDER(cls) -> list[str]:
        return ["HT", "EZ", "HD", "DT", "NC", "HR", "FL", "NF", "SD", "PF", "SO", "CL"]

class RankEmotes:
    @property
    def X(self) -> str:
        return "<:grade_X:1484023749073174538>"

    @property
    def XH(self) -> str:
        return "<:grade_XH:1484023751250022410>"

    @property
    def SH(self) -> str:
        return "<:grade_SH:1484023746065858694>"

    @property
    def S(self) -> str:
        return "<:grade_S:1484023744115507280>"

    @property
    def A(self) -> str:
        return "<:grade_A:1484023647638130849>"

    @property
    def B(self) -> str:
        return "<:grade_B:1484023737824182413>"

    @property
    def C(self) -> str:
        return "<:grade_C:1484023739786989649>"

    @property
    def D(self) -> str:
        return "<:grade_D:1484023742081532044>"

    @classmethod
    def get(cls, rank: str) -> str:
        return getattr(cls(), rank.upper())

class EmbedUtils:
    GRADE_IMAGE_URL = "https://raw.githubusercontent.com/mfaridn03/dilf-cup-bot/refs/heads/main/data/grades/{}.png"

    @classmethod
    async def recent_score(
        cls,
        ctx: commands.Context,
        username: str,
        player_id: int,
        score: ossapi.Score,
        beatmap_max_combo: int,
    ) -> discord.Embed:
        pp = score.pp or 0
        acc = round(score.accuracy * 100, 2)

        mods = [mod.acronym for mod in score.mods]
        if mods == ["CL"]:
            mods = []
        elif "CL" in mods:
            mods.remove("CL")
        mods.sort(key=lambda x: ModUtils.MOD_ORDER().index(x))

        n0 = score.statistics.miss or 0
        n50 = score.statistics.meh or 0
        n100 = score.statistics.ok or 0
        n300 = score.statistics.great or 0
        hit_text = f"""```ansi
[2;34m{n300}[0m[2;30m/[0m[2;36m{n100}[0m[2;30m/[0m[2;33m{n50}[0m[2;30m/[0m[2;31m{n0}[0m
```"""

        play_combo = score.max_combo
        map_combo = beatmap_max_combo

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

class TopPlaysPaginator(discord.ui.View):
    PER_PAGE = 5

    def __init__(
        self,
        entries: list[tuple[str, str]],
        author_name: str,
        player_id: int,
        total_pp: float,
        avatar_url: str,
    ):
        super().__init__(timeout=60)
        self.entries = entries
        self.author_name = author_name
        self.player_id = player_id
        self.total_pp = total_pp
        self.avatar_url = avatar_url

        self.page = 0
        self.max_page = max(0, (len(entries) - 1) // self.PER_PAGE)

        self._update_buttons()

    def _update_buttons(self):
        self.btn_first.disabled = self.page == 0
        self.btn_prev.disabled = self.page == 0
        self.btn_next.disabled = self.page == self.max_page
        self.btn_last.disabled = self.page == self.max_page

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed()
        embed.set_author(name=f"{self.author_name}'s top plays", icon_url=self.avatar_url)
        embed.set_thumbnail(url=f"https://a.ppy.sh/{self.player_id}?img.jpeg")
        embed.set_footer(text=f"Page {self.page + 1}/{self.max_page + 1} • Total PP: {self.total_pp}")

        start = self.page * self.PER_PAGE
        for i, (title, desc) in enumerate(self.entries[start:start + self.PER_PAGE], start=start):
            embed.add_field(name=f"{i + 1}. {title}", value=desc, inline=False)

        return embed

    async def _go_to(self, interaction: discord.Interaction, page: int):
        self.page = page
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="<<", style=discord.ButtonStyle.secondary)
    async def btn_first(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._go_to(interaction, 0)

    @discord.ui.button(label="<", style=discord.ButtonStyle.primary)
    async def btn_prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._go_to(interaction, self.page - 1)

    @discord.ui.button(label="⏹", style=discord.ButtonStyle.danger)
    async def btn_stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=None)
        self.stop()

    @discord.ui.button(label=">", style=discord.ButtonStyle.primary)
    async def btn_next(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._go_to(interaction, self.page + 1)

    @discord.ui.button(label=">>", style=discord.ButtonStyle.secondary)
    async def btn_last(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._go_to(interaction, self.max_page)

    async def on_timeout(self):
        if self.message:
            await self.message.edit(view=None)