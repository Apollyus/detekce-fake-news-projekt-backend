import hashlib
import secrets
import time
from typing import Dict, Tuple, Optional
from fastapi import HTTPException, Header, Depends, status
from source.modules.config import config

# Store for admin tokens (in memory, but could be moved to Redis or similar)
# Format: {"token": (expiration_timestamp, hashed_password)}
ADMIN_TOKENS: Dict[str, Tuple[float, str]] = {}
# Token validity period (30 minutes)
TOKEN_VALIDITY = 30 * 60  # seconds

def hash_password(password: str) -> str:
    """Create a secure hash of the password"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_admin_token(admin_password: str) -> Tuple[str, int]:
    """
    Generate admin token if password is correct
    Returns token and expiration time in seconds
    """
    # Hash the provided password
    hashed_password = hash_password(admin_password)
    
    # Compare with stored admin password hash
    stored_hash = hash_password(config.ADMIN_PASSWORD)
    
    if hashed_password != stored_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin password"
        )
    
    # Generate secure token
    token = secrets.token_urlsafe(32)
    
    # Store token with expiration
    expiry = time.time() + TOKEN_VALIDITY
    ADMIN_TOKENS[token] = (expiry, hashed_password)
    
    return token, TOKEN_VALIDITY

def verify_admin_token(token: str) -> bool:
    """Verify if an admin token is valid and not expired"""
    if token not in ADMIN_TOKENS:
        return False
    
    expiry, _ = ADMIN_TOKENS[token]
    if time.time() > expiry:
        # Token expired, remove it
        ADMIN_TOKENS.pop(token, None)
        return False
    
    return True

async def admin_required(
    admin_token: Optional[str] = Header(None, alias="X-Admin-Token")
):
    """
    Dependency to require admin authentication
    Usage: add `admin = Depends(admin_required)` to any protected endpoint
    """
    if not admin_token or not verify_admin_token(admin_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired admin token"
        )
    return True