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
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from source.modules.models import RateLimitStats
from typing import Dict, List, Optional

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

@router.get("/rate-limit-stats", dependencies=[Depends(admin_required)])
async def get_rate_limit_statistics(
    days: int = Query(7, ge=1, le=30, description="Počet dní historie"),
    db: AsyncSession = Depends(get_db)
):
    """
    Poskytuje statistiky o rate limitech za posledních X dní
    
    Parametry:
    - days: Počet dní historie (1-30)
    
    Vrací:
    - Denní souhrny rate limitů
    - Nejčastější IP adresy překračující limity
    - Nejčastěji omezované cesty
    - Souhrnné statistiky
    """
    # Vypočítat datum pro začátek dotazování
    start_date = datetime.now() - timedelta(days=days)
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Připravit výsledný objekt
    result = {
        "daily_summary": [],
        "top_limited_ips": [],
        "top_limited_paths": [],
        "summary": {
            "total_ip_limits": 0,
            "total_global_limits": 0,
            "total_all_limits": 0
        }
    }
    
    # 1. Získat denní souhrny
    daily_query = await db.execute(
        select(
            RateLimitStats.day,
            func.count().filter(RateLimitStats.limit_type == "per_ip").label("ip_limits"),
            func.count().filter(RateLimitStats.limit_type == "global").label("global_limits"),
            func.count().label("total_limits")
        )
        .filter(RateLimitStats.day >= start_date)
        .group_by(RateLimitStats.day)
        .order_by(RateLimitStats.day)
    )
    daily_stats = daily_query.all()
    
    for day, ip_limits, global_limits, total in daily_stats:
        result["daily_summary"].append({
            "date": day.strftime("%Y-%m-%d"),
            "ip_limits": ip_limits,
            "global_limits": global_limits,
            "total": total
        })
    
    # 2. Získat top IP adresy překračující limity
    ip_query = await db.execute(
        select(
            RateLimitStats.ip_address,
            func.count().label("limit_count")
        )
        .filter(
            RateLimitStats.timestamp >= start_date,
            RateLimitStats.limit_type == "per_ip"
        )
        .group_by(RateLimitStats.ip_address)
        .order_by(desc("limit_count"))
        .limit(10)
    )
    ip_stats = ip_query.all()
    
    for ip, count in ip_stats:
        result["top_limited_ips"].append({
            "ip_address": ip,
            "limit_count": count
        })
    
    # 3. Získat nejčastěji omezované cesty
    path_query = await db.execute(
        select(
            RateLimitStats.path,
            func.count().label("limit_count")
        )
        .filter(RateLimitStats.timestamp >= start_date)
        .group_by(RateLimitStats.path)
        .order_by(desc("limit_count"))
        .limit(10)
    )
    path_stats = path_query.all()
    
    for path, count in path_stats:
        result["top_limited_paths"].append({
            "path": path,
            "limit_count": count
        })
    
    # 4. Získat celkové souhrny
    summary_query = await db.execute(
        select(
            func.count().filter(RateLimitStats.limit_type == "per_ip").label("ip_limits"),
            func.count().filter(RateLimitStats.limit_type == "global").label("global_limits"),
            func.count().label("total_limits")
        )
        .filter(RateLimitStats.timestamp >= start_date)
    )
    ip_total, global_total, all_total = summary_query.first()
    
    result["summary"]["total_ip_limits"] = ip_total
    result["summary"]["total_global_limits"] = global_total
    result["summary"]["total_all_limits"] = all_total
    
    return result