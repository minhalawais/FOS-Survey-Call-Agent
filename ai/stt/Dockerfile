FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

WORKDIR /app

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    libsndfile1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install --no-cache-dir \
    fastapi==0.109.0 \
    uvicorn[standard]==0.27.0 \
    python-multipart==0.0.6 \
    faster-whisper==1.0.1 \
    numpy==1.26.3 \
    soundfile==0.12.1

# Copy application
COPY whisper_server.py .

EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "whisper_server:app", "--host", "0.0.0.0", "--port", "8000"]
