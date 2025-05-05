import hashlib
import secrets
import time
from typing import Dict, Tuple, Optional
from fastapi import HTTPException, Header, Depends, status
from source.modules.config import config

# Úložiště pro admin tokeny (v paměti, ale mohlo by být přesunuto do Redis nebo podobně)
# Formát: {"token": (čas_expirace, hashované_heslo)}
ADMIN_TOKENS: Dict[str, Tuple[float, str]] = {}
# Doba platnosti tokenu (30 minut)
TOKEN_VALIDITY = 30 * 60  # sekund

def hash_password(password: str) -> str:
    """Vytvoří bezpečný hash hesla"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_admin_token(admin_password: str) -> Tuple[str, int]:
    """
    Vygeneruje admin token, pokud je heslo správné
    Vrátí token a dobu platnosti v sekundách
    """
    # Vytvoření hashe zadaného hesla
    hashed_password = hash_password(admin_password)
    
    # Porovnání s uloženým hashem admin hesla
    stored_hash = hash_password(config.ADMIN_PASSWORD)
    
    if hashed_password != stored_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Neplatné admin heslo"
        )
    
    # Vygenerování bezpečného tokenu
    token = secrets.token_urlsafe(32)
    
    # Uložení tokenu s dobou expirace
    expiry = time.time() + TOKEN_VALIDITY
    ADMIN_TOKENS[token] = (expiry, hashed_password)
    
    return token, TOKEN_VALIDITY

def verify_admin_token(token: str) -> bool:
    """Ověří, zda je admin token platný a nevypršel"""
    if token not in ADMIN_TOKENS:
        return False
    
    expiry, _ = ADMIN_TOKENS[token]
    if time.time() > expiry:
        # Token vypršel, odstraníme jej
        ADMIN_TOKENS.pop(token, None)
        return False
    
    return True

async def admin_required(
    admin_token: Optional[str] = Header(None, alias="X-Admin-Token")
):
    """
    Dependency pro vyžadování admin autentizace
    Použití: přidejte `admin = Depends(admin_required)` k libovolnému chráněnému endpointu
    """
    if not admin_token or not verify_admin_token(admin_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Neplatný nebo vypršený admin token"
        )
    return True