# ==========================================
# Build Node.js Dependencies
# ==========================================

FROM node:22-slim AS node-builder

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

# ==========================================
# Build Python Dependencies
# ==========================================

FROM python:3.13-slim AS python-builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./

COPY src ./src

RUN pip install --root-user-action ignore --upgrade pip && \
    pip install --root-user-action ignore --no-cache-dir .

# ==========================================
# Final Production Image
# ==========================================

FROM python:3.13-slim AS production

ARG DEBIAN_FRONTEND=noninteractive

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gettext \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# non-root user

RUN useradd -m -r appuser

WORKDIR /app

COPY --from=python-builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=python-builder /usr/local/bin/ /usr/local/bin/

COPY --from=node-builder /app/node_modules /app/node_modules

COPY --chown=appuser:appuser . .

COPY --chown=appuser:appuser entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

RUN mkdir -p /app/static && \
    chown appuser:appuser /app/static

# Build static assets & translations as non-root user

USER appuser

RUN django-admin compilemessages && \
    python src/manage.py collectstatic --no-input --clear

EXPOSE 8000
WORKDIR /app/src

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]