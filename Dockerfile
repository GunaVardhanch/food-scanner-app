# --- Stage 1: Build Frontend ---
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
# Next.js export produces an 'out' directory
RUN npm run build

# --- Stage 2: Build Backend & Serve ---
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies for OpenCV, EasyOCR, etc.
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements first
COPY backend/requirements.txt ./
# Install CPU-specific PyTorch to save space
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy built frontend assets to a 'static' directory in the backend
COPY --from=frontend-builder /app/frontend/out ./static

# Pre-download EasyOCR models to prevent runtime timeouts in Spaces
ENV EASYOCR_MODULE_PATH=/app/easyocr_models
RUN python -c "import easyocr; reader = easyocr.Reader(['en', 'hi', 'mr'], model_storage_directory='/app/easyocr_models', download_enabled=True)"

# Hugging Face Spaces default port is 7860
EXPOSE 7860

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
