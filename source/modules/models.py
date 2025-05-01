from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship # Import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    #created_at = Column(DateTime, default=datetime.utcnow) # Added timestamp
    #updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) # Added timestamp

    # Relationship to the RegistrationKey used by this user
    registration_key_used = relationship("RegistrationKey", back_populates="used_by_user", uselist=False)

class RegistrationKey(Base):
    __tablename__ = "registration_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    used = Column(Boolean, default=False)
    # Changed to ForeignKey linking to User.id
    used_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to the User who used this key
    used_by_user = relationship("User", back_populates="registration_key_used")

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

class Metrics(Base):
    __tablename__ = "metrics" # Matches old table name
    id = Column(Integer, primary_key=True)
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    average_processing_time = Column(Float, default=0.0)
    # Add other fields if needed

class HourlyMetrics(Base):
    __tablename__ = "hourly_metrics" # Matches old table name
    hour = Column(String, primary_key=True) # e.g., "2025-05-01-14"
    request_count = Column(Integer, default=0)

class ErrorMetrics(Base):
    __tablename__ = "error_metrics" # Matches old table name
    error_message = Column(String, primary_key=True)
    count = Column(Integer, default=0)