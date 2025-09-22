FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python deps first (better caching)
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app

# Create non-root user
RUN useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

# Default environment (override via compose/.env)
ENV DJANGO_SETTINGS_MODULE=core.settings.prod

EXPOSE 8000

CMD [ "python", "manage.py", "runserver"]