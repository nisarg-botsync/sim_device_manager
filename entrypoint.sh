#!/bin/sh
set -e

uv run python backend/manage.py migrate --noinput
uv run python backend/manage.py collectstatic --noinput

exec "$@"
