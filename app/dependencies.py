from jwt.exceptions import InvalidTokenError
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import User
from typing import Annotated
import jwt


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db() :
    db = SessionLocal()
    try :
        yield db  
    finally :
        db.close()


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db : Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        info_id = int(username)
    except InvalidTokenError:
        raise credentials_exception
    user = db.query(User).filter(User.id == info_id).first()
    if user is None:
        raise credentials_exception
    return user


