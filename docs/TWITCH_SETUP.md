# Configuration Twitch OAuth pour BiblioRuche

## Étapes pour configurer l'authentification Twitch

### 1. Créer une application Twitch
1. Allez sur https://dev.twitch.tv/console/apps
2. Connectez-vous avec votre compte Twitch
3. Cliquez sur "Register Your Application"

### 2. Remplir les informations de l'application
- **Name**: BiblioRuche (ou le nom de votre choix)
- **OAuth Redirect URLs**: `http://localhost:5000/auth/callback`
- **Category**: Website Integration
- **Client Type**: Confidential

### 3. Récupérer les identifiants
Après création, vous obtiendrez :
- **Client ID** : Visible immédiatement
- **Client Secret** : Cliquez sur "New Secret" pour le générer

### 4. Configurer le fichier .env
Copiez vos identifiants dans le fichier `.env` :

```env
TWITCH_CLIENT_ID=votre_client_id_ici
TWITCH_CLIENT_SECRET=votre_client_secret_ici
TWITCH_REDIRECT_URI=http://localhost:5000/auth/callback
```

### 5. Configurer les administrateurs
Dans le fichier `.env`, listez les noms d'utilisateur Twitch des administrateurs :

```env
ADMIN_TWITCH_USERNAMES=lantredesilver,wenyn,autre_admin
```

**Important** : 
- Utilisez les noms d'utilisateur Twitch exactement comme ils apparaissent (sensible à la casse)
- Séparez plusieurs administrateurs par des virgules sans espaces
- LantreDeSilver et Wenyn sont configurés par défaut

### 6. Test de la configuration
1. Lancez l'application avec `python run.py`
2. Allez sur http://localhost:5000
3. Cliquez sur "Connexion Twitch"
4. Vous devriez être redirigé vers Twitch pour autoriser l'application
5. Après autorisation, vous revenez sur BiblioRuche connecté

### Résolution de problèmes

**Erreur "Invalid redirect URI"** :
- Vérifiez que l'URL de redirection dans l'app Twitch est exactement `http://localhost:5000/auth/callback`
- Pas d'espace, pas de slash final

**Erreur "Invalid client"** :
- Vérifiez que le Client ID et Client Secret sont corrects dans le .env
- Vérifiez qu'il n'y a pas d'espaces avant/après les valeurs

**L'utilisateur n'est pas administrateur** :
- Vérifiez que le nom d'utilisateur Twitch est correctement orthographié dans ADMIN_TWITCH_USERNAMES
- Déconnectez-vous et reconnectez-vous pour que les droits soient mis à jour

### Production
Pour un déploiement en production :
1. Changez l'URL de redirection vers votre domaine : `https://votre-domaine.com/auth/callback`
2. Mettez à jour la configuration Twitch avec la nouvelle URL
3. Utilisez HTTPS obligatoirement en production
