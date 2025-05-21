from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from datetime import datetime
# sqlalchemy.ext.asyncio.AsyncSession is not directly used here, AsyncSessionLocal provides it
from sqlalchemy.future import select
from source.modules.database import AsyncSessionLocal
from source.modules.models import User, UserActivity # Ensure User is imported
# source.modules.auth.oauth2_scheme is not directly used in dispatch logic below
import jwt
import logging
from source.modules.config import config

# Configure this logger in your main application setup if it's not already.
# Example:
# import logging
# logging.basicConfig(level=logging.DEBUG) # Or your preferred level
# logging.getLogger("user_activity").setLevel(logging.DEBUG)
logger = logging.getLogger("user_activity")


class UserActivityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        # This log message helps confirm the middleware is being instantiated.
        logger.info("UserActivityMiddleware initialized.") # Keep INFO for initialization

    async def dispatch(self, request: Request, call_next):
        # logger.debug(f"UserActivityMiddleware: dispatch called for path {request.url.path}") # Comment out
        
        response = await call_next(request)

        authorization = request.headers.get("Authorization")
        # logger.debug(f"UserActivityMiddleware: Authorization header: {'Present' if authorization else 'Missing'}") # Comment out

        if authorization and authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "")
            # logger.debug(f"UserActivityMiddleware: Token found (first 20 chars): {token[:20]}...") # Comment out
            try:
                payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
                # logger.debug(f"UserActivityMiddleware: Token payload decoded: {payload}") # Comment out
                subject_from_token = payload.get("sub") # This could be ID or email
                # logger.debug(f"UserActivityMiddleware: 'sub' claim from token: '{subject_from_token}' (type: {type(subject_from_token)})") # Comment out

                user_id_to_log = None

                if subject_from_token:
                    if isinstance(subject_from_token, int):
                        user_id_to_log = subject_from_token
                        # logger.debug(f"UserActivityMiddleware: 'sub' is an integer: {user_id_to_log}") # Comment out
                    elif isinstance(subject_from_token, str):
                        if subject_from_token.isdigit():
                            user_id_to_log = int(subject_from_token)
                            # logger.debug(f"UserActivityMiddleware: 'sub' is a digit string, converted to int: {user_id_to_log}") # Comment out
                        elif "@" in subject_from_token:
                            # logger.debug(f"UserActivityMiddleware: 'sub' appears to be an email: {subject_from_token}. Looking up user ID.") # Comment out
                            async with AsyncSessionLocal() as db_for_id_lookup:
                                user_by_email_result = await db_for_id_lookup.execute(
                                    select(User.id).filter(User.email == subject_from_token)
                                )
                                user_id_from_email = user_by_email_result.scalar_one_or_none()
                                if user_id_from_email:
                                    user_id_to_log = user_id_from_email
                                    # logger.debug(f"UserActivityMiddleware: Found user ID {user_id_to_log} for email {subject_from_token}") # Comment out
                                else:
                                    logger.warning(f"UserActivityMiddleware: User email '{subject_from_token}' from token not found in database.") # Keep WARNING
                        else:
                            logger.warning(f"UserActivityMiddleware: 'sub' claim '{subject_from_token}' is not a recognized ID or email format.") # Keep WARNING
                    else:
                        logger.warning(f"UserActivityMiddleware: 'sub' claim '{subject_from_token}' has an unexpected type: {type(subject_from_token)}.") # Keep WARNING
                else:
                    logger.warning("UserActivityMiddleware: 'sub' claim is missing or None in token.") # Keep WARNING

                if user_id_to_log is not None:
                    # logger.debug(f"UserActivityMiddleware: User ID to process for activity: {user_id_to_log}") # Comment out
                    async with AsyncSessionLocal() as db:
                        # logger.debug(f"UserActivityMiddleware: DB session opened for user_id {user_id_to_log}.") # Comment out
                        
                        user_lookup_result = await db.execute(
                            select(User.id).filter(User.id == user_id_to_log)
                        )
                        existing_user_id = user_lookup_result.scalar_one_or_none()
                        # logger.debug(f"UserActivityMiddleware: User lookup in 'users' table for ID {user_id_to_log}: {'Found' if existing_user_id else 'Not found'}") # Comment out

                        if not existing_user_id:
                            logger.warning(
                                f"UserActivityMiddleware: User with ID {user_id_to_log} (derived from token) not found in users table. "
                                f"Cannot log activity."
                            ) # Keep WARNING
                        else:
                            # logger.debug(f"UserActivityMiddleware: User {user_id_to_log} confirmed to exist. Proceeding with activity log.") # Comment out
                            activity_result = await db.execute(
                                select(UserActivity).filter(UserActivity.user_id == user_id_to_log)
                            )
                            activity = activity_result.scalar_one_or_none()
                            
                            current_time = datetime.now()
                            if activity:
                                activity.last_activity = current_time
                                # logger.debug(f"UserActivityMiddleware: Updating last_activity for user_id {user_id_to_log} to {current_time}") # Comment out
                            else:
                                new_activity = UserActivity(user_id=user_id_to_log, last_activity=current_time)
                                db.add(new_activity)
                                # logger.debug(f"UserActivityMiddleware: Adding new UserActivity for user_id {user_id_to_log} with last_activity {current_time}") # Comment out
                            
                            try:
                                await db.commit()
                                #logger.info(f"UserActivityMiddleware: DB commit successful for user_id {user_id_to_log}.") # Keep INFO for successful DB operations
                            except Exception as commit_exc:
                                logger.error(f"UserActivityMiddleware: DB commit FAILED for user_id {user_id_to_log}: {commit_exc}", exc_info=True) # Keep ERROR
                                await db.rollback() 

            except jwt.ExpiredSignatureError:
                logger.warning("UserActivityMiddleware: Token has expired.") # Keep WARNING
            except jwt.InvalidTokenError as e:
                logger.warning(f"UserActivityMiddleware: Invalid token: {e}") # Keep WARNING
            except Exception as e:
                logger.error(f"UserActivityMiddleware: Error processing user activity: {e}", exc_info=True) # Keep ERROR
        elif authorization:
            logger.warning(f"UserActivityMiddleware: Authorization header present but not 'Bearer ' type: {authorization}") # Keep WARNING
        # else: # No need to log missing auth header every time if it's common
            # logger.debug("UserActivityMiddleware: No Authorization header found. Skipping activity log for this request.") # Comment out
        
        # logger.debug(f"UserActivityMiddleware: dispatch finished for path {request.url.path}") # Comment out
        return response