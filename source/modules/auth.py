from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from source.modules.config import config
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from source.modules.database import get_db
from source.modules.models import User

SECRET_KEY = config.SECRET_KEY  # Použití SECRET_KEY z konfigurace
if not SECRET_KEY:
    raise ValueError("SECRET_KEY musí být nastaven v souboru .env")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
USER_ROLE = "user"
ADMIN_ROLE = "admin"

# ---- Inicializace ----
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")  # URL pro získání tokenu

# ---- Hashování hesla ----
def hash_password(password: str) -> str:
    """Vytvoří hash z hesla pomocí bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Ověří, zda heslo odpovídá uloženému hashi"""
    return pwd_context.verify(plain_password, hashed_password)

# ---- JWT Token ----
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Vytvoří JWT token s nastavenou dobou expirace"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    # Role se přidává do tokenu při jeho vytváření
    if "role" not in to_encode: # Přidá výchozí roli, pokud není specifikována
        to_encode["role"] = USER_ROLE
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ---- Ověření tokenu & získání uživatele ----
async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> dict: # Změna návratového typu
    """Získá aktuálního uživatele z požadavku pomocí JWT tokenu"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nepodařilo se ověřit přihlašovací údaje",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Získání tokenu z hlavičky Authorization
    token = await oauth2_scheme(request)
    
    # Ověření tokenu
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_sub = payload.get("sub")
        if user_sub is None:
            raise credentials_exception
            
        # Zjištění, zda sub je ID nebo email
        user = None
        # Role se extrahuje z tokenu
        role = payload.get("role", USER_ROLE) # Výchozí role USER_ROLE

        if user_sub.isdigit():
            # Pokud je číselné, považujeme za ID
            result = await db.execute(select(User).filter(User.id == int(user_sub)))
            user = result.scalar_one_or_none()
        else:
            # Jinak předpokládáme, že jde o email
            result = await db.execute(select(User).filter(User.email == user_sub))
            user = result.scalar_one_or_none()
        
        if user is None:
            raise credentials_exception
            
        # Vrátí slovník s ID uživatele, emailem a jeho aktuální rolí z databáze
        return {"user_id": user.id, "email": user.email, "role": user.role} 
    except JWTError:
        raise credentials_exception

async def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Získá aktuálního aktivního uživatele a ověří jeho roli."""
    # Tato funkce může být rozšířena o další logiku, např. kontrolu, zda je uživatel aktivní
    # Prozatím pouze vrací data získaná z get_current_user
    return current_user

async def get_current_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Získá aktuálního uživatele a ověří, zda má roli administrátora."""
    if current_user.get("role") != ADMIN_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nedostatečná oprávnění. Vyžadována role administrátora."
        )
    return current_user