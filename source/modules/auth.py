from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from source.modules.config import config  # Import the config instance, not the module
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from source.modules.database import get_db
from source.modules.models import User

SECRET_KEY = config.SECRET_KEY  # Use the SECRET_KEY from the config
if not SECRET_KEY:
    raise ValueError("SECRET_KEY must be set in the .env file")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ---- Inicializace ----
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")  # token URL

# ---- Hashování hesla ----
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# ---- JWT Token ----
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ---- Ověření tokenu & získání uživatele ----
async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Get token from auth header
    token = await oauth2_scheme(request)
    
    # Validate token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_sub = payload.get("sub")
        if user_sub is None:
            raise credentials_exception
            
        # Try to determine if sub is ID or email
        user = None
        if user_sub.isdigit():
            # If it's numeric, assume it's an ID
            result = await db.execute(select(User).filter(User.id == int(user_sub)))
            user = result.scalar_one_or_none()
        else:
            # Otherwise, assume it's an email
            result = await db.execute(select(User).filter(User.email == user_sub))
            user = result.scalar_one_or_none()
        
        if user is None:
            raise credentials_exception
            
        return {"user_id": user.id}
    except JWTError:
        raise credentials_exception