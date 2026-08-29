from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

class UserRegistration(BaseModel) :
      email : EmailStr
      password : str
      
class UserLogin(BaseModel) :
      email : EmailStr
      password : str     
      
class UserResponse(BaseModel) :
      id : int
      email : str
      
class UserPost(BaseModel) :
      comment : str
   
class PostResponse(BaseModel) :
      id : int
      comment : str
   
class Token(BaseModel) :
      token : str
      refresh_token : str
      
class RefreshRequest(BaseModel):
    refresh_token: str

# Schema representing individual active sessions
class UserSessionResponse(BaseModel):
    id: int
    user_agent: str | None = None
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Profile response including the nested sessions list
class UserProfile(BaseModel):
    id: int
    email: EmailStr
    sessions: list[UserSessionResponse] = []

    model_config = ConfigDict(from_attributes=True)
