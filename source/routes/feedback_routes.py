from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from source.modules.database import get_db
from source.modules.models import UserFeedback, TelemetryRecord
from source.modules.schemas import UserFeedbackCreate, UserFeedbackOut
from source.modules.auth import get_current_user
from source.modules.admin_auth import generate_admin_token, admin_required
from typing import List

router = APIRouter()

@router.post("/feedback", response_model=UserFeedbackOut)
async def create_feedback(
    feedback: UserFeedbackCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Vytvoří novou zpětnou vazbu od uživatele.
    
    Args:
        feedback (UserFeedbackCreate): Data pro zpětnou vazbu
        current_user (dict): Data aktuálně přihlášeného uživatele
        db (AsyncSession): Databázová session
    
    Returns:
        UserFeedbackOut: Vytvořená zpětná vazba
    """
    # Validace hodnocení
    if not 1 <= feedback.rating <= 5:
        raise HTTPException(
            status_code=400,
            detail="Hodnocení musí být v rozsahu 1-5"
        )
    
    # Kontrola existence záznamu telemetrie
    result = await db.execute(
        select(TelemetryRecord).filter(TelemetryRecord.id == feedback.telemetry_record_id)
    )
    telemetry_record = result.scalar_one_or_none()
    
    if not telemetry_record:
        raise HTTPException(
            status_code=404,
            detail="Záznam telemetrie nenalezen"
        )
    
    # Vytvoření nové zpětné vazby
    db_feedback = UserFeedback(
        telemetry_record_id=feedback.telemetry_record_id,
        rating=feedback.rating,
        comment=feedback.comment,
        is_correct=feedback.is_correct
    )
    
    try:
        db.add(db_feedback)
        await db.commit()
        await db.refresh(db_feedback)
        return db_feedback
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Chyba při ukládání zpětné vazby: {str(e)}"
        )

@router.get("/feedback/{telemetry_id}", response_model=UserFeedbackOut)
async def get_feedback(
    telemetry_id: int,
    _: bool = Depends(admin_required),
    db: AsyncSession = Depends(get_db)
):
    """
    Získá zpětnou vazbu pro konkrétní záznam telemetrie.
    
    Args:
        telemetry_id (int): ID záznamu telemetrie
        current_user (dict): Data aktuálně přihlášeného uživatele
        db (AsyncSession): Databázová session
    
    Returns:
        UserFeedbackOut: Zpětná vazba pro daný záznam
    """
    result = await db.execute(
        select(UserFeedback).filter(UserFeedback.telemetry_record_id == telemetry_id)
    )
    feedback = result.scalar_one_or_none()
    
    if not feedback:
        raise HTTPException(
            status_code=404,
            detail="Zpětná vazba nenalezena"
        )
    
    return feedback

@router.get("/feedback/latest", response_model=List[UserFeedbackOut])
async def get_latest_feedback(
    limit: int = Query(10, ge=1, le=100),
    _: bool = Depends(admin_required),
    db: AsyncSession = Depends(get_db)
):
    """
    Získá seznam posledních hodnocení.
    
    Args:
        limit (int): Počet nejnovějších hodnocení k vrácení (1-100)
        _ (bool): Admin autentizace
        db (AsyncSession): Databázová session
    
    Returns:
        List[UserFeedbackOut]: Seznam nejnovějších hodnocení
    """
    result = await db.execute(
        select(UserFeedback)
        .order_by(UserFeedback.created_at.desc())
        .limit(limit)
    )
    feedbacks = result.scalars().all()
    
    if not feedbacks:
        return []
    
    return feedbacks 