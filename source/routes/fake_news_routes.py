from fastapi import APIRouter, Query, Depends
from source.services.fake_news_service import process_fake_news
from source.modules.telemetry_module import get_metrics
from source.modules.admin_auth import admin_required

router = APIRouter()

@router.get("/fake_news_check/{prompt}")
def fake_news_check_path(prompt: str):
    return process_fake_news(prompt)

@router.get("/fake_news_check")
def fake_news_check_query(prompt: str = Query(..., description="Text to check for fake news")):
    return process_fake_news(prompt)

@router.get("/telemetry", dependencies=[Depends(admin_required)])
def get_telemetry_data():
    """Get telemetry data for the fake news detection service (admin only)"""
    return get_metrics()