"""
API Endpoint Overview

General:
---------
GET  /                             - Health check, returns a hello message.
                                     Response: {"message": "Hello, World!"}
GET  /favicon.ico                  - Returns favicon icon image.

OpenAI API (Text Processing):
-----------------------------
GET  /api/v1/{prompt}              - Processes the given prompt using OpenAI API (path param).
                                     Path parameter: prompt (string) - Text to analyze
                                     Response: {"result": "Analysis output"}

GET  /api/v1?prompt=...            - Processes the given prompt using OpenAI API (query param).
                                     Query parameter: prompt (string) - Text to analyze
                                     Response: {"result": "Analysis output"}

Fake News Verification:
-----------------------
GET  /api/v2/fake_news_check/{prompt} - Checks if the given prompt is fake news (path param).
                                        Path parameter: prompt (string) - News text to verify
                                        Response: {"result": analysis, "is_fake": boolean, "confidence": float}

GET  /api/v2/fake_news_check?prompt=... - Checks if the given prompt is fake news (query param).
                                          Query parameter: prompt (string) - News text to verify
                                          Response: {"result": analysis, "is_fake": boolean, "confidence": float}

User Authentication & Management:
---------------------------------
POST /api/register                 - Registers a new user with email, password, and registration key.
                                     Request body: {"email": string, "password": string, 
                                                  "full_name": string, "registration_key": string}
                                     Response: User object

POST /api/login                    - Authenticates user and returns JWT token.
                                     Request body: {"email": string, "password": string}
                                     Response: {"access_token": string, "token_type": "bearer"}

GET  /api/me                       - Returns info about the current authenticated user.
                                     Headers: Authorization: Bearer {token}
                                     Response: User object

POST /api/complete-google-registration - Completes registration for Google OAuth users.
                                         Request body: {"email": string, "full_name": string}
                                         Response: {"message": "Registration completed successfully"}

POST /api/check_user_password      - Checks if a user has a password set.
                                     Request body: {"email": string, "password": string}
                                     Response: {"message": "Password is correct"}

Google OAuth:
-------------
GET  /auth/google_login            - Initiates Google OAuth login flow.
                                     Response: Redirects to Google authentication page

GET  /auth/callback                - Handles Google OAuth callback.
                                     Query parameters: Generated by Google OAuth
                                     Response: Redirects with JWT token

Admin (Registration Keys):
--------------------------
POST /api/generate-keys            - Generates registration keys (admin only).
                                     Headers: Authorization: Bearer {admin_token}
                                     Request body: {"count": integer}
                                     Response: {"keys": [string, string, ...]}

GET  /api/list-keys                - Lists all registration keys (admin only).
                                     Headers: Authorization: Bearer {admin_token}
                                     Response: {"keys": [{key: string, used: boolean}, ...]}

Token & Environment Utilities:
------------------------------
GET  /api/validate_token           - Validates a JWT token and returns user info if valid.
                                     Headers: Authorization: Bearer {token}
                                     Response: User object or error

GET  /api/check-env                - Returns environment variable status (for debugging).
                                     Response: {"env_variables": {"VAR1": "set", "VAR2": "not set", ...}}
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import logging
import sys
from source.middleware.rate_limit_monitor import RateLimitMonitorMiddleware
from source.routes.fake_news_routes import limiter
from source.modules.config import config
from source.routes.fake_news_routes import router as fake_news_router
from source.routes.user_routes import router as user_router
from source.routes.admin_routes import router as admin_router
from source.routes.token_routes import router as token_router
from source.routes.auth_routes import router as auth_router
from source.routes.form_routes import router as form_router
from source.routes.feedback_routes import router as feedback_router
from source.modules.database import engine, Base, AsyncSessionLocal as SessionLocal 
from source.modules.config import config
from sqlalchemy.future import select
from source.modules.models import User 
from source.modules.auth import hash_password
from source.middleware.user_activity_middleware import UserActivityMiddleware

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO, # Default level for console for most loggers
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
root_logger_instance = logging.getLogger() 

# 2. Configure 'user_activity' logger for DEBUG console output
user_activity_logger = logging.getLogger("user_activity")
user_activity_logger.setLevel(logging.DEBUG) # Keep this at DEBUG if you want the middleware's INFO/WARNING/ERROR to show
                                            # If you commented out all DEBUG in middleware and only want its INFO and above,
                                            # you could set this to logging.INFO.
                                            # For now, keeping it DEBUG allows its INFO/WARNING/ERROR to pass through.

# 3. Configure 'fake_news_telemetry' logger for file output
telemetry_logger = logging.getLogger("fake_news_telemetry")
telemetry_log_level_str = config.TELEMETRY_LOG_LEVEL.upper()
telemetry_log_level = getattr(logging, telemetry_log_level_str, logging.INFO)
telemetry_logger.setLevel(telemetry_log_level)

try:
    file_handler = logging.FileHandler("telemetry.log", mode='a') 
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    telemetry_logger.addHandler(file_handler)
    telemetry_logger.propagate = False
    # root_logger_instance.info("Telemetry logger configured to write to telemetry.log and not propagate to console.") # Remove test log
except IOError as e:
    root_logger_instance.error(f"Failed to set up FileHandler for telemetry.log: {e}")


description = """
    # Fake News Detection API 🕵️‍♂️

    Modern API for detecting fake news and managing users.

    ## 🔍 Fake News Detection

    * **Check News (GET `/api/v2/fake_news_check/{prompt}`)** - Analyze text for fake news
    * **Query Check (GET `/api/v2/fake_news_check?prompt=...`)** - Same analysis via query parameter

    ## 👤 User Management

    * **Register (POST `/api/register`)** - Create new account with email and password
    * **Login (POST `/api/login`)** - Get JWT authentication token
    * **Profile (GET `/api/me`)** - Get current user information
    * **Password Check (POST `/api/check_user_password`)** - Verify user password

    ## 🔑 Authentication

    * **Google Login (GET `/auth/google_login`)** - Sign in with Google
    * **Google Callback (GET `/auth/callback`)** - OAuth callback handler
    * **Complete Registration (POST `/api/complete-google-registration`)** - Finish Google signup

    ## ⚙️ Admin Features

    * **Generate Keys (POST `/api/generate-keys`)** - Create registration keys
    * **List Keys (GET `/api/list-keys`)** - View all registration keys

    ## 📝 Feedback

    * **Create Feedback (POST `/api/feedback/feedback`)** - Submit user feedback
    * **Get Feedback (GET `/api/feedback/feedback/{telemetry_id}`)** - Get feedback for specific telemetry record

    ## 🛠️ Utilities

    * **Validate Token (GET `/api/validate_token`)** - Check JWT token validity
    * **Environment Check (GET `/api/check-env`)** - View environment status
    * **Health Check (GET `/`)** - Basic API availability test
"""

summary = """
    Professional fake news detection API with AI-powered analysis, secure user authentication, 
    and administrative tools. Features include Google OAuth integration, registration key management, 
    and comprehensive system utilities for monitoring and maintenance.
"""

env = config.ENVIRONMENT

if env == "production":
    app = FastAPI(
        docs_url=None,    # Disable docs (Swagger UI)
        redoc_url=None,   # Disable redoc
        openapi_url=None,  # Disable OpenAPI schema
        title="Bezfejku API",
        description=description,
        summary=summary,
        version="1.1.0",
        contact={
            "name": "Vojtěch Faltýnek",
            "url": "https://vojtechfal.cz/",
            "email": "faltynekvojtech@gmail.com",
            },
        )

else:
    app = FastAPI(
        title="Bezfejku API",
        description=description,
        summary=summary,
        version="1.1.0",
        contact={
            "name": "Vojtěch Faltýnek",
            "url": "https://vojtechfal.cz/",
            "email": "faltynekvojtech@gmail.com",
        }
    )

if env == "production":
    origins = [
        "https://www.bezfejku.cz",
        "https://bezfejku.cz",
        "http://bezfejku.cz",
        "http://www.bezfejku.cz",
        "https://api.bezfejku.cz",
        "http://api.bezfejku.cz",
        "http://localhost:3000",
        "http://localhost:8000",
    ]
else:
    origins = ["*"]

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.on_event("startup")
async def on_startup():
    # create missing tables
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, checkfirst=True))

    async with SessionLocal() as db:
        admin_email = "admin@admin.admin"
        admin_password = config.ADMIN_PASSWORD

        result = await db.execute(select(User).filter(User.email == admin_email))
        existing_admin = result.scalar_one_or_none()

        if not existing_admin:
            hashed_admin_password = hash_password(admin_password)
            admin_user = User(
                email=admin_email,
                hashed_password=hashed_admin_password,
                role="admin"
            )
            db.add(admin_user)
            await db.commit()
            print(f"✅ Admin user '{admin_email}' created successfully during app startup.")
        else:
            print(f"ℹ️ Admin user '{admin_email}' already exists (checked at app startup).")

# Middleware setup
app.add_middleware(
    SessionMiddleware,
    secret_key=config.SECRET_KEY
)
app.add_middleware(
    RateLimitMonitorMiddleware
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    UserActivityMiddleware
)

# Include routers
app.include_router(fake_news_router, prefix="/api/v2", tags=["Fake News"])
app.include_router(user_router,      prefix="/api",    tags=["User"])
app.include_router(admin_router,     prefix="/api/admin",    tags=["Admin"])
app.include_router(token_router,     prefix="/api",    tags=["Token"])
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(form_router, prefix="/api/forms", tags=["Forms"])
app.include_router(feedback_router, prefix="/api/feedback", tags=["Feedback"])

@app.get("/")
def read_root():
    """
        Zakldani endpoint pro testovani, zda je aplikace dostupna. Neni dulezity, ale je fajn ho mit.
    """
    return {"message": "Hello, World!"}

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join(os.path.dirname(__file__), "favicon.ico"))
