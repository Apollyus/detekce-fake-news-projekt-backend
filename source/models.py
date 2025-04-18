from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

class RegistrationKey(Base):
    __tablename__ = "registration_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    used = Column(Boolean, default=False)
    used_by = Column(String, nullable=True)  # This column isn't in the database
    created_at = Column(DateTime, default=datetime.utcnow)