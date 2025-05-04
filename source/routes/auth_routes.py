from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import os
from source.modules.auth import create_access_token, get_current_user
from source.modules.database import get_db
from source.modules.models import User
from source.modules.config import config
from authlib.integrations.starlette_client import OAuth
import secrets

def get_frontend_url():
    """Returns the appropriate frontend URL based on environment"""
    is_prod = os.getenv('ENVIRONMENT', 'development').lower() == 'production'
    return "https://bezfejku.cz" if is_prod else "http://localhost:3000"

router = APIRouter()
oauth = OAuth()
google = oauth.register(
    name='google',
    client_id=config.GOOGLE_CLIENT_ID,
    client_secret=config.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

@router.get("/google_login")
async def login(request: Request):
    # Generate a secure random state
    state = secrets.token_urlsafe(16)
    request.session["oauth_state"] = state
    
    redirect_uri = request.url_for('auth')
    return await google.authorize_redirect(request, redirect_uri, state=state)

@router.get('/callback')
async def auth(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        # Make sure session is available
        if "_state" not in request.session:
            raise HTTPException(status_code=400, detail="Session state is missing")
       
        # Get token from Google
        token = await google.authorize_access_token(request)
        
        # Pass the token when fetching user info
        userinfo = await google.get('https://www.googleapis.com/oauth2/v3/userinfo', token=token)
        user_data = userinfo.json()
        
        # Check if user exists and create if not - converted to async
        result = await db.execute(select(User).filter(User.email == user_data['email']))
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            # Create user with empty password - indicating OAuth user without set password
            db_user = User(
                email=user_data['email'],
                hashed_password=""  # Empty password indicates OAuth user who needs to complete registration
            )
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
        
        # Create JWT token
        access_token = create_access_token(data={"sub": user_data['email']})

        # Get frontend URL from config
        frontend_url = get_frontend_url()  # Used the correct function here
        
        return RedirectResponse(
            url=f"{frontend_url}/googleLoginSuccess?token={access_token}&email={user_data['email']}"
        )
    except Exception as e:
        # Add debugging to see what's happening
        print(f"OAuth error: {str(e)}")
        await db.rollback()  # Roll back transaction asynchronously
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")
