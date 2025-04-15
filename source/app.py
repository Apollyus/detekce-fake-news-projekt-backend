from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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
from source.schemas import UserCreate, UserOut, UserLogin, TokenResponse, UserCreateWithKey
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

ADMIN_PASSWORD = "vojtamavelkypele123"

app = FastAPI()

origins = ["*"]

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
            
@app.get("/api/v2/{prompt}")
def fake_news_check(prompt: str):
    """
    Endpoint pro zpracovani a overeni textu.
    - prompt: text, ktery chceme zpracovat
    """
    # Fix the condition (it was reversed)
    if is_long_enough_words(prompt, 20):
        first_part = check_and_generate_search_phrase(prompt)
        search_query = first_part["search_query"]
        valid = first_part["valid"]
        keywords = first_part["keywords"]
        
        if not valid:
            return {
                "status": "error",
                "message": "Zadaný text není validní pro ověření..."
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
        
        if not valid:
            return {
                "status": "error",
                "message": "Zadaný text není validní pro ověření..."
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
    

@app.get("/api/v2")
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