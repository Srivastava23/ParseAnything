FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libreoffice \
    tesseract-ocr \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
RUN pip install hatchling

COPY . .
RUN pip install .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "parseanything.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
