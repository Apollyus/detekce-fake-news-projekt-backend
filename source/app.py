from fastapi import FastAPI, Depends, HTTPException, status, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
import os
import sys

# Change relative imports to absolute or ensure correct module structure
from source.models import Base, User, RegistrationKey
from source.database import SessionLocal, engine
from source.summarizer_module import get_summary
from source.filtrace_clanku_module import filter_relevant_articles
from source.generace_hledaci_vety_module import check_and_generate_search_phrase
from source.vyhledavani_googlem_module import google_search
from source.scraping_module import scrape_article
from source.finalni_rozhodnuti_module import evaluate_claim
from sqlalchemy.orm import Session
from source.schemas import UserCreate, UserOut, UserLogin, TokenResponse, UserCreateWithKey, CompleteRegistrationRequest, UserCheckRequest
from source.auth import hash_password, verify_password, create_access_token, get_current_user
from source.utils import generate_registration_key

# Add current directory to path explicitly
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)  # Insert at beginning for priority

import api_call as oapi

# Add this missing dependency function
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def is_long_enough_words(text: str, min_words: int) -> bool:
    words = text.strip().split()
    return len(words) >= min_words

Base.metadata.create_all(bind=engine)

# LOCALHOST 
frontend_url = "https//www.bezfejku.cz/"  # URL of your frontend application

# PRODUCTION
# frontend_url = "https://your-production-frontend-url.com"  # URL of your production frontend application

# Tento redirect URI musí být stejný jako ten, který zadáte v Google Developer Console
redirect_uri = 'http://api.bezfejku.cz/auth/callback'

ADMIN_PASSWORD = "vojtamavelkypele123"

app = FastAPI()

# Nastavení OAuth
oauth = OAuth()

oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID', ''),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET', ''),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Google OAuth 2.0 client
google = oauth.create_client('google')  # Registrujte u Google a použijte svůj Client ID a Secret

origins = ["*"]

# Add a secret key for session - should be a random string in production
# This should ideally come from environment variables
SECRET_KEY = "skibidi-sigma"  # Replace with a secure key in production

# Add SessionMiddleware - MUST be added before other middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
)

app.add_middleware(CORSMiddleware, allow_origins=origins,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def read_root():
    """
        Zakldani endpoint pro testovani, zda je aplikace dostupna. Neni dulezity, ale je fajn ho mit.
    """
    return {"message": "Hello, World!"}

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join(os.path.dirname(__file__), "favicon.ico"))

@app.get("/api/v1/{prompt}")
def read_item(prompt: str):
    """
        Endpoint pro zpracovani textu pomoci OpenAI API.
        - prompt: text, ktery chceme zpracovat
    """
    response = oapi.get_response(prompt)
    return {"response": response, 
            "output_text": response.output_text,
            }

# Add a query parameter endpoint for easier testing
@app.get("/api/v1")
def read_item_query(prompt: str):
    """
        Endpoint pro zpracovani textu pomoci OpenAI API (query parameter version).
        - prompt: text, ktery chceme zpracovat
    """
    response = oapi.get_response(prompt)
    return {"response": response, 
            "output_text": response.output_text,
            }
            
@app.get("/api/v2/fake_news_check/{prompt}")
def fake_news_check(prompt: str):
    """
    Endpoint pro zpracovani a overeni textu.
    - prompt: text, ktery chceme zpracovat
    """
    # Fix the condition (it was reversed)
    if is_long_enough_words(prompt, 4):
        first_part = check_and_generate_search_phrase(prompt)
        search_query = first_part["search_query"]
        valid = first_part["valid"]
        keywords = first_part["keywords"]
        
        if not valid:
            return {
                "status": "error",
                "message": "Zadaný text není validní pro ověření skibidi..."
            }
            
        google_search_results = google_search(search_query)
        if not google_search_results:
            return {
                "status": "error",
                "message": "Nenašli jsme žádné výsledky pro zadaný dotaz."
            }
            
        filtered_articles = filter_relevant_articles(google_search_results, keywords)
        if not filtered_articles:
            return {
                "status": "error",
                "message": "Nenašli jsme žádné relevantní články pro ověření."
            }
            
        filtered_snippets = [article["snippet"] for article in filtered_articles]
        rozhodnuti = evaluate_claim(prompt, filtered_snippets)
        
        if rozhodnuti:
            return {
                "status": "success",
                "message": "Ověření bylo úspěšné.",
                "result": rozhodnuti,
                "filtered_articles": filtered_articles
            }
        
        return {
            "status": "error",
            "message": "Chyba při ověřování tvrzení.",
            "filtered_articles": filtered_articles
        }
    else:
        first_part = check_and_generate_search_phrase(prompt)
        search_query = first_part["search_query"]
        valid = first_part["valid"]
        keywords = first_part["keywords"]
        #TADY JE CHYBA NEBO PROSTE NECO
        if not valid:
            return {
                "status": "error",
                "message": "Zadaný text není validní pro ověření...............",
                "prompt: " : str(prompt),
                "first_part: " : str(first_part),
                "search_query: " : str(search_query),
                "valid: " : str(valid),
                "keywords: " : str(keywords)
            }
            
        google_search_results = google_search(search_query)
        if not google_search_results:
            return {
                "status": "error",
                "message": "Nenašli jsme žádné výsledky pro zadaný dotaz."
            }
            
        filtered_articles = filter_relevant_articles(google_search_results, keywords)
        if not filtered_articles:
            return {
                "status": "error",
                "message": "Nenašli jsme žádné relevantní články pro ověření."
            }
            
        filtered_snippets = [article["snippet"] for article in filtered_articles]
        rozhodnuti = evaluate_claim(prompt, filtered_snippets)
        
        if rozhodnuti:
            return {
                "status": "success",
                "message": "Ověření bylo úspěšné.",
                "result": rozhodnuti,
                "filtered_articles": filtered_articles
            }
        
        return {
            "status": "error",
            "message": "Chyba při ověřování tvrzení.",
            "filtered_articles": filtered_articles
        }
    

@app.get("/api/v2/fake_news_check")
def fake_news_check_query(prompt: str):
    """
    Endpoint pro zpracovani a overeni textu.
    - prompt: text, ktery chceme zpracovat
    """
    first_part = check_and_generate_search_phrase(prompt)
    search_query = first_part["search_query"]
    valid = first_part["valid"]
    keywords = first_part["keywords"]
    
    if not valid:
        return {
            "status": "error",
            "message": "Zadaný text není validní pro ověření. Ujistěte se prosím, že:"
            "\n- Text obsahuje konkrétní tvrzení nebo fakta k ověření"
            "\n- Text je srozumitelný a dává smysl"
            "\n- Text není pouze názor nebo obecné prohlášení"
        }
        
    google_search_results = google_search(search_query)
    if not google_search_results:
        return {
            "status": "error",
            "message": "Nenašli jsme žádné výsledky pro zadaný dotaz."
        }
        
    filtered_articles = filter_relevant_articles(google_search_results, keywords)
    if not filtered_articles:
        return {
            "status": "error",
            "message": "Nenašli jsme žádné relevantní články pro ověření."
        }
        
    filtered_snippets = [article["snippet"] for article in filtered_articles]
    rozhodnuti = evaluate_claim(prompt, filtered_snippets)
    
    if rozhodnuti:
        return {
            "status": "success",
            "message": "Ověření bylo úspěšné.",
            "result": rozhodnuti,
            "filtered_articles": filtered_articles
        }
    
    return {
        "status": "error",
        "message": "Chyba při ověřování tvrzení.",
        "filtered_articles": filtered_articles
    }


@app.post("/api/register", response_model=UserOut)
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

@app.post("/api/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Špatný email nebo heslo")

    if not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Špatný email nebo heslo")

    token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/api/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return {"user_id": current_user["user_id"]}

@app.post("/api/generate-keys")
def generate_keys(
    count: int = Query(1, ge=1, le=100),
    password: str = Query(...),
    db: Session = Depends(get_db)
):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Neplatné heslo")

    generated = []
    existing_keys = db.query(RegistrationKey.key).all()
    existing_set = {k[0] for k in existing_keys}

    while len(generated) < count:
        key = generate_registration_key()
        if key not in existing_set:
            db.add(RegistrationKey(key=key))
            generated.append(key)
            existing_set.add(key)

    db.commit()
    return {"generated_keys": generated}

@app.get("/api/list-keys")
def list_keys(password: str = Query(...), db: Session = Depends(get_db)):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Neplatné heslo")

    keys = db.query(RegistrationKey).all()

    return {
        "keys": [
            {
                "key": k.key,
                "used": k.used,
                "used_by": k.used_by,
                "created_at": k.created_at.isoformat() if k.created_at else None
            } for k in keys
        ]
    }

@app.get("/auth/google_login")
async def login(request: Request):
    redirect_uri = request.url_for('auth')  # Use request.url_for instead of url_for
    return await google.authorize_redirect(request, redirect_uri)

@app.get('/auth/callback')
async def auth(request: Request, db: Session = Depends(get_db)):
    try:
        # Get token from Google
        token = await google.authorize_access_token(request)
        
        # Pass the token when fetching user info
        userinfo = await google.get('https://www.googleapis.com/oauth2/v3/userinfo', token=token)
        user_data = userinfo.json()
        
        # Check if user exists and create if not
        db_user = db.query(User).filter(User.email == user_data['email']).first()
        if not db_user:
            # Create user with empty password - indicating OAuth user without set password
            db_user = User(
                email=user_data['email'],
                hashed_password=""  # Empty password indicates OAuth user who needs to complete registration
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
        
        # Create JWT token
        access_token = create_access_token(data={"sub": user_data['email']})
        
        # Return token or redirect to frontend with token
        return RedirectResponse(url=f"http://localhost:3000/googleLoginSuccess?token={access_token}&email={user_data['email']}")
    except Exception as e:
        # Add debugging to see what's happening
        print(f"OAuth error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")
    
@app.post("/api/complete-google-registration")
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

@app.post("/api/check_user_password")
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
    
@app.get("/api/validate_token")
async def validate_token(request: Request):
    """
    Endpoint pro validaci JWT tokenu.
    Vrací informace o tokenu a uživateli, pokud je token platný.
    """
    try:
        # Extract the authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            return {
                "valid": False,
                "error": "missing_token",
                "message": "Authorization header missing or invalid format"
            }
            
        token = auth_header.replace("Bearer ", "")
        
        # Use the existing token validation functionality
        user_info = get_current_user(token)
        
        # If we got here, token is valid
        return {
            "valid": True,
            "user": {
                "id": user_info["user_id"],
                "email": user_info.get("email")  # Include if available in token payload
            }
        }
        
    except Exception as e:
        error_message = str(e)
        error_type = "invalid_token"
        
        # Provide more specific error types based on common exceptions
        if "expired" in error_message.lower():
            error_type = "token_expired"
        elif "invalid" in error_message.lower():
            error_type = "token_invalid"
            
        return {
            "valid": False,
            "error": error_type,
            "message": error_message
        }