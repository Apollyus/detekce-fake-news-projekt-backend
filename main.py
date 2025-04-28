import uvicorn
from dotenv import load_dotenv
import os

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    
    # Get environment setting
    env = os.getenv("ENVIRONMENT", "local")
    
    # Set host based on environment
    host = "127.0.0.1" if env == "local" else "0.0.0.0"
    
    uvicorn.run(
        "source.app:app",
        host=host,
        port=8000,
        workers=4,
        reload=(env == "local"),  # Enable reload only in local environment
        log_level="info",
        proxy_headers=True,
        forwarded_allow_ips='*'
    )