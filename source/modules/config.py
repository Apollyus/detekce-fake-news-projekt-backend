import os
from dotenv import load_dotenv

# Try to load .env file if it exists
load_dotenv()

# Configuration class for easy access to all environment variables
class Config:
    def get_frontend_url(self):
        """Returns the appropriate frontend URL based on environment"""
        is_prod = os.getenv('ENVIRONMENT', 'development').lower() == 'production'
        return "https://bezfejku.cz" if is_prod else "http://localhost:3000"

    # Security
    SECRET_KEY = os.environ.get("SECRET_KEY", "skibidi-sigma")  # Default only for development
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "vojtamavelkypele123")  # Default only for development

    # API Keys
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
    GOOGLE_SEARCH_ENGINE_ID = os.environ.get("GOOGLE_SEARCH_ENGINE_ID", "")
    MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")

    # URLs
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://www.bezfejku.cz/")
    REDIRECT_URI = os.environ.get("REDIRECT_URI", "https://api.bezfejku.cz/auth/callback")
    
    # OAuth
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

# Create a singleton instance
config = Config()