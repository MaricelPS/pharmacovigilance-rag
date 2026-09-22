# Dockerfile for Hugging Face Spaces deployment
FROM python:3.11-slim

# System deps needed for psycopg2 and healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        polars>=1.0 \
        pandas>=2.0 \
        pyarrow>=15.0 \
        sqlalchemy>=2.0 \
        psycopg2-binary>=2.9 \
        pgvector>=0.3 \
        anthropic>=0.40 \
        voyageai>=0.3 \
        instructor>=1.0 \
        pydantic>=2.0 \
        scipy>=1.11 \
        numpy>=1.26 \
        streamlit>=1.35 \
        plotly>=5.20 \
        python-dotenv>=1.0 \
        requests>=2.31 \
        tqdm>=4.66

# Copy application code (data files excluded via .dockerignore)
COPY src/ ./src/

# Hugging Face Spaces expose the app on port 7860
EXPOSE 7860

# Streamlit config: bind to all interfaces, no telemetry, no CORS
ENV STREAMLIT_SERVER_PORT=7860 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

CMD ["streamlit", "run", "src/app/streamlit_app.py"]