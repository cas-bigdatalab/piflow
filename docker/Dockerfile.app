FROM node:20-alpine AS frontend-build

WORKDIR /frontend

COPY vue-web/package*.json /frontend/
RUN npm install

COPY vue-web /frontend
RUN npm run build:prod

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    pandoc \
    poppler-utils \
    curl \
    nginx \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/sites-enabled/default \
    && rm -f /etc/nginx/conf.d/default.conf

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app
COPY docker/nginx.app.conf /etc/nginx/conf.d/default.conf
COPY docker/start-app.sh /start-app.sh
COPY --from=frontend-build /frontend/dist /usr/share/nginx/html

RUN chmod +x /start-app.sh

EXPOSE 5174

CMD ["/start-app.sh"]
