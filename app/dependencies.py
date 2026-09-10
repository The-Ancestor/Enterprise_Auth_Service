from jwt.exceptions import InvalidTokenError
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi.security import OAuth2PasswordBearer
#from app.main import limiter, redis_client
from fastapi import HTTPException, Depends, Header
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from .database import AsyncSessionLocal
from .models import User
from typing import Annotated, AsyncGenerator
import jwt
import redis.asyncio as aioredis
from sqlalchemy import select

_redis_client: aioredis.Redis | None = None
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def set_redis_client(client: aioredis.Redis) -> None:
    """Sets the global Redis client instance (called in main lifespan or test fixtures)."""
    global _redis_client
    _redis_client = client

async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """FastAPI dependency to yield the active Redis client."""
    if _redis_client is None:
        raise RuntimeError("Redis client has not been initialized.")
    yield _redis_client

async def get_db():
    async with AsyncSessionLocal() as db:
        yield db

async def handle_idempotency(x_idempotency_key: str = Header(...), redis_client = Depends(get_redis)):
    redis_key = f"idempotency_key:{x_idempotency_key}"
    
    acquired = await redis_client.get(redis_key) # We map if the key already exists in our RAM 
    
    if acquired and acquired == "PROCESSING": # KEY FOUND BUT PROCESS NOT DONE... SO WE DROP THE REQUEST 
        raise HTTPException(
            status_code=409,
            detail="Email registration already in progress"
        )
    
    if acquired and acquired != "PROCESSING":
        return redis_key
         
    ac = await redis_client.set(redis_key, "PROCESSING", nx=True, ex=60) # KEY WILL HAVE A LIFETIME OF 60 SECONDS
    if not ac:
        raise HTTPException(
            status_code=409, 
            detail="Concurrent request detected"
        )
         
    return redis_key 


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db : AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub") # String format here
        if username is None:
            raise credentials_exception
        info_id = int(username) # Change it to integer so we can find the User via id in the DB 
    except InvalidTokenError:
        raise credentials_exception
    result = await db.execute(select(User).where(User.id == info_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


