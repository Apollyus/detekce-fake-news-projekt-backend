FROM python:3.13-slim

WORKDIR /app

# Install system dependencies for building Python packages with C extensions
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    cmake \
    pkg-config \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir bcrypt==3.2.2 && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port that FastAPI will run on
EXPOSE 8000

ENV ENVIRONMENT=prod

# Command to run the application
#CMD ["uvicorn", "source.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
CMD ["python", "main.py"]