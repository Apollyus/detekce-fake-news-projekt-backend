from pydantic import BaseModel, EmailStr, constr, validator
from typing import Optional
import re
from html import escape
from datetime import datetime

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

class FormSubmission(BaseModel):
    full_name: constr(min_length=2, max_length=100)
    email: EmailStr
    subject: constr(min_length=3, max_length=100)
    message: constr(min_length=10, max_length=1000)
    # Add id and created_at if you want them in the response
    id: int | None = None # Or just int if always present
    created_at: datetime | None = None # Or just datetime

    # Add Config class for ORM mode
    class Config:
        orm_mode = True

    @validator('full_name', 'subject', 'message')
    def sanitize_text(cls, v):
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]*>', '', v)
        # Escape special characters
        clean_text = escape(clean_text)
        # Remove multiple spaces
        clean_text = ' '.join(clean_text.split())
        return clean_text

    @validator('full_name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z\s-]+$', v):
            raise ValueError('Name should only contain letters, spaces, and hyphens')
        return v