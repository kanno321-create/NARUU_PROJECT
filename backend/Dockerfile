FROM python:3.12-slim AS base

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/v1/health').raise_for_status()"

CMD ["uvicorn", "naruu_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
