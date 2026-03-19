from decimal import ROUND_HALF_UP, Decimal

from utils import ModUtils, RankEmotes

class PlayerTop:
    def __init__(self, discord_id: int, data: dict):
        self._data = data
        self.data = self.sort()
        self.total_pp = self._calculate_total_pp()

    def sort(self) -> list[tuple[str, dict]]:
        _sorted = sorted(
            self._data.items(),
            key=lambda x: x[1]["pp"],
            reverse=True,
        )
        return _sorted
    
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
        mods = f"{','.join(score_data['mods'])}"
        # bathbot formatting
        # return f"{artist} - {title} [{diff}]\n{rank_emote} **{pp}pp** ({acc}%) [**{combo}x**/{max_combo}x] **{mods}**"
        part1 = f"{artist} - {title} [{diff}]"
        part2 = f"{rank_emote} {pp}pp ```ansi\n"
        part3 = "[2;32m{}[0m • [2;33m[[1;33m{}[0m[2;33m/{}x][0m • [2;35m{}[0m".format(
            f"{acc}%",
            str(combo) + "x",
            max_combo,
            f"{mods.replace(',','')}",
        )
        part3 += "```"
        return part1, part2 + part3

    def _calculate_total_pp(self) -> float:
        cur_weight = 1.0
        total = 0.0

        for entry in self.data:
            _, score_data = entry
            total += score_data["pp"] * cur_weight
            cur_weight *= 0.95
        
        return round(total, 2)  # hopefully no floating point issues
        