from fastapi import APIRouter, Query, Depends
from source.services.fake_news_service import process_fake_news

# Vytvoření routeru pro endpointy spojené s detekcí fake news
router = APIRouter()

@router.get("/fake_news_check/{prompt}")
async def fake_news_check_path(prompt: str):
    """
    Endpoint pro kontrolu textu na fake news - parametr jako součást cesty URL.
    
    Parametry:
    - prompt: Text, který má být analyzován na přítomnost fake news
    
    Vrací výsledek analýzy z fake news služby.
    """
    result = await process_fake_news(prompt)
    return result

@router.get("/fake_news_check")
async def check_fake_news(prompt: str):
    """
    Endpoint pro kontrolu textu na fake news - parametr jako query parametr.
    
    Parametry:
    - prompt: Text, který má být analyzován na přítomnost fake news (jako query parametr ?prompt=...)
    
    Vrací výsledek analýzy z fake news služby.
    """
    result = await process_fake_news(prompt)
    return result