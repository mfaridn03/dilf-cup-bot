import json
import ossapi

import redis.asyncio as aioredis
from discord.ext import commands

USERS_HASH = "discord-osu"
USERNAME_CACHE = "discord-osuname"  # ew but im too lazy to change properly
BEATMAPS_HASH = "beatmap-combo"
PLAYER_HASH = "player_scores:{}"

class RedisStore:
    def __init__(self):
        self.redis = aioredis.Redis(decode_responses=True)

    async def close(self):
        await self.redis.aclose()

    # discord id -> osu id
    async def link_discord_osu(self, discord_id: int, osu_id: int = None):
        if not osu_id:
            # unlink if id not provided
            await self.redis.hdel(USERS_HASH, discord_id)
            return
        
        await self.redis.hset(USERS_HASH, discord_id, osu_id)

    async def unlink_discord_osu(self, discord_id: int):
        await self.link_discord_osu(discord_id, None)

    async def get_discord_osu(self, discord_id: int) -> int | None:
        osu_id = await self.redis.hget(USERS_HASH, discord_id)
        if not osu_id:
            return None
        return int(osu_id)

    # discord id -> osu username
    async def cache_osuname(self, discord_id: int, username: str = None):
        if not username:
            # clear if username not provided
            await self.redis.hdel(USERNAME_CACHE, discord_id)
            return
        
        await self.redis.hset(USERNAME_CACHE, discord_id, username)

    async def uncache_osuname(self, discord_id: int):
        await self.cache_osuname(discord_id, None)

    async def get_osuname(self, discord_id: int) -> str:
        return await self.redis.hget(USERNAME_CACHE, discord_id)

    # beatmap -> max combo caching
    async def has_beatmap_combo(self, beatmap_id: int) -> bool:
        return await self.redis.hexists(BEATMAPS_HASH, beatmap_id)
    
    async def cache_beatmap_combo(self, beatmap_id: int, max_combo: int):
        await self.redis.hset(BEATMAPS_HASH, beatmap_id, max_combo)

    async def get_beatmap_combo(self, beatmap_id: int) -> int:
        return int(await self.redis.hget(BEATMAPS_HASH, beatmap_id))

    # saving user scores
    async def save_score(self, ctx: commands.Context, score: ossapi.Score) -> bool:
        """
        save user score to db. called after ,recent
        format:

        player:discord_id -> {
            "beatmap_id": {
                "pp": float,
                "acc": float,
                "mods": list[str],
                "combo": int,
                "max_combo": int,
                "score_id": int,
                "title": str,
                "diff": str,
                "artist": str
            }
        }

        returns: bool - True if score was saved, False if score was not saved/not higher pp
        """
        _player_hash = PLAYER_HASH.format(ctx.author.id)

        # if beatmap id already exists, overwrite IF new pp is higher
        if await self.redis.hexists(_player_hash, str(score.beatmap_id)):
            data = json.loads(await self.redis.hget(_player_hash, str(score.beatmap_id)))
            if data["pp"] - score.pp < 0.00001:  # i hate floating point comparisons
                return False

        # save score to db
        max_combo = await self.get_beatmap_combo(score.beatmap_id)
        mods = [mod.acronym for mod in score.mods]
        if mods == ["CL"]:
            mods = ["NM"]
        elif "CL" in mods:
            mods.remove("CL")

        data = {
            "pp": score.pp,
            "acc": score.accuracy,
            "mods": mods,
            "combo": score.max_combo,
            "max_combo": max_combo,
            "score_id": score.id,
            "title": score.beatmapset.title,
            "diff": score.beatmap.version,
            "artist": score.beatmapset.artist,
        }
        await self.redis.hset(_player_hash, str(score.beatmap_id), json.dumps(data))
        
        debug_str = f"{ctx.author.name}: "
        debug_str += f"{score.beatmapset.artist} - {score.beatmapset.title} [{score.beatmap.version}]"
        debug_str += f" | {score.pp}pp | {score.accuracy * 100}% | {score.max_combo}x/{max_combo}x"
        print(debug_str)
        return True
    
    async def get_scores(self, discord_id: int) -> dict:
        _player_hash = PLAYER_HASH.format(discord_id)
        result = await self.redis.hgetall(_player_hash)
        return {str(k): json.loads(v) for k, v in result.items()}
    
    async def reset_scores(self, ctx: commands.Context):
        """
        Reset all scores for a user
        """
        await self.redis.delete(PLAYER_HASH.format(ctx.author.id))
