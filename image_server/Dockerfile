FROM python:3.11-slim

WORKDIR /srv

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install curl for healthchecks/debug
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Create unprivileged user early
RUN useradd -m appuser && chown -R appuser:appuser /srv

# Switch to unprivileged user
USER appuser

# Copy minimal project metadata and install deps
COPY --chown=appuser:appuser pyproject.toml uv.lock README.md ./
RUN uv sync --frozen

# Copy server code (will be overridden by volume mount in development)
COPY --chown=appuser:appuser main.py ./main.py
COPY --chown=appuser:appuser server.py ./server.py
COPY --chown=appuser:appuser conf ./conf

EXPOSE 8888

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8888/health || exit 1

CMD ["uv", "run", "python", "server.py"]
