import secrets
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import IntegrityError
from ..security import password_hash, verify_password, get_password_hash, create_access_token, hash_token
from ..models import User, UserSession, Posts
from app.main import limiter
from app.dependencies import get_db, get_current_user
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
def register(request : Request, user : UserRegistration, db : Session = Depends(get_db)) :
      hashed = password_hash.hash(user.password)
      usr = User(email=user.email, password=hashed)
      try :
           db.add(usr)
           db.commit()
           db.refresh(usr)
           return {
           "id" : usr.id,
           "email" : usr.email
           }
           
      except IntegrityError :
           db.rollback()
           raise HTTPException(status_code=409, detail="Invalid registration")
           
       
@router.post("/login", response_model=Token)
@limiter.limit("100/minute")
def login(request : Request, user : UserLogin, db : Session = Depends(get_db), user_agent: str | None = Header(default=None)) :
      USR = db.query(User).filter(User.email == user.email).first()
      
      if USR and verify_password(user.password, USR.password) :
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
            db.commit()
            
            return {
            "token": access_token,
            "refresh_token": db_refresh_token
            }
         
      else :
            raise HTTPException(status_code=401, detail="User Login Invalid")

@router.get("/profile", response_model=UserProfile) 
def profile(user : User = Depends(get_current_user), db : Session = Depends(get_db)):
    return user
 

@router.post("/posts", response_model=PostResponse)
def posts(p : UserPost, user : User = Depends(get_current_user), db : Session = Depends(get_db)) :
    
    info = Posts(user_id = user.id, comment = p.comment)
    db.add(info)
    db.commit()
    db.refresh(info)
    return {
    "id" : info.id,
    "comment" : p.comment
    }
    
    
    
@router.get("/posts/{user_id}", response_model=list[PostResponse])
def get_user_posts(user_id : int, user : User = Depends(get_current_user), db : Session = Depends(get_db)) :
    if user.id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
        
    return db.query(Posts).filter(Posts.user_id == user_id).all()
  
  
    
@router.post("/refresh", response_model=Token)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    hashed_refresh_token = hash_token(payload.refresh_token)
    session_record = db.query(UserSession).filter(UserSession.refresh_token == hashed_refresh_token).first()
    
    if not session_record:
        raise HTTPException(
            status_code=401, 
            detail="Invalid refresh token"
        )
        
    # Check if the token has expired
    if session_record.expires_at < datetime.utcnow():
        db.delete(session_record)
        db.commit()
        raise HTTPException(
            status_code=401, 
            detail="Refresh token has expired. Please log in again."
        )
    
    db.delete(session_record)
    db.commit()
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_refresh_token = secrets.token_hex(32)
    new_hashed_refresh_token = hash_token(new_refresh_token)
    refresh_expire = datetime.now(timezone.utc) + timedelta(days=7)
    
    new_session = UserSession(user_id=session_record.user_id,refresh_token=new_hashed_refresh_token, expires_at=refresh_expire)
    db.add(new_session)
    db.commit()
            

    new_access_token = create_access_token(
        data={"sub": str(session_record.user_id)}, 
        expires_delta=access_token_expires
    )
    

    return {
        "token": new_access_token,
        "refresh_token": new_refresh_token
    }
         
         

@router.post("/logout")
async def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    # Find the specific session row in the database
    hashed_refresh_token = hash_token(payload.refresh_token)
    session_record = db.query(UserSession).filter(UserSession.refresh_token == hashed_refresh_token).first()
    
    if session_record:
        # Delete the row from the database
        db.delete(session_record)
        db.commit()
        
    return {"detail": "Successfully logged out. Session revoked."}

