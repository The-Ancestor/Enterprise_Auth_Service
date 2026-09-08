import secrets, json, asyncio
import redis.asyncio as aioredis
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Header, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from ..security import password_hash, verify_password, get_password_hash, create_access_token, hash_token
from ..models import User, UserSession, Posts
from app.main import limiter, redis_client
from app.dependencies import get_db, get_current_user, handle_idempotency, get_redis
from ..schemas import UserRegistration, UserLogin, UserResponse, Token, RefreshRequest, UserProfile, UserPost, PostResponse
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


router = APIRouter(prefix="/auth", tags=["Authentication Pipeline"])

@router.get("/home")
@limiter.limit("100/minute")
async def home(request : Request) :
      return {
      "message" : "UNDERDOG BLOCK"
      }
      
@router.post("/register", response_model=UserResponse)
@limiter.limit("100/minute")
async def register(request : Request, user : UserRegistration, db : AsyncSession = Depends(get_db), redis_key : str = Depends(handle_idempotency), redis_client: aioredis.Redis = Depends(get_redis)) :
      cached = await redis_client.get(redis_key)   
      if cached and cached != "PROCESSING" :
         return Response(content=cached, media_type="application/json")
         
      hashed = await asyncio.to_thread(password_hash.hash, user.password)
      # hashed = password_hash.hash(user.password)
      usr = User(email=user.email, password=hashed)
      
      try :
           db.add(usr)
           await db.commit()
           await db.refresh(usr)
           load = {
           "id" : usr.id,
           "email" : usr.email,
           "message" : "success"
           }
           await redis_client.set(redis_key, json.dumps(load), ex=86400)
           return load
           
      except IntegrityError :
           await db.rollback()
           await redis_client.delete(redis_key)
           raise HTTPException(status_code=409, detail="Invalid registration")
           
       
@router.post("/login", response_model=Token)
@limiter.limit("100/minute")
async def login(request : Request, user : UserLogin, db : AsyncSession = Depends(get_db), user_agent: str | None = Header(default=None)) :
      result = await db.execute(select(User).where(User.email == user.email))
      USR = result.scalar_one_or_none()
      
      if USR and await asyncio.to_thread(verify_password, user.password, USR.password):
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(data={"sub": str(USR.id)}, expires_delta=access_token_expires)
            
            # Generate secure random string for refresh token
            db_refresh_token = secrets.token_hex(32)
            hashed_refresh_token = hash_token(db_refresh_token)
            refresh_expire = datetime.now(timezone.utc) + timedelta(days=7)

            new_session = UserSession(
            user_id=USR.id,
            refresh_token=hashed_refresh_token,
            expires_at=refresh_expire,
            user_agent=user_agent
            )
            db.add(new_session)
            await db.commit()
            
            return {
            "token": access_token,
            "refresh_token": db_refresh_token
            }
         
      else :
            raise HTTPException(status_code=401, detail="User Login Invalid")

@router.get("/profile", response_model=UserProfile) 
async def profile(user : User = Depends(get_current_user)) :
    return user
 

@router.post("/posts", response_model=PostResponse)
async def posts(p : UserPost, user : User = Depends(get_current_user), db : AsyncSession = Depends(get_db)) :
    
    info = Posts(user_id = user.id, comment = p.comment)
    db.add(info)
    await db.commit()
    await db.refresh(info)
    return {
    "id" : info.id,
    "comment" : p.comment
    }
    
    
    
@router.get("/posts/{user_id}", response_model=list[PostResponse])
async def get_user_posts(user_id : int, user : User = Depends(get_current_user), db : AsyncSession = Depends(get_db)) :
    if user.id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
        
    result = await db.execute(select(Posts).where(Posts.user_id == user_id))
    return result.scalars().all()
  
    
@router.post("/refresh", response_model=Token)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    hashed_refresh_token = hash_token(payload.refresh_token)
    result = await db.execute(select(UserSession).where(UserSession.refresh_token == hashed_refresh_token))
    session_record = result.scalar_one_or_none()
    
    if not session_record:
        raise HTTPException(
            status_code=401, 
            detail="Invalid refresh token"
        )
        
    # Check if the token has expired
    # if session_record.expires_at < datetime.now(timezone.utc):
    #    await db.delete(session_record)
    #    await db.commit()
    #    raise HTTPException(
    #        status_code=401, 
    #        detail="Refresh token has expired. Please log in again."
    #    )
    
    # Check if the token has expired
    expires_at = session_record.expires_at
    if expires_at.tzinfo is None:
       expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < datetime.now(timezone.utc):
       await db.delete(session_record)
       await db.commit()
       raise HTTPException(
             status_code=401, 
             detail="Refresh token has expired. Please log in again."
       )
    
    await db.delete(session_record)
    await db.commit()
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_refresh_token = secrets.token_hex(32)
    new_hashed_refresh_token = hash_token(new_refresh_token)
    refresh_expire = datetime.now(timezone.utc) + timedelta(days=7)
    
    new_session = UserSession(user_id=session_record.user_id,refresh_token=new_hashed_refresh_token, expires_at=refresh_expire)
    db.add(new_session)
    await db.commit()
            

    new_access_token = create_access_token(
        data={"sub": str(session_record.user_id)}, 
        expires_delta=access_token_expires
    )
    

    return {
        "token": new_access_token,
        "refresh_token": new_refresh_token
    }
         
         

@router.post("/logout")
async def logout(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    # Find the specific session row in the database
    hashed_refresh_token = hash_token(payload.refresh_token)
    result = await db.execute(select(UserSession).where(UserSession.refresh_token == hashed_refresh_token))
    session_record = result.scalar_one_or_none()
    
    if session_record:
        # Delete the row from the database
        await db.delete(session_record)
        await db.commit()
        
    return {"detail": "Successfully logged out. Session revoked."}

