FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080 \
    TMPDIR=/tmp/workbookcare

WORKDIR /app

RUN addgroup --system app \
    && adduser --system --ingroup app app \
    && install -d -o app -g app -m 700 "$TMPDIR"

COPY pyproject.toml ./
COPY --chown=app:app app ./app
RUN pip install --upgrade pip && pip install .

USER app

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ['PORT'] + '/health/live', timeout=3).read()" || exit 1

CMD ["python", "-m", "app.runtime"]
