from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from source.modules.database import get_db
from source.modules.models import RegistrationKey
from source.modules.config import config
from source.modules.utils import generate_registration_key
from source.modules.admin_auth import generate_admin_token, admin_required
from typing import Dict, List, Any
from source.modules.telemetry_module import get_metrics

router = APIRouter()
ADMIN_PASSWORD = config.ADMIN_PASSWORD

@router.post("/generate-keys")
async def generate_keys(
    count: int = Query(1, ge=1, le=100),
    _: bool = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """
    Generates a list of registration keys and stores them in the database.
    """
    keys = []
    for _ in range(count):
        key = generate_registration_key()
        db_key = RegistrationKey(key=key)
        db.add(db_key)
        keys.append(db_key.key)

    await db.commit()  # Commit all changes asynchronously
    return {"keys": keys}

@router.get("/list-keys")
async def list_keys(
    _: bool = Depends(admin_required),
    db: AsyncSession = Depends(get_db)):
    """
    Lists all registration keys from the database.
    """
    result = await db.execute(select(RegistrationKey))
    keys = result.scalars().all()  # Get the list of keys
    return {"keys": [key.key for key in keys]}

@router.post("/admin-login", response_model=Dict[str, Any])
async def admin_login(admin_password: str):
    """
    Generate a secure admin token by providing the admin password.
    This token can be used for subsequent admin operations.
    """
    if admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password")
    
    token, expires_in = generate_admin_token(admin_password)
    return {"token": token, "expires_in": expires_in}

@router.get("/telemetry", dependencies=[Depends(admin_required)])
async def get_telemetry_data():
    """
    Get telemetry data for the fake news detection service (admin only)
    """
    return await get_metrics()  # Ensure telemetry is async
