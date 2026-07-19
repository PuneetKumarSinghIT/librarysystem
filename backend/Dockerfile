# Backend image — runs REST gateway (default) or gRPC server.
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for asyncpg / argon2 build wheels are prebuilt; keep image slim.
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install .

COPY . .
RUN pip install .

EXPOSE 8000 50051

# Default: REST gateway. Override command for the gRPC server.
CMD ["uvicorn", "library.main_rest:app", "--host", "0.0.0.0", "--port", "8000"]
