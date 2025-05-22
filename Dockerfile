## Stage 1: build stage
FROM python:3.13-slim AS builder

RUN mkdir /app

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# install packages and node
RUN pip install --upgrade pip

RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# install pip requirements
COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

# install node_modules
COPY package*.json ./

RUN npm i

## Stage 2: production stage
FROM python:3.13-slim

RUN useradd -m -r appuser && \
    mkdir /app && \
    chown -R appuser /app

# Copy the python dependencies and node_modules from the builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder  /app/node_modules/ /app/node_modules/

# install gettext for translations (compiling)
RUN apt-get update && apt-get install -y gettext \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# copy the code
COPY --chown=appuser:appuser . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/src

# switch to non-root user
USER appuser

# compile translations 
RUN django-admin compilemessages

# migrate db changes
RUN python manage.py migrate --no-input

EXPOSE 8000

# start applicaiton with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "wsgi:application"]