from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from source.modules.config import config

# Konfigurace URL pro připojení k databázi, zajištění použití asyncpg driveru
if config.SQLALCHEMY_DATABASE_URL and not config.SQLALCHEMY_DATABASE_URL.startswith("postgresql+asyncpg://"):
    SQLALCHEMY_DATABASE_URL = config.SQLALCHEMY_DATABASE_URL.replace(
        "postgresql://", "postgresql+asyncpg://"
    )
else:
    SQLALCHEMY_DATABASE_URL = (
        config.SQLALCHEMY_DATABASE_URL
        if config.SQLALCHEMY_DATABASE_URL
        else f"postgresql+asyncpg://{config.DB_USER}:{config.DB_PASSWORD}@"
             f"{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
    )

# Vytvoření asynchronního engine pro práci s databází
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,  # Vypnutí logu SQL dotazů
)

# Vytvoření továrny sessions pro asynchronní přístup k databázi
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Objekty zůstanou použitelné i po commitu
    autoflush=False,  # Deaktivace automatického flushe změn do DB
    autocommit=False,  # Vypnutí automatického commitu
)

# Základní třída pro všechny ORM modely v aplikaci
Base = declarative_base()

import source.modules.models  

# Dependency injection funkce pro FastAPI, poskytuje DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session  # Předá session endpointu a po dokončení se automaticky uzavře