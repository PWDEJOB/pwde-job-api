import redis.asyncio as aioredis
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables FIRST

redis_host = os.getenv("REDIS_HOST")
redis_password = os.getenv("REDIS_PASSWORD")

REDIS_URL = f"rediss://:{redis_password}@{redis_host}:6379"

redis = aioredis.from_url(REDIS_URL, decode_responses=True)