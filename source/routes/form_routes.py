from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from typing import List, Dict, Any

from source.modules.database import get_db
from source.modules.schemas import FormSubmission as FormSubmissionSchema
from source.modules.models import FormSubmission as FormSubmissionModel
from source.modules.auth import get_current_admin_user

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
    
@router.get("/submissions", response_model=List[FormSubmissionSchema]) # Změna response_model na FormSubmissionSchema
async def get_form_submissions(
    limit: int = None,
    current_admin: dict = Depends(get_current_admin_user),  # Použití nové admin závislosti
    db: AsyncSession = Depends(get_db)   # Použití AsyncSession pro připojení k databázi
):
    """
    Získání seznamu odeslaných formulářů s volitelným omezením počtu nejnovějších záznamů.
    Tento endpoint vyžaduje admin autentizaci.
    
    Parametry:
    - limit: Volitelný. Počet nejnovějších záznamů k vrácení
    
    Vrací seznam odeslaných formulářů s jejich kompletním obsahem.
    """
    # Dotaz s volitelným omezením počtu nejnovějších záznamů
    query = select(FormSubmissionModel).order_by(FormSubmissionModel.created_at.desc())
    if limit:
        query = query.limit(limit)
    
    result = await db.execute(query)
    submissions = result.scalars().all()  # Asynchronní načtení všech výsledků
    
    return submissions # Přímo vracíme list objektů, Pydantic se postará o konverzi