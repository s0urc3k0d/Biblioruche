# BiblioRuche - Python Flask Application
FROM python:3.11-slim

# Métadonnées
LABEL maintainer="BiblioRuche Team"
LABEL version="1.0"
LABEL description="Application de gestion de club de lecture communautaire"

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=run.py
ENV FLASK_ENV=production

# Créer un utilisateur non-root pour la sécurité
RUN groupadd -r biblioruche && useradd -r -g biblioruche biblioruche

# Répertoire de travail
WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn psycopg2-binary

# Copier le code de l'application
COPY --chown=biblioruche:biblioruche . .

# Créer les répertoires nécessaires
RUN mkdir -p instance/ebooks instance/covers \
    && chown -R biblioruche:biblioruche instance

# Passer à l'utilisateur non-root
USER biblioruche

# Exposer le port
EXPOSE 5000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Commande de démarrage
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "run:app"]
