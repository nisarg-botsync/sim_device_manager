FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev

COPY backend/ ./backend/
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x entrypoint.sh

ENV PYTHONPATH=/app/backend \
    DJANGO_SETTINGS_MODULE=core.settings \
    PYTHONUNBUFFERED=1

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uv", "run", "gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
