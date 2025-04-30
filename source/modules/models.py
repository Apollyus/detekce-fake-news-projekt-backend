from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
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

class FormSubmission(Base):
    __tablename__ = "form_submissions"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class TelemetryRecord(Base):
    __tablename__ = "telemetry_records"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    prompt = Column(String, nullable=False)
    prompt_length = Column(Integer)
    success = Column(Boolean, default=False)
    duration = Column(Float)
    result_type = Column(String)
    error_message = Column(String, nullable=True)
    steps_data = Column(String)  # JSON string
    processing_data = Column(String)  # JSON string