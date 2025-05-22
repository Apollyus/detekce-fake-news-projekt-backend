from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from datetime import datetime
from sqlalchemy.future import select
from source.modules.database import AsyncSessionLocal
from source.modules.models import User, UserActivity, UserActivityLog
import jwt
import logging
from source.modules.config import config

logger = logging.getLogger("user_activity")

class UserActivityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        logger.info("UserActivityMiddleware initialized.")

    async def dispatch(self, request: Request, call_next):
        # Get client IP address and method
        client_ip = request.client.host if request.client else "unknown"
        endpoint = request.url.path
        http_method = request.method
        
        # Track action type based on the endpoint
        action_type = self._determine_action_type(endpoint)
        
        # Current user email (will be populated if authenticated)
        user_email = None
        user_id = None
        
        # Process the request first
        response = await call_next(request)
        status_code = response.status_code

        # Try different authorization headers (case insensitive)
        auth_header = None
        for header_name, header_value in request.headers.items():
            if header_name.lower() == 'authorization':
                auth_header = header_value
                break
                
        authorization = auth_header
        
        # Check if cookie contains authentication
        cookie_header = request.headers.get("cookie")
        token = None
        
        # Try to extract a token from multiple sources
        if authorization and authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "")
        elif cookie_header and "token=" in cookie_header:
            # Extract token from cookie
            cookie_parts = cookie_header.split(";")
            for part in cookie_parts:
                if part.strip().startswith("token="):
                    token = part.strip().replace("token=", "")
                    break
        
        # If we have a token from any source, try to decode it
        if token:
            try:
                payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
                
                subject_from_token = payload.get("sub")  # This could be ID or email
                
                # Try to get email from multiple possible token locations
                user_email = payload.get("email") or payload.get("preferred_username") or payload.get("username")
                
                user_id_to_log = None

                if subject_from_token:
                    if isinstance(subject_from_token, int):
                        user_id_to_log = subject_from_token
                    elif isinstance(subject_from_token, str):
                        if subject_from_token.isdigit():
                            user_id_to_log = int(subject_from_token)
                        elif "@" in subject_from_token:
                            user_email = subject_from_token  # Use the email from token
                            async with AsyncSessionLocal() as db_for_id_lookup:
                                user_by_email_result = await db_for_id_lookup.execute(
                                    select(User.id).filter(User.email == subject_from_token)
                                )
                                user_id_from_email = user_by_email_result.scalar_one_or_none()
                                if user_id_from_email:
                                    user_id_to_log = user_id_from_email
                                else:
                                    logger.warning(f"User email '{subject_from_token}' from token not found in database.")
                        else:
                            logger.warning(f"'sub' claim '{subject_from_token}' is not a recognized ID or email format.")
                    else:
                        logger.warning(f"'sub' claim '{subject_from_token}' has unexpected type: {type(subject_from_token)}.")
                elif user_email:
                    # Try to get user by email if sub is missing
                    async with AsyncSessionLocal() as db_for_id_lookup:
                        user_by_email_result = await db_for_id_lookup.execute(
                            select(User.id).filter(User.email == user_email)
                        )
                        user_id_from_email = user_by_email_result.scalar_one_or_none()
                        if user_id_from_email:
                            user_id_to_log = user_id_from_email

                if user_id_to_log is not None:
                    async with AsyncSessionLocal() as db:
                        # Get user data including email
                        user_lookup_result = await db.execute(
                            select(User).filter(User.id == user_id_to_log)
                        )
                        user_record = user_lookup_result.scalar_one_or_none()

                        if not user_record:
                            logger.warning(f"User with ID {user_id_to_log} not found in users table.")
                        else:
                            # If we didn't get email from token, use the one from database
                            if not user_email:
                                user_email = user_record.email
                                
                            # Update the UserActivity record for the user
                            activity_result = await db.execute(
                                select(UserActivity).filter(UserActivity.user_id == user_id_to_log)
                            )
                            activity = activity_result.scalar_one_or_none()
                            
                            current_time = datetime.now()
                            if activity:
                                activity.last_activity = current_time
                            else:
                                new_activity = UserActivity(user_id=user_id_to_log, last_activity=current_time)
                                db.add(new_activity)
                            
                            # Log detailed activity to the UserActivityLog table
                            try:
                                # Create activity log record
                                activity_log = UserActivityLog(
                                    user_id=user_id_to_log,
                                    email=user_email,
                                    ip_address=client_ip,
                                    action_type=action_type,
                                    endpoint=endpoint,
                                    http_method=http_method,  # Add HTTP method
                                    status_code=status_code,  # Add status code
                                    timestamp=current_time
                                )
                                db.add(activity_log)
                                await db.commit()
                            except Exception as commit_exc:
                                logger.error(f"DB commit failed for user_id {user_id_to_log}: {commit_exc}")
                                await db.rollback()
                
                # Even if we don't have a valid user_id but have email (e.g., failed login),
                # still log the activity
                elif user_email:
                    await self._log_anonymous_activity(user_email, client_ip, action_type, endpoint)

            except jwt.ExpiredSignatureError:
                await self._log_anonymous_activity("expired_token", client_ip, action_type, endpoint)
            except jwt.InvalidTokenError:
                await self._log_anonymous_activity("invalid_token", client_ip, action_type, endpoint)
            except Exception as e:
                logger.error(f"Error processing user activity: {e}")
        else:
            # Log anonymous activity
            await self._log_anonymous_activity("anonymous", client_ip, action_type, endpoint)
        
        return response
    
    def _determine_action_type(self, endpoint: str) -> str:
        """Determine the action type based on the endpoint"""
        if "/login" in endpoint:
            return "Přihlášení"
        elif "/register" in endpoint:
            return "Registrace"
        elif "/fake_news_check" in endpoint or "/analyze" in endpoint:
            return "Analýza textu"
        elif "/api" in endpoint and ("/v1/" in endpoint or "/v2/" in endpoint):
            return "API požadavek" 
        elif "/admin/" in endpoint:
            return "Admin přístup"
        else:
            return "Ostatní"
    
    async def _log_anonymous_activity(self, identifier: str, ip_address: str, action_type: str, endpoint: str):
        """Log activity for anonymous or problematic auth users"""
        try:
            async with AsyncSessionLocal() as db:
                activity_log = UserActivityLog(
                    user_id=None,  # No user ID for anonymous
                    email=identifier,  # Could be "anonymous", "expired_token", email, etc.
                    ip_address=ip_address,
                    action_type=action_type,
                    endpoint=endpoint,
                    timestamp=datetime.now()
                )
                db.add(activity_log)
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to log anonymous activity: {e}")