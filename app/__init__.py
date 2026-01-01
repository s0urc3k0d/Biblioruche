from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
import os

# Charger les variables d'environnement
load_dotenv()

# Initialiser les extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
      # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///biblioruche.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Mode debug
    app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Configuration des sessions
    app.config['SESSION_COOKIE_SECURE'] = False  # True en production avec HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 heure
    
    # Configuration Twitch OAuth
    app.config['TWITCH_CLIENT_ID'] = os.getenv('TWITCH_CLIENT_ID')
    app.config['TWITCH_CLIENT_SECRET'] = os.getenv('TWITCH_CLIENT_SECRET')
    app.config['TWITCH_REDIRECT_URI'] = os.getenv('TWITCH_REDIRECT_URI')
    
    # Administrateurs par défaut
    app.config['ADMIN_USERNAMES'] = os.getenv('ADMIN_TWITCH_USERNAMES', 'lantredesilver,wenyn').split(',')
    
    # Initialiser les extensions avec l'app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter avec Twitch pour accéder à cette page.'
    
    # Enregistrer les blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Créer les tables de base de données
    with app.app_context():
        db.create_all()
    
    return app
