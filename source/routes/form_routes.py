from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from typing import List, Dict, Any

from source.modules.database import get_db
from source.modules.schemas import FormSubmission as FormSubmissionSchema
from source.modules.models import FormSubmission as FormSubmissionModel
from source.modules.admin_auth import admin_required

# Router pro obsluhu formulářových endpointů
router = APIRouter()

@router.post("/submit", response_model=FormSubmissionSchema)
async def submit_form(
    form: FormSubmissionSchema,
    db: AsyncSession = Depends(get_db)
):
    """
    Endoint pro odeslání kontaktního formuláře.
    
    Omezuje odesílání na jeden formulář denně z jednoho emailu.
    Ukládá data formuláře do databáze.
    """
    try:
        # Kontrola, zda již dnes nebyl odeslán formulář se stejným emailem
        result = await db.execute(
            select(FormSubmissionModel).filter(
                FormSubmissionModel.email == form.email,
                FormSubmissionModel.created_at >= datetime.now().replace(hour=0, minute=0, second=0)
            )
        )
        existing_submission = result.scalar_one_or_none()
        
        if existing_submission:
            raise HTTPException(
                status_code=400,
                detail="Již jste dnes odeslali formulář s tímto emailem"
            )

        # Vytvoření nového záznamu v databázi
        db_submission = FormSubmissionModel(
            full_name=form.full_name,
            email=form.email,
            subject=form.subject,
            message=form.message
        )
        
        db.add(db_submission)
        
        try:
            # Potvrzení transakce a načtení nově vytvořeného záznamu
            await db.commit()
            await db.refresh(db_submission)
            return db_submission
        except Exception:
            # V případě chyby vrátíme změny zpět
            await db.rollback()
            raise HTTPException(status_code=500, detail="Database error")
            
    except HTTPException as he:
        # Propagace HTTP výjimek beze změny
        raise he
    except Exception as e:
        # Zachycení obecných výjimek
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )
    
@router.get("/submissions", response_model=List[Dict[str, Any]])
async def get_form_submissions(
    limit: int = None,
    _: bool = Depends(admin_required),  # Použití admin závislosti pro ověření
    db: AsyncSession = Depends(get_db)   # Použití AsyncSession pro připojení k databázi
):
    """
    Získání seznamu odeslaných formulářů s volitelným omezením počtu nejnovějších záznamů.
    Tento endpoint vyžaduje admin autentizaci pomocí tokenu.
    
    Parametry:
    - limit: Volitelný. Počet nejnovějších záznamů k vrácení
    - X-Admin-Token: Povinná hlavička s admin tokenem z /admin-login
    
    Vrací seznam odeslaných formulářů s jejich kompletním obsahem.
    """
    # Dotaz s volitelným omezením počtu nejnovějších záznamů
    query = await db.execute(select(FormSubmissionModel).order_by(FormSubmissionModel.created_at.desc()))
    
    submissions = query.scalars().all()  # Asynchronní načtení všech výsledků
    
    # Převod na formát slovníku pro odpověď
    result = []
    for submission in submissions:
        result.append({
            "id": submission.id,
            "full_name": submission.full_name,
            "email": submission.email,
            "subject": submission.subject,
            "message": submission.message,
            "created_at": submission.created_at
        })
    
    return result