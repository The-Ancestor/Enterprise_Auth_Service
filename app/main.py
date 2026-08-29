from fastapi import FastAPI
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.database import Base, engine, SessionLocal
import app.models as models

Base.metadata.create_all(bind=engine)
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🟢 Enterprise Core Authentication Service Starting Up...")
    
    yield 
    
    print("🔴 Enterprise Core Authentication Service Shutting Down Gracefully...")

app = FastAPI(
    title="Enterprise Core Authentication Service",
    description="A production-ready, fully sectioned identity management API portfolio piece.",
    version="1.0.0"
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

