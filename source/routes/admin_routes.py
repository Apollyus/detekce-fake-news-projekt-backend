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

# Vytvoření routeru pro administrativní endpointy
router = APIRouter()
# Načtení admin hesla z konfigurace
ADMIN_PASSWORD = config.ADMIN_PASSWORD

@router.post("/generate-keys")
async def generate_keys(
    count: int = Query(1, ge=1, le=100),
    _: bool = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    """
    Vygeneruje zadaný počet registračních klíčů a uloží je do databáze.
    Vyžaduje admin autentizaci.
    """
    keys = []
    for _ in range(count):
        key = generate_registration_key()
        db_key = RegistrationKey(key=key)
        db.add(db_key)
        keys.append(db_key.key)

    await db.commit()  # Asynchronní potvrzení všech změn v databázi
    return {"keys": keys}

@router.get("/list-keys")
async def list_keys(
    _: bool = Depends(admin_required),
    db: AsyncSession = Depends(get_db)):
    """
    Zobrazí seznam všech registračních klíčů z databáze.
    Vyžaduje admin autentizaci.
    """
    result = await db.execute(select(RegistrationKey))
    keys = result.scalars().all()  # Získání seznamu klíčů
    return {"keys": [key.key for key in keys]}

@router.post("/admin-login", response_model=Dict[str, Any])
async def admin_login(admin_password: str):
    """
    Generuje bezpečný admin token po zadání správného admin hesla.
    Tento token lze použít pro následné administrativní operace.
    """
    if admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Neplatné admin heslo")
    
    token, expires_in = generate_admin_token(admin_password)
    return {"token": token, "expires_in": expires_in}

@router.get("/telemetry", dependencies=[Depends(admin_required)])
async def get_telemetry_data():
    """
    Získá telemetrická data pro službu detekce fake news (pouze pro adminy).
    Vyžaduje admin autentizaci.
    """
    return await get_metrics()  # Zajištění asynchronního volání telemetrie