# Definice schémat pro validaci dat používaných v API aplikace pro detekci fake news
from pydantic import BaseModel, EmailStr, constr, validator  # Import Pydantic tříd pro validaci dat
from typing import Optional  # Import pro označení volitelných polí
import re  # Import pro práci s regulárními výrazy
from html import escape  # Import pro escapování HTML znaků
from datetime import datetime  # Import pro práci s časovými údaji

class UserCreate(BaseModel):
    """Schéma pro vytvoření nového uživatele"""
    email: EmailStr  # Email uživatele (validovaný formát)
    password: str  # Heslo uživatele

class UserOut(BaseModel):
    """Schéma pro výstup informací o uživateli (bez citlivých údajů)"""
    id: int  # ID uživatele
    email: EmailStr  # Email uživatele

    class Config:
        """Konfigurace pro automatické mapování z ORM objektů"""
        from_attributes = True  # Povoluje konverzi z ORM objektů

class UserLogin(BaseModel):
    """Schéma pro přihlášení uživatele"""
    email: EmailStr  # Email uživatele
    password: str  # Heslo uživatele

class TokenResponse(BaseModel):
    """Schéma pro odpověď s přístupovým tokenem"""
    access_token: str  # Přístupový token
    token_type: str = "bearer"  # Typ tokenu (výchozí hodnota "bearer")

class UserCreateWithKey(UserCreate):
    """Rozšířené schéma pro vytvoření uživatele s registračním klíčem"""
    registration_key: str  # Registrační klíč pro ověření

class CompleteRegistrationRequest(BaseModel):
    """Schéma pro dokončení registrace uživatele"""
    token: str  # Token pro ověření
    email: str  # Email uživatele
    password: str  # Heslo uživatele
    registrationKey: str  # Registrační klíč

class UserCheckRequest(BaseModel):
    """Schéma pro ověření uživatele"""
    email: str  # Email uživatele
    token: str  # Token pro ověření

class FormSubmission(BaseModel):
    """Schéma pro odeslání kontaktního formuláře"""
    full_name: constr(min_length=2, max_length=100)  # Celé jméno (omezená délka 2-100 znaků)
    email: EmailStr  # Email odesílatele
    subject: constr(min_length=3, max_length=100)  # Předmět zprávy (omezená délka 3-100 znaků)
    message: constr(min_length=10, max_length=1000)  # Obsah zprávy (omezená délka 10-1000 znaků)
    # Volitelná pole pro odpověď
    id: int | None = None  # ID záznamu formuláře (volitelné)
    created_at: datetime | None = None  # Čas vytvoření záznamu (volitelné)

    # Konfigurace pro ORM režim
    class Config:
        """Konfigurace pro automatické mapování z ORM objektů"""
        orm_mode = True  # Povoluje konverzi z ORM objektů

    @validator('full_name', 'subject', 'message')
    def sanitize_text(cls, v):
        """Validátor pro sanitizaci textových vstupů"""
        # Odstranění HTML tagů
        clean_text = re.sub(r'<[^>]*>', '', v)
        # Escapování speciálních znaků
        clean_text = escape(clean_text)
        # Odstranění vícenásobných mezer
        clean_text = ' '.join(clean_text.split())
        return clean_text

    @validator('full_name')
    def validate_name(cls, v):
        """Validátor pro kontrolu formátu jména"""
        if not re.match(r'^[a-zA-Z\s-]+$', v):
            raise ValueError('Jméno by mělo obsahovat pouze písmena, mezery a pomlčky')
        return v

class UserFeedbackCreate(BaseModel):
    """Schéma pro vytvoření zpětné vazby od uživatele"""
    telemetry_id: str  # UUID jako string, už ne číselné ID
    rating: int  # Hodnocení 1-5
    comment: Optional[str] = None  # Volitelný komentář
    is_correct: bool  # Zda byla analýza správná nebo ne

class UserFeedbackOut(BaseModel):
    """Schéma pro výstup zpětné vazby"""
    id: int
    telemetry_record_id: int
    rating: int
    comment: Optional[str]
    is_correct: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserFeedbackWithPromptOut(BaseModel):
    """Schéma pro výstup zpětné vazby včetně promptu"""
    id: int
    telemetry_record_id: int  # Interní ID (můžete zachovat pro debugging)
    telemetry_id: str  # UUID pro veřejné API
    rating: int
    comment: Optional[str]
    is_correct: bool
    created_at: datetime
    prompt: str  # Text, který byl ověřován

    class Config:
        from_attributes = True