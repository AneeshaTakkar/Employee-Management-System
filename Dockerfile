FROM python:3.11-slim

# System libraries needed by OpenCV / TensorFlow at runtime
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (layer caching - faster rebuilds when only code changes)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your project
COPY . .

# HF Spaces routes traffic to port 7860 - this is fixed, not optional
EXPOSE 7860
ENV PORT=7860

# gunicorn serves Flask in production (app.py must have `app = Flask(__name__)`)
# --timeout 120 because DeepFace model loading can be slow on first request
CMD ["gunicorn", "-b", "0.0.0.0:7860", "--timeout", "120", "--workers", "1", "app:app"]
