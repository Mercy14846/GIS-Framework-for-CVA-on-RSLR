FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DSS_DATA_DIR=/app/data
WORKDIR /app
COPY backend/pyproject.toml ./pyproject.toml
COPY backend/src ./src
RUN pip install --no-cache-dir ".[ingest]"
COPY data ./data
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s CMD python -c "import urllib.request as u; u.urlopen('http://localhost:8000/api/v1/health')"
CMD ["uvicorn", "coastal_dss.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
