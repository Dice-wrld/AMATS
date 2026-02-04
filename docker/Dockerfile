FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev gcc git curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip setuptools wheel && pip install -r /app/requirements.txt

# Copy project
COPY . /app/

# Create static/media directories
RUN mkdir -p /vol/web/static && mkdir -p /vol/web/media

# Collect static files
ENV DJANGO_SETTINGS_MODULE=amats_project.settings
RUN python manage.py collectstatic --noinput || true

CMD ["gunicorn", "amats_project.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
