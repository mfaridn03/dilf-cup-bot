from decimal import ROUND_HALF_UP, Decimal

from utils import ModUtils, RankEmotes

class PlayerTop:
    def __init__(self, discord_id: int, data: dict):
        self.data = data

    def sort(self) -> list[tuple[str, dict]]:
        _sorted = sorted(
            self.data.items(),
            key=lambda x: x[1]["pp"],
            reverse=True,
        )
        self.data = _sorted
        return self.data
    
    def format_entry(self, entry: tuple[str, dict]) -> str:
        _, score_data = entry

        artist = score_data["artist"]
        title = score_data["title"]
        diff = score_data["diff"]

        pp = Decimal(score_data["pp"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        acc = Decimal(score_data["acc"] * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
        _r = score_data["rank"]
        rank_emote = RankEmotes.get(_r)
        combo = int(score_data["combo"])
        max_combo = int(score_data["max_combo"])
        mods = score_data["mods"]
        mods.sort(key=lambda x: ModUtils.MOD_ORDER().index(x))
        mods = f"+{','.join(score_data['mods'])}"
        # bathbot formatting
        return f"{artist} - {title} [{diff}]\n{rank_emote} **{pp}pp** ({acc}%) [**{combo}x**/{max_combo}x] **{mods}**"
