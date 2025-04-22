from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# schemas.py
class UserCreateWithKey(UserCreate):
    registration_key: str

class CompleteRegistrationRequest(BaseModel):
    token: str
    email: str
    password: str
    registrationKey: str

class UserCheckRequest(BaseModel):
    email: str
    token: str