from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from source.modules.database import get_db
from source.modules.models import RegistrationKey, User, UserActivity # Přidán import UserActivity
from source.modules.config import config
from source.modules.utils import generate_registration_key
from source.modules.auth import get_current_admin_user # Použití nové auth funkce
from typing import Dict, List, Any, Optional # Přidán Optional
from source.modules.telemetry_module import get_metrics
from sqlalchemy import func, desc, update # Přidán update
from datetime import datetime, timedelta
from source.modules.models import RateLimitStats

# Vytvoření routeru pro administrativní endpointy
router = APIRouter()
# Načtení admin hesla z konfigurace
ADMIN_PASSWORD = config.ADMIN_PASSWORD

@router.post("/generate-keys")
async def generate_keys(
    count: int = Query(1, ge=1, le=100),
    # Použití nové dependency pro admin ověření
    current_admin: dict = Depends(get_current_admin_user), 
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
    # Použití nové dependency pro admin ověření
    current_admin: dict = Depends(get_current_admin_user), 
    db: AsyncSession = Depends(get_db)):
    """
    Zobrazí seznam všech registračních klíčů z databáze.
    Vyžaduje admin autentizaci.
    """
    result = await db.execute(select(RegistrationKey))
    keys = result.scalars().all()  # Získání seznamu klíčů
    return {"keys": [key.key for key in keys]}

@router.get("/telemetry", dependencies=[Depends(get_current_admin_user)]) # Použití nové dependency
async def get_telemetry_data():
    """
    Získá telemetrická data pro službu detekce fake news (pouze pro adminy).
    Vyžaduje admin autentizaci.
    """
    return await get_metrics()  # Zajištění asynchronního volání telemetrie

@router.get("/rate-limit-stats", dependencies=[Depends(get_current_admin_user)]) # Použití nové dependency
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

@router.put("/users/role", dependencies=[Depends(get_current_admin_user)]) # Změna cesty a odstranění user_id z cesty
async def update_user_role_by_email( # Přejmenování funkce a parametru
    email: str = Query(..., description="Email uživatele, jehož role se má změnit"), # Přidán Query parametr email
    role: str = Query(..., description="Nová role uživatele (user nebo admin)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Aktualizuje roli zadaného uživatele podle emailu.
    Vyžaduje admin autentizaci.
    """
    if role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Neplatná role. Povolené hodnoty jsou 'user' nebo 'admin'.")

    # Získání uživatele podle emailu
    user_result = await db.execute(select(User).filter(User.email == email)) # Vyhledání podle emailu
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail=f"Uživatel s emailem '{email}' nebyl nalezen.")

    # Aktualizace role
    await db.execute(update(User).where(User.email == email).values(role=role)) # Aktualizace podle emailu
    await db.commit()

    return {"message": f"Role uživatele {user.email} byla aktualizována na {role}."}

@router.get("/users", dependencies=[Depends(get_current_admin_user)])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Získá seznam všech uživatelů.
    Vyžaduje admin autentizaci.
    """
    users_result = await db.execute(select(User).offset(skip).limit(limit))
    users = users_result.scalars().all()
    return users

@router.get("/user-statistics", dependencies=[Depends(get_current_admin_user)])
async def get_user_statistics(
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive user statistics including:
    - Total number of users
    - Number of admin users
    - Number of regular users
    - Number of users active in the last 30 days (total, admins, regular)
    Requires admin authentication.
    """
    try:
        # Calculate the cutoff time for 30-day activity
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        # Get total user counts
        result_total_users = await db.execute(select(func.count(User.id)))
        total_users = result_total_users.scalar_one()
        
        # Get admin count
        result_admin_users = await db.execute(
            select(func.count(User.id))
            .filter(User.role == "admin")
        )
        admin_users = result_admin_users.scalar_one()
        
        # Calculate regular users
        regular_users = total_users - admin_users
        
        # Get users active in last 30 days
        result_active_users = await db.execute(
            select(User.id, User.role)
            .join(UserActivity, User.id == UserActivity.user_id)
            .filter(UserActivity.last_activity >= thirty_days_ago)
            .group_by(User.id, User.role)
        )
        active_users_data = result_active_users.all()
        
        # Count active users by role
        active_total = len(active_users_data)
        active_admins = sum(1 for user_row in active_users_data if user_row.role == "admin")
        active_regular = active_total - active_admins
        
        return {
            "total_users": total_users,
            "admin_users": admin_users,
            "regular_users": regular_users,
            "active_users_30d": {
                "total": active_total,
                "admin": active_admins,
                "regular": active_regular
            },
            "timestamp": datetime.now()
        }
    except HTTPException: # Re-raise HTTPException if it's already one
        raise
    except Exception as e:
        # Log the exception here if you have a logger configured
        # logger.error(f"Error fetching user statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching user statistics.")
