from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from source.modules.database import get_db
from source.modules.models import RegistrationKey
from source.modules.config import config
from source.modules.utils import generate_registration_key
from source.modules.admin_auth import generate_admin_token, admin_required
from typing import Dict, List, Any

router = APIRouter()
ADMIN_PASSWORD = config.ADMIN_PASSWORD

@router.post("/generate-keys")
def generate_keys(
    count: int = Query(1, ge=1, le=100),
    _: bool = Depends(admin_required),  # Keep only this authentication
    db: Session = Depends(get_db),
):
    # Remove the password parameter and check - admin_required already handles auth
    
    keys = []
    for _ in range(count):
        key = generate_registration_key()
        db_key = RegistrationKey(key=key)
        db.add(db_key)
        db.commit()
        db.refresh(db_key)
        keys.append(db_key.key)

    return {"keys": keys}

@router.get("/list-keys")
def list_keys(
    _: bool = Depends(admin_required),
    db: Session = Depends(get_db)):
    
    keys = db.query(RegistrationKey).all()
    return {"keys": [key.key for key in keys]}

@router.post("/admin-login", response_model=Dict[str, Any])
async def admin_login(admin_password: str):
    """
    Generate a secure admin token by providing the admin password.
    This token can be used for subsequent admin operations.
    """
    token, expires_in = generate_admin_token(admin_password)
    return {"token": token, "expires_in": expires_in}