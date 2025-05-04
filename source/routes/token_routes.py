from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from source.modules.auth import get_current_user
from source.modules.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("/validate_token")
async def validate_token(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user(request, db)
    if user:
        return JSONResponse(content={"valid": True})
    else:
        return JSONResponse(content={"valid": False}, status_code=401)