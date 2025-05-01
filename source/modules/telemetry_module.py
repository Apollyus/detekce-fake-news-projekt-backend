import time
import json
import os
import logging
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='telemetry.log'
)

logger = logging.getLogger('fake_news_telemetry')

# Define database path
DB_PATH = Path("data/telemetry/telemetry.db")

# Ensure telemetry directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Database connection lock to prevent concurrent operations
db_lock = threading.Lock()

def get_db_connection():
    """Get a connection to the SQLite database"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize the database schema if it doesn't exist"""
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create metrics table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY,
            total_requests INTEGER DEFAULT 0,
            successful_requests INTEGER DEFAULT 0,
            failed_requests INTEGER DEFAULT 0,
            average_processing_time REAL DEFAULT 0.0
        )
        ''')
        
        # Create hourly metrics table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS hourly_metrics (
            id INTEGER PRIMARY KEY,
            hour TEXT UNIQUE,
            request_count INTEGER DEFAULT 0
        )
        ''')
        
        # Create error counts table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS error_metrics (
            id INTEGER PRIMARY KEY,
            error_message TEXT UNIQUE,
            count INTEGER DEFAULT 0
        )
        ''')
        
        # Create request logs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS request_logs (
            request_id TEXT PRIMARY KEY,
            timestamp TEXT,
            prompt TEXT,
            prompt_length INTEGER,
            success INTEGER,
            duration REAL,
            steps TEXT,
            processing_data TEXT,
            result_type TEXT,
            error_message TEXT
        )
        ''')
        
        # Initialize metrics record if it doesn't exist
        cursor.execute('SELECT COUNT(*) FROM metrics')
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO metrics DEFAULT VALUES')
        
        conn.commit()
        conn.close()

# Initialize database on module import
init_database()

def get_metrics():
    """Get current telemetry metrics from database"""
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get main metrics
        cursor.execute('SELECT * FROM metrics WHERE id = 1')
        metrics = dict(cursor.fetchone())
        
        # Get hourly metrics
        cursor.execute('SELECT hour, request_count FROM hourly_metrics')
        metrics["requests_by_hour"] = {row["hour"]: row["request_count"] for row in cursor.fetchall()}
        
        # Get error counts
        cursor.execute('SELECT error_message, count FROM error_metrics')
        metrics["error_counts"] = {row["error_message"]: row["count"] for row in cursor.fetchall()}
        
        # Get recent requests (last 100)
        cursor.execute('''
        SELECT * FROM request_logs 
        ORDER BY timestamp DESC 
        LIMIT 100
        ''')
        metrics["recent_requests"] = []
        for row in cursor.fetchall():
            request = dict(row)
            # Deserialize JSON fields
            request["steps"] = json.loads(request["steps"])
            request["processing_data"] = json.loads(request["processing_data"])
            metrics["recent_requests"].append(request)
        
        conn.close()
        return metrics

def update_db_metrics(update_function):
    """Update metrics in a thread-safe way using a provided function"""
    with db_lock:
        conn = get_db_connection()
        update_function(conn)
        conn.commit()
        conn.close()

def log_request_start(prompt: str) -> Dict[str, Any]:
    """Log the start of a request and return request metadata"""
    request_id = f"{int(time.time())}-{hash(prompt) % 10000}"
    start_time = time.time()

    # Log to telemetry.log file with truncated prompt (first 100 chars)
    truncated_prompt = prompt[:100] + "..." if len(prompt) > 100 else prompt
    logger.info(f"Request {request_id} started: prompt_length={len(prompt)}, prompt=\"{truncated_prompt}\"")
    
    # Update metrics
    def update_start_metrics(conn):
        cursor = conn.cursor()
        
        # Increment total requests
        cursor.execute('UPDATE metrics SET total_requests = total_requests + 1 WHERE id = 1')
        
        # Update hourly metrics
        hour = datetime.now().strftime("%Y-%m-%d-%H")
        cursor.execute('''
        INSERT INTO hourly_metrics (hour, request_count) 
        VALUES (?, 1)
        ON CONFLICT(hour) DO UPDATE SET request_count = request_count + 1
        ''', (hour,))
    
    update_db_metrics(update_start_metrics)
    
    # Create request context with timing and metadata
    return {
        "request_id": request_id,
        "start_time": start_time,
        "prompt": prompt,
        "prompt_length": len(prompt),
        "steps": {},
        "processing_data": {}
    }

def log_step_time(request_context: Dict[str, Any], step_name: str) -> None:
    """Log the time taken for a specific step"""
    current_time = time.time()
    duration = current_time - request_context.get("step_start_time", request_context["start_time"])
    
    # Log to telemetry.log file
    logger.debug(f"Step {step_name} completed for request {request_context['request_id']}: duration={duration:.3f}s")
    
    request_context["steps"][step_name] = {
        "end_time": current_time,
        "duration": current_time - request_context.get("step_start_time", request_context["start_time"])
    }
    request_context["step_start_time"] = current_time

def log_processing_data(request_context: Dict[str, Any], data_type: str, data: Any) -> None:
    """Log processing data like keywords, search phrases, etc."""
    request_context["processing_data"][data_type] = data

def log_request_end(request_context: Dict[str, Any], success: bool, result: Dict[str, Any]) -> None:
    """Log the end of a request with results"""
    end_time = time.time()
    total_duration = end_time - request_context["start_time"]
    
    # Create complete request record
    request_record = {
        "request_id": request_context["request_id"],
        "timestamp": datetime.now().isoformat(),
        "prompt": request_context["prompt"],
        "prompt_length": request_context["prompt_length"],
        "success": 1 if success else 0,
        "duration": total_duration,
        "steps": json.dumps(request_context["steps"]),
        "processing_data": json.dumps(request_context["processing_data"]),
        "result_type": result.get("status"),
        "error_message": None if success else result.get("message")
    }
    
    # Update metrics with this request
    def update_end_metrics(conn):
        cursor = conn.cursor()
        
        # Update success/failure counts
        if success:
            cursor.execute('UPDATE metrics SET successful_requests = successful_requests + 1 WHERE id = 1')
        else:
            cursor.execute('UPDATE metrics SET failed_requests = failed_requests + 1 WHERE id = 1')
            
            # Track error type
            error_message = result.get("message", "Unknown error")
            cursor.execute('''
            INSERT INTO error_metrics (error_message, count) 
            VALUES (?, 1)
            ON CONFLICT(error_message) DO UPDATE SET count = count + 1
            ''', (error_message,))
        
        # Update average processing time
        cursor.execute('''
        UPDATE metrics 
        SET average_processing_time = 
            (average_processing_time * (total_requests - 1) + ?) / total_requests 
        WHERE id = 1
        ''', (total_duration,))
        
        # Insert request log
        cursor.execute('''
        INSERT INTO request_logs 
        (request_id, timestamp, prompt, prompt_length, success, duration, 
         steps, processing_data, result_type, error_message) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request_record["request_id"],
            request_record["timestamp"],
            request_record["prompt"],
            request_record["prompt_length"],
            request_record["success"],
            request_record["duration"],
            request_record["steps"],
            request_record["processing_data"],
            request_record["result_type"],
            request_record["error_message"]
        ))
        
        # Maintain retention policy - keep only last 100 records
        #cursor.execute('''
        #DELETE FROM request_logs 
        #WHERE request_id NOT IN (
        #    SELECT request_id FROM request_logs 
        #    ORDER BY timestamp DESC 
        #    LIMIT 100
        #)
        #''')
    
    update_db_metrics(update_end_metrics)
    
    # Log the full request information with verdict and confidence if available
    log_message = f"Request {request_context['request_id']} completed: success={success}, duration={total_duration:.2f}s"
    
    # Extract verdict information from different possible locations in the result
    verdict = "UNKNOWN"
    confidence = 0.0
    
    if success:
        # Try to extract verdict directly from result
        if isinstance(result.get("result"), dict) and "verdict" in result["result"]:
            # Case 1: verdict is in result["result"]["verdict"]
            verdict = result["result"]["verdict"]
            confidence = result["result"].get("confidence", 0.0)
        elif isinstance(result.get("result"), str):
            # Case 2: result["result"] is directly the verdict string
            verdict = result["result"]
        elif "data" in result and isinstance(result["data"], dict):
            if "evaluation_result" in result["data"]:
                # Case 3: older format with data.evaluation_result
                eval_result = result["data"]["evaluation_result"]
                verdict = eval_result.get("verdict", verdict)
                confidence = eval_result.get("confidence", confidence)
    
    log_message += f", verdict={verdict}, confidence={confidence:.2f}"
    
    logger.info(log_message)
    
def log_error(request_context: Dict[str, Any], error: Exception, step: Optional[str] = None) -> None:
    """Log an error that occurred during processing"""
    logger.error(f"Error in request {request_context['request_id']} at step {step}: {str(error)}")
    
    # Track error type
    def update_error_metrics(conn):
        cursor = conn.cursor()
        error_type = type(error).__name__
        cursor.execute('''
        INSERT INTO error_metrics (error_message, count) 
        VALUES (?, 1)
        ON CONFLICT(error_message) DO UPDATE SET count = count + 1
        ''', (error_type,))
    
    update_db_metrics(update_error_metrics)

def log_external_api_failure(request_context: Dict[str, Any], service_name: str, 
                           error: Exception, response_code: Optional[int] = None) -> None:
    """Log failures when calling external APIs
    
    Args:
        request_context: The current request context
        service_name: Name of the external service (e.g., 'google', 'mistral')
        error: The exception that occurred
        response_code: Optional HTTP status code if available
    """
    error_details = {
        "service": service_name,
        "error_type": type(error).__name__,
        "message": str(error),
        "response_code": response_code
    }
    
    # Log processing data to the request context (will be saved to DB later)
    log_processing_data(request_context, f"{service_name}_api_error", error_details)
    
    # Log basic info to telemetry.log file
    logger.error(f"External API failure in request {request_context['request_id']}: "
                f"{service_name} - {type(error).__name__} - {str(error)}")

    # Update error metrics in database
    def update_api_error_metrics(conn):
        cursor = conn.cursor()
        error_key = f"{service_name}_api_error: {type(error).__name__}"
        cursor.execute('''
        INSERT INTO error_metrics (error_message, count) 
        VALUES (?, 1)
        ON CONFLICT(error_message) DO UPDATE SET count = count + 1
        ''', (error_key,))
    
    update_db_metrics(update_api_error_metrics)