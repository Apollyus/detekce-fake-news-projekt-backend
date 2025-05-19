"""Modul user_routes implementuje REST API pro správu uživatelů,
včetně registrace, přihlášení, získání informací o uživateli,
dokončení registrace přes Google a kontroly hesla."""
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
    """
    Registruje nového uživatele pomocí registračního klíče.
    Args:
        user (UserCreateWithKey): data pro registraci (email, heslo, klíč)
        db (AsyncSession): databázová session
    Returns:
        UserOut: registrovaný uživatel
    """
    result = await db.execute(select(RegistrationKey).filter(RegistrationKey.key == user.registration_key))
    # Načtení registračního klíče z DB
    reg_key = result.scalar_one_or_none()
    if not reg_key or reg_key.used:
        raise HTTPException(status_code=400, detail="Neplatný nebo použitý registrační klíč")

    result = await db.execute(select(User).filter(User.email == user.email))
    # Kontrola, zda uživatel již existuje v DB
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
    """
    Přihlášení uživatele a vytvoření přístupového tokenu.
    Args:
        user_data (UserLogin): přihlašovací údaje (email, heslo)
        db (AsyncSession): databázová session
    Returns:
        dict: obsahuje access_token a token_type
    """
    result = await db.execute(select(User).filter(User.email == user_data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Špatný email nebo heslo")

    token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Získá informace o aktuálně přihlášeném uživateli.
    Args:
        current_user (dict): data ověřeného uživatele získané z tokenu
    Returns:
        dict: obsahuje user_id, email a roli
    """
    return {
        "user_id": current_user.get("user_id"),
        "email": current_user.get("email"),
        "role": current_user.get("role")
    }

@router.post("/complete-google-registration")
async def complete_registration(request_data: CompleteRegistrationRequest, db: AsyncSession = Depends(get_db)):
    """
    Dokončí registraci uživatele přes Google.
    Args:
        request_data (CompleteRegistrationRequest): data pro dokončení registrace
        db (AsyncSession): databázová session
    Returns:
        dict: status a zpráva o úspěchu
    """
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
    """
    Zkontroluje, zda má uživatel nastavené heslo.
    Args:
        request_data (UserCheckRequest): data pro kontrolu (email)
        db (AsyncSession): databázová session
    Returns:
        dict: needsPassword (bool) indikující, jestli je potřeba nastavit heslo
    """
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
