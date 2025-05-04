from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from source.modules.database import get_db
from source.modules.models import User, RegistrationKey
from source.modules.schemas import (
    UserCreateWithKey, UserOut, UserLogin,
    TokenResponse, CompleteRegistrationRequest,
    UserCheckRequest
)
from source.modules.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter()

@router.post("/register", response_model=UserOut)
async def register(user: UserCreateWithKey, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RegistrationKey).filter(RegistrationKey.key == user.registration_key))
    reg_key = result.scalar_one_or_none()
    if not reg_key or reg_key.used:
        raise HTTPException(status_code=400, detail="Neplatný nebo použitý registrační klíč")

    result = await db.execute(select(User).filter(User.email == user.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="Uživatel už existuje")

    new_user = User(
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    db.add(new_user)
    reg_key.used = True

    try:
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == user_data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Špatný email nebo heslo")

    token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {"user_id": current_user["user_id"]}

@router.post("/complete-google-registration")
async def complete_registration(request_data: CompleteRegistrationRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RegistrationKey).filter(RegistrationKey.key == request_data.registrationKey))
    reg_key = result.scalar_one_or_none()
    if not reg_key or reg_key.used:
        raise HTTPException(status_code=400, detail="Neplatný nebo použitý registrační klíč")

    result = await db.execute(select(User).filter(User.email == request_data.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Uživatel nenalezen")

    user.hashed_password = hash_password(request_data.password)
    reg_key.used = True
    reg_key.used_by = request_data.email

    try:
        await db.commit()
        return {"status": "success", "message": "Registrace úspěšně dokončena"}
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Chyba při ukládání změn")

@router.post("/check_user_password")
async def check_user_password(request_data: UserCheckRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).filter(User.email == request_data.email))
        user = result.scalar_one_or_none()

        if not user:
            return {"message": "Uživatel nenalezen"}

        has_password = bool(user.hashed_password and len(user.hashed_password) > 2)
        return {"needsPassword": not has_password}
    except Exception as e:
        print(f"Error checking user password: {str(e)}")
        raise HTTPException(status_code=500, detail="Chyba při kontrole uživatele")
