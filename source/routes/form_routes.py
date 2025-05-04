from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from typing import List, Dict, Any

from source.modules.database import get_db
from source.modules.schemas import FormSubmission as FormSubmissionSchema
from source.modules.models import FormSubmission as FormSubmissionModel
from source.modules.admin_auth import admin_required

router = APIRouter()

@router.post("/submit", response_model=FormSubmissionSchema)
async def submit_form(
    form: FormSubmissionSchema,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Check for existing submissions
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

        # Create new submission
        db_submission = FormSubmissionModel(
            full_name=form.full_name,
            email=form.email,
            subject=form.subject,
            message=form.message
        )
        
        db.add(db_submission)
        
        try:
            await db.commit()
            await db.refresh(db_submission)
            return db_submission
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=500, detail="Database error")
            
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )
    
@router.get("/submissions", response_model=List[Dict[str, Any]])
async def get_form_submissions(
    limit: int = None,
    _: bool = Depends(admin_required),  # Use the admin dependency
    db: AsyncSession = Depends(get_db)   # Use AsyncSession for database connection
):
    """
    Get form submissions with optional limit on number of recent entries.
    This endpoint requires admin authentication via token.
    
    Parameters:
    - limit: Optional. Number of most recent submissions to return
    - X-Admin-Token: Required header with admin token from /admin-login
    
    Returns a list of form submissions with their complete content.
    """
    # Query with optional limit on most recent submissions
    query = await db.execute(select(FormSubmissionModel).order_by(FormSubmissionModel.created_at.desc()))
    
    submissions = query.scalars().all()  # Fetch all the results asynchronously
    
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
