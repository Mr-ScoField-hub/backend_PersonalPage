FROM nvidia/cuda:12.2.0-cudnn8-runtime-ubuntu22.04

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libjpeg-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY requirements-gpu.txt /app/requirements.txt

# Install PyTorch GPU version first for caching
RUN pip install --no-cache-dir torch==2.2.2+cu122 torchvision==0.17.2+cu122 --index-url https://download.pytorch.org/whl/cu122

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV PORT=8080
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
