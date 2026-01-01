# 🗺️ BiblioRuche - Roadmap

> Dernière mise à jour : Janvier 2026

---

## 📋 Table des matières

1. [Corrections et Bugs](#-corrections-et-bugs)
2. [Améliorations Prioritaires](#-améliorations-prioritaires)
3. [Nouvelles Fonctionnalités](#-nouvelles-fonctionnalités)
4. [Améliorations Techniques](#-améliorations-techniques)
5. [Améliorations UX/UI](#-améliorations-uxui)
6. [Sécurité](#-sécurité)
7. [Documentation](#-documentation)

---

## 🐛 Corrections et Bugs

### 🔴 Critique (à corriger immédiatement)

| # | Description | Fichier(s) concerné(s) | Status |
|---|-------------|------------------------|--------|
| C1 | **Protection CSRF manquante sur certaines routes GET sensibles** : Les routes `approve_proposal`, `reject_proposal`, `toggle_admin`, `close_vote` utilisent GET au lieu de POST, ce qui les rend vulnérables aux attaques CSRF | `app/routes/admin.py` | ✅ Terminé |
| C2 | **Pas de validation du type de fichier uploadé** : Préparation nécessaire avant l'ajout de la fonctionnalité d'upload d'epub | À créer | ⏳ À faire |
| C3 | **datetime.now() appelé sans timezone** : Peut causer des incohérences de dates entre serveurs | `app/models.py` | ✅ Terminé |

### 🟠 Important (à corriger rapidement)

| # | Description | Fichier(s) concerné(s) | Status |
|---|-------------|------------------------|--------|
| I1 | **Pas de limite de taille sur les champs TextArea** : Les descriptions pourraient être trop longues côté client | `app/forms.py`, templates | ✅ Terminé |
| I2 | **Gestion d'erreur incomplète sur les appels API Twitch** : Si Twitch est down, l'erreur n'est pas bien gérée | `app/routes/auth.py` | ✅ Terminé |
| I3 | **Pas de confirmation avant actions destructives** : Suppression de lecture, rejet de proposition sans confirmation | `app/templates/admin/*` | ⏳ À faire |
| I4 | **Vote fermé accessible si URL connue** : Un utilisateur peut voir les résultats même sans avoir voté | `app/routes/main.py` | ✅ Terminé |
| I5 | **Pas de rate limiting** : Un utilisateur peut spammer les propositions de livres | `app/routes/main.py` | ✅ Terminé |

### 🟡 Mineur (à corriger quand possible)

| # | Description | Fichier(s) concerné(s) | Status |
|---|-------------|------------------------|--------|
| M1 | **Messages flash non traduits/inconsistants** : Certains en français, d'autres formats différents | Tous les fichiers routes | ✅ Terminé |
| M2 | **Pagination manquante** : Liste des livres peut devenir très longue | `app/routes/main.py` | ✅ Terminé |
| M3 | **Pas de gestion des erreurs 404/500 personnalisées** : Pages d'erreur par défaut de Flask | `app/__init__.py` | ✅ Terminé |
| M4 | **Fichiers de migration orphelins** : Scripts de migration dans `/migrations` sans framework | `migrations/` | ✅ Terminé |
| M5 | **Console.log potentiels en production** : Vérifier le JS dans les templates | `app/templates/base.html` | ✅ Terminé |

---

## ⭐ Améliorations Prioritaires

### 📚 Bibliothèque d'Ebooks (Upload EPUB)

> **Priorité : HAUTE** | Demandé par : Propriétaire

#### Description
Permettre aux administrateurs d'uploader des fichiers EPUB dans une bibliothèque centralisée, accessible en téléchargement par les utilisateurs connectés. Les ebooks peuvent être associés aux sessions de lecture.

#### Fonctionnalités détaillées

| # | Fonctionnalité | Description | Status |
|---|----------------|-------------|--------|
| E1 | **Upload d'EPUB par admin** | Interface d'upload avec validation du format (EPUB uniquement), limite de taille (ex: 50MB) | ⏳ À faire |
| E2 | **Bibliothèque d'ebooks** | Page listant tous les ebooks disponibles avec recherche et filtres | ⏳ À faire |
| E3 | **Téléchargement sécurisé** | Téléchargement réservé aux utilisateurs connectés avec compteur de téléchargements | ⏳ À faire |
| E4 | **Association livre ↔ ebook** | Lier un fichier EPUB à un `BookProposal` existant | ⏳ À faire |
| E5 | **Association lecture ↔ ebook** | Lors de la création d'une lecture, sélectionner un ebook de la bibliothèque | ⏳ À faire |
| E6 | **Métadonnées EPUB** | Extraction automatique des métadonnées (titre, auteur, couverture) depuis l'EPUB | ⏳ À faire |
| E7 | **Gestion des fichiers** | Interface admin pour supprimer/remplacer les fichiers uploadés | ⏳ À faire |

#### Modèle de données proposé
```python
class Ebook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)  # en bytes
    book_id = db.Column(db.Integer, db.ForeignKey('book_proposal.id'), nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.now)
    download_count = db.Column(db.Integer, default=0)
    
    # Relations
    book = db.relationship('BookProposal', backref='ebook_files')
    uploader = db.relationship('User')
```

---

### 🎬 BiblioCinéClub (Module Film)

> **Priorité : HAUTE** | Demandé par : Propriétaire

#### Description
Module événementiel activable/désactivable par les administrateurs pour organiser des sessions de visionnage de films en groupe. Fonctionne de manière similaire aux lectures mais en version simplifiée (pas de propositions utilisateurs).

#### Fonctionnalités détaillées

| # | Fonctionnalité | Description | Status |
|---|----------------|-------------|--------|
| F1 | **Activation/Désactivation globale** | Toggle admin pour activer/masquer tout le module CinéClub | ✅ Terminé |
| F2 | **Gestion des films (admin)** | CRUD complet pour les films (titre, réalisateur, année, synopsis, affiche, durée) | ✅ Terminé |
| F3 | **Création de vote film** | Admin crée un vote avec sélection de films | ✅ Terminé |
| F4 | **Vote utilisateurs** | Les utilisateurs votent pour leur film préféré | ✅ Terminé |
| F5 | **Session de visionnage** | Programmer une séance avec date/heure, film sélectionné | ✅ Terminé |
| F6 | **Inscription au visionnage** | Les utilisateurs s'inscrivent à la séance | ✅ Terminé |
| F7 | **Historique des séances** | Archive des films visionnés | ✅ Terminé |
| F8 | **Badges CinéClub** | Badges spécifiques (Premier film, Cinéphile, etc.) | ✅ Terminé |
| F9 | **Masquage dynamique** | Liens et pages masqués quand le module est désactivé | ✅ Terminé |

#### Modèles de données proposés
```python
class CineClubSettings(db.Model):
    """Configuration globale du module CinéClub"""
    id = db.Column(db.Integer, primary_key=True)
    is_enabled = db.Column(db.Boolean, default=False)
    welcome_message = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.now)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))

class Film(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    director = db.Column(db.String(200))
    year = db.Column(db.Integer)
    duration = db.Column(db.Integer)  # en minutes
    synopsis = db.Column(db.Text)
    poster_url = db.Column(db.String(500))
    genre = db.Column(db.String(100))
    added_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

class FilmVotingSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, default=datetime.now)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='active')  # active, closed
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    winner_film_id = db.Column(db.Integer, db.ForeignKey('film.id'))

class FilmVoteOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voting_session_id = db.Column(db.Integer, db.ForeignKey('film_voting_session.id'), nullable=False)
    film_id = db.Column(db.Integer, db.ForeignKey('film.id'), nullable=False)

class FilmVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    voting_session_id = db.Column(db.Integer, db.ForeignKey('film_voting_session.id'), nullable=False)
    vote_option_id = db.Column(db.Integer, db.ForeignKey('film_vote_option.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

class ViewingSession(db.Model):
    """Session de visionnage de film"""
    id = db.Column(db.Integer, primary_key=True)
    film_id = db.Column(db.Integer, db.ForeignKey('film.id'), nullable=False)
    viewing_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='upcoming')  # upcoming, current, completed
    description = db.Column(db.Text)
    stream_url = db.Column(db.String(500))  # Lien vers le stream/watch party
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

class ViewingParticipation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    viewing_session_id = db.Column(db.Integer, db.ForeignKey('viewing_session.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.now)
```

#### Structure des routes
```
/cineclub/                    # Page d'accueil CinéClub (si activé)
/cineclub/films               # Liste des films
/cineclub/vote/<id>           # Page de vote
/cineclub/viewing/<id>        # Détail d'une séance
/admin/cineclub/              # Dashboard admin CinéClub
/admin/cineclub/settings      # Activer/désactiver le module
/admin/cineclub/films         # Gestion des films
/admin/cineclub/create-vote   # Créer un vote
/admin/cineclub/viewings      # Gestion des séances
```

---

## 🚀 Nouvelles Fonctionnalités

### 📊 Statistiques et Analytics

| # | Fonctionnalité | Description | Priorité | Status |
|---|----------------|-------------|----------|--------|
| S1 | **Dashboard statistiques public** | Nombre de lectures, participants, livres lus | 🟡 Moyenne | ✅ Terminé |
| S2 | **Statistiques admin avancées** | Graphiques d'activité, tendances, export CSV | 🟡 Moyenne | 🔄 Partiel |
| S3 | **Classement des lecteurs** | Leaderboard basé sur les participations/badges | 🟢 Basse | ✅ Terminé |
| S4 | **Statistiques personnelles** | Page "Mes stats" détaillée pour chaque utilisateur | 🟢 Basse | ⏳ À faire |

### 🔔 Notifications

| # | Fonctionnalité | Description | Priorité | Status |
|---|----------------|-------------|----------|--------|
| N1 | **Notifications in-app** | Cloche avec notifications non lues | 🟡 Moyenne | ✅ Terminé |
| N2 | **Notifications par email** | Optionnel, pour les événements importants | 🟢 Basse | ⏳ À faire |
| N3 | **Webhooks Discord** | Notifications automatiques sur un serveur Discord | 🟡 Moyenne | ⏳ À faire |
| N4 | **Rappels de lecture** | Notification X jours avant la fin d'une lecture | 🟢 Basse | ⏳ À faire |

### 💬 Social et Communauté

| # | Fonctionnalité | Description | Priorité |
|---|----------------|-------------|----------|
| SO1 | **Commentaires sur les lectures** | Fil de discussion par lecture | 🟡 Moyenne |
| SO2 | **Système de like sur les avis** | Voter pour les meilleurs avis | 🟢 Basse |
| SO3 | **Partage social** | Boutons de partage Twitter/Facebook | 🟢 Basse |
| SO4 | **Profils enrichis** | Bio, livres préférés, liens sociaux | 🟢 Basse |

### 📖 Gestion des livres avancée

| # | Fonctionnalité | Description | Priorité | Status |
|---|----------------|-------------|----------|--------|
| L1 | **Intégration API livres** | Auto-complétion via Google Books / Open Library | 🟠 Haute | ✅ Terminé |
| L2 | **Couvertures automatiques** | Récupération des couvertures via ISBN | 🟠 Haute | ✅ Terminé |
| L3 | **Liste de lecture personnelle** | "À lire plus tard" pour chaque utilisateur | 🟡 Moyenne | ⏳ À faire |
| L4 | **Catégories/Tags** | Système de tags pour organiser les livres | 🟡 Moyenne | ⏳ À faire |
| L5 | **Recherche avancée** | Filtres multiples (genre, année, auteur, note) | 🟡 Moyenne | ⏳ À faire |

### 🎮 Gamification avancée

| # | Fonctionnalité | Description | Priorité |
|---|----------------|-------------|----------|
| G1 | **Niveaux utilisateur** | Système XP et niveaux | 🟢 Basse |
| G2 | **Badges secrets** | Badges cachés à découvrir | 🟢 Basse |
| G3 | **Défis mensuels** | Objectifs communautaires | 🟢 Basse |
| G4 | **Badges personnalisés** | Admin peut créer de nouveaux badges | 🟡 Moyenne |

---

## 🔧 Améliorations Techniques

### 🗄️ Base de données et Performance

| # | Amélioration | Description | Priorité | Status |
|---|--------------|-------------|----------|--------|
| DB1 | **Migration vers Flask-Migrate/Alembic** | Gestion propre des migrations de schéma | 🟠 Haute | ✅ Terminé |
| DB2 | **Index sur les colonnes fréquentes** | Optimisation des requêtes (status, dates, user_id) | 🟡 Moyenne | ⏳ À faire |
| DB3 | **Support PostgreSQL** | Configuration pour production avec PostgreSQL | 🟡 Moyenne | ✅ Terminé |
| DB4 | **Système de cache** | Redis/Flask-Caching pour les pages fréquentes | 🟡 Moyenne | ⏳ À faire |
| DB5 | **Soft delete** | Marquage "supprimé" au lieu de vraie suppression | 🟢 Basse | ⏳ À faire |

### 🧪 Tests et Qualité

| # | Amélioration | Description | Priorité | Status |
|---|--------------|-------------|----------|--------|
| T1 | **Tests unitaires** | pytest + couverture des modèles et routes | 🟠 Haute | ✅ Terminé |
| T2 | **Tests d'intégration** | Tests end-to-end des workflows | 🟡 Moyenne | ⏳ À faire |
| T3 | **CI/CD Pipeline** | GitHub Actions pour tests automatiques | 🟡 Moyenne | ⏳ À faire |
| T4 | **Linting automatique** | flake8, black, isort en pre-commit | 🟡 Moyenne | ⏳ À faire |

### 📡 API et Intégrations

| # | Amélioration | Description | Priorité | Status |
|---|--------------|-------------|----------|--------|
| A1 | **API REST** | Endpoints JSON pour intégrations externes | 🟡 Moyenne | ✅ Terminé |
| A2 | **Documentation API** | Swagger/OpenAPI | 🟢 Basse | ⏳ À faire |
| A3 | **Webhooks sortants** | Notifier des services externes | 🟢 Basse | ⏳ À faire |
| A4 | **Bot Twitch** | Intégration avec le chat Twitch | 🟢 Basse | ⏳ À faire |

### 🚀 Déploiement

| # | Amélioration | Description | Priorité | Status |
|---|--------------|-------------|----------|--------|
| D1 | **Docker** | Containerisation de l'application | 🟠 Haute | ✅ Terminé |
| D2 | **docker-compose** | Stack complète (app + db + redis) | 🟠 Haute | ✅ Terminé |
| D3 | **Variables d'environnement** | Meilleure gestion des secrets | 🟡 Moyenne | ✅ Terminé |
| D4 | **Health checks** | Endpoints de monitoring | 🟡 Moyenne | ✅ Terminé |
| D5 | **Logging structuré** | Logs JSON avec niveaux appropriés | 🟡 Moyenne | ✅ Terminé |

---

## 🎨 Améliorations UX/UI

### 📱 Responsive et Accessibilité

| # | Amélioration | Description | Priorité |
|---|--------------|-------------|----------|
| R1 | **PWA** | Progressive Web App avec offline support | 🟡 Moyenne |
| R2 | **Amélioration mobile** | Menus et cartes optimisés mobile | 🟡 Moyenne |
| R3 | **Accessibilité WCAG** | Labels ARIA, contrastes, navigation clavier | 🟡 Moyenne |
| R4 | **Mode compact** | Vue liste alternative aux cartes | 🟢 Basse |

### ✨ Interface

| # | Amélioration | Description | Priorité |
|---|--------------|-------------|----------|
| U1 | **Skeleton loading** | Placeholders pendant le chargement | 🟢 Basse |
| U2 | **Animations améliorées** | Transitions plus fluides | 🟢 Basse |
| U3 | **Thèmes personnalisés** | Choix de couleurs principales | 🟢 Basse |
| U4 | **Mode lecture** | Interface épurée pour lire les descriptions | 🟢 Basse |
| U5 | **Drag & drop** | Réorganisation des éléments admin | 🟢 Basse |

### 📝 Formulaires

| # | Amélioration | Description | Priorité |
|---|--------------|-------------|----------|
| FO1 | **Auto-save brouillon** | Sauvegarder les formulaires en cours | 🟡 Moyenne |
| FO2 | **Validation temps réel** | Feedback immédiat sur les champs | 🟡 Moyenne |
| FO3 | **Éditeur Markdown** | Pour les descriptions longues | 🟢 Basse |
| FO4 | **Upload avec preview** | Voir l'image/fichier avant envoi | 🟡 Moyenne |

---

## 🔒 Sécurité

| # | Amélioration | Description | Priorité |
|---|--------------|-------------|----------|
| SE1 | **Rate limiting** | Limiter les requêtes par IP/utilisateur | ✅ Terminé |
| SE2 | **Headers de sécurité** | CSP, X-Frame-Options, etc. | 🟠 Haute |
| SE3 | **Audit log** | Tracer toutes les actions admin | 🟡 Moyenne |
| SE4 | **2FA optionnel** | Double authentification pour admins | 🟢 Basse |
| SE5 | **Rotation des tokens** | Rafraîchir les tokens OAuth | 🟡 Moyenne |
| SE6 | **Sanitization HTML** | Nettoyer les entrées utilisateur | ✅ Terminé |
| SE7 | **Backup automatique** | Sauvegardes régulières de la BDD | 🟠 Haute |

---

## 📚 Documentation

| # | Amélioration | Description | Priorité |
|---|--------------|-------------|----------|
| DO1 | **Guide d'installation détaillé** | Avec captures d'écran | 🟡 Moyenne |
| DO2 | **Guide administrateur** | Documentation des fonctionnalités admin | 🟡 Moyenne |
| DO3 | **Guide développeur** | Architecture, conventions, contribution | 🟡 Moyenne |
| DO4 | **Changelog** | Historique des versions | 🟡 Moyenne |
| DO5 | **FAQ utilisateurs** | Questions fréquentes | 🟢 Basse |

---

## 📅 Planning suggéré

### Phase 1 - Stabilisation ✅ COMPLÉTÉE
- [x] Corrections critiques (C1, C3) - CSRF + timezone
- [x] Corrections importantes (I1, I2, I4, I5) - maxlength, Twitch API, rate limiting
- [x] Pages d'erreur personnalisées (M3) - 404, 500, 403, 429
- [x] Pagination livres (M2)
- [x] Sanitisation HTML (SE6) - bleach
- [x] Réorganisation projet (M4, M5) - scripts/, docs/, tests/
- [ ] Confirmation actions destructives (I3) - en attente

### Phase 2 - Bibliothèque Ebooks (3-4 semaines) ✅ COMPLÉTÉE
- [x] Modèle Ebook en base de données
- [x] Routes ebooks (Blueprint) avec rate limiting
- [x] Interface d'upload admin avec validation EPUB
- [x] Catalogue public avec pagination et filtres
- [x] Téléchargement pour utilisateurs connectés
- [x] Gestion des couvertures
- [x] Liaison optionnelle avec les propositions de livres

### Phase 3 - BibliocinéClub (3-4 semaines) ✅ COMPLÉTÉE
- [x] Modèles CinéClub (Film, VotingSession, ViewingSession, etc.)
- [x] Système toggle activation/désactivation
- [x] Masquage dynamique dans la navigation
- [x] Routes cineclub (Blueprint)
- [x] Propositions de films par utilisateurs
- [x] Système de votes pour films
- [x] Séances de visionnage avec inscription
- [x] Interface admin complète
- [x] Badges CinéClub (7 badges)

### Phase 4 - Améliorations techniques (2-3 semaines) ✅ COMPLÉTÉE
- [x] Docker et docker-compose (dev + prod)
- [x] Flask-Migrate (Alembic)
- [x] Tests unitaires pytest (conftest, models, routes, badges)
- [x] Logging structuré JSON (pythonjsonlogger)
- [x] Health checks
- [x] Support PostgreSQL (docker-compose.prod.yml)

### Phase 5 - Fonctionnalités bonus ✅ COMPLÉTÉE
- [x] Intégration API Open Library (auto-complétion livres)
- [x] Système de notifications in-app (modèle + API)
- [x] Page statistiques publique avec Chart.js
- [x] API REST (/api/books, /api/stats, /api/notifications)
- [x] Classement des contributeurs

### Phase 6 - Améliorations UX/Sécurité (Janvier 2026) ✅
- [x] Headers de sécurité HTTP (CSP, X-Frame-Options, X-Content-Type-Options, etc.)
- [x] Interface notifications (cloche UI dans navbar avec dropdown)
- [x] Recherche avancée avec filtres (genre, année, tri)
- [x] Auto-complétion formulaires (Open Library API)
- [ ] CI/CD Pipeline (GitHub Actions) - Reporté
- [ ] Webhooks Discord - Reporté
- [ ] Backup automatique BDD - Reporté

---

## 📊 Légende des priorités

| Icône | Niveau | Description |
|-------|--------|-------------|
| 🔴 | Critique | Bloque l'utilisation ou pose un risque de sécurité |
| 🟠 | Haute | Important pour l'expérience utilisateur |
| 🟡 | Moyenne | Amélioration significative |
| 🟢 | Basse | Nice to have |

## 📊 Légende des statuts

| Icône | Status | Description |
|-------|--------|-------------|
| ⏳ | À faire | Non commencé |
| 🔄 | En cours | Développement en cours |
| ✅ | Terminé | Implémenté et testé |
| ❌ | Abandonné | Ne sera pas fait |

---

*Ce document est vivant et sera mis à jour au fur et à mesure de l'avancement du projet.*
