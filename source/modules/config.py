import os
from dotenv import load_dotenv

# Pokus o načtení .env souboru, pokud existuje
load_dotenv()

# Konfigurační třída pro snadný přístup ke všem proměnným prostředí
class Config:
    def get_frontend_url(self):
        """Vrací vhodnou URL frontendu podle aktuálního prostředí"""
        is_prod = os.getenv('ENVIRONMENT', 'development').lower() == 'production'
        return "https://bezfejku.cz" if is_prod else "http://localhost:3000"

    # Bezpečnost
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        print("Warning: SECRET_KEY is not set in .env, using default (unsafe for production).")
        SECRET_KEY = "your_default_secret_key_for_development_only_1234567890!@#$%^&*()"
    ALGORITHM = "HS256" # Define the algorithm here
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "vojtamavelkypele123")  # Výchozí hodnota pouze pro vývoj

    # API klíče
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
    GOOGLE_SEARCH_ENGINE_ID = os.environ.get("GOOGLE_SEARCH_ENGINE_ID", "")
    MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")

    # URL adresy
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://www.bezfejku.cz/")
    REDIRECT_URI = os.environ.get("REDIRECT_URI", "https://api.bezfejku.cz/auth/callback")
    
    # OAuth autentizace
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

    # Telemetrie
    TELEMETRY_ENABLED = os.environ.get("TELEMETRY_ENABLED", "true").lower() == "true"
    TELEMETRY_LOG_LEVEL = os.environ.get("TELEMETRY_LOG_LEVEL", "INFO")

    # Prostředí
    ENVIRONMENT = os.environ.get("ENVIRONMENT", "production").lower()

    # Databáze
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if DATABASE_URL:
        # Použití kompletní URL adresy, pokud je poskytnuta
        SQLALCHEMY_DATABASE_URL = DATABASE_URL
    else:
        DB_USER = os.environ.get("DB_USER")
        DB_PASSWORD = os.environ.get("DB_PASSWORD")
        DB_HOST = os.environ.get("DB_HOST")
        DB_PORT = os.environ.get("DB_PORT")
        DB_NAME = os.environ.get("DB_NAME")
        print("Nastavení DB:", DB_USER, DB_HOST, DB_PORT, DB_NAME)
        if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
            raise ValueError("Chybí jedna nebo více povinných proměnných prostředí pro databázi.")
        SQLALCHEMY_DATABASE_URL = (
            f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )

    # Admin heslo
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")  # Výchozí hodnota pouze pro vývoj

# Vytvoření singleton instance
config = Config()