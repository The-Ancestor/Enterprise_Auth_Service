from pydantic import BaseModel, EmailStr

class UserRegistration(BaseModel) :
      email : EmailStr
      password : str
      
class UserLogin(BaseModel) :
      email : EmailStr
      password : str     
      
class UserResponse(BaseModel) :
      email : str
      
class Token(BaseModel) :
      token : str
      refresh_token : str
      
class RefreshRequest(BaseModel):
    refresh_token: str

