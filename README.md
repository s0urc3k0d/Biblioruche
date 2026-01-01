# BiblioRuche 📚

BiblioRuche est une application web de bibliothèque numérique collaborative créée pour l'émission "L'Essaim Littéraire" de la chaîne Twitch de Wenyn. Cette application permet à la communauté de proposer des livres, de voter et de suivre les lectures communes.

## Fonctionnalités principales

### Pour tous les utilisateurs :
- 🔐 **Connexion via Twitch** : Authentification sécurisée avec votre compte Twitch
- 📖 **Proposition de livres** : Proposez vos livres favoris à la communauté
- 🗳️ **Participation aux votes** : Votez pour choisir le prochain livre à lire
- 📚 **Suivi des lectures** : Consultez les lectures en cours et à venir

### Pour les administrateurs :
- ⚙️ **Gestion des propositions** : Approuver ou rejeter les propositions de livres
- 🗳️ **Création de votes** : Organiser des votes pour choisir les prochains livres
- 📅 **Programmation des lectures** : Planifier les sessions de lecture avec dates de début, fin et débrief
- 🗄️ **Archivage** : Archiver les lectures terminées
- 👥 **Gestion des utilisateurs** : Gérer les droits d'administration

## Installation

### Prérequis
- Python 3.8 ou plus récent
- Un compte développeur Twitch pour l'OAuth

### Étapes d'installation

1. **Cloner le projet** (si vous l'avez récupéré depuis Git) ou utilisez les fichiers fournis

2. **Installer les dépendances** :
   ```powershell
   pip install -r requirements.txt
   ```

3. **Configuration de l'application Twitch** :
   - Allez sur https://dev.twitch.tv/console/apps
   - Créez une nouvelle application
   - Notez le `Client ID` et le `Client Secret`
   - Ajoutez `http://localhost:5000/auth/callback` comme URL de redirection OAuth

4. **Configuration de l'environnement** :
   - Copiez le fichier `.env.example` vers `.env`
   - Remplissez les valeurs dans le fichier `.env` :
     ```
     TWITCH_CLIENT_ID=votre_client_id_twitch
     TWITCH_CLIENT_SECRET=votre_client_secret_twitch
     TWITCH_REDIRECT_URI=http://localhost:5000/auth/callback
     SECRET_KEY=votre_cle_secrete_flask
     DATABASE_URL=sqlite:///biblioruche.db
     ADMIN_TWITCH_USERNAMES=lantredesilver,wenyn
     FLASK_DEBUG=True
     ```

5. **Génération d'une clé secrète** :
   ```powershell
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Utilisez la sortie comme valeur pour `SECRET_KEY`

6. **Lancement de l'application** :
   ```powershell
   python run.py
   ```

7. **Accès à l'application** :
   Ouvrez votre navigateur et allez sur http://localhost:5000

## Structure du projet

```
BiblioRuche/
├── app/                          # Package principal de l'application
│   ├── __init__.py              # Configuration de l'application Flask
│   ├── models.py                # Modèles de base de données
│   ├── forms.py                 # Formulaires WTForms
│   ├── routes/                  # Routes de l'application
│   │   ├── main.py             # Routes principales (publiques)
│   │   ├── auth.py             # Routes d'authentification Twitch
│   │   └── admin.py            # Routes d'administration
│   ├── templates/               # Templates HTML
│   │   ├── base.html           # Template de base
│   │   ├── index.html          # Page d'accueil
│   │   ├── books.html          # Page des livres
│   │   ├── readings.html       # Page des lectures
│   │   ├── propose_book.html   # Formulaire de proposition
│   │   ├── vote_detail.html    # Page de vote
│   │   └── admin/              # Templates d'administration
│   │       ├── dashboard.html  # Tableau de bord admin
│   │       └── create_vote.html # Création de vote
│   └── static/                  # Fichiers statiques
│       └── css/
│           └── style.css       # Styles personnalisés
├── requirements.txt             # Dépendances Python
├── run.py                      # Point d'entrée de l'application
├── .env                        # Configuration d'environnement
└── README.md                   # Ce fichier
```

## Base de données

L'application utilise SQLite par défaut, parfait pour le développement et les petites communautés. La base de données est créée automatiquement au premier lancement.

### Modèles de données :
- **User** : Utilisateurs connectés via Twitch
- **BookProposal** : Propositions de livres
- **VotingSession** : Sessions de vote
- **VoteOption** : Options de vote (livres)
- **Vote** : Votes individuels
- **ReadingSession** : Sessions de lecture programmées

## Configuration des administrateurs

Les administrateurs sont définis par leurs noms d'utilisateur Twitch dans le fichier `.env` :
```
ADMIN_TWITCH_USERNAMES=lantredesilver,wenyn,autre_admin
```

La première connexion d'un utilisateur listé comme administrateur lui donnera automatiquement les droits d'administration.

## Développement

### Modification des modèles de base de données
Si vous modifiez les modèles dans `models.py`, supprimez le fichier `biblioruche.db` pour que les tables soient recréées au prochain lancement.

### Ajout de nouvelles fonctionnalités
- Routes principales : `app/routes/main.py`
- Routes d'administration : `app/routes/admin.py`
- Nouveaux templates : `app/templates/`
- Styles : `app/static/css/style.css`

## Déploiement en production

Pour un déploiement en production :

1. Changez `FLASK_DEBUG=False` dans `.env`
2. Utilisez une base de données plus robuste (PostgreSQL recommandé)
3. Configurez un serveur web (nginx + gunicorn)
4. Utilisez HTTPS et mettez à jour l'URL de redirection Twitch

## Support

Cette application a été créée pour la communauté de l'Essaim Littéraire. Pour toute question ou suggestion d'amélioration, contactez LantreDeSilver.

## Licence

Projet créé pour la chaîne Twitch de Wenyn - L'Essaim Littéraire
