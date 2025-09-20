import json
from fastapi import Request, HTTPException

from utils.redis_server.redis_client import redis

async def getAuthUserIdByToken(access_token):
    value = await redis.get(access_token)
    if value:
        session_data = json.loads(value)
        return session_data.get("auth_userID")
    return None

async def getAuthUserIdFromRequest(request: Request):
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    access_token = token.split("Bearer ")[1]
    
    auth_userID = await getAuthUserIdByToken(access_token)
    if not auth_userID:
        raise HTTPException(status_code=401, detail="Session not found in Redis")
    
    return auth_userID

async def settingAuthUserToRedis(session_data, access_token):
    return await redis.set(access_token, json.dumps(session_data), ex=None)

async def deleteSessionRedis(access_token):
    return await redis.delete(access_token)