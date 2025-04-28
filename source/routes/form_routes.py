from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from source.modules.database import get_db
from source.modules.schemas import FormSubmission
from source.modules.models import FormSubmission as FormSubmissionModel

router = APIRouter()

@router.post("/submit", response_model=FormSubmission)
async def submit_form(
    form: FormSubmission,
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