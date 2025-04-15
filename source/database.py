from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite databáze v aktuálním adresáři
SQLALCHEMY_DATABASE_URL = "sqlite:///./users.db"

# Připojení k databázi
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Session pro komunikaci s DB
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Základní třída pro modely
Base = declarative_base()
