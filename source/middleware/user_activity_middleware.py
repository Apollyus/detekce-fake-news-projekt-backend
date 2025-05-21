from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from source.modules.database import AsyncSessionLocal
from source.modules.models import UserActivity
from source.modules.auth import oauth2_scheme
import jwt
import logging
from source.modules.config import config

logger = logging.getLogger("user_activity")

class UserActivityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Only track authenticated routes
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "")
            
            try:
                # Decode the token to get user_id
                payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
                user_id = payload.get("sub")
                
                if user_id and user_id.isdigit():
                    # Update the user's last activity timestamp
                    async with AsyncSessionLocal() as db:
                        result = await db.execute(select(UserActivity).filter(UserActivity.user_id == int(user_id)))
                        activity = result.scalar_one_or_none()
                        
                        if activity:
                            activity.last_activity = datetime.now()
                        else:
                            db.add(UserActivity(user_id=int(user_id), last_activity=datetime.now()))
                        
                        await db.commit()
            except Exception as e:
                logger.error(f"Error updating user activity: {e}")
        
        return response