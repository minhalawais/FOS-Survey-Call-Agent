FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install --no-cache-dir \
    fastapi==0.109.0 \
    uvicorn[standard]==0.27.0 \
    piper-tts==1.2.0 \
    numpy==1.26.3 \
    soundfile==0.12.1

# Copy application
COPY piper_server.py .

# Create voices directory
RUN mkdir -p /app/voices

EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "piper_server:app", "--host", "0.0.0.0", "--port", "8000"]
