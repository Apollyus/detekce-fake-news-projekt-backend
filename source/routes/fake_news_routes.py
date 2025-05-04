from fastapi import APIRouter, Query, Depends
from source.services.fake_news_service import process_fake_news

router = APIRouter()

@router.get("/fake_news_check/{prompt}")
async def fake_news_check_path(prompt: str):
    result = await process_fake_news(prompt)
    return result

@router.get("/fake_news_check")
async def check_fake_news(prompt: str):
    result = await process_fake_news(prompt)
    return result