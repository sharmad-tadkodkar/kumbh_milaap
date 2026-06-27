# Backend face-search web service (FastAPI + OpenCV).
# Deploy target: Render free Docker web service. The Next.js frontend is
# deployed separately (Vercel) and calls this service's /api/search directly.
FROM python:3.11-slim

# OpenCV runtime libs (needed even for the headless build's video decode).
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first for better layer caching.
COPY requirements-server.txt .
RUN pip install --no-cache-dir -r requirements-server.txt

# Download the ONNX face models (gitignored, fetched at build time).
# These are Git-LFS files in opencv_zoo — the /media/ host serves the real
# binaries (raw.githubusercontent.com would return an LFS pointer instead).
RUN mkdir -p models \
    && curl -fSL "https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx" \
         -o models/face_detection_yunet_2023mar.onnx \
    && curl -fSL "https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx" \
         -o models/face_recognition_sface_2021dec.onnx \
    # Fail the build if a download is too small (i.e. an LFS pointer, not the model).
    && test "$(wc -c < models/face_detection_yunet_2023mar.onnx)" -gt 100000 \
    && test "$(wc -c < models/face_recognition_sface_2021dec.onnx)" -gt 1000000

# App code + data (footage, cctv_zones.json, *.py). web/ excluded via .dockerignore.
COPY . .

ENV PORT=8000
EXPOSE 8000

# Render injects $PORT; default to 8000 for local runs.
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]
