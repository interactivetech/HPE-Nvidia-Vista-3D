FROM --platform=linux/amd64 python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV STREAMLIT_SERVER_PORT=8502
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_THEME_BASE=dark

# System deps for plotly and Open3D
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libx11-6 \
    libxau6 \
    libxcb1 \
    libxdmcp6 \
    libglib2.0-0 \
    libxext6 \
    libxrender1 \
  && rm -rf /var/lib/apt/lists/*

# Install uv for dependency management
RUN pip install --no-cache-dir uv

# Install only open3d deps
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Runtime env
ENV DOCKER_CONTAINER=true

# Copy open3d app code
COPY Open3d_Viewer.py ./Open3d_Viewer.py
COPY utils ./utils

# Expose UI port
EXPOSE 8502

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8502/_stcore/health || exit 1

CMD ["uv", "run", "streamlit", "run", "Open3d_Viewer.py", "--server.port=8502", "--server.address=0.0.0.0"]
