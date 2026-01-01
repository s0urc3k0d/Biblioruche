# Configuration Twitch pour BiblioRuche - Vérification urgente

## IMPORTANT : Vérification de l'URL de redirection

L'erreur de sécurité OAuth est probablement due à une mauvaise configuration de l'URL de redirection dans la console de développement Twitch.

### Étapes à suivre immédiatement :

1. **Aller sur la console de développement Twitch :**
   - https://dev.twitch.tv/console/apps

2. **Trouver votre application BiblioRuche**

3. **Vérifier/Modifier l'URL de redirection OAuth :**
   - **URL actuelle dans .env :** `http://127.0.0.1:5000/auth/callback`
   - **Doit être exactement :** `http://127.0.0.1:5000/auth/callback`

4. **Si l'URL était différente (par exemple localhost), la changer pour :**
   ```
   http://127.0.0.1:5000/auth/callback
   ```

5. **Sauvegarder les modifications dans la console Twitch**

### Test après modification :

1. Aller sur : http://127.0.0.1:5000/auth/test-session
2. Tester : http://127.0.0.1:5000/auth/login
3. Vérifier que la redirection fonctionne sans erreur de state

### Si l'erreur persiste :

- Effacer les cookies du navigateur pour 127.0.0.1:5000
- Redémarrer l'application Flask
- Vérifier les logs dans le terminal pour plus de détails

### URLs importantes :
- Application : http://127.0.0.1:5000
- Test session : http://127.0.0.1:5000/auth/test-session
- Login Twitch : http://127.0.0.1:5000/auth/login
- Diagnostic (nécessite admin) : http://127.0.0.1:5000/auth/diagnostic
