FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DRY_RUN=true \
    REAL_PUBLISHING=false \
    REVIEW_LEVEL=L0 \
    HOST=0.0.0.0 \
    PORT=8787

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir ".[web]" \
    && useradd --create-home --uid 10001 distribution \
    && mkdir -p /app/data /app/platform_ready \
    && chown -R distribution:distribution /app

USER distribution
EXPOSE 8787
VOLUME ["/app/data", "/app/platform_ready"]

CMD ["distribution-os", "serve", "--host", "0.0.0.0", "--port", "8787"]
