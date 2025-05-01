import time
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
# Removed threading and sqlite3

# Import SQLAlchemy components
from sqlalchemy import func # Import func for calculations like average
from .database import SessionLocal # Assuming SessionLocal is defined in database.py
from . import models # Import your models module

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='telemetry.log'
)
logger = logging.getLogger('fake_news_telemetry')

# Define database path (still useful for logging/context, but not direct connection)
DB_PATH = Path("data/telemetry/telemetry.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Removed db_lock, get_db_connection, update_db_metrics

def get_metrics():
    """Get current telemetry metrics using SQLAlchemy"""
    metrics = {
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "average_processing_time": 0.0,
        "requests_by_hour": {},
        "error_counts": {},
        "recent_requests": []
    } # Default structure

    try:
        with SessionLocal() as db:
            # --- Aggregate Metrics ---
            # Query Metrics model
            metrics_record = db.query(models.Metrics).filter(models.Metrics.id == 1).first()
            if metrics_record:
                metrics["total_requests"] = metrics_record.total_requests
                metrics["successful_requests"] = metrics_record.successful_requests
                metrics["failed_requests"] = metrics_record.failed_requests
                metrics["average_processing_time"] = metrics_record.average_processing_time

            # Query HourlyMetrics model
            hourly_records = db.query(models.HourlyMetrics).all()
            metrics["requests_by_hour"] = {rec.hour: rec.request_count for rec in hourly_records}

            # Query ErrorMetrics model
            error_records = db.query(models.ErrorMetrics).all()
            metrics["error_counts"] = {rec.error_message: rec.count for rec in error_records}
            # --- End Aggregate Metrics ---

            # Get recent requests (last 100) using TelemetryRecord model
            recent_requests_db = db.query(models.TelemetryRecord)\
                                   .order_by(models.TelemetryRecord.timestamp.desc())\
                                   .limit(100)\
                                   .all()

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
                    # Deserialize JSON fields safely
                    "steps": json.loads(rec.steps_data) if rec.steps_data else {},
                    "processing_data": json.loads(rec.processing_data) if rec.processing_data else {}
                }
                metrics["recent_requests"].append(request_data)

    except Exception as e:
        logger.error(f"Failed to get metrics from database: {e}")
        metrics["error"] = f"Failed to retrieve metrics: {e}" # Add error info

    return metrics


def log_request_start(prompt: str) -> Dict[str, Any]:
    """Log the start of a request and return request metadata"""
    request_id = f"{int(time.time())}-{hash(prompt) % 10000}"
    start_time = time.time()

    truncated_prompt = prompt[:100] + "..." if len(prompt) > 100 else prompt
    logger.info(f"Request {request_id} started: prompt_length={len(prompt)}, prompt=\"{truncated_prompt}\"")

    # --- Aggregate Metrics Update ---
    try:
        with SessionLocal() as db:
            # Ensure the main metrics record exists
            metrics_record = db.query(models.Metrics).filter(models.Metrics.id == 1).first()
            if not metrics_record:
                metrics_record = models.Metrics(id=1)
                db.add(metrics_record)
                # Need to flush to get the object ready for update in the same session if needed
                db.flush()

            # Increment total requests
            metrics_record.total_requests += 1

            # Update hourly metrics
            hour_str = datetime.now().strftime("%Y-%m-%d-%H")
            hourly_record = db.query(models.HourlyMetrics).filter(models.HourlyMetrics.hour == hour_str).first()
            if hourly_record:
                hourly_record.request_count += 1
            else:
                db.add(models.HourlyMetrics(hour=hour_str, request_count=1))

            db.commit()
    except Exception as e:
        logger.error(f"Failed to update start metrics in database: {e}")
    # --- End Aggregate Metrics Update ---

    return {
        "request_id": request_id,
        "start_time": start_time,
        "prompt": prompt,
        "prompt_length": len(prompt),
        "steps": {},
        "processing_data": {}
    }

# log_step_time remains the same (no DB interaction)
def log_step_time(request_context: Dict[str, Any], step_name: str) -> None:
    """Log the time taken for a specific step"""
    current_time = time.time()
    duration = current_time - request_context.get("step_start_time", request_context["start_time"])
    logger.debug(f"Step {step_name} completed for request {request_context['request_id']}: duration={duration:.3f}s")
    request_context["steps"][step_name] = {
        "end_time": current_time,
        "duration": duration # Use calculated duration
    }
    request_context["step_start_time"] = current_time

# log_processing_data remains the same (no DB interaction)
def log_processing_data(request_context: Dict[str, Any], data_type: str, data: Any) -> None:
    """Log processing data like keywords, search phrases, etc."""
    request_context["processing_data"][data_type] = data

def log_request_end(request_context: Dict[str, Any], success: bool, result: Dict[str, Any]) -> None:
    """Log the end of a request with results using SQLAlchemy"""
    end_time = time.time()
    total_duration = end_time - request_context["start_time"]

    # Prepare data for TelemetryRecord model
    request_record_data = {
        "request_id": request_context["request_id"],
        "timestamp": datetime.now(), # Use datetime object
        "prompt": request_context["prompt"],
        "prompt_length": request_context["prompt_length"],
        "success": success, # Use boolean directly
        "duration": total_duration,
        "steps_data": json.dumps(request_context["steps"]), # Keep as JSON string
        "processing_data": json.dumps(request_context["processing_data"]), # Keep as JSON string
        "result_type": result.get("status"),
        "error_message": None if success else result.get("message")
    }

    try:
        with SessionLocal() as db:
            # Insert the TelemetryRecord
            db_record = models.TelemetryRecord(**request_record_data)
            db.add(db_record)

            # --- Aggregate Metrics Update ---
            metrics_record = db.query(models.Metrics).filter(models.Metrics.id == 1).first()
            if not metrics_record: # Should exist from log_request_start, but check just in case
                metrics_record = models.Metrics(id=1)
                db.add(metrics_record)
                db.flush() # Ensure it's ready

            # Update success/failure counts
            if success:
                metrics_record.successful_requests += 1
            else:
                metrics_record.failed_requests += 1

            # Update average processing time (simple moving average)
            # Note: total_requests might be slightly off if commit fails, but generally ok
            total_req = metrics_record.total_requests # Get current total
            if total_req > 0:
               # Avoid division by zero and handle first request
               if metrics_record.average_processing_time == 0.0 and total_req == 1:
                   metrics_record.average_processing_time = total_duration
               else:
                   # Weighted average: (old_avg * (n-1) + new_value) / n
                   metrics_record.average_processing_time = ((metrics_record.average_processing_time * (total_req - 1)) + total_duration) / total_req

            if not success:
                # Track error type in ErrorMetrics table
                error_message = result.get("message", "Unknown error")
                # Limit error message length if necessary
                error_message = error_message[:255] if error_message else "Unknown error"

                error_record = db.query(models.ErrorMetrics).filter(models.ErrorMetrics.error_message == error_message).first()
                if error_record:
                    error_record.count += 1
                else:
                    db.add(models.ErrorMetrics(error_message=error_message, count=1))
            # --- End Aggregate Metrics Update ---

            db.commit() # Commit TelemetryRecord and any metric updates

    except Exception as e:
        logger.error(f"Failed to log request end to database: {e}")

    # Log to file (remains the same)
    log_message = f"Request {request_context['request_id']} completed: success={success}, duration={total_duration:.2f}s"
    verdict = "UNKNOWN"
    confidence = 0.0
    if success:
        if isinstance(result.get("result"), dict) and "verdict" in result["result"]:
            verdict = result["result"]["verdict"]
            confidence = result["result"].get("confidence", 0.0)
        elif isinstance(result.get("result"), str):
            verdict = result["result"]
        elif "data" in result and isinstance(result["data"], dict):
            if "evaluation_result" in result["data"]:
                eval_result = result["data"]["evaluation_result"]
                verdict = eval_result.get("verdict", verdict)
                confidence = eval_result.get("confidence", confidence)
    log_message += f", verdict={verdict}, confidence={confidence:.2f}"
    logger.info(log_message)


def log_error(request_context: Dict[str, Any], error: Exception, step: Optional[str] = None) -> None:
    """Log an error that occurred during processing"""
    error_type = type(error).__name__
    error_str = str(error)[:255] # Limit length
    logger.error(f"Error in request {request_context['request_id']} at step {step}: {error_type} - {error_str}")

    # --- Aggregate Metrics Update ---
    try:
        with SessionLocal() as db:
            # Track error type in ErrorMetrics table
            error_key = f"ProcessingError: {error_type}"
            error_record = db.query(models.ErrorMetrics).filter(models.ErrorMetrics.error_message == error_key).first()
            if error_record:
                error_record.count += 1
            else:
                db.add(models.ErrorMetrics(error_message=error_key, count=1))
            db.commit()
    except Exception as e:
        logger.error(f"Failed to update error metrics in database: {e}")
    # --- End Aggregate Metrics Update ---


def log_external_api_failure(request_context: Dict[str, Any], service_name: str,
                           error: Exception, response_code: Optional[int] = None) -> None:
    """Log failures when calling external APIs"""
    error_type = type(error).__name__
    error_str = str(error)[:255] # Limit length
    error_details = {
        "service": service_name,
        "error_type": error_type,
        "message": error_str,
        "response_code": response_code
    }
    log_processing_data(request_context, f"{service_name}_api_error", error_details)
    logger.error(f"External API failure in request {request_context['request_id']}: "
                f"{service_name} - {error_type} - {error_str}")

    # --- Aggregate Metrics Update ---
    try:
        with SessionLocal() as db:
            # Track API error type in ErrorMetrics table
            error_key = f"{service_name}_api_error: {error_type}"
            error_record = db.query(models.ErrorMetrics).filter(models.ErrorMetrics.error_message == error_key).first()
            if error_record:
                error_record.count += 1
            else:
                db.add(models.ErrorMetrics(error_message=error_key, count=1))
            db.commit()
    except Exception as e:
        logger.error(f"Failed to update API error metrics in database: {e}")
    # --- End Aggregate Metrics Update ---
