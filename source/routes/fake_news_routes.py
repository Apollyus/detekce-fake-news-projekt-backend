import logging
from fastapi import APIRouter, Query, Depends, Request
from source.services.fake_news_service import process_fake_news
from slowapi import Limiter
from slowapi.util import get_remote_address
from source.modules.auth import get_current_active_user

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Create a limiter instance with the key function (using IP address)
limiter = Limiter(key_func=get_remote_address)

# Funkce pro globální rate limiting - vždy vrací stejný klíč
def get_global_key(*args, **kwargs):
    return "global"

# Vytvoření routeru pro endpointy spojené s detekcí fake news
router = APIRouter()

@router.get("/fake_news_check/{prompt}")
@limiter.limit("5/minute", error_message="Překročen limit 5 požadavků za minutu. Zkuste to znovu později.")
@limiter.limit("20/minute", key_func=get_global_key, error_message="Aplikace je momentálně přetížena. Zkuste to znovu později.")
async def fake_news_check_path(request: Request, prompt: str, current_user: dict = Depends(get_current_active_user)):
    """
    Endpoint pro kontrolu textu na fake news - parametr jako součást cesty URL.
    Vyžaduje přihlášeného uživatele.
    
    Parametry:
    - prompt: Text, který má být analyzován na přítomnost fake news
    
    Vrací výsledek analýzy z fake news služby.
    """
    try:
        try:
            result = await process_fake_news(prompt)
            return result
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Network error: {str(e)}")
            return {
                "error": "Server is currently unavailable",
                "message": "The server encountered an error while processing your request. Please try again later.",
                "details": str(e)
            }, 503
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                "error": "Internal Server Error",
                "message": "An unexpected error occurred while processing your request.",
                "details": str(e)
            }, 500
    except (ConnectionError, TimeoutError) as e:
        return {
            "error": "Server is currently unavailable",
            "message": "The server encountered an error while processing your request. Please try again later.",
            "details": str(e)
        }, 503
    except Exception as e:
        return {
            "error": "Internal Server Error",
            "message": "An unexpected error occurred while processing your request.",
            "details": str(e)
        }, 500

@router.get("/fake_news_check")
@limiter.limit("5/minute", error_message="Překročen limit 5 požadavků za minutu. Zkuste to znovu později.")
@limiter.limit("20/minute", key_func=get_global_key, error_message="Aplikace je momentálně přetížena. Zkuste to znovu později.")
async def check_fake_news(request: Request, prompt: str, current_user: dict = Depends(get_current_active_user)):
    """
    Endpoint pro kontrolu textu na fake news - parametr jako query parametr.
    Vyžaduje přihlášeného uživatele.
    
    Parametry:
    - prompt: Text, který má být analyzován na přítomnost fake news (jako query parametr ?prompt=...)
    
    Vrací výsledek analýzy z fake news služby.
    """
    try:
        try:
            result = await process_fake_news(prompt)
            return result
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Network error: {str(e)}")
            return {
                "error": "Server is currently unavailable",
                "message": "The server encountered an error while processing your request. Please try again later.",
                "details": str(e)
            }, 503
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                "error": "Internal Server Error",
                "message": "An unexpected error occurred while processing your request.",
                "details": str(e)
            }, 500
    except (ConnectionError, TimeoutError) as e:
        return {
            "error": "Server is currently unavailable",
            "message": "The server encountered an error while processing your request. Please try again later.",
            "details": str(e)
        }, 503
    except Exception as e:
        return {
            "error": "Internal Server Error",
            "message": "An unexpected error occurred while processing your request.",
            "details": str(e)
        }, 500