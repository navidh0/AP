# ====================================
# Stage 1: Build Tailwind CSS
# ====================================
FROM node:20-alpine AS assets
WORKDIR /app/theme/static_src

# Install Node dependencies
COPY theme/static_src/package*.json ./
RUN npm ci --no-audit --no-fund

# Copy Tailwind config + source files
COPY theme/static_src ./

# Build Tailwind CSS → output to theme/static/css/dist/styles.css
RUN mkdir -p /app/theme/static/css/dist \
 && npx tailwindcss -i ./src/styles.css -o /app/theme/static/css/dist/styles.css --minify

# ====================================
# Stage 2: Django + Gunicorn
# ====================================
FROM python:3.12-slim AS web
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install build essentials (no postgres libs needed since we use sqlite)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Copy compiled Tailwind CSS from Node stage
COPY --from=assets /app/theme/static/css/dist/styles.css ./theme/static/css/dist/styles.css

EXPOSE 8000

# Run Gunicorn with Django (core is your project)
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
