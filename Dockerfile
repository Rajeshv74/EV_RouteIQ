FROM python:3.10-slim

WORKDIR /app

# System deps (libgomp1 needed by PyTorch CPU)
RUN apt-get update && apt-get install -y \
    libgomp1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# ── Step 1: CPU-only PyTorch (750 MB vs 2.5 GB for CUDA) ──────────
# This is the critical fix — without +cpu it times out on HF Spaces
RUN pip install --no-cache-dir \
    torch==2.1.2+cpu \
    torchvision==0.16.2+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# ── Step 2: All other dependencies ────────────────────────────────
RUN pip install --no-cache-dir \
    timm==0.9.16 \
    flask==3.0.3 \
    flask-cors==4.0.1 \
    Pillow==10.3.0 \
    requests==2.31.0 \
    reportlab==4.1.0 \
    numpy==1.26.4 \
    gunicorn==21.2.0

# ── Step 3: Copy all project files ────────────────────────────────
COPY . .

# HF Spaces requires port 7860
EXPOSE 7860
ENV PORT=7860

# Use gunicorn for production (more stable than flask dev server)
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "1", "--timeout", "120", "app:app"]