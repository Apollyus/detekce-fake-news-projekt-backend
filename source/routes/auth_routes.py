from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from source.modules.auth import create_access_token, get_current_user
from source.modules.database import get_db
from source.modules.models import User
from source.modules.config import config
from authlib.integrations.starlette_client import OAuth

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
    return await google.authorize_redirect(request, config.REDIRECT_URI)

@router.get('/callback')
async def auth(request: Request, db: Session = Depends(get_db)):
    try:
        # Get token from Google
        token = await google.authorize_access_token(request)
        
        # Pass the token when fetching user info
        userinfo = await google.get('https://www.googleapis.com/oauth2/v3/userinfo', token=token)
        user_data = userinfo.json()
        
        # Check if user exists and create if not
        db_user = db.query(User).filter(User.email == user_data['email']).first()
        if not db_user:
            # Create user with empty password - indicating OAuth user without set password
            db_user = User(
                email=user_data['email'],
                hashed_password=""  # Empty password indicates OAuth user who needs to complete registration
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
        
        # Create JWT token
        access_token = create_access_token(data={"sub": user_data['email']})

        # Get frontend URL from config
        #frontend_url = config.get_frontend_url()
        frontend_url = "https://www.bezfejku.cz"
        
        return RedirectResponse(
            url=f"{frontend_url}/googleLoginSuccess?token={access_token}&email={user_data['email']}"
        )
    except Exception as e:
        # Add debugging to see what's happening
        print(f"OAuth error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")