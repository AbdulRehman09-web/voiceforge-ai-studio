# ──────────────────────────────────────────────────────────────────────────────
# Zenvyrolabs Voice Studio - Production Docker Image
# Python 3.11 + CPU PyTorch + F5-TTS + Gradio
# ──────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# System Dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        git \
        curl \
        build-essential \
        dnsutils \
        iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Working Directory
WORKDIR /app

# Environment Variables
ENV PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=180 \
    PIP_RETRIES=10 \
    RUNNING_IN_DOCKER=1 \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=7860

# Upgrade pip
RUN pip install --no-cache-dir --upgrade "pip<25"

# Install Compatible PyTorch Stack
#
# F5-TTS works reliably with Torch 2.5.1.
# Installing Torch and Torchaudio together prevents ABI mismatches.
RUN pip install --no-cache-dir \
    torch==2.5.1 \
    torchaudio==2.5.1 \
    --index-url https://download.pytorch.org/whl/cpu

# Freeze Torch Versions
# Prevent any later dependency from silently upgrading Torch.
RUN pip freeze | grep -iE '^(torch|torchaudio)==' > /tmp/torch-constraints.txt

# Install Python Dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir \
    -c /tmp/torch-constraints.txt \
    -r requirements.txt

# Copy Application
COPY . .

# Create Runtime Directories
RUN mkdir -p \
    saved_voices \
    rvc_models \
    training_data \
    hf_cache \
    temp

# Expose Gradio Port
EXPOSE 7860

# Health Check
HEALTHCHECK --interval=30s \
            --timeout=5s \
            --start-period=60s \
            --retries=5 \
    CMD curl -fsS http://127.0.0.1:7860/ || exit 1

# Launch Application
CMD ["python", "app.py"]