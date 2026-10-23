FROM node:22.23.4-bookworm-slim AS docs

ENV ASTRO_TELEMETRY_DISABLED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && dpkg --compare-versions "$(dpkg-query -W -f='${Version}' ca-certificates)" ge '20250419~deb12u2' \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY package.json package-lock.json astro.config.mjs ./
COPY src ./src
COPY public ./public
COPY logo_hollow.png ./logo_hollow.png

RUN npm ci && npm run docs:build


FROM python:3.14.9-slim-trixie AS app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_DEBUG=False

# The eMudhra fix must be present in the OS store used by urllib and SMTP.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && dpkg --compare-versions "$(dpkg-query -W -f='${Version}' ca-certificates)" ge '20250419+deb13u1' \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=docs /app/.runtime/site /app/.runtime/site

RUN DJANGO_SECRET_KEY=build-only-secret python manage.py collectstatic --noinput

CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py ensure_admin && gunicorn green_pipe_config.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]
