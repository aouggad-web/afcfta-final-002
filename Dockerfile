# Multi-stage build
FROM python:3.11-slim as builder

RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

# Security hardening: run as non-root user
RUN useradd -m -u 1000 appuser

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
# Ensure python logs are sent straight to terminal
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY --chown=appuser:appuser . /app

USER appuser

# Données tarifaires : vérifier puis dériver, à la construction de l'image.
#
# crawled_normalized/ n'est pas versionné — 2 Go, et des fichiers au-delà de la
# limite de 100 Mo par fichier de GitHub. Il était jusqu'ici régénéré dans le
# seul job de CI, si bien qu'une image construite depuis ce Dockerfile démarrait
# sans lui : le backend servait alors les pays dont les données ne dépendent pas
# de ce dossier, et se taisait sur les autres. Le défaut ne se voyait qu'en
# production.
#
# La vérification passe en premier et n'est pas un simple contrôle de forme :
# elle recalcule l'empreinte SHA-256 de chaque fichier servi et la confronte au
# manifeste. Une donnée altérée, tronquée à la copie ou périmée arrête la
# construction au lieu d'être normalisée puis servie. Mieux vaut une image qui
# ne se construit pas qu'une image qui calcule des droits de douane faux.
RUN python scripts/fetch_tariff_artifacts.py --verify-only \
 && python scripts/normalize_crawled.py

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import sys, requests; r = requests.get('http://localhost:8000/api/health', timeout=8); sys.exit(0 if r.status_code == 200 else 1)"

CMD ["sh", "-c", "exec uvicorn backend.server:app --host 0.0.0.0 --port 8000 --proxy-headers \"--forwarded-allow-ips=${UVICORN_FORWARDED_ALLOW_IPS:-127.0.0.1}\""]
