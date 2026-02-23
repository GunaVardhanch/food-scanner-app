FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for OpenCV, EasyOCR, YOLO, etc.
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to cache the heavy pip layer
COPY requirements.txt .

# Crucial: Install CPU-only PyTorch first to save gigabytes of space and avoid OOM issues
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install the rest of the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set EasyOCR model directory and pre-download models to prevent runtime timeouts
ENV EASYOCR_MODULE_PATH=/app/easyocr_models
RUN python -c "import easyocr; reader = easyocr.Reader(['en', 'hi', 'mr'], model_storage_directory='/app/easyocr_models', download_enabled=True)"

# Expose the port (Railway metadata)
EXPOSE 8000

# Start Uvicorn - note: we use the $PORT env var if Railway provides it
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-7860}
