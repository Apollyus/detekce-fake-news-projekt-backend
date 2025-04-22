from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from source.modules.auth import get_current_user

router = APIRouter()

@router.get("/validate_token")
async def validate_token(request: Request):
    user = await get_current_user(request)
    if user:
        return JSONResponse(content={"valid": True})
    else:
        return JSONResponse(content={"valid": False}, status_code=401)