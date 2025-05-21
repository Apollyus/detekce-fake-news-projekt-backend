from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship # Import pro definici vztahů mezi modely
from datetime import datetime
from .database import Base

class User(Base):
    """Model pro uživatele systému"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True) # Primární klíč
    email = Column(String, unique=True, index=True, nullable=False) # Email uživatele (unikátní)
    hashed_password = Column(String, nullable=False) # Hashované heslo
    role = Column(String, default="user", nullable=False)  # Přidáno: Role uživatele (user, admin)
    #created_at = Column(DateTime, default=datetime.utcnow) # Časové razítko vytvoření
    #updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) # Časové razítko aktualizace

    # Vztah k registračnímu klíči použitému uživatelem
    registration_key_used = relationship("RegistrationKey", back_populates="used_by_user", uselist=False)
    activity = relationship("UserActivity", back_populates="user", uselist=False)

class RegistrationKey(Base):
    """Model pro registrační klíče"""
    __tablename__ = "registration_keys"

    id = Column(Integer, primary_key=True, index=True) # Primární klíč
    key = Column(String, unique=True, index=True, nullable=False) # Hodnota registračního klíče
    used = Column(Boolean, default=False) # Příznak použití klíče
    # Cizí klíč odkazující na uživatele, který klíč použil
    used_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True) 
    created_at = Column(DateTime, default=datetime.utcnow) # Datum vytvoření klíče

    # Vztah k uživateli, který tento klíč použil
    used_by_user = relationship("User", back_populates="registration_key_used")

class FormSubmission(Base):
    """Model pro uložení kontaktních formulářů"""
    __tablename__ = "form_submissions"

    id = Column(Integer, primary_key=True, index=True) # Primární klíč
    full_name = Column(String, nullable=False) # Celé jméno odesílatele
    email = Column(String, nullable=False) # Email odesílatele
    subject = Column(String, nullable=False) # Předmět zprávy
    message = Column(String, nullable=False) # Obsah zprávy
    created_at = Column(DateTime, default=datetime.utcnow) # Datum vytvoření záznamu

class TelemetryRecord(Base):
    """Model pro záznam telemetrie systému"""
    __tablename__ = "telemetry_records"

    id = Column(Integer, primary_key=True, index=True) # Primární klíč
    request_id = Column(String, unique=True, index=True) # Unikátní ID požadavku
    timestamp = Column(DateTime, default=datetime.utcnow) # Časové razítko
    prompt = Column(String, nullable=False) # Vstupní text/dotaz
    prompt_length = Column(Integer) # Délka vstupního textu
    success = Column(Boolean, default=False) # Úspěšnost zpracování
    duration = Column(Float) # Doba zpracování
    result_type = Column(String) # Typ výsledku
    error_message = Column(String, nullable=True) # Chybová zpráva (pokud nastala)
    steps_data = Column(String)  # JSON řetězec s daty o jednotlivých krocích
    processing_data = Column(String)  # JSON řetězec s daty o zpracování
    
    # Vztah k hodnocení od uživatele
    user_feedback = relationship("UserFeedback", back_populates="telemetry_record", uselist=False)

class UserFeedback(Base):
    """Model pro hodnocení výsledků od uživatelů"""
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, index=True)
    telemetry_record_id = Column(String, ForeignKey("telemetry_records.request_id"), nullable=False)  # Opraveno na request_id
    rating = Column(Integer, nullable=False)  # Hodnocení 1-5
    comment = Column(String, nullable=True)  # Volitelný komentář
    is_correct = Column(Boolean, nullable=False)  # Zda byla analýza správná
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Vztah k záznamu telemetrie
    telemetry_record = relationship("TelemetryRecord", back_populates="user_feedback")

class Metrics(Base):
    """Model pro agregované metriky systému"""
    __tablename__ = "metrics" # Název tabulky odpovídá původnímu
    id = Column(Integer, primary_key=True) # Primární klíč
    total_requests = Column(Integer, default=0) # Celkový počet požadavků
    successful_requests = Column(Integer, default=0) # Počet úspěšných požadavků
    failed_requests = Column(Integer, default=0) # Počet neúspěšných požadavků
    average_processing_time = Column(Float, default=0.0) # Průměrná doba zpracování
    # Další pole mohou být přidána podle potřeby

class HourlyMetrics(Base):
    """Model pro hodinové metriky systému"""
    __tablename__ = "hourly_metrics" # Název tabulky odpovídá původnímu
    hour = Column(String, primary_key=True) # Hodina jako primární klíč (např. "2025-05-01-14")
    request_count = Column(Integer, default=0) # Počet požadavků v dané hodině

class ErrorMetrics(Base):
    """Model pro metriky chyb"""
    __tablename__ = "error_metrics" # Název tabulky odpovídá původnímu
    error_message = Column(String, primary_key=True) # Chybová zpráva jako primární klíč
    count = Column(Integer, default=0) # Počet výskytů této chyby

class RateLimitStats(Base):
    __tablename__ = "rate_limit_stats"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=func.now(), index=True)
    ip_address = Column(String(50), index=True)
    path = Column(String(255))
    limit_type = Column(String(20))  # "per_ip" nebo "global"
    error_message = Column(Text, nullable=True)
    
    # Denní agregace pro reporting
    day = Column(DateTime, index=True)  # jen datum bez času pro snadnou agregaci

class UserActivity(Base):
    __tablename__ = "user_activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    last_activity = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="activity")