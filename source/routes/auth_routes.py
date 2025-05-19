from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import os
from source.modules.auth import create_access_token, get_current_user
from source.modules.database import get_db
from source.modules.models import User
from source.modules.config import config
from authlib.integrations.starlette_client import OAuth
# Import pro nové dependency funkce
from source.modules.auth import get_current_active_user, get_current_admin_user 

def get_frontend_url():
    """Vrátí příslušnou URL frontendu podle prostředí"""
    is_prod = os.getenv('ENVIRONMENT', 'development').lower() == 'production'
    return "https://bezfejku.cz" if is_prod else "http://localhost:3000"

# Vytvoření routeru pro autentizační endpointy
router = APIRouter()
# Inicializace OAuth klienta
oauth = OAuth()
# Registrace Google OAuth poskytovatele
google = oauth.register(
    name='google',
    client_id=config.GOOGLE_CLIENT_ID,
    client_secret=config.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

@router.get("/google_login")
async def login(request: Request):
    """
    Endpoint pro zahájení Google přihlášení.
    Přesměruje uživatele na Google OAuth přihlašovací stránku.
    """
    return await google.authorize_redirect(request, config.REDIRECT_URI)

@router.get('/callback')
async def auth(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Callback endpoint pro zpracování odpovědi z Google OAuth.
    Ověří token, získá informace o uživateli, vytvoří uživatele v databázi (pokud neexistuje),
    vygeneruje JWT token a přesměruje uživatele zpět na frontend.
    """
    try:
        # Získání tokenu od Google
        token = await google.authorize_access_token(request)
        
        # Předání tokenu při získávání informací o uživateli
        userinfo = await google.get('https://www.googleapis.com/oauth2/v3/userinfo', token=token)
        user_data = userinfo.json()
        
        # Kontrola, zda uživatel existuje, a vytvoření, pokud ne - převedeno na asynchronní
        result = await db.execute(select(User).filter(User.email == user_data['email']))
        db_user = result.scalar_one_or_none()
        
        user_role = "user" # Výchozí role pro nové OAuth uživatele
        if not db_user:
            # Vytvoření uživatele s prázdným heslem - indikuje OAuth uživatele bez nastaveného hesla
            db_user = User(
                email=user_data['email'],
                hashed_password="",  # Prázdné heslo indikuje OAuth uživatele, který musí dokončit registraci
                role=user_role # Přiřazení role
            )
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
        else:
            user_role = db_user.role # Pokud uživatel existuje, použijeme jeho stávající roli
        
        # Vytvoření JWT tokenu s rolí
        access_token = create_access_token(data={"sub": user_data['email'], "role": user_role})

        # Získání URL frontendu z konfigurace
        frontend_url = get_frontend_url()
        
        # Přesměrování uživatele zpět na frontend s tokenem a emailem
        return RedirectResponse(
            url=f"{frontend_url}/googleLoginSuccess?token={access_token}&email={user_data['email']}"
        )
    except Exception as e:
        # Přidání ladění pro zjištění, co se děje
        print(f"OAuth chyba: {str(e)}")
        await db.rollback()  # Asynchronní vrácení transakce
        raise HTTPException(status_code=400, detail=f"OAuth chyba: {str(e)}")