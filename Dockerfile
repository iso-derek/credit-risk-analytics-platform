FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_HEADLESS=true

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --create-home app

COPY requirements-tested.txt ./
RUN python -m pip install --requirement requirements-tested.txt \
    && python -m pip check

COPY --chown=app:app app.py project.json ./
COPY --chown=app:app .streamlit .streamlit
COPY --chown=app:app src src
COPY --chown=app:app config config

RUN python -m compileall -q app.py src

USER app
EXPOSE 8502

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8502/_stcore/health', timeout=5).read()"

CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8502"]
