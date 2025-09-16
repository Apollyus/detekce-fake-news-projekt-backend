# Use official Playwright image as base - updated to latest version
FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

# Set timezone and make installation non-interactive
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Prague

# Install GPG and fix the key issue, then install Python 3.13
RUN apt-get update && apt-get install -y \
    gnupg \
    software-properties-common \
    curl \
    tzdata \
    && curl -fsSL https://keyserver.ubuntu.com/pks/lookup?op=get\&search=0xF23C5A6CF475977595C89F51BA6932366A755776 | gpg --dearmor > /etc/apt/trusted.gpg.d/deadsnakes.gpg \
    && echo "deb https://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu jammy main" > /etc/apt/sources.list.d/deadsnakes-ppa.list \
    && apt-get update \
    && apt-get install -y \
    python3.13 \
    python3.13-dev \
    python3.13-venv \
    build-essential \
    gcc \
    g++ \
    cmake \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install pip for Python 3.13
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.13

# Set Python 3.13 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.13 1
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.13 1

# Create non-root user for Playwright
RUN groupadd -r appuser && useradd -r -g appuser -G audio,video appuser \
    && mkdir -p /home/appuser/Downloads \
    && mkdir -p /app \
    && chown -R appuser:appuser /home/appuser \
    && chown -R appuser:appuser /app

WORKDIR /app

# Copy requirements first to leverage Docker caching
COPY requirements.txt .

# Install Python dependencies using Python 3.13
RUN python3.13 -m pip install --no-cache-dir --upgrade pip && \
    python3.13 -m pip install --no-cache-dir bcrypt==3.2.2 && \
    python3.13 -m pip install --no-cache-dir -r requirements.txt

# Copy the application code and set proper ownership
COPY . .
RUN chown -R appuser:appuser /app

# Set environment variables for Playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# Switch to non-root user
USER appuser

EXPOSE 8000
ENV ENVIRONMENT="production"

CMD python3.13 init_db.py && python3.13 main.py