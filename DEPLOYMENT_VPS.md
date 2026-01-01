# 🚀 Guide de Déploiement BiblioRuche sur VPS Ubuntu

> **Configuration cible :**
> - VPS Ubuntu Server
> - Docker + Docker Compose
> - Nginx Reverse Proxy (existant)
> - Port local : 4001
> - Domaines : `biblioruche.sourcekod.fr` et `www.biblioruche.sourcekod.fr`
> - SSL via Certbot (Let's Encrypt)

---

## 📋 Table des matières

1. [Prérequis](#1-prérequis)
2. [Installation de Docker](#2-installation-de-docker)
3. [Déploiement de l'application](#3-déploiement-de-lapplication)
4. [Configuration Nginx (HTTP)](#4-configuration-nginx-http)
5. [Installation du certificat SSL](#5-installation-du-certificat-ssl)
6. [Configuration Nginx (HTTPS)](#6-configuration-nginx-https)
7. [Vérifications et tests](#7-vérifications-et-tests)
8. [Maintenance](#8-maintenance)

---

## 1. Prérequis

### Sur votre VPS, vérifiez que vous avez :

```bash
# Vérifier la version Ubuntu
lsb_release -a

# Vérifier que Nginx est installé
nginx -v

# Vérifier les ports utilisés
sudo netstat -tlnp | grep -E ':(80|443|4001|5000)'
```

### Créer le répertoire de l'application

```bash
# Créer le dossier pour BiblioRuche
sudo mkdir -p /var/www/biblioruche
sudo chown $USER:$USER /var/www/biblioruche
cd /var/www/biblioruche
```

---

## 2. Installation de Docker

### 2.1 Supprimer les anciennes versions (si présentes)

```bash
sudo apt-get remove docker docker-engine docker.io containerd runc 2>/dev/null
```

### 2.2 Installer les dépendances

```bash
sudo apt-get update
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release
```

### 2.3 Ajouter la clé GPG officielle de Docker

```bash
sudo mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
```

### 2.4 Configurer le repository Docker

```bash
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

### 2.5 Installer Docker Engine et Docker Compose

```bash
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 2.6 Ajouter votre utilisateur au groupe docker

```bash
sudo usermod -aG docker $USER
```

> ⚠️ **Important** : Déconnectez-vous et reconnectez-vous pour que les changements prennent effet, ou exécutez :
```bash
newgrp docker
```

### 2.7 Vérifier l'installation

```bash
docker --version
docker compose version
```

---

## 3. Déploiement de l'application

### 3.1 Cloner le repository

```bash
cd /var/www/biblioruche
git clone https://github.com/s0urc3k0d/Biblioruche.git .
```

### 3.2 Créer le fichier docker-compose.prod.yml

Créez un fichier de configuration Docker pour la production avec le port 4001 :

```bash
cat > docker-compose.prod.yml << 'EOF'
services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: biblioruche-web
    restart: unless-stopped
    ports:
      - "127.0.0.1:4001:5000"
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
      - TWITCH_CLIENT_ID=${TWITCH_CLIENT_ID}
      - TWITCH_CLIENT_SECRET=${TWITCH_CLIENT_SECRET}
      - TWITCH_REDIRECT_URI=https://biblioruche.sourcekod.fr/auth/twitch/callback
    volumes:
      - ./instance:/app/instance
    networks:
      - biblioruche-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

networks:
  biblioruche-network:
    driver: bridge
EOF
```

### 3.3 Créer le fichier .env

```bash
cat > .env << 'EOF'
# Générer une clé secrète sécurisée
SECRET_KEY=VOTRE_CLE_SECRETE_TRES_LONGUE_ET_ALEATOIRE

# Configuration Twitch OAuth
TWITCH_CLIENT_ID=votre_client_id_twitch
TWITCH_CLIENT_SECRET=votre_client_secret_twitch
EOF
```

> 💡 **Générer une clé secrète sécurisée** :
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 3.4 Créer le dossier instance (pour la BDD SQLite)

```bash
mkdir -p instance
chmod 755 instance
```

> 📝 **Si vous avez une base de données existante**, copiez-la :
```bash
# Depuis votre machine locale (avec scp)
scp instance/biblioruche.db user@votre-vps:/var/www/biblioruche/instance/
```

### 3.5 Construire et démarrer l'application

```bash
cd /var/www/biblioruche
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### 3.6 Vérifier que le conteneur fonctionne

```bash
# Vérifier le status
docker compose -f docker-compose.prod.yml ps

# Vérifier les logs
docker compose -f docker-compose.prod.yml logs -f

# Tester localement
curl http://127.0.0.1:4001
```

---

## 4. Configuration Nginx (HTTP)

> ⚠️ Cette configuration est **temporaire** - elle sera modifiée après l'installation de Certbot.

### 4.1 Créer le fichier de configuration Nginx

```bash
sudo nano /etc/nginx/sites-available/biblioruche
```

### 4.2 Configuration HTTP (avant Certbot)

```nginx
# /etc/nginx/sites-available/biblioruche
# Configuration HTTP - AVANT CERTBOT

server {
    listen 80;
    listen [::]:80;
    server_name biblioruche.sourcekod.fr www.biblioruche.sourcekod.fr;

    # Logs
    access_log /var/log/nginx/biblioruche.access.log;
    error_log /var/log/nginx/biblioruche.error.log;

    # Pour Certbot (validation du domaine)
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Proxy vers l'application Docker
    location / {
        proxy_pass http://127.0.0.1:4001;
        proxy_http_version 1.1;
        
        # Headers proxy
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (si nécessaire)
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # Fichiers statiques (optionnel, pour optimisation)
    location /static/ {
        proxy_pass http://127.0.0.1:4001/static/;
        proxy_cache_valid 200 1d;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
}
```

### 4.3 Activer le site

```bash
# Créer le lien symbolique
sudo ln -s /etc/nginx/sites-available/biblioruche /etc/nginx/sites-enabled/

# Tester la configuration
sudo nginx -t

# Recharger Nginx
sudo systemctl reload nginx
```

### 4.4 Vérifier que le site fonctionne en HTTP

```bash
curl -I http://biblioruche.sourcekod.fr
```

> ✅ Vous devriez voir une réponse HTTP 200 avec les headers de sécurité.

---

## 5. Installation du certificat SSL

### 5.1 Installer Certbot (si pas déjà installé)

```bash
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx
```

### 5.2 Obtenir le certificat SSL

```bash
sudo certbot --nginx -d biblioruche.sourcekod.fr -d www.biblioruche.sourcekod.fr
```

> 📝 **Certbot vous demandera** :
> 1. Votre adresse email (pour les notifications d'expiration)
> 2. D'accepter les conditions d'utilisation
> 3. Si vous voulez partager votre email avec l'EFF
> 4. Si vous voulez rediriger automatiquement HTTP vers HTTPS → **Choisissez OUI (2)**

### 5.3 Vérifier le renouvellement automatique

```bash
# Tester le renouvellement
sudo certbot renew --dry-run

# Vérifier le timer systemd
sudo systemctl status certbot.timer
```

---

## 6. Configuration Nginx (HTTPS)

> Après Certbot, le fichier sera automatiquement modifié. Voici la configuration finale recommandée avec optimisations.

### 6.1 Configuration HTTPS complète (après Certbot)

```bash
sudo nano /etc/nginx/sites-available/biblioruche
```

```nginx
# /etc/nginx/sites-available/biblioruche
# Configuration HTTPS - APRÈS CERTBOT

# Redirection HTTP → HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name biblioruche.sourcekod.fr www.biblioruche.sourcekod.fr;

    # Pour Certbot (renouvellement)
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Redirection vers HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# Redirection www → non-www (optionnel mais recommandé)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name www.biblioruche.sourcekod.fr;

    # Certificats SSL (générés par Certbot)
    ssl_certificate /etc/letsencrypt/live/biblioruche.sourcekod.fr/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/biblioruche.sourcekod.fr/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    return 301 https://biblioruche.sourcekod.fr$request_uri;
}

# Serveur principal HTTPS
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name biblioruche.sourcekod.fr;

    # Certificats SSL (générés par Certbot)
    ssl_certificate /etc/letsencrypt/live/biblioruche.sourcekod.fr/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/biblioruche.sourcekod.fr/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Logs
    access_log /var/log/nginx/biblioruche.access.log;
    error_log /var/log/nginx/biblioruche.error.log;

    # Taille max upload (pour les ebooks)
    client_max_body_size 50M;

    # Headers de sécurité supplémentaires (en plus de ceux de Flask)
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # HSTS (HTTP Strict Transport Security)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # Proxy vers l'application Docker
    location / {
        proxy_pass http://127.0.0.1:4001;
        proxy_http_version 1.1;
        
        # Headers proxy essentiels
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffering optimisé
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
    }

    # Fichiers statiques avec cache longue durée
    location /static/ {
        proxy_pass http://127.0.0.1:4001/static/;
        proxy_cache_valid 200 7d;
        expires 7d;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options "nosniff" always;
    }

    # Favicon
    location = /favicon.ico {
        proxy_pass http://127.0.0.1:4001/static/favicon.ico;
        expires 30d;
        access_log off;
    }

    # Bloquer l'accès aux fichiers sensibles
    location ~ /\. {
        deny all;
    }

    location ~ ^/(instance|migrations|__pycache__|\.git) {
        deny all;
    }
}
```

### 6.2 Appliquer la configuration

```bash
# Tester la configuration
sudo nginx -t

# Si OK, recharger Nginx
sudo systemctl reload nginx
```

---

## 7. Vérifications et tests

### 7.1 Tester l'application

```bash
# Vérifier HTTPS
curl -I https://biblioruche.sourcekod.fr

# Vérifier la redirection HTTP → HTTPS
curl -I http://biblioruche.sourcekod.fr

# Vérifier la redirection www → non-www
curl -I https://www.biblioruche.sourcekod.fr
```

### 7.2 Tester les headers de sécurité

```bash
curl -I https://biblioruche.sourcekod.fr 2>&1 | grep -E "(X-Frame|X-Content|X-XSS|Strict-Transport|Content-Security)"
```

### 7.3 Tester le certificat SSL

```bash
# Vérifier le certificat
echo | openssl s_client -servername biblioruche.sourcekod.fr -connect biblioruche.sourcekod.fr:443 2>/dev/null | openssl x509 -noout -dates
```

Ou utilisez : https://www.ssllabs.com/ssltest/analyze.html?d=biblioruche.sourcekod.fr

### 7.4 Vérifier les logs

```bash
# Logs Nginx
sudo tail -f /var/log/nginx/biblioruche.access.log
sudo tail -f /var/log/nginx/biblioruche.error.log

# Logs Docker
cd /var/www/biblioruche
docker compose -f docker-compose.prod.yml logs -f
```

---

## 8. Maintenance

### 8.1 Mettre à jour l'application

```bash
cd /var/www/biblioruche

# Récupérer les dernières modifications
git pull origin main

# Reconstruire et redémarrer
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### 8.2 Commandes utiles

```bash
# Status de l'application
docker compose -f docker-compose.prod.yml ps

# Logs en temps réel
docker compose -f docker-compose.prod.yml logs -f

# Redémarrer l'application
docker compose -f docker-compose.prod.yml restart

# Arrêter l'application
docker compose -f docker-compose.prod.yml down

# Démarrer l'application
docker compose -f docker-compose.prod.yml up -d

# Accéder au shell du conteneur
docker compose -f docker-compose.prod.yml exec web sh

# Voir l'utilisation des ressources
docker stats biblioruche-web
```

### 8.3 Backup de la base de données

```bash
# Créer un backup
cp /var/www/biblioruche/instance/biblioruche.db /var/www/biblioruche/instance/biblioruche_backup_$(date +%Y%m%d).db

# Script de backup automatique (à ajouter dans crontab)
# crontab -e
# 0 3 * * * cp /var/www/biblioruche/instance/biblioruche.db /var/www/biblioruche/backups/biblioruche_$(date +\%Y\%m\%d).db
```

### 8.4 Mise à jour de Twitch OAuth

Après le déploiement, **mettez à jour l'URL de callback** dans la console Twitch :

1. Allez sur https://dev.twitch.tv/console/apps
2. Sélectionnez votre application BiblioRuche
3. Modifiez l'URL de redirection OAuth :
   - **Ancienne** : `http://localhost:5000/auth/twitch/callback`
   - **Nouvelle** : `https://biblioruche.sourcekod.fr/auth/twitch/callback`

---

## 📝 Récapitulatif des ports et services

| Service | Port interne | Port externe | Accès |
|---------|--------------|--------------|-------|
| BiblioRuche (Docker) | 5000 | 4001 (localhost) | Via Nginx |
| Nginx HTTP | - | 80 | Redirige vers HTTPS |
| Nginx HTTPS | - | 443 | Point d'entrée public |

---

## 🆘 Dépannage

### L'application ne démarre pas

```bash
# Vérifier les logs
docker compose -f docker-compose.prod.yml logs web

# Vérifier le fichier .env
cat .env

# Vérifier les permissions de instance/
ls -la instance/
```

### Erreur 502 Bad Gateway

```bash
# Vérifier que le conteneur tourne
docker compose -f docker-compose.prod.yml ps

# Vérifier le port 4001
curl http://127.0.0.1:4001

# Vérifier les logs Nginx
sudo tail -20 /var/log/nginx/biblioruche.error.log
```

### Certificat SSL expiré

```bash
# Renouveler manuellement
sudo certbot renew

# Vérifier le timer
sudo systemctl status certbot.timer
```

### Base de données corrompue

```bash
# Restaurer depuis backup
cp /var/www/biblioruche/backups/biblioruche_YYYYMMDD.db /var/www/biblioruche/instance/biblioruche.db

# Redémarrer
docker compose -f docker-compose.prod.yml restart
```

---

## ✅ Checklist de déploiement

- [ ] Docker installé et fonctionnel
- [ ] Repository cloné dans `/var/www/biblioruche`
- [ ] Fichier `.env` créé avec les bonnes variables
- [ ] `docker-compose.prod.yml` créé avec port 4001
- [ ] Base de données copiée (si existante)
- [ ] Conteneur Docker démarré et fonctionnel
- [ ] Configuration Nginx HTTP créée et activée
- [ ] Site accessible en HTTP
- [ ] Certbot installé
- [ ] Certificat SSL obtenu
- [ ] Configuration Nginx HTTPS appliquée
- [ ] Redirection HTTP → HTTPS fonctionnelle
- [ ] Redirection www → non-www fonctionnelle
- [ ] Headers de sécurité présents
- [ ] URL de callback Twitch mise à jour
- [ ] Test de connexion Twitch réussi

---

*Guide créé le 1er janvier 2026 pour BiblioRuche v1.0*
