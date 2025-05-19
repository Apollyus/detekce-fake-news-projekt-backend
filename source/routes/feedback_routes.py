from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from source.modules.database import get_db
from source.modules.models import UserFeedback, TelemetryRecord
from source.modules.schemas import UserFeedbackCreate, UserFeedbackOut, UserFeedbackWithPromptOut
from source.modules.auth import get_current_user
from source.modules.admin_auth import generate_admin_token, admin_required
from typing import List
from sqlalchemy.orm import joinedload

router = APIRouter()

@router.post("", response_model=UserFeedbackOut)  # Changed "/" to ""
async def create_feedback(
    feedback: UserFeedbackCreate,
    #current_user: dict = Depends(get_current_user),
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
    query = select(TelemetryRecord).where(TelemetryRecord.request_id == feedback.telemetry_id)
    result = await db.execute(query)
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(status_code=404, detail="Záznam telemetrie nebyl nalezen")
    
    
    # Vytvoření nové zpětné vazby
    db_feedback = UserFeedback(
        telemetry_record_id=record.request_id,  # Opraveno: použijeme request_id (String) místo record.id (Integer)
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

@router.get("/feedback/{telemetry_id}", response_model=UserFeedbackWithPromptOut)
async def get_feedback(
    telemetry_id: int,  # Stále používáme číselné ID pro interní API
    _: bool = Depends(admin_required),
    db: AsyncSession = Depends(get_db)
):
    """
    Získá zpětnou vazbu pro konkrétní záznam telemetrie včetně promptu.
    
    Args:
        telemetry_id (int): ID záznamu telemetrie
        _ (bool): Admin autentizace
        db (AsyncSession): Databázová session
    
    Returns:
        UserFeedbackWithPromptOut: Zpětná vazba pro daný záznam včetně promptu
    """
    # Použijeme joinedload pro získání vztahu telemetry_record
    result = await db.execute(
        select(UserFeedback)
        .options(joinedload(UserFeedback.telemetry_record))
        .filter(UserFeedback.telemetry_record_id == telemetry_id)
    )
    feedback = result.scalar_one_or_none()
    
    if not feedback:
        raise HTTPException(
            status_code=404,
            detail="Zpětná vazba nenalezena"
        )
    
    # Vytvoříme odpověď s údaji z obou tabulek
    response = {
        "id": feedback.id,
        "telemetry_record_id": feedback.telemetry_record_id,
        "rating": feedback.rating,
        "comment": feedback.comment,
        "is_correct": feedback.is_correct,
        "created_at": feedback.created_at,
        "prompt": feedback.telemetry_record.prompt,  # Přidáme prompt z telemetry záznamu
        "request_id": feedback.telemetry_record.request_id  # Přidáme UUID
    }
    
    return response

@router.get("/feedback/latest", response_model=List[UserFeedbackWithPromptOut])
async def get_latest_feedback(
    limit: int = Query(10, ge=1, le=100),
    _: bool = Depends(admin_required),
    db: AsyncSession = Depends(get_db)
):
    """
    Získá seznam posledních hodnocení včetně promptů.
    """
    result = await db.execute(
        select(UserFeedback)
        .options(joinedload(UserFeedback.telemetry_record))
        .order_by(UserFeedback.created_at.desc())
        .limit(limit)
    )
    feedbacks = result.scalars().all()
    
    if not feedbacks:
        return []
    
    # Vytvoříme odpovědi s údaji z obou tabulek
    responses = []
    for feedback in feedbacks:
        responses.append({
            "id": feedback.id,
            "telemetry_record_id": feedback.telemetry_record_id,
            "rating": feedback.rating,
            "comment": feedback.comment,
            "is_correct": feedback.is_correct,
            "created_at": feedback.created_at,
            "prompt": feedback.telemetry_record.prompt,
            "request_id": feedback.telemetry_record.request_id
        })
    
    return responses