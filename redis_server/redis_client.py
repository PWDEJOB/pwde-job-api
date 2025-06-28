import redis.asyncio as aioredis
import os
from dotenv import load_dotenv

redis_host = os.getenv("REDIS_HOST")
redis_password = os.getenv("REDIS_PASSWORD")

load_dotenv()

REDIS_URL = f"rediss://:{redis_password}@{redis_host}:6379"

redis = aioredis.from_url(REDIS_URL, decode_responses=True)