import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
import redis.asyncio as aioredis
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.database import Base, engine
from app.dependencies import set_redis_client

limiter = Limiter(key_func=get_remote_address)

redis_client: aioredis.Redis | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    
    # Only connect to real Redis & DB if not in pytest mode
    if os.getenv("TESTING", "0") != "1":
        # 1. Startup: Create DB tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # 2. Startup: Initialize production Redis client
        redis_client = aioredis.from_url("redis://localhost:6379", decode_responses=True)
        set_redis_client(redis_client)
    
    yield
    
    # 3. Shutdown: Close real Redis connection pool
    if os.getenv("TESTING", "0") != "1" and redis_client is not None:
        await redis_client.aclose()

app = FastAPI(
    title="Enterprise Core Authentication Service",
    description="A production-ready, fully sectioned identity management API portfolio piece.",
    version="1.0.0",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

from app.routers import auth
app.include_router(auth.router)

@app.get("/", tags=["System Health"])
async def root_diagnostic():
    return {
        "status": "online",
        "service": "Identity Management Engine",
        "documentation": "/docs"
    }
