import redis.asyncio as aioredis

USERS_HASH = "discord-osu"
USERNAME_CACHE = "discord-osuname"  # ew but im too lazy to change properly
BEATMAPS_HASH = "beatmap-combo"

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
    async def cache_beatmap_combo(self, beatmap_id: int, max_combo: int):
        await self.redis.hset(BEATMAPS_HASH, beatmap_id, max_combo)

    async def get_beatmap_combo(self, beatmap_id: int) -> int:
        return int(await self.redis.hget(BEATMAPS_HASH, beatmap_id))
