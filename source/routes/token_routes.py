from fastapi import APIRouter, Request, Depends  # APIRouter groups routes, Request carries HTTP data, Depends for DI
from fastapi.responses import JSONResponse        # JSONResponse for sending JSON payloads
from source.modules.auth import get_current_user  # function to authenticate and retrieve the current user
from source.modules.database import get_db        # dependency provider for database sessions
from sqlalchemy.ext.asyncio import AsyncSession   # AsyncSession enables async DB operations

router = APIRouter()  # initialize API router for token-related endpoints

@router.get("/validate_token")  # define GET endpoint for token validation
async def validate_token(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Validate the authentication token provided in the request and return validity status.
    """
    # Retrieve user from token; will return None if invalid or expired
    user = await get_current_user(request, db)
    if user:
        # Token valid: respond with valid True
        return JSONResponse(content={"valid": True})
    else:
        # Token invalid or expired: respond with valid False and HTTP status 401
        return JSONResponse(content={"valid": False}, status_code=401)