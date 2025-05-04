from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from source.modules.config import config

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

# Vytvoření async engine
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,
)
# Session maker pro AsyncSession
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Deklarace base třídy pro ORM modely
Base = declarative_base()

import source.modules.models  

# Dependency pro získání session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
