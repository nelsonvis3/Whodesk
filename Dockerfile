FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Primero las dependencias: así Docker reutiliza esta capa si el código cambia pero requirements.txt no.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# collectstatic necesita una SECRET_KEY; esta solo existe durante el build.
RUN SECRET_KEY=build-only DEBUG=False python manage.py collectstatic --noinput \
    && useradd --create-home app && chown -R app /app
USER app

EXPOSE 8000
CMD ["sh", "docker-entrypoint.sh"]
