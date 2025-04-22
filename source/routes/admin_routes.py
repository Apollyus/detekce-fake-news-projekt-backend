from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from source.modules.database import get_db
from source.modules.models import RegistrationKey
from source.modules.config import config
from source.modules.utils import generate_registration_key

router = APIRouter()
ADMIN_PASSWORD = config.ADMIN_PASSWORD

@router.post("/generate-keys")
def generate_keys(
    count: int = Query(1, ge=1, le=100),
    password: str = Query(...),
    db: Session = Depends(get_db)
):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid password")

    keys = []
    for _ in range(count):
        key = generate_registration_key()
        db_key = RegistrationKey(key=key)
        db.add(db_key)
        db.commit()
        db.refresh(db_key)
        keys.append(db_key.key)

    return {"keys": keys}

@router.get("/list-keys")
def list_keys(password: str = Query(...), db: Session = Depends(get_db)):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid password")

    keys = db.query(RegistrationKey).all()
    return {"keys": [key.key for key in keys]}