# Telemetrický modul pro sledování a protokolování metrik systému detekce fake news
# Modul odpovídá za sledování požadavků, chyb a výkonnostních metrik
import time
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import random
import uuid

# Import komponentů SQLAlchemy pro asynchronní operace
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from .database import AsyncSessionLocal
from . import models

# Konfigurace logování
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='telemetry.log'
)
logger = logging.getLogger('fake_news_telemetry')

# Definice cesty k databázi (pro logování/kontext)
DB_PATH = Path("source")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

async def get_metrics():
    """Získání aktuálních telemetrických metrik z databáze
    
    Shromažďuje statistiky požadavků, úspěšnosti, doby zpracování a chyb.
    Vrací strukturovaný slovník s metrikami a nedávnými požadavky.
    """
    metrics = {
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "average_processing_time": 0.0,
        "requests_by_hour": {},
        "error_counts": {},
        "recent_requests": []
    }

    try:
        async with AsyncSessionLocal() as db:
            # --- Agregované metriky ---
            # Dotaz na model Metrics
            result = await db.execute(select(models.Metrics).filter(models.Metrics.id == 1))
            metrics_record = result.scalar_one_or_none()
            
            if metrics_record:
                metrics["total_requests"] = metrics_record.total_requests
                metrics["successful_requests"] = metrics_record.successful_requests
                metrics["failed_requests"] = metrics_record.failed_requests
                metrics["average_processing_time"] = metrics_record.average_processing_time

            # Dotaz na model HourlyMetrics - statistika po hodinách
            result = await db.execute(select(models.HourlyMetrics))
            hourly_records = result.scalars().all()
            metrics["requests_by_hour"] = {rec.hour: rec.request_count for rec in hourly_records}

            # Dotaz na model ErrorMetrics - statistika chyb
            result = await db.execute(select(models.ErrorMetrics))
            error_records = result.scalars().all()
            metrics["error_counts"] = {rec.error_message: rec.count for rec in error_records}
            # --- Konec agregovaných metrik ---

            # Získání posledních 100 požadavků pomocí modelu TelemetryRecord
            result = await db.execute(
                select(models.TelemetryRecord)
                .order_by(models.TelemetryRecord.timestamp.desc())
                .limit(100)
            )
            recent_requests_db = result.scalars().all()

            for rec in recent_requests_db:
                request_data = {
                    "id": rec.id,
                    "request_id": rec.request_id,
                    "timestamp": rec.timestamp.isoformat() if rec.timestamp else None,
                    "prompt": rec.prompt,
                    "prompt_length": rec.prompt_length,
                    "success": rec.success,
                    "duration": rec.duration,
                    "result_type": rec.result_type,
                    "error_message": rec.error_message,
                    # Bezpečná deserializace JSON polí
                    "steps": json.loads(rec.steps_data) if rec.steps_data else {},
                    "processing_data": json.loads(rec.processing_data) if rec.processing_data else {}
                }
                metrics["recent_requests"].append(request_data)

    except Exception as e:
        logger.error(f"Failed to get metrics from database: {e}")
        metrics["error"] = f"Failed to retrieve metrics: {e}"

    return metrics


async def log_request_start(prompt: str) -> Dict[str, Any]:
    """Zaprotokoluje začátek požadavku a vrátí metadata požadavku
    
    Vytváří jedinečné ID požadavku, zaznamená čas začátku a 
    aktualizuje celkové statistiky požadavků v databázi.
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()

    truncated_prompt = prompt[:100] + "..." if len(prompt) > 100 else prompt
    logger.info(f"Request {request_id} started: prompt_length={len(prompt)}, prompt=\"{truncated_prompt}\"")

    # --- Aktualizace agregovaných metrik ---
    try:
        async with AsyncSessionLocal() as db:
            # Zajištění existence hlavního záznamu metrik
            result = await db.execute(select(models.Metrics).filter(models.Metrics.id == 1))
            metrics_record = result.scalar_one_or_none()
            
            if not metrics_record:
                metrics_record = models.Metrics(id=1)
                db.add(metrics_record)
                await db.flush()

            # Přičtení k celkovému počtu požadavků
            metrics_record.total_requests += 1

            # Aktualizace hodinových metrik
            hour_str = datetime.now().strftime("%Y-%m-%d-%H")
            result = await db.execute(select(models.HourlyMetrics).filter(models.HourlyMetrics.hour == hour_str))
            hourly_record = result.scalar_one_or_none()
            
            if hourly_record:
                hourly_record.request_count += 1
            else:
                db.add(models.HourlyMetrics(hour=hour_str, request_count=1))

            await db.commit()
    except Exception as e:
        logger.error(f"Failed to update start metrics in database: {e}")
        await db.rollback()
    # --- Konec aktualizace agregovaných metrik ---

    return {
        "request_id": request_id,
        "start_time": start_time,
        "prompt": prompt,
        "prompt_length": len(prompt),
        "steps": {},
        "processing_data": {}
    }

def log_step_time(request_context: Dict[str, Any], step_name: str) -> None:
    """Zaprotokoluje čas strávený na konkrétním kroku zpracování
    
    Měří dobu trvání jednotlivých kroků v procesu zpracování požadavku
    a ukládá tyto informace do kontextu požadavku.
    """
    current_time = time.time()
    duration = current_time - request_context.get("step_start_time", request_context["start_time"])
    logger.debug(f"Step {step_name} completed for request {request_context['request_id']}: duration={duration:.3f}s")
    request_context["steps"][step_name] = {
        "end_time": current_time,
        "duration": duration
    }
    request_context["step_start_time"] = current_time

def log_processing_data(request_context: Dict[str, Any], data_type: str, data: Any) -> None:
    """Zaznamenává data zpracování jako klíčová slova, hledané fráze atd.
    
    Ukládá mezivýsledky a data z procesu zpracování požadavku
    do kontextu požadavku pro analýzu a ladění.
    """
    request_context["processing_data"][data_type] = data

async def log_request_end(request_context: Dict[str, Any], success: bool, result_data: Dict[str, Any]) -> int:
    """Zaprotokoluje ukončení požadavku s výsledky
    
    Vypočítá celkovou dobu trvání požadavku, aktualizuje statistiky úspěšnosti/selhání
    a ukládá záznam do databáze včetně průběžných dat.
    
    Returns:
        int: ID vytvořeného záznamu telemetrie
    """
    end_time = time.time()
    total_duration = end_time - request_context["start_time"]

    # Příprava dat pro model TelemetryRecord
    request_record_data = {
        "request_id": request_context["request_id"],
        "timestamp": datetime.now(),
        "prompt": request_context["prompt"],
        "prompt_length": request_context["prompt_length"],
        "success": success,
        "duration": total_duration,
        "steps_data": json.dumps(request_context["steps"]),
        "processing_data": json.dumps(request_context["processing_data"]),
        "result_type": result_data.get("status"),
        "error_message": None if success else result_data.get("message")
    }

    try:
        async with AsyncSessionLocal() as db:
            # Vložení záznamu TelemetryRecord
            db_record = models.TelemetryRecord(**request_record_data)
            db.add(db_record)
            await db.flush()  # Získáme ID před commit
            record_id = db_record.id

            # --- Aktualizace agregovaných metrik ---
            db_result = await db.execute(select(models.Metrics).filter(models.Metrics.id == 1))
            metrics_record = db_result.scalar_one_or_none()
            
            if not metrics_record:
                metrics_record = models.Metrics(id=1)
                db.add(metrics_record)
                await db.flush()

            # Aktualizace počtu úspěšných/neúspěšných požadavků
            if success:
                metrics_record.successful_requests += 1
            else:
                metrics_record.failed_requests += 1

            # Aktualizace průměrné doby zpracování (jednoduchý klouzavý průměr)
            total_req = metrics_record.total_requests
            if total_req > 0:
                if metrics_record.average_processing_time == 0.0 and total_req == 1:
                    metrics_record.average_processing_time = total_duration
                else:
                    # Vážený průměr: (starý_průměr * (n-1) + nová_hodnota) / n
                    metrics_record.average_processing_time = ((metrics_record.average_processing_time * (total_req - 1)) + total_duration) / total_req

            if not success:
                # Sledování typů chyb v tabulce ErrorMetrics
                error_message = result_data.get("message", "Unknown error")
                # Omezení délky chybové zprávy v případě potřeby
                error_message = error_message[:255] if error_message else "Unknown error"

                db_result = await db.execute(select(models.ErrorMetrics).filter(models.ErrorMetrics.error_message == error_message))
                error_record = db_result.scalar_one_or_none()
                
                if error_record:
                    error_record.count += 1
                else:
                    db.add(models.ErrorMetrics(error_message=error_message, count=1))
            # --- Konec aktualizace agregovaných metrik ---

            await db.commit()
            return record_id

    except Exception as e:
        logger.error(f"Failed to log request end to database: {e}")
        await db.rollback()
        raise e

    # Protokolování do souboru
    log_message = f"Request {request_context['request_id']} completed: success={success}, duration={total_duration:.2f}s"
    verdict = "UNKNOWN"
    confidence = 0.0
    if success:
        if isinstance(result_data.get("result"), dict) and "verdict" in result_data["result"]:
            verdict = result_data["result"]["verdict"]
            confidence = result_data["result"].get("confidence", 0.0)
        elif isinstance(result_data.get("result"), str):
            verdict = result_data["result"]
        elif "data" in result_data and isinstance(result_data["data"], dict):
            if "evaluation_result" in result_data["data"]:
                eval_result = result_data["data"]["evaluation_result"]
                verdict = eval_result.get("verdict", verdict)
                confidence = eval_result.get("confidence", confidence)
    log_message += f", verdict={verdict}, confidence={confidence:.2f}"
    logger.info(log_message)


async def log_error(request_context: Dict[str, Any], error: Exception, step: Optional[str] = None) -> None:
    """Zaprotokoluje chybu, která nastala během zpracování
    
    Zaznamená typ chyby, krok, ve kterém nastala, a aktualizuje
    statistiky chyb v databázi.
    """
    error_type = type(error).__name__
    error_str = str(error)[:255]  # Omezení délky
    logger.error(f"Error in request {request_context['request_id']} at step {step}: {error_type} - {error_str}")

    # --- Aktualizace agregovaných metrik ---
    try:
        async with AsyncSessionLocal() as db:
            # Sledování typu chyby v tabulce ErrorMetrics
            error_key = f"ProcessingError: {error_type}"
            
            result = await db.execute(select(models.ErrorMetrics).filter(models.ErrorMetrics.error_message == error_key))
            error_record = result.scalar_one_or_none()
            
            if error_record:
                error_record.count += 1
            else:
                db.add(models.ErrorMetrics(error_message=error_key, count=1))
                
            await db.commit()
            
    except Exception as e:
        logger.error(f"Failed to update error metrics in database: {e}")
        await db.rollback()
    # --- Konec aktualizace agregovaných metrik ---


async def log_external_api_failure(request_context: Dict[str, Any], service_name: str,
                          error: Exception, response_code: Optional[int] = None) -> None:
    """Zaprotokoluje selhání při volání externích API
    
    Zaznamená typ chyby, službu, která selhala, a aktualizuje
    statistiky selhání externích API v databázi.
    """
    error_type = type(error).__name__
    error_str = str(error)[:255]  # Omezení délky
    error_details = {
        "service": service_name,
        "error_type": error_type,
        "message": error_str,
        "response_code": response_code
    }
    log_processing_data(request_context, f"{service_name}_api_error", error_details)
    logger.error(f"External API failure in request {request_context['request_id']}: "
                f"{service_name} - {error_type} - {error_str}")

    # --- Aktualizace agregovaných metrik ---
    try:
        async with AsyncSessionLocal() as db:
            # Sledování typu API chyby v tabulce ErrorMetrics
            error_key = f"{service_name}_api_error: {error_type}"
            
            result = await db.execute(select(models.ErrorMetrics).filter(models.ErrorMetrics.error_message == error_key))
            error_record = result.scalar_one_or_none()
            
            if error_record:
                error_record.count += 1
            else:
                db.add(models.ErrorMetrics(error_message=error_key, count=1))
                
            await db.commit()
            
    except Exception as e:
        logger.error(f"Failed to update API error metrics in database: {e}")
        await db.rollback()
    # --- Konec aktualizace agregovaných metrik ---