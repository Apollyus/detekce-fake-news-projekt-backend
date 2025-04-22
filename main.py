import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "source.app:app",
        host="0.0.0.0",
        port=8000,
        workers=4,  # Number of worker processes
        reload=False,  # Disable auto-reload in production
        log_level="info",
        proxy_headers=True,  # Important when running behind a proxy
        forwarded_allow_ips='*'  # Configure based on your production setup
    )