from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any

from source.modules.database import get_db
from source.modules.schemas import FormSubmission as FormSubmissionSchema
from source.modules.models import FormSubmission as FormSubmissionModel
from source.modules.models import User
from source.modules.auth import get_current_user
from source.modules.config import config

router = APIRouter()

@router.post("/submit", response_model=FormSubmissionSchema)
async def submit_form(
    form: FormSubmissionSchema,
    db: Session = Depends(get_db)
):
    try:
        # Kontrola, zda již neexistuje podobný záznam (volitelné)
        existing_submission = db.query(FormSubmissionModel).filter(
            FormSubmissionModel.email == form.email,
            FormSubmissionModel.created_at >= datetime.now().replace(hour=0, minute=0, second=0)
        ).first()
        
        if existing_submission:
            raise HTTPException(
                status_code=400,
                detail="Již jste dnes odeslali formulář s tímto emailem"
            )

        # Vytvoření nového záznamu
        db_submission = FormSubmissionModel(
            full_name=form.full_name,
            email=form.email,
            subject=form.subject,
            message=form.message
        )
        
        # Přidání do databáze
        db.add(db_submission)
        
        try:
            # Uložení změn
            db.commit()
            # Obnovení dat
            db.refresh(db_submission)
        except Exception as db_error:
            # Rollback v případě chyby
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Chyba při ukládání do databáze"
            )

        return db_submission

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "message": "Nastala chyba při odesílání formuláře"
            }
        )
    
@router.get("/submissions", response_model=List[Dict[str, Any]])
async def get_form_submissions(
    limit: int = None,
    admin_password: str = None,
    db: Session = Depends(get_db)
):
    """
    Get form submissions with optional limit on number of recent entries.
    This endpoint requires admin password authentication.
    
    Parameters:
    - limit: Optional. Number of most recent submissions to return
    - admin_password: Required. Administrator password for access
    
    Returns a list of form submissions with their complete content.
    """
    # Simple admin password check
    if not admin_password or admin_password != config.ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access form submissions - invalid admin password"
        )
    
    # Query with optional limit on most recent submissions
    query = db.query(FormSubmissionModel).order_by(FormSubmissionModel.created_at.desc())
    
    if limit and isinstance(limit, int) and limit > 0:
        query = query.limit(limit)
    
    submissions = query.all()
    
    # Convert to dictionary format for response
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