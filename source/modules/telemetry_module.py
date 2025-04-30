import time
import json
import os
import logging
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

# Define telemetry data storage path
TELEMETRY_FILE = Path("data/telemetry/telemetry_data.json")

# Ensure telemetry directory exists
TELEMETRY_FILE.parent.mkdir(parents=True, exist_ok=True)

# Initialize default metrics structure
def init_metrics():
    return {
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "average_processing_time": 0,
        "requests_by_hour": {},
        "error_counts": {},
        "recent_requests": []  # Will store the last 100 requests with full details
    }

# File access lock to prevent concurrent writes
file_lock = threading.Lock()

def read_metrics():
    """Read metrics from JSON file"""
    if TELEMETRY_FILE.exists():
        try:
            with file_lock:
                with open(TELEMETRY_FILE, 'r') as file:
                    return json.load(file)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error reading telemetry data: {str(e)}")
            return init_metrics()
    else:
        metrics = init_metrics()
        write_metrics(metrics)
        return metrics

def write_metrics(metrics_data):
    """Write metrics to JSON file"""
    try:
        with file_lock:
            with open(TELEMETRY_FILE, 'w') as file:
                json.dump(metrics_data, file, indent=2)
    except IOError as e:
        logger.error(f"Error writing telemetry data: {str(e)}")

def update_metrics(update_function):
    """Update metrics in a thread-safe way"""
    with file_lock:
        metrics = read_metrics()
        update_function(metrics)
        write_metrics(metrics)

def log_request_start(prompt: str) -> Dict[str, Any]:
    """Log the start of a request and return request metadata"""
    request_id = f"{int(time.time())}-{hash(prompt) % 10000}"
    start_time = time.time()
    
    # Update metrics
    def update_start_metrics(metrics):
        # Get hour for hourly metrics
        hour = datetime.now().strftime("%Y-%m-%d-%H")
        if hour not in metrics["requests_by_hour"]:
            metrics["requests_by_hour"][hour] = 0
        metrics["requests_by_hour"][hour] += 1
        metrics["total_requests"] += 1
    
    update_metrics(update_start_metrics)
    
    # Create request context with timing and metadata
    return {
        "request_id": request_id,
        "start_time": start_time,
        "prompt": prompt,  # Save the original user prompt
        "prompt_length": len(prompt),
        "steps": {},
        "processing_data": {}  # To store keywords, search phrases, etc.
    }

def log_step_time(request_context: Dict[str, Any], step_name: str) -> None:
    """Log the time taken for a specific step"""
    current_time = time.time()
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
        "success": success,
        "duration": total_duration,
        "steps": request_context["steps"],
        "processing_data": request_context["processing_data"],
        "result_type": result.get("status"),
        "error_message": None if success else result.get("message")
    }
    
    # Update metrics with this request
    def update_end_metrics(metrics):
        if success:
            metrics["successful_requests"] += 1
        else:
            metrics["failed_requests"] += 1
            
            # Track error type
            error_message = result.get("message", "Unknown error")
            if error_message not in metrics["error_counts"]:
                metrics["error_counts"][error_message] = 0
            metrics["error_counts"][error_message] += 1
        
        # Update average processing time
        total_requests = metrics["successful_requests"] + metrics["failed_requests"]
        if total_requests > 0:
            metrics["average_processing_time"] = (
                (metrics["average_processing_time"] * (total_requests - 1) + total_duration) / total_requests
            )
        
        # Keep last 100 requests
        metrics["recent_requests"].insert(0, request_record)
        if len(metrics["recent_requests"]) > 100:
            metrics["recent_requests"] = metrics["recent_requests"][:100]
    
    update_metrics(update_end_metrics)
    
    # Log the full request information
    logger.info(json.dumps(request_record))

def log_error(request_context: Dict[str, Any], error: Exception, step: Optional[str] = None) -> None:
    """Log an error that occurred during processing"""
    logger.error(f"Error in request {request_context['request_id']} at step {step}: {str(error)}")
    
    # Track error type
    def update_error_metrics(metrics):
        error_type = type(error).__name__
        if error_type not in metrics["error_counts"]:
            metrics["error_counts"][error_type] = 0
        metrics["error_counts"][error_type] += 1
    
    update_metrics(update_error_metrics)

def get_metrics() -> Dict[str, Any]:
    """Get current telemetry metrics"""
    return read_metrics()