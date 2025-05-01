import uvicorn
from source.modules.config import config

if __name__ == "__main__":
    
    # Get environment setting
    env = config.ENVIRONMENT
    print(f"Running in {env} environment")
    
    # Set host based on environment
    host = "127.0.0.1" if env == "development" else "0.0.0.0"
    
    uvicorn.run(
        "source.app:app",
        host=host,
        port=8000,
        workers=4,
        reload=(env == "development"),  # Enable reload only in local environment
        log_level="info",
        proxy_headers=True,
        forwarded_allow_ips='*'
    )