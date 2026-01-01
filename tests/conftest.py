# -*- coding: utf-8 -*-
"""
Configuration pytest pour BiblioRuche
"""

import pytest
import os
import sys

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, BookProposal, Badge


@pytest.fixture(scope='session')
def app():
    """Crée une instance de l'application pour les tests"""
    # Configuration de test
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['SECRET_KEY'] = 'test-secret-key'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    
    app = create_app()
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    })
    
    # Créer les tables
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Client de test Flask"""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Session de base de données pour les tests"""
    with app.app_context():
        # Nettoyer avant chaque test
        db.session.rollback()
        
        # Vider les tables
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
        
        yield db.session
        
        # Nettoyer après chaque test
        db.session.rollback()


@pytest.fixture
def test_user(db_session):
    """Crée un utilisateur de test"""
    user = User(
        twitch_id='123456',
        username='testuser',
        display_name='Test User',
        email='test@example.com',
        avatar_url='https://example.com/avatar.png',
        is_admin=False
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def admin_user(db_session):
    """Crée un utilisateur admin de test"""
    user = User(
        twitch_id='789012',
        username='adminuser',
        display_name='Admin User',
        email='admin@example.com',
        avatar_url='https://example.com/admin.png',
        is_admin=True
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_book(db_session, test_user):
    """Crée un livre de test"""
    book = BookProposal(
        title='Test Book',
        author='Test Author',
        description='A test book description',
        proposed_by=test_user.id,
        status='approved'
    )
    db_session.add(book)
    db_session.commit()
    return book
