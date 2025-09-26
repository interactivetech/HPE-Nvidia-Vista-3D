FROM --platform=linux/amd64 python:3.11-slim

WORKDIR /srv

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install curl for healthchecks/debug
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Copy minimal project metadata and install deps
COPY pyproject.toml ./
RUN uv sync --frozen

# Create unprivileged user
RUN useradd -m appuser
USER appuser

# Copy server code
COPY --chown=appuser:appuser main.py ./main.py
COPY --chown=appuser:appuser server.py ./server.py
COPY --chown=appuser:appuser conf ./conf

EXPOSE 8888

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8888/health || exit 1

CMD ["uv", "run", "python", "server.py"]


