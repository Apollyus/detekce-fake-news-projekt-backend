FROM python:3.13-slim

WORKDIR /app

# Install system dependencies for Playwright and for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    cmake \
    pkg-config \
    python3-dev \
    # Added dependencies for Playwright browsers
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir bcrypt==3.2.2 && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers and their dependencies
RUN playwright install --with-deps

# Copy the application code
COPY . .

# Expose the port that FastAPI will run on
EXPOSE 8000

ENV ENVIRONMENT="production"

# Command to run the application
#CMD ["uvicorn", "source.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
CMD python init_db.py && python main.py