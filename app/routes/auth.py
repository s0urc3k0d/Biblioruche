from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, current_user
from app import db, login_manager, limiter
from app.models import User
import requests
import secrets
import urllib.parse
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth_bp.route('/login')
@limiter.limit("10 per minute")  # Limite les tentatives de connexion
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # Vérifier la configuration Twitch
    if not current_app.config.get('TWITCH_CLIENT_ID') or not current_app.config.get('TWITCH_CLIENT_SECRET'):
        flash('Configuration Twitch manquante. Veuillez contacter un administrateur.', 'error')
        logger.error('Configuration Twitch OAuth manquante')
        return redirect(url_for('main.index'))
    
    # Générer un state pour la sécurité OAuth
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state    # Paramètres pour l'authentification Twitch
    params = {
        'client_id': current_app.config['TWITCH_CLIENT_ID'],
        'redirect_uri': current_app.config['TWITCH_REDIRECT_URI'],
        'response_type': 'code',
        'scope': 'user:read:email',
        'state': state
    }
    
    auth_url = 'https://id.twitch.tv/oauth2/authorize?' + urllib.parse.urlencode(params)
    return redirect(auth_url)

@auth_bp.route('/callback')
@limiter.limit("10 per minute")
def callback():
    # Vérifications de base
    received_state = request.args.get('state')
    stored_state = session.get('oauth_state')
    
    # Vérifier s'il y a une erreur OAuth
    error = request.args.get('error')
    if error:
        error_description = request.args.get('error_description', 'Aucune description')
        flash(f'Erreur d\'authentification Twitch : {error_description}', 'error')
        logger.warning(f'Erreur OAuth Twitch: {error} - {error_description}')
        return redirect(url_for('main.index'))
    
    if not received_state or not stored_state or received_state != stored_state:
        flash('Erreur de sécurité OAuth. Veuillez réessayer.', 'error')
        logger.warning('Erreur de validation du state OAuth')
        return redirect(url_for('main.index'))
    
    code = request.args.get('code')
    if not code:
        flash('Erreur lors de l\'authentification avec Twitch.', 'error')
        logger.warning('Code OAuth manquant')
        return redirect(url_for('main.index'))
    
    # Échanger le code contre un token d'accès
    token_data = {
        'client_id': current_app.config['TWITCH_CLIENT_ID'],
        'client_secret': current_app.config['TWITCH_CLIENT_SECRET'],
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': current_app.config['TWITCH_REDIRECT_URI']
    }
    
    try:
        token_response = requests.post(
            'https://id.twitch.tv/oauth2/token', 
            data=token_data,
            timeout=10
        )
        token_response.raise_for_status()
    except requests.exceptions.Timeout:
        flash('Le serveur Twitch met trop de temps à répondre. Veuillez réessayer.', 'error')
        logger.error('Timeout lors de la requête de token Twitch')
        return redirect(url_for('main.index'))
    except requests.exceptions.ConnectionError:
        flash('Impossible de se connecter à Twitch. Vérifiez votre connexion internet.', 'error')
        logger.error('Erreur de connexion à Twitch')
        return redirect(url_for('main.index'))
    except requests.exceptions.HTTPError as e:
        flash('Erreur lors de l\'obtention du token d\'accès Twitch.', 'error')
        logger.error(f'Erreur HTTP Twitch token: {e.response.status_code} - {e.response.text}')
        return redirect(url_for('main.index'))
    except requests.exceptions.RequestException as e:
        flash('Une erreur inattendue s\'est produite avec Twitch.', 'error')
        logger.error(f'Erreur requête Twitch: {str(e)}')
        return redirect(url_for('main.index'))
    
    token_info = token_response.json()
    access_token = token_info.get('access_token')
    
    if not access_token:
        flash('Token d\'accès invalide reçu de Twitch.', 'error')
        logger.error('Token d\'accès manquant dans la réponse Twitch')
        return redirect(url_for('main.index'))
    
    # Obtenir les informations de l'utilisateur
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Client-Id': current_app.config['TWITCH_CLIENT_ID']
    }
    
    try:
        user_response = requests.get(
            'https://api.twitch.tv/helix/users', 
            headers=headers,
            timeout=10
        )
        user_response.raise_for_status()
    except requests.exceptions.Timeout:
        flash('Le serveur Twitch met trop de temps à répondre.', 'error')
        logger.error('Timeout lors de la requête utilisateur Twitch')
        return redirect(url_for('main.index'))
    except requests.exceptions.ConnectionError:
        flash('Impossible de récupérer vos informations Twitch.', 'error')
        logger.error('Erreur de connexion API utilisateur Twitch')
        return redirect(url_for('main.index'))
    except requests.exceptions.HTTPError as e:
        flash('Erreur lors de la récupération de vos informations Twitch.', 'error')
        logger.error(f'Erreur HTTP Twitch user: {e.response.status_code}')
        return redirect(url_for('main.index'))
    except requests.exceptions.RequestException as e:
        flash('Une erreur inattendue s\'est produite.', 'error')
        logger.error(f'Erreur requête utilisateur Twitch: {str(e)}')
        return redirect(url_for('main.index'))
    
    user_data_response = user_response.json()
    if not user_data_response.get('data'):
        flash('Aucune donnée utilisateur reçue de Twitch.', 'error')
        logger.error('Données utilisateur vides de Twitch')
        return redirect(url_for('main.index'))
    
    user_data = user_data_response['data'][0]
    
    # Vérifier si l'utilisateur existe déjà (par twitch_id d'abord, puis par username)
    user = User.query.filter_by(twitch_id=user_data['id']).first()
    
    if not user:
        # Chercher par username
        user = User.query.filter_by(username=user_data['login']).first()
        
        if user:
            # L'utilisateur existe par username mais sans twitch_id, on l'associe
            user.twitch_id = user_data['id']
            user.display_name = user_data['display_name']
            user.email = user_data.get('email')
            user.avatar_url = user_data['profile_image_url']
            
            # Vérifier si l'utilisateur est devenu admin
            if user_data['login'].lower() in [admin.lower() for admin in current_app.config['ADMIN_USERNAMES']]:
                user.is_admin = True
                
            db.session.commit()
            flash(f'Compte associé avec Twitch ! Bon retour, {user.display_name}!', 'success')
        else:
            # Créer un nouvel utilisateur
            is_admin = user_data['login'].lower() in [admin.lower() for admin in current_app.config['ADMIN_USERNAMES']]
            
            user = User(
                twitch_id=user_data['id'],
                username=user_data['login'],
                display_name=user_data['display_name'],
                email=user_data.get('email'),
                avatar_url=user_data['profile_image_url'],
                is_admin=is_admin
            )
            db.session.add(user)
            db.session.commit()
            
            flash(f'Bienvenue sur BiblioRuche, {user.display_name}!', 'success')
    else:
        # L'utilisateur existe déjà par twitch_id, mettre à jour les informations
        user.display_name = user_data['display_name']
        user.email = user_data.get('email')
        user.avatar_url = user_data['profile_image_url']
        
        # Vérifier si l'utilisateur est devenu admin
        if user_data['login'].lower() in [admin.lower() for admin in current_app.config['ADMIN_USERNAMES']]:
            user.is_admin = True
        
        db.session.commit()
        flash(f'Content de vous revoir, {user.display_name}!', 'success')
    
    login_user(user)
    
    # Nettoyer la session
    session.pop('oauth_state', None)
    
    # Rediriger vers la page suivante ou l'accueil
    next_page = request.args.get('next')
    return redirect(next_page) if next_page else redirect(url_for('main.index'))

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('main.index'))

