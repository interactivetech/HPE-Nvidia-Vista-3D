FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_THEME_BASE=dark

# System deps for plotly, medical imaging, and 3D processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    dcm2niix \
    libgomp1 \
    libgl1 \
    libglib2.0-0 \
  && rm -rf /var/lib/apt/lists/*

# Install uv for dependency management
RUN pip install --no-cache-dir uv

# Install only frontend deps
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Runtime env
ENV DOCKER_CONTAINER=true

# Copy minimal app code into image to avoid bind mounts in production
COPY app.py ./app.py
COPY Tools.py ./Tools.py
COPY NiiVue_Viewer.py ./NiiVue_Viewer.py
COPY assets ./assets
COPY utils ./utils

# Expose UI port
EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["uv", "run", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]


