from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
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
def register(user: UserCreateWithKey, db: Session = Depends(get_db)):
    # Ověření klíče
    reg_key = db.query(RegistrationKey).filter(RegistrationKey.key == user.registration_key).first()
    if not reg_key or reg_key.used:
        raise HTTPException(status_code=400, detail="Neplatný nebo použitý registrační klíč")

    # Ověření e-mailu
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Uživatel už existuje")

    # Vytvoření uživatele
    new_user = User(
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    db.add(new_user)

    # Označení klíče jako použitý
    reg_key.used = True

    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Špatný email nebo heslo")

    if not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Špatný email nebo heslo")

    token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return {"user_id": current_user["user_id"]}

@router.post("/complete-google-registration")
def complete_registration(request_data: CompleteRegistrationRequest, db: Session = Depends(get_db)):
    """
    Endpoint pro dokončení registrace pomocí Google přihlášení.
    Ověří registrační klíč a nastaví heslo pro existujícího uživatele.
    """
    # Ověření klíče
    reg_key = db.query(RegistrationKey).filter(RegistrationKey.key == request_data.registrationKey).first()
    if not reg_key:
        raise HTTPException(status_code=400, detail="Neplatný registrační klíč")
    if reg_key.used:
        raise HTTPException(status_code=400, detail="Registrační klíč byl již použit")

    # Ověření uživatele
    user = db.query(User).filter(User.email == request_data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Uživatel nenalezen")

    # Aktualizace hesla uživatele
    user.hashed_password = hash_password(request_data.password)
    
    # Označení klíče jako použitý
    reg_key.used = True
    reg_key.used_by = request_data.email
    
    db.commit()
    
    return {"status": "success", "message": "Registrace úspěšně dokončena"}

@router.post("/check_user_password")
def check_user_password(request_data: UserCheckRequest, db: Session = Depends(get_db)):
    """
    Endpoint pro kontrolu, zda uživatel má nastavené heslo.
    Vrací true, pokud uživatel existuje a má heslo; false jinak.
    """
    try:
        # Verify the token is valid first (optional but recommended for security)
        # This depends on how you want to handle authentication - you could skip this step
        # if you want to allow checking without authentication
        
        # Find the user
        user = db.query(User).filter(User.email == request_data.email).first()
        
        if not user:
            # User doesn't exist
            return {
                "message": "Uživatel nenalezen"
                }
        
        # Check if the user has a valid password
        # For OAuth users, we can consider auto-generated passwords as "no password"
        # This assumes your OAuth implementation uses a specific pattern or length
        # You might need to adapt this logic based on how you generate OAuth passwords
        
        # Simple check - if password exists and is not empty
        has_password = bool(user.hashed_password and len(user.hashed_password) > 2)
        
        if has_password:
            # User has a password
            return {"needsPassword": False}
        else:
            # User does not have a password
            # This could mean they are an OAuth user or just haven't set a password
            return {"needsPassword": True}
        
    except Exception as e:
        # Log the error but don't expose details
        print(f"Error checking user password: {str(e)}")
        raise HTTPException(status_code=500, detail="Chyba při kontrole uživatele")