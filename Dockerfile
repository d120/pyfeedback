# Stage 1
FROM python:3.13-slim AS builder

RUN mkdir /app

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade pip

RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY package*.json ./

RUN npm i

# Stage 2
FROM python:3.13-slim

RUN useradd -m -r appuser && \
    mkdir /app && \
    chown -R appuser /app

COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

RUN apt-get update && apt-get install -y gettext \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app

COPY --chown=appuser:appuser . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/src

RUN python manage.py migrate --no-input
RUN python manage.py compilemessages

USER appuser

EXPOSE 8000


CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "wsgi:application"]